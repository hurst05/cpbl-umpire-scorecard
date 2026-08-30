# CPBL 逐球數據與主審判決分析系統

基於中華職棒官方進階數據網（`stats.cpbl.com.tw`）直接解析 Trackman 數據的好球帶幾何判定、打席時序還原與主審評分卡分析工具。

---

## 🛠️ 開發環境與套件管理

本專案全面採用現代高效能管理工具：
- **Python 環境與套件管理**：[`uv`](https://github.com/astral-sh/uv)
- **Node.js 前端套件管理**：[`pnpm`](https://pnpm.io/)

---

## 🚀 快速開始

### 1. 安裝依賴環境
```powershell
pnpm run setup
```
*(此指令會自動執行 `pnpm install` 與 `uv sync`)*

### 2. 啟動開發伺服器（前後端同步運行）
```powershell
pnpm run dev
```
或雙擊執行本機 `start.bat`。

- 前端介面：`http://127.0.0.1:5173/`
- 後端 API：`http://127.0.0.1:8000/`

---

## 📜 常用指令

| 指令 | 說明 |
| :--- | :--- |
| `pnpm run setup` | 一鍵安裝前後端所有依賴 (`pnpm install` + `uv sync`) |
| `pnpm run dev` | 同時啟動後端 FastAPI (8000) 與前端 Vite (5173) |
| `pnpm run dev:backend` | 僅啟動後端 API 伺服器 (支援自動熱重載) |
| `pnpm run dev:frontend` | 僅啟動前端 Vite 開發伺服器 |
| `pnpm run lint:py` | 透過 `uv run ruff` 檢查後端代碼品質 |
| `pnpm run format:py` | 透過 `uv run ruff` 自動格式化後端代碼 |
| `pnpm run test:backend` | 透過 `uv run pytest` 執行後端測試 |
