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
        )
