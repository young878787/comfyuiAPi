# ComfyUI AI Chat - 角色設計助手

基於 FastAPI + Vue 3 的 AI 角色設計對話與圖片生成系統，支援 GitHub Models / Google AI 多模態對話，並整合 ComfyUI 進行高品質圖片生成。

## 功能特色

- **AI 多模態對話** — 支援文字與圖片輸入，可附加圖片讓 AI 分析
- **圖片生成** — 透過 ComfyUI API 生成角色圖片，支援完整參數調整
- **Session 管理** — 多對話 Session，完整保存聊天記錄與生成圖片
- **思考過程顯示** — AI 的 `<thought>` 推理過程可折疊查看
- **Markdown 渲染** — AI 回覆支援完整 Markdown 格式

## 系統架構

```
FastAPI 後端 (port 8000)
└── 服務 Vue 3 SPA (frontend/dist/)
└── REST API (/api/...)

Vue 3 前端 (Vite 開發伺服器 port 3000，代理 /api → 8000)
├── /chat  — 對話頁面（支援圖片拖曳）
└── /draw  — 圖片生成頁面
```

## 系統需求

- Python 3.10+
- Node.js 18+（僅開發/建置時需要）
- ComfyUI 運行於 `http://127.0.0.1:8188`
- GitHub Models API Token **或** Google AI API Key

## 快速開始

### 1. 安裝 Python 依賴

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. 設定環境變數

```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

開啟 `.env`，至少填入以下必要項目：

```ini
# 選擇 AI 供應商："github" 或 "google"
AI_PROVIDER=github

# GitHub Models
GITHUB_API_TOKEN=your_github_token_here

# 或 Google AI
# GOOGLE_API_KEY=your_google_api_key_here
```

### 3. 確認 ComfyUI 已啟動

確保 ComfyUI 運行於 `http://127.0.0.1:8188`，並已載入所需模型。

---

## 啟動方式

### 方式一：生產模式（推薦）

先建置前端，再啟動後端。Frontend 由 FastAPI 直接服務。

```bash
# 1. 建置前端（首次或修改前端後執行）
cd frontend
npm install
npm run build
cd ..

# 2. 啟動後端
python app/main.py
```

訪問：`http://localhost:8000`

---

### 方式二：開發模式（前後端分離熱重載）

後端和前端分別啟動，支援雙向熱重載。

**終端 1 — 啟動後端**
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**終端 2 — 啟動前端開發伺服器**
```bash
cd frontend
npm install
npm run dev
```

訪問：`http://localhost:3000`（Vite 自動代理 `/api` → `http://localhost:8000`）

---

## 使用說明

1. **建立 Session** — 點擊左側邊欄的「+」新增對話
2. **AI 對話** (`/chat`) — 輸入訊息，可拖曳或附加圖片讓 AI 分析
3. **圖片生成** (`/draw`) — 填入提示詞，調整寬高/Steps/CFG/Sampler，點擊「生成圖片」
4. **查看歷史** — 點擊已生成圖片可全螢幕預覽，支援下載

## 專案結構

```
comfyuiAPi/
├── app/                        # Python 後端 (Clean Architecture)
│   ├── main.py                 # FastAPI 入口，服務 Vue SPA + API
│   ├── config.py               # Pydantic 設定
│   ├── application/
│   │   ├── services/           # 業務邏輯
│   │   └── dtos/               # 資料傳輸物件
│   ├── domain/
│   │   ├── models/             # 領域模型
│   │   └── exceptions.py
│   ├── infrastructure/
│   │   ├── adapters/           # AI 適配器（GitHub / Google / ComfyUI）
│   │   └── repositories/       # 資料儲存
│   └── presentation/
│       └── routes/             # API 路由
│
├── frontend/                   # Vue 3 + Vite 前端
│   ├── src/
│   │   ├── views/              # ChatView.vue, DrawView.vue
│   │   ├── components/         # SessionSidebar.vue, MessageBubble.vue
│   │   ├── stores/             # sessionStore.js（共享狀態）
│   │   ├── router/             # vue-router
│   │   └── utils/              # thoughtFilter.js
│   └── dist/                   # 建置輸出（gitignored，執行前需 npm run build）
│
├── workflow/                   # ComfyUI Workflow JSON
│   ├── qwen image.json         # 輕量模型（Steps=12, CFG=1.0）
│   └── Anima.json              # 動漫模型（Steps=35, CFG=4.0）
│
├── sessions/                   # Session 資料（gitignored）
├── logs/                       # 日誌（gitignored）
├── outputs/                    # 舊版輸出目錄（gitignored）
├── .env.example                # 環境變數範本
└── requirements.txt
```

## API 端點

### Session
| 方法 | 路徑 | 說明 |
|------|------|------|
| `POST` | `/api/sessions` | 建立 Session |
| `GET` | `/api/sessions` | 列出所有 Session |
| `GET` | `/api/sessions/{id}` | 取得 Session 詳情 |
| `PUT` | `/api/sessions/{id}/title` | 更新標題 |
| `DELETE` | `/api/sessions/{id}` | 刪除 Session |

### Chat
| 方法 | 路徑 | 說明 |
|------|------|------|
| `POST` | `/api/chat/send` | 發送訊息（支援 `image_base64` + `image_mime_type`）|
| `GET` | `/api/chat/history/{session_id}` | 取得聊天記錄 |

### Image
| 方法 | 路徑 | 說明 |
|------|------|------|
| `POST` | `/api/image/generate` | 呼叫 ComfyUI 生成圖片 |
| `GET` | `/api/image/view/{session_id}/{filename}` | 顯示圖片 |
| `GET` | `/api/image/download/{session_id}/{filename}` | 下載圖片 |
| `GET` | `/api/image/list/{session_id}` | 列出 Session 圖片 |

## 環境變數說明

完整範本見 `.env.example`。常用項目：

| 變數 | 說明 | 預設值 |
|------|------|--------|
| `AI_PROVIDER` | `github` 或 `google` | `github` |
| `GITHUB_API_TOKEN` | GitHub Models API Token | — |
| `GOOGLE_API_KEY` | Google AI API Key | — |
| `PROMPT_TEMPLATE` | `qwen` 或 `anima` | `qwen` |
| `COMFYUI_API_URL` | ComfyUI 地址 | `http://127.0.0.1:8188` |
| `APP_PORT` | 後端監聽 Port | `8000` |
| `FRONTEND_DIR` | Vue dist 目錄 | `./frontend/dist` |

## 故障排除

**ComfyUI 無法連線**
- 確認 ComfyUI 正在運行：`http://127.0.0.1:8188`
- 檢查 `COMFYUI_API_URL` 設定

**AI API 錯誤**
- 確認 API Token 有效且有配額
- 檢查 `AI_PROVIDER` 與對應的 Token 變數是否匹配

**前端顯示空白**
- 確認已執行 `npm run build`（生產模式）
- 或確認 Vite dev server 已啟動（開發模式）

**查看詳細錯誤**
```bash
cat logs/app.log
```

## 授權

MIT License
