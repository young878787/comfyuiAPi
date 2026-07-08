"""Service for AI prompt modification and ComfyUI generation SSE pipeline."""

import json
import logging
import random
import asyncio
from pathlib import Path
from typing import Optional, AsyncGenerator

from app.config import settings
from app.domain.models.prompt_template import get_template
from app.infrastructure.adapters.ai_adapter_factory import create_ai_adapter
from app.application.services.image_service import ImageService
from app.application.dtos.common import GenerateRequest

logger = logging.getLogger(__name__)


def get_workflow_path(workflow_name: str) -> Path:
    """Find the path of the workflow file based on workflow name."""
    workflow_dir = Path("workflow")
    name_lower = workflow_name.lower().strip()
    
    # Try to scan files
    if workflow_dir.exists():
        for f in workflow_dir.glob("*.json"):
            if f.stem.lower().strip() == name_lower:
                return f
            # Match with spaces removed
            if f.stem.lower().replace(" ", "") == name_lower.replace(" ", ""):
                return f
                
    # Fallback paths
    if "anima" in name_lower:
        return workflow_dir / "Anima.json"
    if "qwen" in name_lower:
        return workflow_dir / "qwen image.json"
        
    return workflow_dir / f"{workflow_name}.json"


def _strip_code_block(text: str) -> str:
    """Extract content from within a fenced code block, stripping the language identifier line."""
    text = text.strip()
    if not text.startswith("```"):
        return text
    # Remove opening fence
    lines = text.split("\n")
    # First line is ``` or ```text etc — skip it
    lines = lines[1:]
    # Remove closing fence if present
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _clean_prompt_text(text: str) -> str:
    """Remove stray markdown formatting and trim whitespace."""
    import re
    # Remove markdown bold/italic markers
    text = re.sub(r'\*{1,3}', '', text)
    # Remove markdown headers
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    # Remove lines that are purely Chinese/Japanese explanation (heuristic)
    cleaned_lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append(line)
            continue
        # Keep the line if it contains mostly ASCII/English content
        ascii_ratio = sum(1 for c in stripped if ord(c) < 128) / max(len(stripped), 1)
        if ascii_ratio > 0.3 or stripped.startswith(('masterpiece', 'best', 'score', 'A ', 'She ', 'He ', 'The ', 'Her ', 'His ')):
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()


def extract_final_prompt(response_text: str) -> str:
    """Extract the final prompt block from AI response."""
    # 1. Check for [FINAL_PROMPT] marker (primary path for Anima Builder)
    if "[FINAL_PROMPT]" in response_text:
        parts = response_text.split("[FINAL_PROMPT]")
        if len(parts) > 1:
            content = parts[-1].strip()  # Take the last [FINAL_PROMPT] block
            # Check for code block within the content
            if "```" in content:
                # Extract the code block content
                fence_parts = content.split("```")
                if len(fence_parts) >= 3:
                    # Content between first pair of fences
                    inner = fence_parts[1].strip()
                    lines = inner.split("\n")
                    # Skip language identifier line (e.g. 'text', 'plaintext')
                    if lines and (lines[0].strip().isalpha() or not lines[0].strip()):
                        return "\n".join(lines[1:]).strip()
                    return inner
                elif len(fence_parts) >= 2:
                    inner = fence_parts[1].strip()
                    lines = inner.split("\n")
                    if lines and (lines[0].strip().isalpha() or not lines[0].strip()):
                        return "\n".join(lines[1:]).strip()
                    return inner
            # No code block — clean and return the content directly
            return _clean_prompt_text(content)
            
    # 2. Look for "正向提示詞" or "positive prompt" block
    lower_text = response_text.lower()
    pos_idx = lower_text.find("正向提示詞")
    if pos_idx == -1:
        pos_idx = lower_text.find("positive prompt")
        
    if pos_idx != -1:
        sub_text = response_text[pos_idx:]
        code_idx = sub_text.find("```")
        if code_idx != -1:
            code_parts = sub_text[code_idx:].split("```")
            if len(code_parts) > 1:
                inner = code_parts[1].strip()
                lines = inner.split("\n")
                if lines and (lines[0].strip().isalpha() or not lines[0].strip()):
                    return "\n".join(lines[1:]).strip()
                return inner
                
    # 3. Fallback: Find the last code block (most likely the prompt)
    if "```" in response_text:
        parts = response_text.split("```")
        # Take the last code block (if there are multiple, the final one is usually the prompt)
        if len(parts) >= 3:
            inner = parts[-2].strip()
            lines = inner.split("\n")
            if lines and (lines[0].strip().isalpha() or not lines[0].strip()):
                return "\n".join(lines[1:]).strip()
            return inner
        elif len(parts) > 1:
            inner = parts[1].strip()
            lines = inner.split("\n")
            if lines and (lines[0].strip().isalpha() or not lines[0].strip()):
                return "\n".join(lines[1:]).strip()
            return inner
            
    # 4. Ultimate fallback: Clean and return the whole response
    return _clean_prompt_text(response_text)


class GenerateService:
    """AI prompt editor + ComfyUI image generator SSE pipeline service."""
    
    def __init__(self, image_service: ImageService):
        """Initialize service with ImageService."""
        self.image_service = image_service
        self.ai_adapter = None
        
    async def generate(self, request: GenerateRequest) -> AsyncGenerator[str, None]:
        """
        AI prompt modification + ComfyUI image generation streaming pipeline.
        
        Args:
            request: The generation request options
            
        Yields:
            str: SSE formatted text chunk (data: {json}\n\n)
        """
        # Validate request parameters
        # For text-to-image, prompt or idea must be provided.
        # For image-to-image/upscale, they can both be empty.
        if not request.prompt and not request.idea and not request.image_base64:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Prompt and Idea cannot both be empty.'})}\n\n"
            return
            
        attempts = max(1, min(5, request.attempts or 1))
        use_ai = bool(request.idea)
        
        # Resolve workflow file path
        workflow_path = get_workflow_path(request.workflow)
        if not workflow_path.exists():
            yield f"data: {json.dumps({'type': 'error', 'message': f'Workflow configuration file not found: {workflow_path.name}'})}\n\n"
            return
            
        ai_model = ""
        ai_provider = ""
        messages = []
        
        if use_ai:
            try:
                if not self.ai_adapter:
                    self.ai_adapter = create_ai_adapter()
                    
                ai_provider = settings.ai_provider
                ai_model = settings.google_model if ai_provider == "google" else settings.opencode_model
                
                # Fetch template name
                template_name = "anima" if "anima" in request.workflow.lower() else "qwen"
                template = get_template(template_name)
                system_prompt = template.system_prompt
                
                if request.prompt:
                    user_msg = (
                        f"原始提示詞：\n{request.prompt}\n\n"
                        f"想法：\n{request.idea}\n\n"
                        f"請根據以上原始提示詞與想法，按照規範輸出 [FINAL_PROMPT]。"
                    )
                else:
                    user_msg = (
                        f"想法：\n{request.idea}\n\n"
                        f"請根據以上想法，按照規範從零構建完整提示詞並輸出 [FINAL_PROMPT]。"
                    )
                    
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg}
                ]
            except Exception as e:
                logger.error("AI Adapter initialization failed", exc_info=True)
                yield f"data: {json.dumps({'type': 'error', 'message': f'AI prompt modification initialization failed: {str(e)}'})}\n\n"
                return

        seeds = []
        for i in range(attempts):
            if request.seed is not None and i == 0:
                seeds.append(request.seed)
            else:
                seeds.append(random.randint(1, 2**32 - 1))
                
        # Upload reference image if provided
        input_image_name = None
        if request.image_base64:
            try:
                import base64
                import time
                
                # Determine extension
                ext = "png"
                if request.image_mime_type:
                    if "jpeg" in request.image_mime_type or "jpg" in request.image_mime_type:
                        ext = "jpg"
                    elif "webp" in request.image_mime_type:
                        ext = "webp"
                
                filename = f"upscale_{int(time.time())}_{random.randint(1000, 9999)}.{ext}"
                image_bytes = base64.b64decode(request.image_base64)
                
                # Upload using comfyui_adapter from image_service
                upload_res = await self.image_service.comfyui_adapter.upload_image(image_bytes, filename)
                input_image_name = upload_res.get("name")
                logger.info(f"Uploaded reference image as {input_image_name} to ComfyUI")
            except Exception as e:
                logger.error("Failed to decode or upload reference image", exc_info=True)
                yield f"data: {json.dumps({'type': 'error', 'message': f'上傳參考圖片失敗: {str(e)}'})}\n\n"
                return

        # We use a queue to receive pipeline stage updates and results in real-time
        event_queue = asyncio.Queue()
        
        async def run_pipeline(attempt_num: int, temp: float, seed: int):
            # Stage 1: AI Prompt Modification
            if use_ai:
                await event_queue.put({
                    "type": "stage_update",
                    "attempt_num": attempt_num,
                    "stage": "ai"
                })
                try:
                    logger.info(f"Pipeline {attempt_num}: calling AI with temperature={temp:.2f}")
                    ai_response = await self.ai_adapter.generate_response(messages, temperature=temp)
                    extracted_prompt = extract_final_prompt(ai_response)
                    logger.info(f"Pipeline {attempt_num}: AI Prompt generated successfully: {extracted_prompt[:50]}...")
                except Exception as e:
                    logger.error(f"AI Prompt generation failed for pipeline {attempt_num}", exc_info=True)
                    await event_queue.put({
                        "type": "error",
                        "attempt_num": attempt_num,
                        "message": f"AI prompt modification failed: {str(e)}"
                    })
                    return
            else:
                extracted_prompt = request.prompt or ""

            # Stage 2: ComfyUI image generation
            await event_queue.put({
                "type": "stage_update",
                "attempt_num": attempt_num,
                "stage": "comfyui",
                "prompt": extracted_prompt
            })
            
            try:
                saved_path, metadata = await self.image_service.generate_image(
                    positive_prompt=extracted_prompt,
                    negative_prompt=request.negative_prompt or "",
                    width=request.width,
                    height=request.height,
                    steps=request.steps,
                    cfg=request.cfg,
                    seed=seed,
                    sampler=request.sampler,
                    scheduler=request.scheduler,
                    original_prompt=request.prompt or "",
                    user_idea=request.idea or "",
                    ai_model=ai_model,
                    ai_provider=ai_provider,
                    workflow_name=request.workflow,
                    workflow_path=str(workflow_path),
                    checkpoint=request.checkpoint,
                    input_image_name=input_image_name
                )
                await event_queue.put({
                    "type": "success",
                    "attempt_num": attempt_num,
                    "saved_path": saved_path,
                    "metadata": metadata,
                    "prompt": extracted_prompt
                })
            except Exception as e:
                logger.error(f"ComfyUI pipeline {attempt_num} failed", exc_info=True)
                await event_queue.put({
                    "type": "failure",
                    "attempt_num": attempt_num,
                    "error": str(e)
                })

        # Launch all pipelines concurrently
        for i in range(attempts):
            # Linearly scale temperature between 0.4 and 1.0
            if attempts > 1:
                temp = 0.4 + i * (1.0 - 0.4) / (attempts - 1)
            else:
                temp = 0.7
            
            seed = seeds[i]
            asyncio.create_task(run_pipeline(i + 1, temp, seed))

        # State tracking
        stages = {i: "pending" for i in range(1, attempts + 1)}
        results = {}
        completed_count = 0

        def make_status_message() -> str:
            ai_count = sum(1 for s in stages.values() if s == "ai")
            cui_count = sum(1 for s in stages.values() if s == "comfyui")
            done_count = sum(1 for s in stages.values() if s == "done")
            failed_count = sum(1 for s in stages.values() if s == "failed")
            
            parts = []
            if ai_count > 0:
                parts.append(f"AI 優化中 ({ai_count})")
            if cui_count > 0:
                parts.append(f"ComfyUI 繪圖中 ({cui_count})")
            if done_count > 0:
                parts.append(f"已完成 {done_count}")
            if failed_count > 0:
                parts.append(f"失敗 {failed_count}")
                
            return "⏳ " + " | ".join(parts) if parts else "⏳ 初始化任務..."

        # Initial progress message
        yield f"data: {json.dumps({'type': 'progress', 'completed': 0, 'total': attempts, 'message': make_status_message()})}\n\n"

        while completed_count < attempts:
            try:
                # Wait for next event or trigger heartbeat to keep SSE connection alive
                event = await asyncio.wait_for(event_queue.get(), timeout=1.5)
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'type': 'heartbeat', 'completed': completed_count, 'total': attempts, 'message': make_status_message()})}\n\n"
                continue

            num = event["attempt_num"]
            etype = event["type"]

            if etype == "stage_update":
                stages[num] = event["stage"]
                yield f"data: {json.dumps({'type': 'progress', 'completed': completed_count, 'total': attempts, 'message': make_status_message()})}\n\n"
            
            elif etype == "error":
                stages[num] = "failed"
                completed_count += 1
                results[str(num)] = {
                    "attempt_num": num,
                    "error": event["message"]
                }
                yield f"data: {json.dumps({'type': 'progress', 'completed': completed_count, 'total': attempts, 'message': make_status_message()})}\n\n"

            elif etype == "success":
                stages[num] = "done"
                completed_count += 1
                metadata = event["metadata"]
                results[str(num)] = {
                    "attempt_num": num,
                    "modified_prompt": event["prompt"],
                    "saved_paths": [event["saved_path"]],
                    "ai_metadata": {"model": ai_model, "provider": ai_provider} if use_ai else None,
                    "note": f"Seed: {metadata.seed}"
                }
                yield f"data: {json.dumps({'type': 'progress', 'completed': completed_count, 'total': attempts, 'message': make_status_message()})}\n\n"

            elif etype == "failure":
                stages[num] = "failed"
                completed_count += 1
                results[str(num)] = {
                    "attempt_num": num,
                    "error": event["error"]
                }
                yield f"data: {json.dumps({'type': 'progress', 'completed': completed_count, 'total': attempts, 'message': make_status_message()})}\n\n"

        # Final completed event
        yield f"data: {json.dumps({'type': 'done', 'results': results})}\n\n"




