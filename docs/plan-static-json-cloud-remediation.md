# 靜態 JSON 上雲修正實作計畫（Luna 執行版）

## 1. 任務目標

修正目前靜態 JSON 上雲實作，使其完整符合 `docs/spec-static-json-cloud.md`，並維持本機既有功能不變：

- 本機仍由 Vue、FastAPI、SQLite、collector 與 analyzer 提供完整功能。
- 所有資料抓取與分析只在本機執行。
- 正式網站只讀取建置產物內的 JSON，不呼叫 `/api/*`。
- 發布由本機單一命令完成；`main` 不保存資料快照或建置產物。
- 任一匯出、驗證、測試或建置步驟失敗時，不得更新線上版本。

本計畫只處理上雲所需修改與審查發現的回歸，不新增產品功能。

## 2. 實作限制

1. 直接在目前工作目錄實作，不建立 worktree。
2. 保留以下既有 FastAPI 路由與行為：
   - `/api/game/{game_id}`
   - `/api/game/sno/{sno}`
   - `/api/schedule`
   - `/api/games/cached`
   - `/api/batch-collect`
3. 不新增 collector CLI；移除目前 `server/collector.py` 新增的 CLI、SQLite 寫入及 `--export` 邏輯。
4. 不修改 `server/analyzer.py` 的分析行為；撤回與本功能無關的純格式變更。
5. 不新增 npm 或 Python runtime dependency。匯出、驗證與發布優先使用 Python 標準庫、PowerShell、既有 pnpm/uv/git。
6. 不提交下列內容至 `main`：
   - `data/*.db*`
   - `public/data/`
   - `public/data_tmp_*/`
   - `.static-export/`
   - `dist/`
7. 不自動 force-push，不修改使用者其他未提交變更。

## 3. 建議實作順序

依下列階段執行。每階段先補測試或可驗證條件，再修改實作；前一階段通過後才進入下一階段。

### Phase 0：整理範圍與基準

1. 執行並記錄基準結果：

   ```powershell
   pnpm run test:backend
   pnpm run lint:py
   pnpm exec eslint .
   pnpm exec vite build
   ```

2. 確認 `git status --short`，不得覆蓋與本任務無關的使用者變更。
3. 刪除已遺留的 `public/data_tmp_20452/`；這是未提交的產生物，可重新匯出，不應進入發布內容。
4. 更新 `.gitignore`，至少加入：

   ```gitignore
   public/data/
   public/data_tmp_*/
   .static-export/
   ```

5. 保留既有 `dist/` ignore 與 `data/*.db*` ignore。

完成條件：`git status` 不再列出任何產生的 JSON、暫存快照或 `dist` 內容。

### Phase 1：建立嚴格的靜態資料驗證器

新增 `server/verify_static.py`，提供可由 Python 呼叫及 CLI 執行的驗證入口。

建議介面：

```python
def verify_static_snapshot(snapshot_dir: str | Path) -> dict:
    """驗證成功時回傳摘要；失敗時拋出具體例外。"""
```

CLI 範例：

```powershell
uv run python -m server.verify_static --input .static-export/data
```

驗證器必須檢查：

1. `manifest.json` 存在、是 UTF-8 且可由標準 JSON parser 解析。
2. `schema_version` 必須是整數 `1`。
3. `generated_at` 必須是包含時區的 ISO 8601 時間。
4. `games` 必須是陣列。
5. 每筆摘要具備規格要求欄位及正確基本型別。
6. `games` 依 `game_date`、`game_sno` 由新到舊排序。
7. 非空資料時，`default_game_id` 等於 `games[0].game_id`；空資料時必須為 `null`。
8. 每個 `game_id` 唯一，且符合目前支援的 `2026-A-{sno}` 格式。
9. 每個 manifest 項目都有且只有一個 `games/{game_id}.json`。
10. `games/` 不得有 manifest 未引用的孤兒 JSON。
11. 每個場次 JSON 可解析，且至少具備：
    - `game_info`
    - `umpire_metrics`
    - `plate_appearances`
    - `all_called_pitches`
12. 所有 JSON 必須拒絕 `NaN`、`Infinity`、`-Infinity`。
13. 快照不得包含 SQLite、WAL、SHM、token、cookie 或其他非預期檔案。

錯誤訊息必須指出具體檔案與原因，CLI 驗證失敗時回傳非零 exit code。

### Phase 2：修正匯出器與一致性邊界

修改 `server/export_static.py`。

#### 2.1 匯出目的地

- 預設輸出改為工作區內的 `.static-export/data/`，不要直接寫入 `public/data/`。
- 接受測試傳入的自訂 SQLite 路徑及輸出路徑。
- 自訂 SQLite 路徑不存在時直接失敗，不得順便初始化另一個預設資料庫。

#### 2.2 資料選取與轉換

- 只匯出 SQLite 中具有完整、可解析 `data_json` 的資料。
- 任一 manifest 候選場次的 `data_json` 缺失或損壞時，整次匯出失敗；不可只警告後繼續。
- 先解析完整場次，再將摘要加入 manifest，避免 manifest 指向不存在的檔案。
- 使用明確排序：`game_date DESC, game_sno DESC`。
- JSON 寫入統一使用 UTF-8、`ensure_ascii=False`、`allow_nan=False`。

#### 2.3 暫存與驗證

1. 在 `.static-export/` 下建立本次執行專用的暫存目錄。
2. 在暫存目錄產生所有 detail JSON 與 manifest。
3. 呼叫 `verify_static_snapshot()` 驗證該暫存目錄。
4. 驗證成功後，將該目錄作為這次 build 的唯一資料來源。
5. 驗證失敗時清除本次暫存、回傳非零 exit code，不更動上一份有效快照。

不要再採用「先清空 `public/data/`，再逐檔複製」的流程。

建議成功輸出摘要包含：

```json
{
  "snapshot_dir": ".static-export/data",
  "total_games": 51,
  "default_game_id": "2026-A-297"
}
```

### Phase 3：補齊匯出與驗證測試

擴充 `tests/test_export_static.py`，並新增 `tests/test_verify_static.py`。至少涵蓋：

1. 正常資料可產生完整 manifest 與 detail。
2. 空資料庫產生 `games: []`、`default_game_id: null`。
3. 多場比賽排序正確。
4. `data_json` 缺失時匯出失敗。
5. `data_json` 損壞時匯出失敗，且 manifest 不得殘留該場。
6. 任一層資料含 `NaN` 或 Infinity 時匯出失敗。
7. schema version 錯誤時驗證失敗。
8. manifest 缺少必要欄位時驗證失敗。
9. manifest 引用缺失 detail 時驗證失敗。
10. `games/` 有孤兒檔時驗證失敗。
11. detail JSON 損壞或缺少必要頂層欄位時驗證失敗。
12. 驗證失敗時保留上一份有效快照，不留下半套輸出。
13. CLI 失敗時回傳非零 exit code。

測試必須使用暫存目錄與暫存 SQLite，不依賴真實 `data/cpbl_cache.db`。

### Phase 4：修正前端資料抽象層

修改 `src/services/dataService.js`，將模式判斷集中為模組初始化時的固定值。

#### 4.1 模式解析

```js
const dataMode = import.meta.env.VITE_DATA_MODE
  || (import.meta.env.DEV ? 'api' : 'static')

if (!['api', 'static'].includes(dataMode)) {
  throw new Error(`Unsupported data mode: ${dataMode}`)
}
```

- `isStaticMode()` 只回傳 `dataMode === 'static'`。
- 無效值必須立即報錯，不能默認切到 production/static。

#### 4.2 Manifest contract

`fetchManifest()` 必須：

- 僅在 static mode 讀取 `${BASE_URL}data/manifest.json`。
- 檢查 HTTP status。
- 捕捉 JSON parse error，轉為可理解的 manifest 損壞訊息。
- 驗證 `schema_version === 1` 與 `Array.isArray(games)`。
- 不吞掉錯誤。

建議將 manifest Promise 快取，避免首頁和 `MultiGameStats` 重複請求；若採用快取，測試必須能重置或隔離快取。

#### 4.3 API 一致性

- `fetchGameList()`：static 回傳已驗證 manifest 的 `games`；API mode 保持 `/api/games/cached`。
- `fetchDefaultGameId()`：static 回傳 manifest 的 `default_game_id` 或 `null`，不得回退到硬編碼場次。
- `fetchGame()`：
  - static 404 使用可辨識的未發布錯誤。
  - JSON 損壞使用不同且可理解的錯誤。
  - API mode 保持現有路由與行為。
- `runBatchCollect()`：static mode 明確拒絕；API mode 保持現有 POST。

若不引入前端測試框架，至少將純驗證邏輯抽成可由 Node 直接測試的無 DOM 函式，並以現有 Node runtime 建立小型測試腳本。不得為此新增重量級 dependency。

### Phase 5：修正 Vue 錯誤狀態與靜態資訊

#### 5.1 `src/App.vue`

- 初始場次不得硬編碼為靜態 fallback 的唯一依據。
- static manifest 載入失敗時顯示 manifest/schema 錯誤，不再接著載入 `2026-A-295`。
- 空 manifest 顯示「目前沒有已發布場次」，不要呼叫 `fetchGame(null)`。
- 場次 404 顯示「此場次尚未發布」。
- 場次 JSON 損壞顯示不同錯誤，不保留可能誤導的半套新資料。
- 載入新場次失敗時，可保留上一場完整資料，但錯誤狀態必須清楚；不得將部分 response 寫入 `gameData`。
- 修復主題回歸：切回亮色時寫入 `localStorage.setItem('theme', 'light')`。

#### 5.2 `src/components/MultiGameStats.vue`

- static mode 讀取同一份已驗證 manifest。
- 顯示 `generated_at`（轉為使用者可讀的台北時間）及已發布場次數量。
- manifest 載入失敗時顯示可見錯誤與重試操作，不可只 `console.error` 或顯示成 0 場。
- static mode 繼續隱藏批次抓取控制項。
- API mode 保留依日期批次抓取操作。
- 保留載入分析、匯出摘要 JSON、匯出 CSV。

若要避免 App 與子元件各自抓 manifest，可由 App 載入後以 props 傳入，或由 data service 提供快取；選擇較小且不破壞既有元件介面的方案。

### Phase 6：建立可重現的 static build

新增 `.env.static`：

```dotenv
VITE_DATA_MODE=static
VITE_BASE_PATH=/cpbl-umpire-scorecard/
```

修改 `vite.config.js` 使用 Vite 的 `loadEnv(mode, process.cwd(), '')` 取得 `VITE_BASE_PATH`，確保 `vite build --mode static` 能在 Windows PowerShell、Linux 及 CI 一致運作，不依賴 inline environment variable。

建置資料不得來自受版控的 `public/data/`。可採以下其中一種簡單方式：

1. 發布腳本在暫存 staging 目錄準備 Vite `publicDir`；或
2. Vite static mode 將 `.static-export/data/` 複製到 `dist/data/`。

無論採哪種方式，必須符合：

- Vite 只讀取已驗證快照。
- 一般 `pnpm run dev` 不受影響。
- build 前後不需要把 JSON 複製進受版控的 `public/data/`。
- `dist/index.html` 資源 URL 以 `/cpbl-umpire-scorecard/` 開頭。
- `dist/data/manifest.json` 與所有場次檔存在。
- `dist/` 不含 `data_tmp_*`、SQLite 或其他本機檔案。

### Phase 7：建立本機發布命令

新增 `scripts/publish-pages.ps1`，並調整 `package.json`：

```json
{
  "scripts": {
    "export:static": "uv run python -m server.export_static",
    "verify:static": "uv run python -m server.verify_static --input .static-export/data && vite build --mode static",
    "build:pages": "vite build --mode static",
    "publish:pages": "powershell -NoProfile -ExecutionPolicy Bypass -File scripts/publish-pages.ps1"
  }
}
```

實際命令可依 PowerShell 相容性微調，但語意必須一致。

`publish-pages.ps1` 依序執行：

1. 確認位於正確 repository。
2. 確認必要工具存在：git、pnpm、uv。
3. 執行 `pnpm run export:static`。
4. 執行靜態 contract 驗證。
5. 執行 `pnpm run lint:py`。
6. 執行 `pnpm run test:backend`。
7. 執行 `pnpm exec eslint .`。
8. 執行 `pnpm run build:pages`。
9. 驗證 `dist/`：base path、manifest/detail 完整、沒有暫存或敏感檔。
10. 所有步驟成功後，才將完整 `dist/` 發布到 `gh-pages`。

腳本規則：

- 設定 `$ErrorActionPreference = 'Stop'`。
- 每個外部命令後檢查 `$LASTEXITCODE`。
- 任一步驟失敗立即停止，不執行 git push。
- 不使用 `git reset --hard`、`git checkout --` 或 force push。
- 不把 `dist/` 加入目前 `main` 的 index。
- 發布可使用獨立臨時目錄建立 gh-pages commit，避免污染工作樹。
- push 前再次確認目標 branch 是 `gh-pages`、remote 是預期 repository。
- commit message 包含資料產生時間與場次數，例如：

  ```text
  Publish static scorecards: 51 games (2026-08-30)
  ```

- 若 remote 或 gh-pages 尚未設定，清楚報錯並停止，不自行猜測 remote。

### Phase 8：移除不符合規格的遠端部署與範圍外修改

1. 移除 `.github/workflows/deploy-pages.yml`，因為它會在遠端從 `main` 重建網站，且無法存取本機 SQLite。
2. 移除 `server/collector.py` 新增的：
   - `os` import
   - `collect_and_save_game()`
   - `batch_collect_and_save_date()`
   - `main()` 與 argparse CLI
   - `--export`
3. 撤回 `server/analyzer.py` 與上雲無關的格式變更。
4. 確認 `server/app.py` 的現有抓取、分析、快取與批次 API 沒有被改變。

## 4. 測試與驗收矩陣

### 4.1 自動檢查

全部必須成功：

```powershell
pnpm run export:static
uv run python -m server.verify_static --input .static-export/data
pnpm run lint:py
pnpm run test:backend
pnpm exec eslint .
pnpm run build:pages
pnpm run verify:static
```

### 4.2 靜態網站 smoke test

使用本機 HTTP server 從 project base path 開啟 production build，確認：

1. 首頁正常讀取 manifest 預設場次。
2. Network 中沒有任何 `/api/*` request。
3. 輸入已發布場次可載入完整分析。
4. 輸入未發布場次顯示「此場次尚未發布」。
5. 逐打席、好球帶、軌跡、編號、主審評分卡、誤判篩選、得利球隊、相似球正常。
6. 跨場次清單數量與 manifest 一致。
7. 靜態 banner 顯示資料產生時間與場次數。
8. JSON 與 CSV 匯出仍可用。
9. 批次抓取控制項在 static mode 不存在。
10. 瀏覽器 console 無 error。

### 4.3 本機 API mode 回歸測試

執行 `pnpm run dev`，確認：

1. 首頁資料請求使用 `/api/*`。
2. 已快取場次可載入。
3. 未快取有效場次仍可由後端抓取、分析並存入 SQLite。
4. 依日期批次抓取仍可操作。
5. 跨場次清單、JSON 與 CSV 匯出仍可用。
6. 深色切換後改回亮色，重新整理仍維持亮色。

### 4.4 失敗路徑

至少人工或自動驗證：

1. 暫時提供不相容 schema，UI 顯示版本錯誤。
2. manifest 為非法 JSON，UI 顯示索引損壞。
3. detail 為非法 JSON，UI 顯示場次資料損壞。
4. 匯出資料含 NaN，匯出失敗。
5. manifest 引用缺失 detail，驗證失敗。
6. lint、pytest、ESLint、驗證或 build 任一步失敗時，`publish:pages` 不 push。

## 5. 完成定義

只有同時符合下列條件才算完成：

- 所有 Phase 的必要修改完成。
- `server/verify_static.py` 與失敗案例測試存在且通過。
- `pnpm run publish:pages` 存在，流程順序符合規格，失敗時不 push。
- `main` 不包含 `public/data/`、`.static-export/` 或 `dist/`。
- 不再有遠端 workflow 嘗試從 `main` 重建資料站。
- production build 在 project base path 正常運作且不呼叫 `/api/*`。
- manifest/schema/detail 錯誤在 UI 中可區分且可理解。
- static banner 顯示 `generated_at` 與發布場次數。
- 本機 API 模式所有既有功能維持正常。
- collector CLI 與無關 analyzer 格式變更已撤回。
- 最終回報列出修改檔案、驗證命令、測試結果及任何仍存在的限制。

## 6. Luna 執行時的提交建議

若要分段提交，建議使用下列順序；未經使用者要求不要自行 push：

1. `Add strict static snapshot validation`
2. `Make static export fail safely`
3. `Handle static manifest errors in UI`
4. `Add reproducible Pages build scripts`
5. `Remove out-of-scope deployment changes`

每次提交前執行與該階段相關的最小測試，最後再執行完整驗收矩陣。
