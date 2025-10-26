# Qwen3VL API Service

獨立的 Qwen3-VL 推理服務，提供無狀態的 AI 生成 API。

## 特性

- ✅ **無狀態設計**: 每次請求都是獨立的，不保留歷史記錄
- ✅ **乾淨提示詞**: 調用方組合完整上下文後傳入，確保模型狀態乾淨
- ✅ **支援圖片**: 可上傳圖片進行視覺分析
- ✅ **易於調用**: 標準 REST API，任何語言都可調用
- ✅ **高性能**: 本地推理，無網路延遲
- ✅ **共用配置**: 與主服務共用 `.env` 配置檔

## 架構

```
Qwen3VL Service (Port 8001)
├─ /health                  健康檢查
├─ /generate                文字生成
└─ /generate-with-image     圖片 + 文字生成
```

## API 端點

### 1. 健康檢查

```bash
GET http://127.0.0.1:8001/health
```

**回應範例:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_name": "Qwen3-VL-4B-Thinking",
  "device": "cuda"
}
```

### 2. 文字生成

```bash
POST http://127.0.0.1:8001/generate
Content-Type: application/json

{
  "prompt": "<|system|>\n你是一位角色設計師\n<|end|>\n<|user|>\n請設計一個賽博龐克角色\n<|end|>\n<|assistant|>\n",
  "temperature": 0.7,
  "max_tokens": 2048,
  "top_p": 0.9
}
```

**回應範例:**
```json
{
  "content": "好的！這是一個賽博龐克風格的角色設計...",
  "model": "Qwen3-VL-4B-Thinking",
  "tokens_generated": 342,
  "generation_time": 5.23
}
```

### 3. 圖片 + 文字生成

```bash
POST http://127.0.0.1:8001/generate-with-image
Content-Type: multipart/form-data

prompt: "請描述這張圖片中的角色設計"
image: <file>
temperature: 0.7
max_tokens: 2048
```

**回應格式同上**

## 提示詞格式

為了確保模型狀態乾淨，調用方需要自行組合完整的提示詞，包含：

```
<|system|>
你的 system prompt
<|end|>

<|user|>
用戶訊息 1
<|end|>

<|assistant|>
AI 回應 1
<|end|>

<|user|>
用戶訊息 2
<|end|>

<|assistant|>
```

最後的 `<|assistant|>` 會觸發模型開始生成。

## Python 調用範例

```python
import httpx

async def call_qwen3vl(prompt: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://127.0.0.1:8001/generate",
            json={
                "prompt": prompt,
                "temperature": 0.7,
                "max_tokens": 2048
            },
            timeout=120.0
        )
        return response.json()

# 使用範例
result = await call_qwen3vl(
    "<|system|>\n你是助手\n<|end|>\n<|user|>\n你好\n<|end|>\n<|assistant|>\n"
)
print(result["content"])
```

## JavaScript 調用範例

```javascript
async function callQwen3VL(prompt) {
  const response = await fetch('http://127.0.0.1:8001/generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      prompt: prompt,
      temperature: 0.7,
      max_tokens: 2048
    })
  });
  
  return await response.json();
}

// 使用範例
const result = await callQwen3VL(
  "<|system|>\n你是助手\n<|end|>\n<|user|>\n你好\n<|end|>\n<|assistant|>\n"
);
console.log(result.content);
```

## 配置

服務從主專案的 `.env` 檔案讀取配置：

```env
# Qwen3VL Service
QWEN3VL_API_URL=http://127.0.0.1:8001
QWEN3VL_MODEL_PATH=AImodels/Qwen3-VL-4B-Thinking
QWEN3VL_SERVICE_PORT=8001
QWEN3VL_SERVICE_HOST=0.0.0.0
QWEN3VL_MAX_TOKENS=2048
QWEN3VL_TEMPERATURE=0.7
```

## 啟動方式

### 方式 1: 使用啟動腳本

```bash
./start_qwen3vl_service.sh
```

### 方式 2: 手動啟動

```bash
cd qwen3vl_service
source ../.venv/bin/activate
python main.py
```

## 性能優化

### GPU 記憶體優化
- 使用 `torch.float16` 減少顯存使用
- `device_map="auto"` 自動分配到多 GPU
- 支援 8 卡 RTX 2060 6GB 配置

### 延遲載入
- 模型在服務啟動時載入一次
- 後續請求直接使用已載入的模型
- 避免重複載入，提升回應速度

## 注意事項

1. **無狀態設計**: 服務不保存任何對話歷史，調用方需要自行管理上下文
2. **提示詞組合**: 調用方負責組合完整的提示詞（包含 system prompt 和對話歷史）
3. **超時設定**: 建議設定至少 120 秒的超時時間
4. **圖片格式**: 支援 PNG、JPG、WEBP 等常見格式
5. **並發處理**: 目前使用單線程，建議不要同時發送大量請求

## 與主服務的整合

主服務 (Port 8000) 會自動調用此服務進行 AI 推理：

```
用戶 → 主服務 (8000) → Qwen3VL 服務 (8001) → 返回結果
```

主服務負責：
- Session 管理
- 聊天歷史儲存
- 提示詞組合
- ComfyUI 圖片生成

Qwen3VL 服務負責：
- 純粹的 AI 推理
- 文字生成
- 圖片視覺分析

## 故障排除

### 模型載入失敗
- 檢查 `QWEN3VL_MODEL_PATH` 是否正確
- 確認模型檔案完整
- 查看 GPU 記憶體是否足夠

### 服務無回應
- 檢查 port 8001 是否被佔用
- 查看日誌輸出
- 嘗試重啟服務

### GPU 記憶體不足
- 減少 `max_tokens` 參數
- 使用更少的 GPU
- 考慮使用量化模型

## License

MIT
