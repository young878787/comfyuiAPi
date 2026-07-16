"""Image metadata domain model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ImageMetadata:
    """
    Image metadata entity.

    Attributes:
        filename: Image filename (e.g., img_001.png)
        positive_prompt: Positive prompt used for generation
        negative_prompt: Negative prompt used for generation
        width: Image width in pixels
        height: Image height in pixels
        steps: Number of sampling steps
        cfg: CFG scale value
        seed: Random seed used
        sampler: Sampler name
        scheduler: Scheduler name
        generated_at: Generation timestamp
        original_prompt: User's original input prompt
        user_idea: User's modifications/ideas for prompt
        final_prompt: AI modified/final prompt used
        ai_model: AI model used for editing
        ai_provider: AI provider used for editing
        workflow_name: Name of the workflow file used
        checkpoint: Name of the checkpoint model used
    """

    filename: str
    positive_prompt: str
    negative_prompt: str
    width: int
    height: int
    steps: int
    cfg: float
    seed: int
    sampler: str
    scheduler: str
    generated_at: datetime
    original_prompt: str = ""
    user_idea: str = ""
    final_prompt: str = ""
    ai_model: str = ""
    ai_provider: str = ""
    workflow_name: str = ""
    checkpoint: str = ""
    comfyui_filename: str = ""

    def to_dict(self) -> dict:
        """Convert metadata to dictionary."""
        return {
            "filename": self.filename,
            "positive_prompt": self.positive_prompt,
            "negative_prompt": self.negative_prompt,
            "width": self.width,
            "height": self.height,
            "steps": self.steps,
            "cfg": self.cfg,
            "seed": self.seed,
            "sampler": self.sampler,
            "scheduler": self.scheduler,
            "generated_at": self.generated_at.isoformat(),
            "original_prompt": self.original_prompt,
            "user_idea": self.user_idea,
            "final_prompt": self.final_prompt,
            "ai_model": self.ai_model,
            "ai_provider": self.ai_provider,
            "workflow_name": self.workflow_name,
            "checkpoint": self.checkpoint,
            "comfyui_filename": self.comfyui_filename,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ImageMetadata":
        """Create metadata from dictionary."""
        return cls(
            filename=data["filename"],
            positive_prompt=data["positive_prompt"],
            negative_prompt=data["negative_prompt"],
            width=data["width"],
            height=data["height"],
            steps=data["steps"],
            cfg=data["cfg"],
            seed=data["seed"],
            sampler=data["sampler"],
            scheduler=data["scheduler"],
            generated_at=datetime.fromisoformat(data["generated_at"]),
            original_prompt=data.get("original_prompt", ""),
            user_idea=data.get("user_idea", ""),
            final_prompt=data.get("final_prompt", ""),
            ai_model=data.get("ai_model", ""),
            ai_provider=data.get("ai_provider", ""),
            workflow_name=data.get("workflow_name", ""),
            checkpoint=data.get("checkpoint", ""),
            comfyui_filename=data.get("comfyui_filename", ""),
        )
