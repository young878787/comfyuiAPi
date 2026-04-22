"""Configuration routes."""

from fastapi import APIRouter
from app.config import settings

router = APIRouter(prefix="/api/config", tags=["config"])

@router.get("")
async def get_config():
    """Get public application configuration."""
    
    # Determine default parameters based on prompt_template
    # Default is Qwen settings if not overridden by env
    steps = settings.default_steps
    cfg = settings.default_cfg
    negative_prompt = "EasyNegative, disconnected limbs, malformed limbs, Multiple people, (mutated hands and fingers:1.2), (extra arms:1.1), (poorly drawn face:1.1), malformed hands, grayscale, (poorly drawn hands:1.2), mutation, ugly, floating limbs, out of focus, normal quality, disfigured, lowres, blurry, worstquality, no_pupils"
    
    # If the user is using the Anima template, and hasn't explicitly changed defaults,
    # we should provide the Anima defaults.
    if settings.prompt_template.lower() == "anima":
        steps = 35
        cfg = 4.0
        negative_prompt = "worst quality, low quality, score_1, score_2, score_3, lowres, bad anatomy, bad hands, bad fingers, extra fingers, missing fingers, deformed hands, mutated hands, blurry, jpeg artifacts, watermark, signature, text, oldests, normal quality, low detail, bad drawing, deformed, disfigured, ugly, extra limbs, missing limbs, fused fingers, too many fingers, poorly drawn face, poorly drawn eyes, bad eyes"
        
    return {
        "template": settings.prompt_template,
        "default_steps": steps,
        "default_cfg": cfg,
        "default_width": settings.default_image_width,
        "default_height": settings.default_image_height,
        "default_sampler": settings.default_sampler,
        "default_scheduler": settings.default_scheduler,
        "default_negative_prompt": negative_prompt,
    }
