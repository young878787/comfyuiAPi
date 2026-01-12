# n8n Workflow 使用說明與範例

## 📋 Workflow 功能

這個 n8n workflow 提供完整的 ComfyUI AI Chat 整合，包含：

1. **自動 Session 管理**: 每天自動創建以日期命名的 Session
2. **智能聊天處理**: 發送訊息給 AI 並處理回應
3. **自動提示詞提取**: 從 AI 回應中提取 ComfyUI 提示詞
4. **圖片生成**: 自動調用 ComfyUI API 生成圖片
5. **結構化輸出**: 返回易於處理的 JSON 格式結果

---

## 🚀 快速開始

### 1. 導入 Workflow

1. 打開 n8n 介面
2. 點擊右上角 `⋮` → `Import from File`
3. 選擇 `n8n_workflow_complete.json`
4. 點擊 `Import`

### 2. 啟動 Workflow

1. 點擊 Workflow 右上角的 `Active` 開關
2. 記下 Webhook URL (例如: `http://localhost:5678/webhook/chat`)

### 3. 確保服務運行

```bash
# 確保在虛擬環境中
source .venv/bin/activate

# 啟動 Qwen3VL 服務 (終端 1)
cd qwen3vl_service && python main.py

# 啟動主服務 (終端 2)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📥 輸入格式

### 基本對話 (不生成圖片)

```bash
curl -X POST http://localhost:5678/webhook/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好，請介紹一下自己",
    "generate_image": false
  }'
```

### 對話 + 自動生圖

```bash
curl -X POST http://localhost:5678/webhook/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "設計一個賽博龐克風格的女戰士角色",
    "generate_image": true
  }'
```

### JSON 輸入欄位說明

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `message` | string | ✅ | 發送給 AI 的訊息內容 |
| `generate_image` | boolean | ❌ | 是否自動生成圖片 (預設: false) |

---

## 📤 輸出格式

### 範例 1: 純對話回應

**輸入**:
```json
{
  "message": "你好，請介紹一下自己",
  "generate_image": false
}
```

**輸出**:
```json
{
  "success": true,
  "session_id": "session_20251231_001",
  "message_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "ai_response": "嗨嗨！我是露西亞，一位熱愛動漫和角色設計的青少女設計師～✨\n\n我平常最喜歡做的事情就是把腦海中的各種角色構思變成實際的視覺作品...",
  "timestamp": "2025-12-31T10:30:45.123456",
  "image_generated": false
}
```

### 範例 2: 設計角色 + 生成圖片

**輸入**:
```json
{
  "message": "設計一個賽博龐克風格的女戰士角色",
  "generate_image": true
}
```

**輸出**:
```json
{
  "success": true,
  "session_id": "session_20251231_001",
  "message_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "ai_response": "## 設計概念\n\n哇！賽博龐克女戰士，這個主題超帥的！...\n\n---\n**ComfyUI 提示詞**\n\n**正向提示詞:**\n```\ncyberpunk female warrior, neon lights, futuristic armor...\n```",
  "timestamp": "2025-12-31T10:35:22.456789",
  "image_generated": true,
  "image_filename": "20251231_103530_1234567890.png",
  "image_url": "http://localhost:8000/api/image/view/session_20251231_001/20251231_103530_1234567890.png"
}
```

### 範例 3: 錯誤處理

**輸入**: (空訊息)
```json
{
  "message": "",
  "generate_image": false
}
```

**輸出**:
```json
{
  "success": false,
  "error": "Message cannot be empty",
  "status_code": 422
}
```

---

## 🔄 Workflow 流程詳解

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Webhook 接收訊息                                          │
│    輸入: { message, generate_image }                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. 列出所有 Session                                          │
│    GET /api/sessions                                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. 檢查今天的 Session                                        │
│    - 取得今天日期: 20251231                                  │
│    - 搜尋標題為 "20251231" 的 Session                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
              ┌───────┴────────┐
              │ Session 存在？  │
              └───────┬────────┘
                      │
          ┌───────────┼───────────┐
          │ 是                    │ 否
          ▼                       ▼
   ┌─────────────┐      ┌──────────────────┐
   │ 使用現有 ID │      │ 創建新 Session    │
   └─────────────┘      │ 標題: "20251231" │
          │             └──────────────────┘
          │                      │
          └──────────┬───────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. 發送聊天訊息                                              │
│    POST /api/chat/send                                      │
│    { session_id, message }                                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. 處理 AI 回應                                              │
│    - 提取 AI 回應內容                                        │
│    - 自動偵測是否包含 ComfyUI 提示詞                         │
│    - 提取正向/負向提示詞                                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
              ┌───────┴─────────┐
              │ 需要生成圖片？   │
              └───────┬─────────┘
                      │
          ┌───────────┼───────────┐
          │ 是                    │ 否
          ▼                       ▼
┌──────────────────┐        ┌──────────────┐
│ 6. 生成圖片      │        │ 跳過圖片生成  │
│ POST /api/image/ │        └──────────────┘
│      generate    │               │
└──────────────────┘               │
          │                        │
          └────────────┬───────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. 整合最終結果                                              │
│    - 組合 AI 回應                                            │
│    - 附加圖片資訊 (如果有)                                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. 返回結果                                                  │
│    輸出: { success, session_id, ai_response, image_url... } │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 實際應用場景

### 場景 A: Telegram Bot 整合

```
Telegram Trigger → 解析訊息 → 調用 Workflow → 回傳結果
```

**n8n 配置**:
1. 添加 **Telegram Trigger** 節點
2. 連接到你的 Workflow (移除 Webhook 節點)
3. 設定回應訊息格式

### 場景 B: Discord Bot 整合

```
Discord Trigger → 檢查指令 → 調用 Workflow → 發送嵌入訊息
```

### 場景 C: Slack Bot 整合

```
Slack Trigger → 解析 Slash Command → 調用 Workflow → 回覆
```

### 場景 D: 定時自動生成

```
Cron Trigger (每天早上) → 預設訊息 → 自動生圖 → 發送通知
```

---

## 🔧 自定義配置

### 修改 Session 命名規則

在 **"檢查今天的 Session"** 節點的程式碼中修改:

```javascript
// 原始: 20251231
const todayTitle = `${year}${month}${day}`;

// 改為: 2025-12-31
const todayTitle = `${year}-${month}-${day}`;

// 改為: Daily Chat 2025-12-31
const todayTitle = `Daily Chat ${year}-${month}-${day}`;
```

### 修改圖片生成參數

在 **"生成圖片 (API)"** 節點的 JSON Body 中修改:

```json
{
  "width": 1024,      // 改變寬度
  "height": 1024,     // 改變高度
  "steps": 20,        // 增加步數
  "cfg": 7.5,         // 調整 CFG
  "sampler": "euler_a"  // 更換採樣器
}
```

---

## 🐛 常見問題

### Q1: Webhook 返回 404

**原因**: Workflow 未啟動  
**解決**: 確認 Workflow 右上角的 `Active` 開關已打開

### Q2: Session 創建失敗

**原因**: 主服務 (8000) 未運行  
**解決**: 
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Q3: AI 回應超時

**原因**: Qwen3VL 服務 (8001) 未運行或模型載入中  
**解決**: 
```bash
cd qwen3vl_service && python main.py
```

### Q4: 圖片生成失敗

**原因**: ComfyUI (8188) 未運行  
**解決**: 啟動 ComfyUI 服務

### Q5: 提示詞提取失敗

**原因**: AI 回應格式不符合預期  
**解決**: 檢查 **"處理 AI 回應"** 節點的正則表達式

---

## 📊 效能建議

### 併發處理

如果需要處理多個請求，建議設定:

1. n8n 設定 → Executions → Concurrent Executions: 10
2. 使用 Queue Mode 避免請求阻塞

### 快取優化

可以在 Workflow 中添加快取節點:
- 快取今天的 Session ID (1 天)
- 避免重複查詢 Session 列表

### 錯誤重試

在每個 HTTP Request 節點設定:
- **繼續失敗**: 關閉
- **重試次數**: 3
- **重試間隔**: 1000ms

---

## 🔐 安全建議

1. **Production 環境**: 將 Webhook 改為需要認證
2. **Rate Limiting**: 添加頻率限制節點
3. **輸入驗證**: 檢查訊息長度和內容
4. **日誌記錄**: 記錄所有請求以便追蹤

---

## 📝 延伸功能

### 想添加更多功能？

1. **多語言支援**: 偵測輸入語言並自動切換
2. **情緒分析**: 分析用戶情緒並調整回應風格
3. **歷史查詢**: 查詢過去的對話記錄
4. **批量處理**: 一次處理多個設計請求
5. **圖片編輯**: 整合 Image Editing 功能

---

**文檔版本**: 1.0  
**最後更新**: 2025-12-31  
**支援**: RushiaMode Team
