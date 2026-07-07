# Anima Prompt Builder 標準規範（可重複使用 / 可由 SD Prompt 轉換）

版本：v1.0  
語言：繁體中文  
目的：建立一套 **可重複使用、可由 SD 舊式提示詞轉換、保持通用性** 的 Anima Prompt Builder 標準。

---

## 1. 目標

這份規範的重點不是只產生「一串 prompt」，而是建立一套 **可解析、可清洗、可重組、可擴充** 的提示詞標準，讓你的系統可以：

1. 吃入舊 SD / SDXL 類 prompt。
2. 自動分類 tag。
3. 清理冗餘與衝突。
4. 轉成 Anima 較穩定的輸出格式。
5. 保留角色、服裝、場景、風格的通用性。
6. 支援未來接 LoRA、角色資料庫、角色池召回、自然語言描述補強。

---

## 2. 核心設計原則

### 2.1 先結構化，再輸出
不要把 prompt 當一條純字串保存。  
內部標準應該先拆成欄位，最後才渲染為 prompt 字串。

### 2.2 分離「概念」與「表達」
同一個概念可能有多種輸出方式。
例如：
- 概念：角色 = 潤羽露西亞
- 表達 A：`uruha rushia, hololive`
- 表達 B：自然語言敘述她的髮色、髮型、服裝與氛圍

Builder 內部應保存 **概念層資料**，而不是只保存最後字串。

### 2.3 優先通用性，不綁死單一模型習慣
標準要能：
- 吃 booru / SD 類 tag
- 轉成 Anima 混合式 prompt
- 日後也能輸出為純 tag 版、混合版、角色召回版

### 2.4 限制冗餘
常見舊 prompt 問題：
- 品質詞過多
- 同義 tag 重複
- 具體與抽象 tag 疊太厚
- 角色名與外觀 tag 不一致

Builder 應有「去重 / 收斂 / 規範化」流程。

### 2.5 最終輸出以「tag + 自然語言」混合為主
對 Anima 類模型，推薦主格式不是純 booru 長串，而是：

**標準化 tag 區塊 + 1~4 句自然語言畫面描述**

---

## 3. 建議系統架構

```text
輸入層
  ├─ 原始 SD prompt
  ├─ 使用者補充需求
  ├─ 角色資料庫 / 服裝資料庫 / LoRA 設定
  └─ Builder 參數（輸出模式、風格強度、是否保留 LoRA trigger）

處理層
  ├─ Tokenize / split
  ├─ 去權重 / 解跳脫 / 正規化
  ├─ 分類到各 block
  ├─ 去重與衝突解決
  ├─ 補足缺失欄位
  └─ 產生自然語言描述

輸出層
  ├─ Canonical Structured Prompt（中介結構）
  ├─ Anima Hybrid Prompt
  ├─ Booru Tag Prompt
  └─ Debug / Compare / Trace 版本
```

---

## 4. Canonical Structured Prompt（內部標準格式）

建議你的 Builder 內部一律先轉成這種結構。

```yaml
meta:
  quality: [masterpiece, best quality]
  score: score_7
  safety: safe
  time_bias: newest
  resolution: highres

subject:
  count: 1girl
  solo: true

franchise:
  series: [hololive]
  copyright: []

character:
  name: uruha rushia
  variant: null
  aliases: []
  native_character_pool_confidence: high

appearance:
  hair_color: [mint green]
  hair_style: [short hair, double buns]
  eyes: []
  body: [flat chest]
  facial_features: [blush]

outfit:
  upper: [black cropped uniform jacket, button-up top]
  lower: [black loose pants, baggy pants]
  accessories: [black face mask, lapel pin, metallic badge]
  details: [silver buttons, leather trim, subtle red accents]
  exposed_features: [midriff, navel]

pose:
  posture: [standing]
  hands: [both hands resting on stomach]
  view: [slightly side-facing]
  gaze: [looking at viewer]
  expression: [soft blush, calm expression]

environment:
  location: [city street]
  time: [nighttime]
  ground: [wet ground, reflective pavement]
  props: [streetlights]
  atmosphere: [neon glow]

lighting:
  key: [cool ambient light]
  rim: [warm rim light]

style:
  medium: [anime coloring]
  composition: [cinematic, stylish]
  banned_style_name: []

extensions:
  lora_triggers: []
  keep_raw_special_tokens: []

natural_language:
  scene_summary: "A stylish anime illustration of Uruha Rushia standing on a wet neon-lit city street at night."
  action_summary: "She is turned slightly to the side while looking at the viewer, with both hands resting naturally on her stomach."
  outfit_summary: "She wears a black cropped uniform-style outfit with silver buttons, leather trim, and subtle red accents."
  mood_summary: "The scene feels cinematic and moody, with cool ambient night lighting and a warm rim light around her silhouette."
```

---

## 5. Prompt Block 標準順序

最終輸出時，建議固定順序。  
這樣方便閱讀、除錯、比較、做 A/B test。

### 5.1 標準順序

1. `meta`：品質 / 分數 / 安全 / 年代 / 解析度
2. `subject`：1girl / solo / 主體數量
3. `franchise`：作品 / 系列
4. `character`：角色名 / 版本名
5. `appearance`：髮色、髮型、眼睛、體型、臉部特徵
6. `outfit`：服裝、配件、材質、細節
7. `pose`：姿勢、視角、視線、手部動作、表情
8. `environment`：場景、時間、地面、背景元素
9. `lighting`：主光、邊光、氛圍光
10. `style`：上色、構圖、風格語氣
11. `natural_language`：整體畫面描述

---

## 6. Builder 輸出模式



### 6.2 Mode B：Anima Hybrid Mode（推薦預設）
適合：
- Anima 類模型
- 通用生成
- 可讀性與穩定性兼顧

格式：
```text
masterpiece, best quality, score_7, safe, newest, highres, 1girl, solo, uruha rushia, hololive, mint green hair, short hair, double buns, blush, black face mask, black cropped uniform jacket, button-up top, silver buttons, leather trim, lapel pin, metallic badge, midriff, navel, black loose pants, baggy pants, standing, both hands resting on stomach, slightly side-facing, looking at viewer, nighttime, city street, streetlights, neon glow, reflective pavement, wet ground, cool ambient light, warm rim light, anime coloring.

A stylish anime illustration of Uruha Rushia standing on a wet neon-lit city street at night. She is turned slightly to the side while looking at the viewer, with both hands resting naturally on her stomach. Her outfit is a black cropped uniform-style jacket with silver buttons, leather trim, a lapel pin, and a metallic badge, paired with loose black pants. The reflective pavement, neon glow, cool ambient lighting, and warm rim light create a cinematic and moody atmosphere.
```


---

## 7. SD Prompt → Anima Prompt 轉換規則

這是 Builder 最核心的一段。

### 7.1 基本流程

```text
原始 prompt
→ tokenize
→ normalize
→ classify
→ deduplicate
→ resolve conflicts
→ rebuild blocks
→ generate natural language
→ render final output
```

### 7.2 Normalize 規則

#### 規則 A：分隔符標準化
把以下格式統一視為 tag separator：
- 逗號 `,`
- 換行
- 多個空格

#### 規則 B：移除多餘空白
- trim
- 合併重複空白
- 移除空 token

#### 規則 C：跳脫字元還原
把：
- `\(` → `(`
- `\)` → `)`

但內部保存時應標記它原本是 literal tag，而非權重語法。

#### 規則 D：權重語法解析
例如：
- `(solo:1.3)` → tag = `solo`, weight = `1.3`
- `((blush))` → tag = `blush`, emphasis = `2x`

轉換到 Anima 時，預設做法：
- 不直接保留括號權重語法到最終 prompt
- 改以「保留概念 + 必要時提升 block 優先度」

也就是：
- `solo:1.3` → `solo`
- `((detailed eyes))` → `detailed eyes`

除非你的後端確定仍需要原始權重語法，才保留在 `extensions.keep_raw_special_tokens`。

---

## 8. 分類規則（Tag Classification）

Builder 要建立自己的字典或分類器，把 tag 分進固定欄位。

### 8.1 Meta 類
例：
- masterpiece
- best quality
- amazing quality
- score_7
- safe
- newest
- highres
- absurdres

### 8.2 Franchise / Copyright 類
例：
- hololive
- honkai: star rail
- blue archive

### 8.3 Character 類
例：
- uruha rushia
- march 7th (honkai: star rail)
- march 7th (preservation) (honkai: star rail)

### 8.4 Subject 類
例：
- 1girl
- 1boy
- solo
- multiple girls

### 8.5 Appearance 類
例：
- green hair
- short hair
- aqua eyes
- blush
- flat chest
- collarbone

### 8.6 Outfit 類
例：
- black jacket
- button-up
- silver buttons
- skirt
- black loose pants
- leather trim
- metallic badge

### 8.7 Pose / Expression 類
例：
- standing
- sitting
- hands on stomach
- looking at viewer
- from side
- open mouth
- one eye closed
- smile

### 8.8 Environment 類
例：
- outdoors
- city street
- nighttime
- wet ground
- reflective pavement
- streetlights

### 8.9 Lighting / Atmosphere 類
例：
- neon glow
- cool ambient light
- warm rim light
- dramatic lighting

### 8.10 Style 類
例：
- anime coloring
- painterly
- cinematic composition
- dynamic pose
- dynamic composition

### 8.11 Extension 類
例：
- LoRA trigger
- 自訂 token
- 模型私有 tag

例如：
- `rushia_blue`
- `<lora:rushia:0.8>`

---

## 9. 去重與收斂規則

這一段很重要，不然 prompt 會越轉越髒。

### 9.1 完全重複刪除
例：
- `shirt, shirt` → 保留一個
- `solo` 重複兩次 → 保留一個

### 9.2 具體詞優先於抽象詞
例：
- `white shirt` 與 `shirt` 同時存在
- `blue skirt` 與 `skirt` 同時存在

預設策略：
- 保留具體詞
- 視情況刪除過度泛化詞

建議規則：
- 如果具體詞存在，抽象父詞可刪除
- 若父詞可能提升召回率，可設為「保留模式」的可選項

### 9.3 同義品質詞收斂
例：
- masterpiece
- best quality
- amazing quality
- very aesthetic
- newest
- absurdres

建議預設只保留：
- `masterpiece`
- `best quality`
- `score_7`
- `safe`
- `newest`
- `highres`

可選保留：
- `very aesthetic`
- `absurdres`

不要讓品質詞佔 prompt 前段太多長度。

### 9.4 衝突詞處理
例：
- `short hair` 與 `long hair`
- `sitting` 與 `standing`
- `open mouth` 與 `mouth closed`

處理順序建議：
1. 角色資料庫優先
2. 使用者最新指示優先
3. 顯式權重較高者優先
4. 若無法判定，保留到 `debug.conflicts`

---

## 10. 自然語言生成規範

Anima Builder 的重點不是只有 tag，還要能穩定產生自然語言描述。

### 10.1 建議固定生成四句

1. **主體句**：誰、在哪裡、什麼時間
2. **姿勢句**：她怎麼站 / 坐 / 看 / 做什麼
3. **服裝句**：服裝、材質、關鍵細節
4. **氛圍句**：光線、情緒、畫面調性

### 10.2 模板

```text
A [style] anime illustration of [character] in [environment] at [time].
[Subject pronoun] is [pose/action], [view/gaze].
[Subject pronoun] wears [outfit summary] with [key accessory/details].
The scene is lit by [lighting], creating a [mood] atmosphere.
```

### 10.3 生成原則
- 不要和 tag 區完全逐字重複
- 要補 tag 難以表達的「關係」與「構圖」
- 優先描述：姿勢、視角、光線、情緒、物件互動
- 保持 2~4 句即可，不要寫成小說

---

## 11. 標準輸出模板

### 11.1 Canonical Markdown Template

```md
## Prompt Metadata
- mode: anima_hybrid
- character: uruha rushia
- series: hololive
- safety: safe
- score: score_7

## Prompt Tags
masterpiece, best quality, score_7, safe, newest, highres, 1girl, solo, uruha rushia, hololive, mint green hair, short hair, double buns, blush, black face mask, black cropped uniform jacket, button-up top, silver buttons, leather trim, lapel pin, metallic badge, midriff, navel, black loose pants, baggy pants, standing, both hands resting on stomach, slightly side-facing, looking at viewer, nighttime, city street, streetlights, neon glow, reflective pavement, wet ground, cool ambient light, warm rim light, anime coloring

## Natural Language Description
A stylish anime illustration of Uruha Rushia standing on a wet neon-lit city street at night. She is turned slightly to the side while looking at the viewer, with both hands resting naturally on her stomach. Her black cropped uniform-style outfit features silver buttons, leather trim, a lapel pin, and a metallic badge. The reflective pavement and neon lighting create a cinematic and moody atmosphere.

## Optional Extensions
- lora_triggers: none
- keep_raw_special_tokens: none
```

---

## 12. 實作規範（給 AI Builder / Agent）

如果你本來就有 AI 透過對話把 prompt 轉成指定形式，建議給它這組規範。

### 12.1 系統規則

1. 先解析使用者需求與原始 prompt。
2. 先產生中介結構，不要直接吐最終 prompt。
3. 把每個 tag 分類到標準 block。
4. 去除重複與衝突。
5. 缺少角色、姿勢、場景、光線時可根據上下文補足。
6. 最終輸出必須遵守固定順序。
7. 預設輸出為 Anima Hybrid Mode。
8. 若偵測到 LoRA trigger，放入 `extensions`，是否保留由參數控制。

### 12.2 Builder 參數建議

```yaml
builder_options:
  output_mode: anima_hybrid
  keep_lora_triggers: false
  keep_quality_overload: false
  preserve_generic_parent_tags: false
  generate_natural_language: true
  natural_language_sentence_count: 4
  use_character_database: true
  conflict_resolution_policy: user_then_character_db
  quality_profile: balanced
```

---

## 13. 最小可用規範（MVP）

如果你要先做簡版，最少只要做這幾件事：

1. 解析逗號分隔 prompt。
2. 把 tag 分到 8 大區塊：
   - meta
   - subject
   - franchise
   - character
   - appearance
   - outfit
   - pose
   - environment
3. 去重。
4. 固定順序輸出。
5. 自動補一段 2~4 句自然語言描述。

只要做到這裡，就已經比很多「直接把原 prompt 改寫」的做法更穩。

---

## 14. 建議不要做的事

### 不建議 1：直接保留所有原始 tag
這樣只會把 SD 舊 prompt 的髒訊息完整帶進 Anima。

### 不建議 2：品質詞無限制累加
過多品質詞常常沒有實質幫助，反而降低可讀性與可控性。

### 不建議 3：自然語言和 tag 完全重複
自然語言應該負責補「關係」與「構圖」，不是把 tag 再唸一次。

### 不建議 4：把每個 prompt 都綁死在單一角色或單一風格
Builder 標準要保留通用性，角色與風格應該是欄位，不是硬編碼。

---

## 15. 一句話總結這套標準

> 先把 SD prompt 結構化、分類、去重，再按照固定 block 順序輸出為「tag + 自然語言」的 Anima Hybrid Prompt。

---

## 16. 你之後可以直接延伸的方向

1. 角色資料庫：
   - 角色名
   - 作品名
   - 預設髮色髮型
   - 招牌服裝
   - 禁止衝突 tag

2. 風格資料庫：
   - 清淡上色
   - 厚塗
   - 偏動畫截圖
   - 偏插畫封面

3. 場景模板：
   - 夜晚城市
   - 教室窗邊
   - 室內展場
   - 雨後街道

4. Builder 評分：
   - tag 重複率
   - 衝突率
   - 自然語言覆蓋率
   - 角色一致性分數

這樣你的系統就會從「prompt 改寫器」升級成真正的 **Prompt Builder / Prompt Normalizer**。
