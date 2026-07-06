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


def extract_final_prompt(response_text: str) -> str:
    """Extract the final prompt block from AI response."""
    # 1. Check for [FINAL_PROMPT] marker
    if "[FINAL_PROMPT]" in response_text:
        parts = response_text.split("[FINAL_PROMPT]")
        if len(parts) > 1:
            content = parts[1].strip()
            if "```" in content:
                inner = content.split("```")[1].strip()
                lines = inner.split("\n")
                if lines and (lines[0].strip().isalpha() or not lines[0].strip()):
                    return "\n".join(lines[1:]).strip()
                return inner
            return content
            
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
                
    # 3. Fallback: Find the first code block
    if "```" in response_text:
        parts = response_text.split("```")
        if len(parts) > 1:
            inner = parts[1].strip()
            lines = inner.split("\n")
            if lines and (lines[0].strip().isalpha() or not lines[0].strip()):
                return "\n".join(lines[1:]).strip()
            return inner
            
    # 4. Ultimate fallback: Return the whole response
    return response_text.strip()


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
        if not request.prompt and not request.idea:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Prompt and Idea cannot both be empty.'})}\n\n"
            return
            
        attempts = max(1, min(5, request.attempts or 1))
        
        modified_prompts = []
        ai_model = ""
        ai_provider = ""
        
        use_ai = bool(request.idea)
        
        if use_ai:
            yield f"data: {json.dumps({'type': 'progress', 'completed': 0, 'total': attempts, 'message': '⏳ AI 修改提示詞中...'})}\n\n"
            
            try:
                if not self.ai_adapter:
                    self.ai_adapter = create_ai_adapter()
                    
                ai_provider = settings.ai_provider
                ai_model = settings.google_model if ai_provider == "google" else settings.github_model
                
                # Fetch template name
                template_name = "anima" if "anima" in request.workflow.lower() else "qwen"
                template = get_template(template_name)
                
                system_prompt = template.system_prompt
                
                if request.prompt:
                    user_msg = (
                        f"我希望修改以下正向提示詞：\n{request.prompt}\n\n"
                        f"我的修改想法 (Idea) 是：\n{request.idea}\n\n"
                        f"請幫我把這些想法融入提示詞中，並依照設計師規範生成。請特別注意：最後必須在一個獨立的代碼塊中，或者使用 `[FINAL_PROMPT]` 標記輸出最後可用於 ComfyUI 的英文正向提示詞（Positive Prompt），例如：\n[FINAL_PROMPT]\n(英文提示詞內容)"
                    )
                else:
                    user_msg = (
                        f"我的修改想法 (Idea) 是：\n{request.idea}\n\n"
                        f"請幫我根據這個想法自由發揮生成完整的提示詞，並依照設計師規範生成。請特別注意：最後必須在一個獨立的代碼塊中，或者使用 `[FINAL_PROMPT]` 標記輸出最後可用於 ComfyUI 的英文正向提示詞（Positive Prompt），例如：\n[FINAL_PROMPT]\n(英文提示詞內容)"
                    )
                    
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg}
                ]
                
                # Call AI adapter
                ai_response = await self.ai_adapter.generate_response(messages)
                extracted_prompt = extract_final_prompt(ai_response)
                
                logger.info("AI Prompt generated successfully", extra={"prompt": extracted_prompt})
                
                for _ in range(attempts):
                    modified_prompts.append(extracted_prompt)
                    
            except Exception as e:
                logger.error("AI Prompt generation failed", exc_info=True)
                yield f"data: {json.dumps({'type': 'error', 'message': f'AI prompt modification failed: {str(e)}'})}\n\n"
                return
        else:
            # Direct prompt mode
            for _ in range(attempts):
                modified_prompts.append(request.prompt)
                
        # Resolve workflow file path
        workflow_path = get_workflow_path(request.workflow)
        if not workflow_path.exists():
            yield f"data: {json.dumps({'type': 'error', 'message': f'Workflow configuration file not found: {workflow_path.name}'})}\n\n"
            return
            
        # Queue ComfyUI tasks
        results = {}
        completed_count = 0
        
        seeds = []
        for i in range(attempts):
            if request.seed is not None and i == 0:
                seeds.append(request.seed)
            else:
                seeds.append(random.randint(1, 2**32 - 1))
                
        # Launch generation tasks concurrently
        tasks = []
        for i in range(attempts):
            task = asyncio.create_task(
                self.image_service.generate_image(
                    positive_prompt=modified_prompts[i],
                    negative_prompt=request.negative_prompt or "",
                    width=request.width,
                    height=request.height,
                    steps=request.steps,
                    cfg=request.cfg,
                    seed=seeds[i],
                    sampler=request.sampler,
                    scheduler=request.scheduler,
                    original_prompt=request.prompt or "",
                    user_idea=request.idea or "",
                    ai_model=ai_model,
                    ai_provider=ai_provider,
                    workflow_name=request.workflow,
                    workflow_path=str(workflow_path)
                )
            )
            tasks.append((i + 1, task))
            
        yield f"data: {json.dumps({'type': 'progress', 'completed': 0, 'total': attempts, 'message': '⏳ ComfyUI 正在生成圖片...'})}\n\n"
        
        while completed_count < attempts:
            await asyncio.sleep(1.5)
            
            new_completed = 0
            for attempt_num, task in tasks:
                if task.done():
                    new_completed += 1
                    if str(attempt_num) not in results:
                        try:
                            saved_path, metadata = task.result()
                            results[str(attempt_num)] = {
                                "attempt_num": attempt_num,
                                "modified_prompt": modified_prompts[attempt_num - 1],
                                "saved_paths": [saved_path],
                                "ai_metadata": {"model": ai_model, "provider": ai_provider} if use_ai else None,
                                "note": f"Seed: {metadata.seed}"
                            }
                        except Exception as e:
                            logger.error(f"ComfyUI attempt {attempt_num} failed", exc_info=True)
                            results[str(attempt_num)] = {
                                "attempt_num": attempt_num,
                                "error": str(e)
                            }
                            
            if new_completed > completed_count:
                completed_count = new_completed
                yield f"data: {json.dumps({'type': 'progress', 'completed': completed_count, 'total': attempts, 'message': f'⏳ 已生成 {completed_count}/{attempts} 張圖片...'})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'heartbeat', 'completed': completed_count, 'total': attempts, 'message': '⏳ 生成中...'})}\n\n"
                
        # Final completed event
        yield f"data: {json.dumps({'type': 'done', 'results': results})}\n\n"
