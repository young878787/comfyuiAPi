# 圖片上傳功能測試指南

## ✅ 已實作功能

### 1. **後端 API**
- ✅ 新增 `/api/chat/send-with-image` 端點
- ✅ 接受 `multipart/form-data` 格式上傳
- ✅ 支援 `session_id`, `message`, `image` 參數
- ✅ 圖片暫存到 `/tmp/qwen3vl_uploads/`
- ✅ 使用後自動清理臨時檔案

### 2. **ChatService 增強**
- ✅ 新增 `send_message_with_image()` 方法
- ✅ 整合 Qwen3VL 圖片分析 API
- ✅ 訊息 metadata 記錄圖片資訊
- ✅ 完整的錯誤處理和日誌記錄

### 3. **前端 UI**
- ✅ 圖片上傳按鈕 (📷 圖示)
- ✅ 檔案選擇對話框
- ✅ 圖片預覽顯示
- ✅ 移除圖片按鈕 (X)
- ✅ 拖拽上傳支援 (Drag & Drop)
- ✅ 視覺反饋 (拖拽高亮)

### 4. **互動流程**
```
用戶操作 → 選擇圖片 → 預覽顯示 → 輸入文字 → 發送
                ↓
         FormData 封裝 → /api/chat/send-with-image
                ↓
         ChatService.send_message_with_image()
                ↓
         存到 /tmp/ → Qwen3VL 分析 → 清理臨時檔案
                ↓
         返回 AI 回應 → 顯示在聊天區
```

## 🧪 測試步驟

### 測試 1: 按鈕上傳
1. 啟動服務 (Port 8000)
2. 打開瀏覽器訪問 `http://localhost:8000`
3. 點擊輸入框左側的 📷 圖片按鈕
4. 選擇一張圖片 (支援 jpg, png, gif 等)
5. 確認圖片預覽顯示在輸入框上方
6. 輸入文字訊息 (例如: "請分析這張圖片")
7. 點擊發送按鈕
8. 查看 AI 回應

### 測試 2: 拖拽上傳
1. 從檔案管理器拖拽圖片到聊天區域
2. 觀察輸入框變成紫色高亮
3. 釋放滑鼠，圖片應該顯示預覽
4. 輸入訊息並發送

### 測試 3: 移除圖片
1. 上傳圖片後點擊預覽右上角的 X 按鈕
2. 確認預覽消失
3. 發送訊息應該是純文字模式

### 測試 4: 檔案驗證
1. 嘗試上傳非圖片檔案 → 應該顯示錯誤
2. 嘗試上傳超過 10MB 的圖片 → 應該顯示錯誤

## 📊 預期結果

### 用戶訊息顯示
```
[圖片圖示] 已附加圖片
請分析這張圖片的內容
```

### AI 回應
模型會分析圖片並給出詳細回應，包含:
- 圖片內容描述
- 角色特徵分析
- 設計建議
- 提示詞生成 (如適用)

## 🔍 檢查點

### 後端日誌
```bash
# 查看 logs/app.log
grep "Image saved for analysis" logs/app.log
grep "AI response with image generated" logs/app.log
```

### 臨時檔案
```bash
# 確認檔案被清理
ls -la /tmp/qwen3vl_uploads/
# 應該是空的或只有當前正在處理的檔案
```

### 網路請求
在瀏覽器開發者工具 (F12) → Network 標籤:
- 查看 `/api/chat/send-with-image` 請求
- 確認 `Content-Type: multipart/form-data`
- 查看上傳的檔案大小

## 🎨 UI 樣式

### 圖片預覽區
- 背景: 粉紅色淡色 (`--bg-secondary`)
- 邊框: 2px 粉紅色
- 最大寬度: 200px
- 最大高度: 150px

### 拖拽高亮
- 背景變為淡紫色
- 虛線邊框效果

### 圖片按鈕
- 透明背景
- hover 時變粉紅色
- 點擊時縮放效果

## ⚠️ 注意事項

1. **確保 Qwen3VL 服務運行**: Port 8001 必須啟動
2. **顯存需求**: 圖片分析需要約 8-10GB 顯存
3. **處理時間**: 圖片分析比純文字慢 2-3 倍
4. **檔案限制**: 
   - 最大 10MB
   - 僅支援圖片格式
   - 自動清理臨時檔案

## 🐛 疑難排解

### 問題 1: 上傳後沒反應
- 檢查瀏覽器 Console 是否有 JavaScript 錯誤
- 確認 Network 請求是否成功
- 查看後端日誌

### 問題 2: AI 回應失敗
- 確認 Qwen3VL 服務正常運行
- 檢查 `/tmp/qwen3vl_uploads/` 權限
- 查看 `logs/app.log` 中的錯誤訊息

### 問題 3: 圖片預覽不顯示
- 確認圖片格式正確
- 檢查檔案大小
- 查看瀏覽器 Console

## 📝 技術細節

### API 接口
```python
@router.post("/send-with-image")
async def send_message_with_image(
    session_id: str = Form(...),
    message: str = Form(...),
    image: UploadFile = File(...)
)
```

### 前端上傳
```javascript
const formData = new FormData();
formData.append('session_id', currentSessionId);
formData.append('message', message);
formData.append('image', uploadedImage);

fetch('/api/chat/send-with-image', {
    method: 'POST',
    body: formData
})
```

### 臨時檔案命名
```
格式: {session_id}_{timestamp}_{original_filename}
範例: session_20251026_001_20251026_143022_character.png
```

---

**實作完成時間**: 2025-10-26  
**版本**: 1.0.0  
**狀態**: ✅ 已完成並測試
