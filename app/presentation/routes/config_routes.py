"""Configuration and status routes."""

import urllib.request
from fastapi import APIRouter
from typing import List, Dict, Any
from pathlib import Path

from app.config import settings
from app.application.dtos.common import StatusResponse, WorkflowInfo

router = APIRouter(tags=["config"])


def check_comfyui_status() -> bool:
    """Check if the ComfyUI server is online."""
    url = settings.comfyui_api_url
    try:
        # Try system-info endpoint first
        with urllib.request.urlopen(f"{url}/system-info", timeout=1.5) as resp:
            return resp.status == 200
    except Exception:
        # Fallback to root check
        try:
            with urllib.request.urlopen(url, timeout=1.5) as resp:
                return True
        except Exception:
            return False


def get_available_workflows() -> List[WorkflowInfo]:
    """Scan and list available workflows with default values."""
    workflow_dir = Path("workflow")
    workflows = []

    # Predefined configs
    anima_defaults = {
        "steps": 35,
        "cfg": 4.0,
        "width": 600,
        "height": 1328,
        "sampler": "dpmpp_2m_sde",
        "scheduler": "simple",
        "negative_prompt": "worst quality, low quality, score_1, score_2, score_3, lowres, bad anatomy, bad hands, bad fingers, extra fingers, missing fingers, deformed hands, mutated hands, blurry, jpeg artifacts, watermark, signature, text, oldests, normal quality, low detail, bad drawing, deformed, disfigured, ugly, extra limbs, missing limbs, fused fingers, too many fingers, poorly drawn face, poorly drawn eyes, bad eyes",
    }

    anima_upscale_defaults = {
        "steps": 14,
        "cfg": 5.0,
        "width": 1536,
        "height": 1536,
        "sampler": "er_sde",
        "scheduler": "sgm_uniform",
        "negative_prompt": "lowres, extra digit, fewer digits, worst quality, jpeg artifacts, signature, watermark, artist name, bad perspective, artistic error, bad proportions, disfigured, deformed body, malformed limbs, flat color, outline, nsfw, sepia, logo",
    }

    qwen_defaults = {
        "steps": 12,
        "cfg": 1.0,
        "width": 608,
        "height": 1328,
        "sampler": "dpmpp_2m_sde_gpu",
        "scheduler": "simple",
        "negative_prompt": "EasyNegative, disconnected limbs, malformed limbs, Multiple people, (mutated hands and fingers:1.2), (extra arms:1.1), (poorly drawn face:1.1), malformed hands, grayscale, (poorly drawn hands:1.2), mutation, ugly, floating limbs, out of focus, normal quality, disfigured, lowres, blurry, worstquality, no_pupils",
    }

    if workflow_dir.exists():
        for f in workflow_dir.glob("*.json"):
            name = f.stem.lower().replace(" ", "")
            if "放大" in name or "upscale" in name:
                workflows.append(
                    WorkflowInfo(
                        name=f.stem.lower().replace(" ", ""),
                        display_name="Anima 放大/圖生圖",
                        file=f.name,
                        defaults=anima_upscale_defaults,
                    )
                )
            elif "anima" in name:
                workflows.append(
                    WorkflowInfo(name="anima", display_name="Anima 動漫模型", file=f.name, defaults=anima_defaults)
                )
            elif "qwen" in name:
                workflows.append(
                    WorkflowInfo(name="qwen", display_name="Qwen Image 模型", file=f.name, defaults=qwen_defaults)
                )
            else:
                # Generic fallback for other workflows
                workflows.append(
                    WorkflowInfo(
                        name=f.stem.lower(),
                        display_name=f.stem,
                        file=f.name,
                        defaults={
                            "steps": 20,
                            "cfg": 7.0,
                            "width": 512,
                            "height": 512,
                            "sampler": "euler",
                            "scheduler": "normal",
                            "negative_prompt": "",
                        },
                    )
                )

    # Sort workflows to place default first
    default_wf = getattr(settings, "default_workflow", "anima")
    workflows.sort(key=lambda w: 0 if w.name == default_wf else 1)

    return workflows


@router.get("/api/config", response_model=StatusResponse)
async def get_config():
    """Get active workflows and application configs."""
    connected = check_comfyui_status()
    workflows = get_available_workflows()
    default_wf = getattr(settings, "default_workflow", "anima")

    return StatusResponse(
        connected=connected,
        comfyui_url=settings.comfyui_api_url,
        workflows=workflows,
        default_workflow=default_wf,
        ai_provider=settings.ai_provider,
    )


@router.get("/api/status")
async def get_status():
    """Query connection status of ComfyUI backend."""
    connected = check_comfyui_status()
    return {
        "status": "online" if connected else "offline",
        "connected": connected,
        "comfyui_url": settings.comfyui_api_url,
    }


@router.get("/api/comfyui/checkpoints", response_model=List[str])
async def get_comfyui_checkpoints():
    """代理 ComfyUI 接口，獲取所有可用的 Checkpoint (及 UNet 擴散模型) 列表"""
    import asyncio
    import json

    folders = ["checkpoints", "diffusion_models", "unet"]

    def fetch_folder(folder_name):
        url = f"{settings.comfyui_api_url}/models/{folder_name}"
        try:
            with urllib.request.urlopen(url, timeout=1.5) as resp:
                if resp.status == 200:
                    return json.loads(resp.read().decode("utf-8"))
        except Exception:
            pass
        return []

    async def get_all():
        tasks = [asyncio.to_thread(fetch_folder, f) for f in folders]
        results = await asyncio.gather(*tasks)
        merged = set()
        for r in results:
            if isinstance(r, list):
                merged.update(r)
        return sorted(list(merged))

    try:
        models = await get_all()
        if not models:
            models = ["JANIMA_v10.safetensors", "qwen_image_fp8_e4m3fn.safetensors"]
        return models
    except Exception:
        return ["JANIMA_v10.safetensors", "qwen_image_fp8_e4m3fn.safetensors"]
