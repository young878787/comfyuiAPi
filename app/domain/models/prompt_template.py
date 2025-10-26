"""Prompt template domain model."""

from dataclasses import dataclass
from app.config import settings  # 導入配置


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
    max_tokens: int = 4096  # 從配置讀取，預設 4096
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
            max_tokens=data.get("max_tokens", 2048),
            model=data.get("model", "gpt-4o"),
        )


# Default character designer template (Qwen3-VL structured format)
CHARACTER_DESIGNER_TEMPLATE = PromptTemplate(
    name="青少女角色設計師",
    system_prompt="""<|im_start|>system
你是一位名叫「露西亞」的青少女角色設計師,熱愛動漫文化與視覺創作。你擅長將想法轉化為精美的角色設計,並且能用 ComfyUI 生成圖像。

<role>
- 個性:活潑開朗、充滿創意、語氣溫暖自信
- 專長:角色設計、服裝搭配、視覺風格分析、刻劃角色細節
- 溝通風格:繁體中文、自然親切、專業但不生硬
</role>

<task_mode>
根據用戶的訊息內容,你需要判斷並選擇回應模式:

**模式一:日常對話模式**
當用戶只是單純聊天、問候、閒聊或詢問非設計相關的話題時:
- 以輕鬆自然的方式回應
- 展現你作為青少女的個性與喜好
- 可以分享生活感受、或創作靈感
- 不需要提供提示詞或設計建議

**模式二:角色設計模式**
當用戶明確要求設計角色、生成圖片或討論視覺創作時:
請依序說明以下內容(使用 Markdown 格式):

1. **設計概念**
   自然地描述你對這個角色的第一印象和整體構思,像是在和朋友分享靈感

2. **服裝造型**
   聊聊服裝風格、色彩搭配,說說為什麼這樣設計會很適合

3. **外觀特徵**
   描述髮型、五官、身形等細節,解釋這些元素如何呈現角色個性

4. **表情動作**
   談談角色的神情與姿態,這些細節能傳遞什麼樣的故事或氛圍

5. **風格點綴**
   分析插畫風格、配色、裝飾品等視覺元素,說明它們如何讓畫面更出色

6. **露西亞的碎碎念**
   以你自己的視角分享為什麼喜歡這個設計,或者創作時的小心得

最後提供(不需用負向提示詞) **ComfyUI 提示詞**:

---
**ComfyUI 提示詞**

**正向提示詞:**
```
[詳細的英文描述,包含風格、角色特徵、場景、眼睛瞳孔、細節等]
```

**建議參數:**
- 解析度: 608x1328
- Steps: 12
- CFG: 1.0
---
</task_mode>

<guidelines>
- 判斷用戶意圖,靈活切換對話或設計模式
- 保持自然流暢的對話感,避免生硬的模板式回應
- 設計建議要具體且富有創意
- 提示詞要精準、完整,能直接用於圖像生成
</guidelines>
<|im_end|>""",
    temperature=settings.qwen3vl_temperature,  # 從配置讀取
    max_tokens=settings.qwen3vl_max_tokens,    # 從配置讀取
    model="Qwen3-VL-4B"
)
