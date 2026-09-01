# CPBL 逐球數據與主審判決分析系統

以中華職棒官方進階數據網的 Trackman 資料為來源，提供逐打席檢視、好球帶幾何判定、球路軌跡、誤判分析、主審評分卡與跨場次統計。

專案採用「本機完整分析、雲端靜態展示」的雙模式架構：

```text
本機：CPBL 資料 → collector → analyzer → SQLite → FastAPI → Vue
                                      │
                                      └→ 靜態 JSON → Vite build → gh-pages

線上：GitHub Pages → Vue + 已發布 JSON（沒有 Python、SQLite 或後端 API）
```

線上版預期網址：[https://hurst05.github.io/cpbl-umpire-scorecard/](https://hurst05.github.io/cpbl-umpire-scorecard/)

## 功能與模式差異

| 功能 | 本機模式 | GitHub Pages 靜態模式 |
| --- | --- | --- |
| 瀏覽已分析場次 | 支援 | 支援 |
| 輸入場次編號 | 可讀取快取，未收錄時即時抓取與分析 | 只能讀取已發布場次 |
| 依日期批次抓取 | 支援 | 不支援 |
| SQLite 讀寫 | 支援 | 不使用 |
| FastAPI `/api/*` | 使用 | 不使用 |
| 逐打席、好球帶與評分卡 | 支援 | 支援 |
| 跨場次摘要 JSON／CSV 匯出 | 支援 | 支援 |

所有 CPBL 抓取與分析只在本機進行。公開網站只包含前端檔案及匯出後的 JSON，因此不需要付費主機或常駐後端。

## 核心指標與分析原理

系統主審評分卡提供兩大維度的客觀評估，兩者具備明確且獨立的數學參照基準：

### 1. 準確率（Accuracy）與邊界容錯範圍（Tolerance）
- **參照基準**：官方規則好球帶邊界（包含本壘板 44cm 與打者身高標準化上下緣）。
- **計算方式**：判定與官方規則相符之判決球數 / 總球數。
- **邊界容錯範圍**：進壘球心距離好球帶邊界小於設定值（0～10 cm）時，視為主審人眼極限容許值，不計入實質誤判。

### 2. 判決一致性（Consistency）
- **參照基準**：**球與球之間的相對進壘位置**（衡量主審是否「雙標」）。
- **計算方式（Method A 鄰域球對比對法）**：
  - 採打者身高校正混合距離，比對全場距離 $\le 8.0\text{ cm}$（約一顆棒球寬）的鄰近球對。
  - 統計相近進壘點中「判決相同（同好或同壞）」的比例。
- **為什麼不受邊界容錯影響？**
  - 「邊界容錯」衡量的是**球與官方邊界的距離**（對與錯）。
  - 「一致性」衡量的是**球與球的相對矛盾**（同進壘點一好一壞）。
  - 即使一顆球離官方邊界很遠或很近，若主審在同一進壘點先判好球後判壞球，依然屬於實質執法矛盾，因此一致性不受邊界容錯滑桿干涉，維持客觀獨立。

## 環境需求

- Node.js 22 建議版本
- pnpm 11.9.0
- Python 3.12 以上
- [uv](https://docs.astral.sh/uv/)
- Git（發布 GitHub Pages 時需要）
- Windows PowerShell（目前的發布腳本使用 PowerShell）

確認工具：

```powershell
node --version
pnpm --version
python --version
uv --version
git --version
```

## 安裝

在 repository 根目錄執行：

```powershell
pnpm run setup
```

此命令會依序執行：

```text
pnpm install
uv sync
```

JavaScript dependency 安裝在 `node_modules/`，Python 虛擬環境由 uv 建立在 `.venv/`。

## 本機分析與開發

### 啟動前後端

```powershell
pnpm run dev
```

- 前端：http://127.0.0.1:5173/
- 後端：http://127.0.0.1:8000/
- 健康檢查：http://127.0.0.1:8000/api/health

Windows 也可以雙擊 `start.bat`。它會啟動前後端並自動開啟瀏覽器；關閉命令視窗即可停止服務。

若只需要其中一端：

```powershell
pnpm run dev:backend
pnpm run dev:frontend
```

### 分析單一場次

1. 執行 `pnpm run dev`。
2. 在網頁上方輸入 2026 年一軍例行賽場次編號，例如 `297`。
3. 按「搜尋」或 Enter。
4. 若 SQLite 已收錄，後端直接回傳快取。
5. 若尚未收錄，後端會從 CPBL 抓取資料、執行分析並存入 SQLite。

場次 ID 的完整格式為 `2026-A-{場次編號}`，例如 `2026-A-297`。

只有 CPBL 來源已有相應 Trackman 資料的場次才能完成分析。來源網站、網路連線或資料格式異常時，前端會顯示抓取失敗訊息。

### 依日期批次分析

1. 開啟「跨場次數據庫」。
2. 選擇日期。
3. 按「批次抓取此日賽事」。
4. 後端會處理該日已完賽且具有 Trackman 資料的比賽。
5. 完成後清單會顯示已存入 SQLite 的場次。

### 本機資料庫

SQLite 預設位置：

```text
data/cpbl_scorecard.db
```

資料庫及其 WAL／SHM 檔不進版控。需要備份分析結果時，先停止本機後端，再自行備份 `data/cpbl_scorecard.db`。

不要把 SQLite、cookie、token 或 CPBL 工作階段資訊放入公開靜態資料。

### 主要 API

| Method | 路徑 | 用途 |
| --- | --- | --- |
| GET | `/api/health` | 健康檢查 |
| GET | `/api/schedule?date=YYYY-MM-DD` | 取得指定日期賽程 |
| GET | `/api/game/{game_id}` | 取得快取或即時分析指定場次 |
| GET | `/api/game/sno/{sno}` | 依場次編號取得分析 |
| GET | `/api/games/cached` | 列出 SQLite 已收錄場次 |
| POST | `/api/batch-collect?date=YYYY-MM-DD` | 批次抓取並分析指定日期 |

## 靜態 JSON 資料

### 匯出

本機分析完成後執行：

```powershell
pnpm run export:static
```

匯出器會讀取 `data/cpbl_scorecard.db`，驗證所有場次資料，產生：

```text
.static-export/data/
  manifest.json
  games/
    2026-A-295.json
    2026-A-296.json
    ...
```

`manifest.json` 包含資料產生時間、預設場次及跨場次摘要；`games/` 保存每一場的完整分析資料。

`.static-export/` 是本機產物，已被 `.gitignore` 排除，不要提交到 `main`。

### 驗證與 production build

```powershell
pnpm run verify:static
```

此命令會：

1. 驗證 manifest schema、場次排序與檔案交叉連結。
2. 驗證所有 JSON 可解析且不含 `NaN`／Infinity。
3. 阻擋 SQLite、WAL、SHM、`.env` 等不應發布的檔案。
4. 執行 `vite build --mode static`。
5. 將已匯出的資料複製到 `dist/data/`。

只重新建置前端時可執行：

```powershell
pnpm run build:pages
```

`build:pages` 要求 `.static-export/data/` 已存在；若尚未匯出會直接失敗。

Static build 設定在 `.env.static`：

```dotenv
VITE_DATA_MODE=static
VITE_BASE_PATH=/cpbl-umpire-scorecard/
```

### 本機預覽 production build

```powershell
pnpm exec vite preview --host 127.0.0.1 --port 4174
```

開啟：

```text
http://127.0.0.1:4174/cpbl-umpire-scorecard/
```

預覽時建議確認：

- 預設場次正常載入。
- 跨場次清單顯示正確場次數及資料產生時間。
- 已發布場次可以切換。
- 未發布場次顯示「此場次尚未發布」。
- 靜態模式沒有批次抓取控制項。
- 瀏覽器沒有 `/api/*` request 或 console error。

## GitHub Pages 上線

### 第一次設定

1. 確認 `origin` 指向正確 repository：

   ```powershell
   git remote -v
   ```

2. 確認 Git commit identity 已設定：

   ```powershell
   git config user.name
   git config user.email
   ```

3. 先完成下方的 dry-run 與第一次正式發布；若遠端還沒有 `gh-pages`，發布腳本會建立該 branch。
4. 在 GitHub repository 開啟 **Settings → Pages**。
5. Source 選擇 **Deploy from a branch**，Branch 選擇 `gh-pages`，目錄選擇 `/ (root)`。

### 發布前 dry-run

Dry-run 會執行完整匯出、驗證、測試、lint 與 build，但不 commit 或 push：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/publish-pages.ps1 -DryRun
```

建議第一次上線及修改發布流程後都先執行 dry-run。

Windows 環境也可以直接雙擊或執行 `publish.bat`：它會先自動執行 dry-run 驗證，全部通過後再提示確認是否正式發布。

### 正式發布

```powershell
pnpm run publish:pages
```

發布流程依序執行：

1. 從本機 SQLite 匯出靜態 JSON。
2. 驗證靜態資料 contract。
3. 執行 Ruff。
4. 執行不含發布整合測試的 backend core suite。
5. 執行 frontend Node tests。
6. 執行完整 ESLint。
7. 建立 Vite static production bundle。
8. 再次驗證 `dist/data`。
9. 將 `dist/` 複製到臨時 Git checkout。
10. Commit 並 push 到 `origin/gh-pages`。

任一步驟失敗都會停止，不應更新線上版本。正式發布會推送 remote；執行前務必確認 `git remote -v`。

### 日常更新線上資料

每次有新場次時：

```text
1. pnpm run dev
2. 在本機 UI 抓取／分析新場次
3. 確認 SQLite 清單與評分卡
4. 執行發布 dry-run（建議）
5. pnpm run publish:pages
6. 開啟 GitHub Pages 確認最新場次與 generated_at
```

不需要把 `.static-export/`、`public/data/` 或 `dist/` commit 到 `main`；發布腳本只將完整 `dist/` 推到 `gh-pages`。

## 測試與程式品質

完整檢查：

```powershell
pnpm run test:backend
pnpm run test:frontend
pnpm run lint:py
pnpm exec eslint .
git diff --check
```

| 指令 | 說明 |
| --- | --- |
| `pnpm run test:backend` | 執行全部 Python tests，包含本機 Git 發布整合測試 |
| `pnpm run test:backend-core` | Publisher 內部使用；排除會呼叫 publisher 的整合測試，避免遞迴 |
| `pnpm run test:frontend` | 使用 Node 內建 test runner 驗證靜態資料邏輯 |
| `pnpm run lint:py` | Ruff 靜態檢查 |
| `pnpm run format:py` | Ruff 格式化 Python；使用前先確認不會擴大無關 diff |
| `pnpm exec eslint .` | Vue／JavaScript ESLint |

成功發布路徑的整合測試使用本機臨時 bare Git repository，不會推送真正的 `origin`。

## 常用指令速查

| 指令 | 用途 |
| --- | --- |
| `pnpm run setup` | 安裝 JavaScript 與 Python dependencies |
| `pnpm run dev` | 同時啟動 Vue 與 FastAPI |
| `pnpm run dev:frontend` | 只啟動 Vite |
| `pnpm run dev:backend` | 只啟動 FastAPI |
| `pnpm run start` | 啟動不含 reload 的 FastAPI，存在 `dist/` 時也會提供靜態檔案 |
| `pnpm run export:static` | SQLite → `.static-export/data` |
| `pnpm run verify:static` | 驗證 snapshot 並建立 static production build |
| `pnpm run build:pages` | 使用既有 snapshot 重新建立 `dist/` |
| `pnpm run publish:pages` | 完整檢查後發布 `dist/` 到 `gh-pages` |

## 目錄結構

```text
src/                         Vue 3 前端
src/components/              逐打席、好球帶、評分卡與跨場次元件
src/services/                API／靜態 JSON 資料介面與驗證
server/app.py                FastAPI routes
server/collector.py          CPBL 資料抓取
server/analyzer.py           好球帶與主審判決分析
server/db.py                 SQLite cache
server/export_static.py      SQLite → 靜態 JSON
server/verify_static.py      靜態資料 contract 驗證
scripts/publish-pages.ps1    本機 GitHub Pages 發布腳本
tests/                       Python tests
tests-js/                    Node tests
data/                        本機 SQLite，不進版控
.static-export/              本機靜態資料快照，不進版控
dist/                        Vite build，不進 main
docs/                        架構規格與後續強化任務
```

## 常見問題

### `Port 5173 is already in use`

已有另一個 Vite 開發伺服器。先關閉自己先前啟動的服務，或只啟動需要的前／後端。不要直接終止不確定來源的程序。

### 網頁顯示「目前沒有已發布之賽事資料」

Static build 找不到有效 manifest，或 SQLite 尚未匯出資料。重新執行：

```powershell
pnpm run export:static
pnpm run verify:static
```

### 網頁顯示「此場次尚未發布」

該場不在目前線上 manifest。回到本機模式抓取及分析該場，再重新發布。

### `publish:pages` 在 Git commit 階段失敗

檢查 Git identity、remote 與權限：

```powershell
git config user.name
git config user.email
git remote -v
```

### GitHub Pages 顯示 404 或資源路徑錯誤

確認 Pages 使用 `gh-pages` branch 的 `/ (root)`，且 `.env.static` 的 base path 為：

```text
/cpbl-umpire-scorecard/
```

## 文件

- [靜態 JSON 上雲規格](docs/spec-static-json-cloud.md)
- [第一輪實作計畫](docs/plan-static-json-cloud-remediation.md)
- [上線後強化任務](docs/task-static-json-cloud-post-launch-hardening.md)

## 注意事項

- CPBL 官方資料結構若改版，collector 或 analyzer 可能需要同步調整。
- 本工具的判定結果依目前資料與幾何規則產生，不代表聯盟官方判決。
- 請遵守來源網站的使用規範，避免高頻率或不必要的批次請求。
- 不要提交 SQLite、靜態匯出產物、token、cookie、`.env` 私密設定或其他本機資訊。

## 授權 (License)

本專案採用 [MIT License](LICENSE) 授權。

