# ComfyUI AI Chat - 角色設計助手

基於 GitHub Models (GPT-4o) 和 ComfyUI 的 AI 圖像生成對話系統。

## 功能特色

- 📝 **AI 對話** - 與青少女角色設計師對話,獲得專業的角色設計建議
- 🎨 **圖片生成** - 使用 ComfyUI 生成高品質角色圖片
- 💾 **Session 管理** - 支援多個對話 Session,保存完整聊天記錄和圖片
- 🎯 **提示詞設計** - AI 返回結構化 Markdown 格式的設計說明和提示詞
- 🖼️ **圖片管理** - 本地儲存圖片,支援下載和查看歷史記錄

## 系統需求

- Python 3.10+
- ComfyUI (已運行在 127.0.0.1:8188)
- GitHub Models API Token

## 快速開始

### 1. 安裝依賴

```bash
# 創建虛擬環境(可選)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows

# 安裝依賴
pip install -r requirements.txt
```

### 2. 配置環境變數

```bash
# 複製環境變數範例
cp .env.example .env

# 編輯 .env 檔案,填入你的 GitHub API Token
nano .env
```

必須配置:
- `GITHUB_API_TOKEN` - 你的 GitHub Models API Token

### 3. 確保 ComfyUI 運行

確保 ComfyUI 已經在 `http://127.0.0.1:8188` 運行,並且已載入所需模型。

### 4. 啟動應用

```bash
# 開發模式(帶自動重載)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或直接運行
python app/main.py
```

### 5. 訪問應用

打開瀏覽器訪問: http://localhost:8000

## 使用方法

### 基本流程

1. **創建對話** - 點擊「+」創建新對話 Session
2. **與 AI 對話** - 描述你想設計的角色,AI 會提供專業建議和提示詞
3. **複製提示詞** - 從 AI 回應中複製提示詞
4. **切換到生圖面板** - 點擊「圖片生成」Tab
5. **貼上提示詞** - 貼上複製的提示詞,調整參數
6. **生成圖片** - 點擊「生成圖片」按鈕
7. **下載圖片** - 圖片生成後可直接下載

### Session 管理

- **創建**: 點擊左側邊欄的「+」按鈕
- **切換**: 點擊 Session 列表中的項目
- **編輯標題**: 點擊頂部的「編輯標題」按鈕
- **刪除**: 點擊「刪除」按鈕(會刪除所有訊息和圖片)

## API 端點

### Session API
- `POST /api/sessions` - 創建 Session
- `GET /api/sessions` - 獲取所有 Session
- `GET /api/sessions/{session_id}` - 獲取 Session 詳情
- `PUT /api/sessions/{session_id}/title` - 更新標題
- `DELETE /api/sessions/{session_id}` - 刪除 Session

### Chat API
- `POST /api/chat/send` - 發送訊息
- `GET /api/chat/history/{session_id}` - 獲取聊天歷史

### Image API
- `POST /api/image/generate` - 生成圖片
- `GET /api/image/view/{session_id}/{filename}` - 查看圖片
- `GET /api/image/download/{session_id}/{filename}` - 下載圖片
- `GET /api/image/list/{session_id}` - 獲取圖片列表

## 專案結構

```
app/
├── domain/              # 領域層 (實體和業務規則)
│   ├── models/          # 資料模型
│   └── exceptions.py    # 自訂異常
├── application/         # 應用層 (業務邏輯)
│   ├── services/        # 服務層
│   └── dtos/            # 資料傳輸物件
├── infrastructure/      # 基礎設施層 (外部服務)
│   ├── adapters/        # API 適配器
│   └── repositories/    # 資料儲存
└── presentation/        # 表現層 (API 和 UI)
    ├── routes/          # API 路由
    ├── templates/       # HTML 模板
    └── static/          # 靜態資源
```

## 配置說明

主要配置項(`.env`):

```bash
# GitHub Models API
GITHUB_API_TOKEN=your_token_here
GITHUB_MODEL=gpt-4o

# ComfyUI API
COMFYUI_API_URL=http://127.0.0.1:8188
COMFYUI_WORKFLOW_PATH=./workflow/qwen image.json

# 應用配置
APP_HOST=0.0.0.0
APP_PORT=8000
SESSION_STORAGE_PATH=./sessions
LOG_LEVEL=INFO

# 預設圖片參數
DEFAULT_IMAGE_WIDTH=608
DEFAULT_IMAGE_HEIGHT=1328
DEFAULT_STEPS=12
DEFAULT_CFG=1.0
```

## 🎨 UI/UX 和模組化系統

本專案採用現代的模組化設計架構,分離 AI 對話和圖片生成功能。

### 模組化組件

- **ChatModule** - 完全獨立的聊天模組
  - 消息管理和渲染
  - 事件系統
  - LocalStorage 持久化
  
- **ImageModule** - 完全獨立的圖片生成模組
  - 表單管理和驗證
  - 狀態持久化
  - 結果顯示

### 文檔資源

- 📖 [MODULAR_DESIGN.md](MODULAR_DESIGN.md) - 完整的模組化設計文檔
- 🔌 [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) - 集成指南和 API 參考
- 📋 [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 快速參考和程式碼片段
- 💡 [INTEGRATION_EXAMPLE.js](INTEGRATION_EXAMPLE.js) - 完整集成示例
- 📊 [MODULAR_SYSTEM_SUMMARY.md](MODULAR_SYSTEM_SUMMARY.md) - 系統完整總結

### UI 優化特點

- ✅ 無滾動佈局 - 所有內容一屏可見
- ✅ 響應式設計 - 支援桌面、平板、手機
- ✅ CSS 變數系統 - 輕鬆自訂主題
- ✅ 事件驅動架構 - 鬆散耦合的組件通信
- ✅ 性能優化 - CSS 精簡 25-33%

### 快速開始模組化

```javascript
// 初始化
const chat = new ChatModule({
    container: '#chat-panel'
});

const image = new ImageModule({
    container: '#image-panel'
});

// 監聽事件
document.addEventListener('messageSent', async (e) => {
    // 發送到後端...
});

document.addEventListener('generateImage', async (e) => {
    // 生成圖片...
});
```

## 開發指南

詳細的開發指引請參考: [github/copilot-instructions.md](github/copilot-instructions.md)

### 開發原則

- 遵循乾淨架構 (Clean Architecture)
- 使用 Type Hints
- 錯誤處理和日誌記錄
- 禁止在日誌中使用 emoji

### 測試

```bash
# 運行單元測試
pytest tests/unit/

# 運行整合測試
pytest tests/integration/

# 檢查程式碼風格
flake8 app/
black app/
```

## 故障排除

### ComfyUI 連線失敗
- 確認 ComfyUI 正在運行: http://127.0.0.1:8188
- 檢查防火牆設定
- 確認 workflow 檔案路徑正確

### GitHub Models API 錯誤
- 檢查 API Token 是否有效
- 確認網路連線正常
- 檢查 API 配額是否用盡

### 圖片生成失敗
- 檢查 ComfyUI 模型是否已載入
- 確認 workflow 節點配置正確
- 查看 logs/app.log 獲取詳細錯誤資訊

## 授權

MIT License

## 作者

RushiaMode Team

## 版本

1.0.0
