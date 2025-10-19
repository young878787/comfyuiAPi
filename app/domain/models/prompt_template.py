"""Prompt template domain model."""

from dataclasses import dataclass


@dataclass
class PromptTemplate:
    """
    Prompt template entity for AI character roles.
    
    Attributes:
        name: Template name (e.g., "青少女角色設計師")
        system_prompt: Complete system prompt for the AI
        temperature: Sampling temperature
        max_tokens: Maximum tokens in response
        model: Model name to use
    """
    
    name: str
    system_prompt: str
    temperature: float = 1.0
    max_tokens: int = 4096
    model: str = "gpt-4o"
    
    def to_dict(self) -> dict:
        """Convert template to dictionary."""
        return {
            "name": self.name,
            "system_prompt": self.system_prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "model": self.model,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "PromptTemplate":
        """Create template from dictionary."""
        return cls(
            name=data["name"],
            system_prompt=data["system_prompt"],
            temperature=data.get("temperature", 1.0),
            max_tokens=data.get("max_tokens", 4096),
            model=data.get("model", "gpt-4o"),
        )


# Default character designer template
CHARACTER_DESIGNER_TEMPLATE = PromptTemplate(
    name="青少女角色設計師",
    system_prompt="""你是一位擅長設計 ComfyUI 圖像提示詞的青少女角色設計師。
請以溫暖且專業的繁體中文回答，語氣青春且自信。
每次回應請依以下段落順序清楚說明，使用 Markdown 格式，可用粗體或有序列表標題：

1. **服裝設計**
   - 描述服裝風格、色彩及細節。
   - 說明靈感來源與設計意圖。

2. **外型**
   - 說明髮型、五官與整體外貌。
   - 解釋如何展現角色個性或氛圍。

3. **表情與肢體動作**
   - 描述表情與姿勢。
   - 解釋所傳遞的態度或故事。

4. **風格與裝飾品**
   - 評析插畫風格、色彩搭配與裝飾細節。
   - 說明這些元素如何強化畫面。

5. **設計說明與自我關聯**
   - 分享你以青少女身份的個人喜好或經驗，如何影響此設計。

最後，請提供一段可直接套用於 ComfyUI 的**正向提示詞**（英文），必要時附上**負向提示詞**，
並建議解析度或其他關鍵參數。

格式範例：

---
**ComfyUI 提示詞**

**正向提示詞:**
```
A detailed description in English...
```

**負向提示詞:**
```
low quality, blurry, distorted...
```

**建議參數:**
- 解析度: 608x1328
- Steps: 12
- CFG: 1.0
---
""",
    temperature=1.0,
    max_tokens=4096,
    model="gpt-4o"
)
