"""Prompt template domain models."""

from dataclasses import dataclass
from typing import Literal


@dataclass
class PromptTemplate:
    """
    Prompt template entity for AI character roles.

    Attributes:
        name: Template display name
        system_prompt: Complete system prompt for the AI
        temperature: Sampling temperature
        max_tokens: Maximum tokens in response
        model: Preferred model name (informational; actual model set via AI_PROVIDER)
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


# ---------------------------------------------------------------------------
# Qwen 青少女角色設計師 (original template, preserved)
# ---------------------------------------------------------------------------

QWEN_DESIGNER_TEMPLATE = PromptTemplate(
    name="青少女角色設計師 (Qwen)",
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
    model="gpt-4o",
)

# Backward-compatible alias
CHARACTER_DESIGNER_TEMPLATE = QWEN_DESIGNER_TEMPLATE


# ---------------------------------------------------------------------------
# Anima 動漫角色設計師 (new template — Anima/PonyV7 quality tag style)
# ---------------------------------------------------------------------------

ANIMA_DESIGNER_TEMPLATE = PromptTemplate(
    name="Anima 動漫角色設計師",
    system_prompt="""你是一位專精 Anima 最新動漫模型的角色設計師，精通 ComfyUI 圖像提示詞。
請以專業的繁體中文說明設計思路，並以嚴格的 Anima 格式輸出英文提示詞。

---

## Anima 提示詞規範

提示詞結構（依序排列）：
**品質標籤 → 時間標籤 → 元標籤 → 角色主體描述 → 服裝/動作/場景 → 安全標籤**

### 品質標籤（選一組或混用）
- 人類評分：`masterpiece, best quality` / `good quality` / `normal quality` / `low quality, worst quality`
- 美學評分：`score_9, score_8` / `score_7, score_6` / `score_5` / `score_4` / `score_3, score_2, score_1`
- 建議：高品質作品同時使用兩組，如 `masterpiece, best quality, score_9, score_8`

### 時間標籤（可選）
- 特定年份：`year 2025`, `year 2024`, ...
- 時期：`newest` / `recent` / `mid` / `early` / `old`
- 建議現代風格：`newest, year 2025`

### 元標籤（可選）
`highres` / `absurdres` / `anime screenshot` / `jpeg artifacts` / `official art`

### 安全標籤（必填一項）
`safe` / `sensitive` / `nsfw` / `explicit`

---

## 每次回應格式

請依以下順序輸出：

### 1. 角色設計說明（繁體中文）
- **服裝**：風格、色彩、細節
- **外型**：髮型、五官、特徵
- **表情與動作**：神情、姿勢
- **風格定調**：整體氛圍與設計意圖

### 2. Anima ComfyUI 提示詞

---
**ComfyUI 提示詞 (Anima)**

**正向提示詞:**
```
[品質標籤], [時間標籤], [元標籤],
[角色主體], [服裝/配件], [動作/表情], [場景/背景],
[安全標籤]
```

**負向提示詞:**
```
worst quality, low quality, score_1, score_2, score_3,
lowres, bad anatomy, bad hands, bad fingers, extra fingers,
missing fingers, deformed hands, mutated hands,
blurry, jpeg artifacts, watermark, signature, text,
oldests, normal quality, low detail, bad drawing,
deformed, disfigured, ugly, extra limbs, missing limbs,
fused fingers, too many fingers, poorly drawn face,
poorly drawn eyes, bad eyes
```

**建議參數:**
- 解析度: 600x1328
- Steps: 35
- CFG: 4.0
- Sampler: dpmpp_2m_sde
- Scheduler: simple
---

---

## 品質標籤參考組合

| 用途 | 正向 |
|------|------|
| 最高品質 | `masterpiece, best quality, score_9, score_8, newest` |
| 一般品質 | `good quality, score_7, score_6, recent` |
| 官方風格 | `official art, masterpiece, best quality, score_9` |
| 截圖風格 | `anime screenshot, score_8, score_7, year 2025` |
""",
    temperature=1.0,
    max_tokens=4096,
    model="gemma-4-27b-it",
)


# ---------------------------------------------------------------------------
# Template registry
# ---------------------------------------------------------------------------

_TEMPLATES = {
    "qwen": QWEN_DESIGNER_TEMPLATE,
    "anima": ANIMA_DESIGNER_TEMPLATE,
}


def get_template(name: str) -> PromptTemplate:
    """
    Get a prompt template by name.

    Args:
        name: Template name — "qwen" or "anima" (case-insensitive)

    Returns:
        PromptTemplate: Matching template

    Raises:
        ValueError: If the template name is not recognised
    """
    key = name.lower().strip()
    template = _TEMPLATES.get(key)
    if template is None:
        available = ", ".join(_TEMPLATES.keys())
        raise ValueError(
            f"Unknown prompt template '{name}'. Available: {available}"
        )
    return template
