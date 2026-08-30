# Spec: 本機抓取分析與靜態 JSON 上雲（雙模式架構）

## Objective

將現有 CPBL 主審判決分析系統調整為雙模式架構：

1. **本機全功能模式（Local Mode）**
   - 完整保留 CPBL 官方資料即時抓取（`collector.py`）、判決分析（`analyzer.py`）、SQLite 讀寫（`db.py`）與 FastAPI（`app.py`）。
   - 前端保留輸入場次後隨選抓取未分析賽事，以及依日期批次抓取完賽賽事的既有操作。
2. **雲端靜態模式（Cloud Static Mode）**
   - GitHub Pages 只提供建置後的 Vue 應用與本機匯出的靜態 JSON。
   - 公開網站不執行 Python、FastAPI、即時抓取、分析或 SQLite 寫入。

所有 CPBL 抓取、解析與計算只在本機執行。本機完成分析後，以單一命令匯出、驗證、建置並發布靜態網站。公開訪客可以瀏覽所有已發布場次並使用既有互動功能，且不需要付費主機或常駐後端。

## Functional Requirements

### 1. 本機全功能模式

- 保留 FastAPI 路由：`/api/game/{game_id}`、`/api/game/sno/{sno}`、`/api/schedule`、`/api/games/cached`、`/api/batch-collect`。
- 輸入有效的 2026 年一軍場次編號時，如果 SQLite 尚未收錄，後端即時從 CPBL 擷取、分析並儲存。
- 「跨場次數據庫」保留依日期批次抓取的操作面板。
- 本機開發執行 `pnpm run dev` 時，前端資料來源固定為 `/api/*`。
- 本規格不新增 collector CLI；單場與批次抓取維持由既有 UI 與 FastAPI 提供。

### 2. 雲端靜態模式

- 正式網站不向 `/api/*` 發送任何請求，只讀取站內靜態資源。
- 首頁讀取完整 `manifest.json`，驗證 `schema_version`，並依 `default_game_id` 載入預設場次。
- 使用者可以依場次編號載入已發布的 2026 年一軍比賽。
- 未發布場次回傳 404 時，顯示「此場次尚未發布」，不嘗試線上抓取或分析。
- 逐打席、好球帶、球路軌跡、主審評分卡、容錯範圍、誤判篩選、得利球隊及同場相似球維持既有行為。
- 跨場次頁面使用 manifest 呈現已發布場次，保留載入分析、匯出摘要 JSON 與匯出 CSV。
- 靜態模式不顯示批次抓取控制項，原位置改為唯讀的資料產生時間與已發布場次數量；本機模式仍顯示完整操作面板。
- schema 不相容、manifest 損壞或場次 JSON 損壞時，顯示可理解的錯誤，不呈現半套資料。

## Architecture & Data Flow

```text
[ 本機 Local Mode ]
CPBL 官方網站 ──> collector.py ──> analyzer.py ──> db.py (SQLite)
                                                    │
                                                    ▼
                                             FastAPI (/api/*)
                                                    │
                                                    ▼
                                             Vue 3 本機 UI

═══════════════════════ 發布分界線 ═══════════════════════

[ 本機發布 Static Publish ]
SQLite ──> export_static.py ──> 暫存 JSON ──> 驗證 ──> Vite build
                                                            │
                                                            ▼
                                                  dist/ 靜態產物
                                                            │
                                              push dist only │
                                                            ▼
                                                    gh-pages 分支
                                                            │
                                                            ▼
                                                    GitHub Pages
```

## Frontend Data Abstraction

前端透過 `src/services/dataService.js` 隔離資料來源。模式使用明確的 `VITE_DATA_MODE`，未設定時才依 Vite 開發狀態選擇預設值；無效值必須立即報錯。

```js
const dataMode = import.meta.env.VITE_DATA_MODE
  || (import.meta.env.DEV ? 'api' : 'static')

if (!['api', 'static'].includes(dataMode)) {
  throw new Error(`Unsupported data mode: ${dataMode}`)
}

export async function fetchManifest() {
  if (dataMode === 'static') {
    const response = await fetch(`${import.meta.env.BASE_URL}data/manifest.json`)
    if (!response.ok) throw new Error(`載入 manifest 失敗: ${response.status}`)

    const manifest = await response.json()
    if (manifest.schema_version !== 1 || !Array.isArray(manifest.games)) {
      throw new Error('靜態資料版本不相容')
    }
    return manifest
  }

  const response = await fetch('/api/games/cached')
  if (!response.ok) throw new Error(`載入本機賽事失敗: ${response.statusText}`)
  const games = await response.json()
  return {
    schema_version: 1,
    generated_at: null,
    default_game_id: games[0]?.game_id ?? null,
    games
  }
}

export async function fetchGame(gameId) {
  const encodedGameId = encodeURIComponent(gameId)
  const url = dataMode === 'static'
    ? `${import.meta.env.BASE_URL}data/games/${encodedGameId}.json`
    : `/api/game/${encodedGameId}`
  const response = await fetch(url)

  if (dataMode === 'static' && response.status === 404) return null
  if (!response.ok) throw new Error(`載入場次失敗: ${response.status}`)
  return response.json()
}

export async function runBatchCollect(date) {
  if (dataMode === 'static') {
    throw new Error('靜態模式不支援批次抓取')
  }
  const response = await fetch(
    `/api/batch-collect?date=${encodeURIComponent(date)}`,
    { method: 'POST' }
  )
  if (!response.ok) throw new Error(`批次抓取失敗: ${response.statusText}`)
  return response.json()
}
```

UI 不直接判斷 hostname，也不在元件中自行組合 `/api/*` 或靜態資料 URL。模式差異集中在 data service；元件只處理成功資料、未發布狀態及錯誤狀態。

## Data Contract

正式站發布以下靜態資料：

```text
data/
  manifest.json
  games/
    2026-A-295.json
    2026-A-296.json
```

### 1. `manifest.json`

```json
{
  "schema_version": 1,
  "generated_at": "2026-08-30T22:30:00+08:00",
  "default_game_id": "2026-A-295",
  "games": [
    {
      "game_id": "2026-A-295",
      "game_sno": 295,
      "game_date": "2026-08-29",
      "field": "臺北大巨蛋",
      "visiting_team": "中信兄弟",
      "home_team": "味全龍",
      "visiting_score": 3,
      "home_score": 2,
      "hp_umpire": "張展榮",
      "overall_acc": 92.5,
      "ball_acc": 94.1,
      "strike_acc": 89.8,
      "missed_count": 11
    }
  ]
}
```

規則：

- `schema_version` 固定為整數 `1`；變更 contract 前必須先更新規格。
- `generated_at` 使用含時區的 ISO 8601 時間。
- `games` 依 `game_date`、`game_sno` 由新到舊排列。
- `default_game_id` 是 `games` 第一筆；空資料庫時為 `null`。
- manifest 中每個 `game_id` 必須有對應且可解析的場次檔。

### 2. `games/{game_id}.json`

保持目前 `GET /api/game/{game_id}` 回傳的完整結構與語意：

```json
{
  "game_info": {},
  "umpire_metrics": {},
  "plate_appearances": [],
  "all_called_pitches": []
}
```

JSON 使用 UTF-8 並保留中文，不允許 `NaN`、`Infinity` 或 `-Infinity`。不得輸出 SQLite、WAL、token、cookie 或其他本機資訊。

## Deployment Strategy

- `main` 分支只保存原始碼、測試、文件與發布工具；`data/*.db`、暫存匯出資料、`public/data/` 及 `dist/` 不進版控。
- `pnpm run publish:pages` 必須在本機執行，因為只有本機能存取 SQLite。
- 發布命令依序執行匯出、驗證、Ruff、pytest、ESLint、Vite static build，任一步驟失敗即停止。
- 資料先產生於工作區內的暫存目錄並完整驗證；建置時才將已驗證資料放入 `dist/data/`。
- 發布命令只將完整 `dist/` 推送到專用 `gh-pages` 分支，不把產物提交到 `main`。
- GitHub Pages 設定為從 `gh-pages` 分支根目錄發布，project site base path 固定為 `/cpbl-umpire-scorecard/`。
- 每次成功發布在 `gh-pages` 產生一個 commit；回滾方式是重新發布指定的既有 commit 內容。
- 不依賴遠端 workflow 重新產生資料。若 GitHub Pages 內部觸發 `pages-build-deployment`，它只負責託管已推送的靜態產物。

### 一致性邊界

匯出器不嘗試在 Windows 上以單一 directory rename 取代非空目錄。它必須：

1. 在新的暫存目錄產生全部場次 JSON 與 manifest。
2. 對暫存目錄執行完整 contract 與交叉連結驗證。
3. 讓 Vite build 與發布流程只讀取這份已驗證快照。
4. 完整 build 成功後才更新 `gh-pages`；失敗時不 push，因此既有線上版本不受影響。

## Tech Stack

- 前端：Vue 3.5、Vite 6、Tailwind CSS 4、Lucide Vue Next
- 本機後端：Python 3.12、FastAPI、Uvicorn、SQLite
- 本機工具：現有 collector、analyzer、db，加上 Python 標準庫實作的靜態匯出與驗證工具
- 雲端：GitHub Pages，base path `/cpbl-umpire-scorecard/`
- 除非實作時證明必要且先取得同意，不新增 npm 或 Python runtime dependency

## Commands

### 既有本機命令

```powershell
pnpm run setup
pnpm run dev
pnpm run dev:frontend
pnpm run dev:backend
pnpm run test:backend
pnpm run lint:py
pnpm exec eslint .
pnpm exec vite build
```

### 新增目標命令

```powershell
# 從本機 SQLite 產生並驗證一份暫存靜態資料快照
pnpm run export:static

# 驗證靜態 contract、檔案交叉連結與 GitHub Pages production build
pnpm run verify:static

# 匯出、執行所有品質檢查、建置並推送 dist 到 gh-pages
pnpm run publish:pages
```

命令必須可從 Windows PowerShell 執行並在失敗時回傳非零 exit code。`publish:pages` 不得在任何驗證失敗後繼續 push。static production build 使用 Vite mode（例如 `vite build --mode static`）載入 `VITE_DATA_MODE=static` 與 Pages base path；不得依賴 Windows 專用的 inline environment variable 語法。

## Project Structure

```text
src/                          Vue 應用原始碼
src/services/dataService.js   API／靜態 JSON 雙模式資料介面
src/components/               現有 UI 元件
server/                       本機後端、抓取器、分析器與匯出工具
server/export_static.py       從 SQLite 產生靜態資料快照
server/verify_static.py       驗證 contract 與檔案交叉連結
scripts/publish-pages.ps1     本機品質檢查、建置與 gh-pages 發布流程
tests/test_analyzer.py        既有分析測試
tests/test_export_static.py   靜態匯出與失敗案例測試
docs/                         規格、發布及回滾文件
data/                         本機 SQLite，不進版控
.static-export/               本機暫存快照，不進版控
public/data/                  本機 static preview 產物，不進版控
dist/                         最終 Pages 產物，不進 main
```

## Code Style

- Vue/JavaScript 使用兩格縮排、單引號、無分號；變數與函式使用 camelCase。
- Python 使用四格縮排、120 字元上限、snake_case，並由 Ruff 格式與 lint 規則約束。
- 路徑必須使用 `import.meta.env.BASE_URL`，不得硬編碼網域根路徑或用 hostname 推測模式。
- 所有 fetch 都要檢查 `response.ok`，並區分「未發布」與「資料載入失敗」。
- 匯出工具採純函式拆分資料轉換與檔案 I/O，讓 contract 能以 pytest fixture 驗證。

```python
def build_manifest(rows: list[dict], generated_at: str) -> dict:
    games = sorted(rows, key=lambda row: (row["game_date"], row["game_sno"]), reverse=True)
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "default_game_id": games[0]["game_id"] if games else None,
        "games": games,
    }
```

## Testing Strategy

### Python 自動測試

- 保留並執行所有既有 analyzer pytest，分析結果不得因上雲修改而改變。
- `tests/test_export_static.py` 使用暫存 SQLite fixture 驗證 manifest 與每場 JSON。
- 測試空資料庫、排序、中文、null、禁止的非有限數值、損壞 `data_json` 與缺少必要頂層欄位。
- 驗證 manifest 的每個 `game_id` 都有對應且可解析的 JSON，且沒有未被 manifest 引用的場次檔。
- 驗證匯出或驗證失敗時回傳非零 exit code，發布命令不執行 push。

### Frontend 與 build 驗證

- 執行 `pnpm exec eslint .` 與 static production build。
- 驗證 build 後的 `dist/index.html` 使用 `/cpbl-umpire-scorecard/` base path。
- 在 static preview 檢查首頁預設場次、指定已發布場次、未發布場次與損壞資料提示。
- 檢查逐打席、評分卡、相似球、容錯範圍、誤判篩選、得利球隊、跨場表格、JSON/CSV 匯出與深色模式。
- 使用瀏覽器 Network 面板確認 static build 沒有 `/api/*` 請求。
- 在本機 API 模式重新 smoke test 單場隨選抓取與日期批次抓取。

目前 repository 沒有前端測試框架；本規格不為此次上雲額外引入一套。前端部分由 ESLint、production build、靜態驗證工具及手動 smoke test 驗收。

## Boundaries

### Always do

- 保留本機 FastAPI、collector、analyzer、SQLite 與既有抓取 UI。
- 本機開發走 `/api/*`，static build 只走站內 JSON。
- 發布前執行 Ruff、pytest、ESLint、靜態資料驗證及 Vite static build。
- 使用已驗證的完整資料快照建置；只有完整 build 成功才更新 `gh-pages`。
- 對不存在、損壞與 schema 不相容的 JSON 顯示不同且可理解的訊息。
- 將發布、首次設定與回滾方式寫入文件。

### Ask first

- 變更 analyzer 公式、SQLite schema 或靜態 JSON contract。
- 新增 npm／Python dependency、前端測試框架或遠端 CI 資料產生流程。
- 改用 GitHub Pages 以外的平台或改變 `gh-pages` 發布策略。
- 移除或重新設計既有資料瀏覽、互動分析與匯出功能。
- 擴充到 2026 年一軍以外的年份或賽事種類。

### Never do

- 將 SQLite、WAL、暫存檔、token、cookie、`.env` 或其他秘密發布或 commit。
- 讓靜態前端直接向 CPBL 發送 cross-origin 抓取請求或重做 Python 分析。
- 在 static build 顯示無效的即時或批次抓取按鈕。
- 因上雲而改變 analyzer 計算結果、視覺設計或無關模組。
- 驗證失敗後繼續 push 或覆蓋既有線上版本。

## Success Criteria

1. `pnpm run dev` 下可用 UI 載入有效的 2026 年一軍場次；未快取場次會抓取、分析並寫入 SQLite。
2. 本機跨場次頁面仍可依日期批次抓取所有符合條件的完賽賽事。
3. `pnpm run export:static` 從本機 SQLite 產生通過 contract 驗證的 manifest 與每場 JSON。
4. manifest 的 `default_game_id`、schema、排序、場次摘要與檔案交叉連結通過自動測試。
5. GitHub Pages 可從 `/cpbl-umpire-scorecard/` 載入所有 CSS、JavaScript 與 JSON，不出現 base-path 404。
6. static build 的 Network 紀錄沒有 `/api/*` 或 CPBL 抓取請求。
7. 已發布場次可載入完整分析；未發布、損壞及 schema 不相容資料各自顯示明確訊息。
8. 逐打席、主審評分卡、好球帶、相似球、容錯範圍、誤判篩選、得利球隊、跨場表格、JSON/CSV 匯出與深色模式在本機及靜態模式通過 smoke test。
9. static build 隱藏抓取控制項並顯示 `generated_at` 與場次數；本機模式保留原控制項。
10. `pnpm run publish:pages` 依序完成匯出、Ruff、pytest、ESLint、驗證與 build，然後只更新 `gh-pages`。
11. 任一品質檢查失敗時，發布命令回傳非零狀態、不 push，現有 Pages 版本不受影響。
12. `main` 與發布內容均不包含 SQLite、WAL、秘密或未驗證的暫存資料。

## Open Questions

目前沒有阻擋技術計畫的未決問題。已確定：

- 本機模式保留所有既有抓取與分析能力，不新增 collector CLI。
- 雲端模式以完整 manifest 加每場 JSON 提供唯讀資料。
- 本機執行發布，產物只推送到 `gh-pages`，不由遠端重新分析或匯出。
- static build 以唯讀更新狀態取代抓取控制項。
