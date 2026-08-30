# Luna 任務：靜態 JSON 上雲第二輪修正

## 1. 任務說明

第一輪上雲實作已完成主要架構，現有 Python 測試、Ruff、靜態匯出、contract 驗證與 Vite production build 均可成功。本任務只修正第二輪程式碼審查發現的發布可靠性與錯誤分類問題，不重新設計整套架構。

實作前先閱讀：

1. `docs/spec-static-json-cloud.md`
2. `docs/plan-static-json-cloud-remediation.md`
3. 本文件

若文件互有衝突，以原始 spec 與本文件列出的第二輪驗收條件為準。

## 2. 範圍與限制

- 直接在目前工作目錄實作，不建立 worktree。
- 不執行 `pnpm run publish:pages`，避免在修正過程中推送 `gh-pages`。
- 未經使用者明確要求，不執行任何 `git push`、force push、branch 刪除或歷史重寫。
- 不修改 CPBL 抓取、分析公式或 FastAPI 路由行為。
- 不新增 collector CLI。
- 不新增 npm 或 Python runtime dependency。
- 保留 static/API 雙模式與現有 UI 功能。
- 不修改或刪除與本任務無關的使用者變更。
- 修正所有本次變更造成的 trailing whitespace，最終 `git diff --check` 必須成功。

## 3. 已知基準

第二輪審查結果：

- `pnpm run test:backend`：22 passed。
- `pnpm run lint:py`：成功。
- `pnpm run export:static`：成功匯出 51 場，預設第 297 場。
- `pnpm run verify:static`：contract 驗證與 Vite static build 成功。
- `dist/data` 再驗證：成功。
- `pnpm exec eslint src vite.config.js eslint.config.js`：成功。
- `pnpm exec eslint .`：失敗，因掃描 `dist/assets`，產生 9 errors、54 warnings。
- production preview 首頁、跨場次清單、發布時間正常。
- production preview 查詢不存在場次時，被顯示成 JSON 損壞，而非「尚未發布」。

## 4. 實作順序

依下列順序實作。每一階段先補可重現失敗的測試或檢查，再修改實作。

### Phase 1：讓完整 ESLint 命令可重複執行

修改 `eslint.config.js`，在 flat config 最前面加入 global ignores：

```js
{
  ignores: [
    'dist/**',
    '.static-export/**',
    'node_modules/**'
  ]
}
```

要求：

1. 不把 generated bundle 的 lint 錯誤改成 warning。
2. 不用修改 `scripts/publish-pages.ps1` 的 `pnpm exec eslint .` 來繞過問題。
3. 不把整個 repository 或 `src/` 排除。
4. 在 `dist/` 與 `.static-export/` 已存在時，完整 `pnpm exec eslint .` 必須成功。

驗證：

```powershell
pnpm run build:pages
pnpm exec eslint .
```

### Phase 2：修正未發布場次判斷與 detail contract

修改 `src/services/dataService.js`。

#### 2.1 查詢前確認場次是否已發布

static mode 的 `fetchGame(gameId)` 必須先取得已驗證的 manifest，並以 manifest 的 `games[].game_id` 判斷場次是否存在。

- 不存在：立即拋出帶有 `isNotFound = true` 的「此場次尚未發布」錯誤，不發送 detail request。
- 存在：才請求 `${BASE_URL}data/games/{gameId}.json`。
- HTTP 404 仍保留為第二層保護。
- API mode 不讀 manifest，保持目前 `/api/game/{gameId}` 行為。

不要只依賴 `Content-Type` 判斷，因為不同靜態主機的 fallback header 可能不同。manifest 是已發布場次的權威索引。

#### 2.2 嚴格驗證 detail 頂層型別

成功解析 JSON 後至少驗證：

```text
root                 object，且不是 array/null
game_info            object，且不是 array/null
umpire_metrics       object，且不是 array/null
plate_appearances    array
all_called_pitches   array
```

型別錯誤必須拋出帶 `isCorrupted = true` 的可理解錯誤，不能讓 Vue 元件在 render 時才發生 TypeError。

#### 2.3 抽出可測試的純函式

在不新增測試框架的前提下，將以下邏輯抽成無 DOM、無 `import.meta.env` 依賴的純函式；可放在 `src/services/staticDataValidation.js`：

- 判斷 manifest 是否包含指定 game ID。
- 驗證 detail 頂層結構。

使用 Node 內建 `node:test` 與 `node:assert/strict` 新增測試，例如：

```text
tests-js/staticDataValidation.test.js
```

在 `package.json` 新增：

```json
"test:frontend": "node --test tests-js/*.test.js"
```

測試至少涵蓋：

1. manifest 包含場次時回傳 true。
2. manifest 不含場次時回傳 false。
3. `game_info: null` 判定損壞。
4. `umpire_metrics: []` 判定損壞。
5. `plate_appearances: {}` 判定損壞。
6. `all_called_pitches: null` 判定損壞。
7. 完整合法結構通過。

### Phase 3：寫檔前驗證 game ID 與輸出路徑

修改 `server/export_static.py`，不要等到 `verify_static_snapshot()` 才驗證 game ID。

#### 3.1 格式限制

目前只發布 2026 年一軍例行賽，game ID 必須符合：

```regex
^2026-A-[1-9]\d*$
```

在任何下列操作之前完成驗證：

- 加入 `games_detail`
- 加入 manifest summary
- 組合輸出檔名
- 寫入場次 JSON

不合法時整次匯出失敗，錯誤訊息包含該 ID，但不可嘗試建立對應路徑。

#### 3.2 路徑邊界

即使 ID 已通過 regex，也要在寫檔前確認解析後的目的路徑仍位於 staging 的 `games/` 內。

Python 3.12 可使用：

```python
resolved_game_path.is_relative_to(resolved_games_dir)
```

不要以字串 `startswith()` 判斷路徑，避免共同前綴誤判。

#### 3.3 測試

在 `tests/test_export_static.py` 新增至少下列案例：

1. `../../outside` 被拒絕，且 staging 外沒有產生 JSON。
2. `2026-B-123` 被拒絕。
3. `2025-A-123` 被拒絕。
4. `2026-A-0` 被拒絕。
5. `2026-A-123` 可正常匯出。

測試只能寫入 pytest 暫存目錄，不可碰觸真實 `.static-export` 或 `data/`。

### Phase 4：補齊敏感與暫存檔檢查

修改 `server/verify_static.py`。

目前只檢查 `Path.suffix`／`os.path.splitext()` 的 `.wal`、`.shm`，攔不到 SQLite 實際常見的：

```text
database.db-wal
database.db-shm
```

驗證器必須拒絕：

- 檔名結尾為 `-wal`
- 檔名結尾為 `-shm`
- 既有禁止副檔名集合中的檔案
- `.env` 與以 `.env.` 開頭的變體

比對使用不分大小寫的檔名。

同時將 `GAME_ID_PATTERN` 收緊為與匯出器共用或等價的 `^2026-A-[1-9]\d*$`。優先避免兩份 regex 漂移：可在不造成循環 import 的前提下，把常數放在單一輕量模組。

在 `tests/test_verify_static.py` 新增：

1. `database.db-wal` 被拒絕。
2. `database.db-shm` 被拒絕。
3. 大小寫變體被拒絕。
4. 非 2026-A 的 manifest game ID 被拒絕。
5. 正常場次 JSON 不受影響。

### Phase 5：讓 snapshot 更新真正失敗安全

修改 `server/export_static.py` 目前「清空 output_dir 後逐檔複製」的流程。

#### 5.1 必要保證

更新流程必須同時滿足：

1. staging 完整產生並通過 contract 驗證前，不碰既有有效 output。
2. 任一刪除、rename、move、copy 或最終驗證失敗時，上一份有效 output 仍可用。
3. 不使用 `ignore_errors=True` 隱藏資料替換失敗。
4. 最終 output 再執行一次 `verify_static_snapshot()`。
5. 成功後 output 不含上一版孤兒檔。
6. 失敗時清理本次 staging；若保留 recovery backup，錯誤訊息必須指出位置。
7. 發布流程只讀取這份成功完成的 output。

#### 5.2 建議 Windows 相容流程

可採用兩階段 rename 加 rollback：

1. 建立唯一 staging 目錄，不要只用 PID；可使用 UUID。
2. 產生並驗證 staging。
3. 若 output 存在，將 output rename 到唯一 backup 路徑。
4. 將 staging rename 為 output。
5. 驗證最終 output。
6. 全部成功後刪除 backup。
7. 步驟 4 或 5 失敗時，移除不完整的新 output，並將 backup rename 回原位置。

這不是以單次 rename 覆蓋非空目錄；每次 rename 的目的地必須不存在。若 Windows 因檔案鎖定導致步驟 3 失敗，匯出應停止且原 output 保持原狀。

若選擇讓 Vite 直接讀取唯一且已驗證的 versioned staging，也可以，但必須同步調整發布腳本與 Vite config，並證明 build 使用的是本次匯出的確切快照，不可使用模糊的「最新目錄」。優先採用修改面較小的方案。

#### 5.3 必要測試

擴充 `tests/test_export_static.py`：

1. staging 驗證失敗時，舊 output 完整保留。
2. 模擬 output rename 失敗時，舊 output 完整保留。
3. 模擬 staging 切換到 output 失敗時，可 rollback 舊 output。
4. 模擬最終驗證失敗時，可 rollback 舊 output。
5. 成功替換後，上一版孤兒 JSON 不存在。
6. 不得只用廣泛的 `pytest.raises(Exception)`；應驗證預期例外與舊 manifest/detail 內容。

可使用 pytest monkeypatch 模擬 `Path.rename`／`os.replace`／`shutil` 失敗，不需要真的鎖住 Windows 檔案。

### Phase 6：讓發布腳本正確處理所有 Git 失敗

修改 `scripts/publish-pages.ps1`。

#### 6.1 原生命令檢查

下列每個會改變或確認 Git 狀態的命令都必須檢查 `$LASTEXITCODE`：

- `git rev-parse`
- `git remote get-url`
- `git clone`
- `git init`
- `git checkout --orphan`
- `git remote add`
- `git add -A`
- `git status --porcelain`
- `git commit`
- `git push`

注意：只有已確認錯誤原因是「remote 尚無 gh-pages branch」時，才能走初始化 orphan branch 流程。不能把網路、權限、認證、remote 不存在等所有 clone 失敗都當成 branch 不存在。

#### 6.2 Commit 成功條件

- `git commit` 失敗時立即停止，不執行 push。
- 只有 commit exit code 為 0 且 HEAD 確實改變後，才能執行 push。
- `git push` exit code 為 0 後，才顯示 `[Publish SUCCESS]`。
- 若工作樹沒有變更，可以顯示 already up to date，但不能使用與新發布相同的成功訊息誤導使用者。
- 錯誤流程仍必須在 `finally` 清理臨時目錄並正確恢復 location。

#### 6.3 Remote 與 branch 邊界

- remote 固定使用 `origin`。
- 取得 remote URL 失敗時停止。
- 在輸出中顯示即將推送的完整 remote URL 與 `gh-pages`，讓使用者在真正 push 前可核對。
- 不使用 force push。
- 不改動目前 `main` 工作樹的 index 或 branch。

#### 6.4 驗證方式

不要對真實 remote 執行測試。使用臨時本機 bare repository 驗證：

1. gh-pages 不存在時可建立初始 commit。
2. gh-pages 已存在時可更新。
3. 模擬 commit 失敗時不執行 push，也不顯示發布成功。
4. 模擬 push 失敗時回傳非零 exit code。
5. 無差異時不建立空 commit。

若為了測試需要，將部署 Git 流程整理成可接受 remote path 與 `-WhatIf`／測試參數的函式；正式 `publish:pages` 仍固定使用 origin，測試參數不得意外降低正式流程的安全檢查。

### Phase 7：補強 static build 失敗條件

修改 `vite.config.js` 的 `staticDataPlugin()`：

- static mode 找不到 `.static-export/data` 時必須 `throw new Error(...)`，不能只 `console.warn` 後讓 build 成功。
- 複製後確認 `dist/data/manifest.json` 存在。
- 建置資料必須是已驗證快照；發布腳本仍需在 build 前顯式執行 verifier。
- 一般 API development mode 不要求 `.static-export/data` 存在。

需要驗證：

1. static snapshot 存在時 `pnpm run build:pages` 成功。
2. 使用暫存測試專案或可注入路徑模擬 snapshot 不存在時，static build 回傳非零。
3. `pnpm run dev` 的 API mode 不受影響。

不要為測試直接刪除使用者真實 `.static-export/data`；如需移動，使用唯一暫存備份並以 `finally` 還原。

### Phase 8：格式與死碼收尾

1. 修正 `.gitignore` EOF 多餘空白行。
2. 修正 `src/App.vue`、`src/components/MultiGameStats.vue` 的 trailing whitespace。
3. 執行 `git diff --check`。
4. 使用 `rg` 確認沒有殘留的舊 CLI、遠端 Pages workflow 或 `public/data_tmp_*`。
5. 不做與本任務無關的格式化。

## 5. 最終驗收

### 5.1 自動測試與建置

全部必須成功：

```powershell
pnpm run export:static
uv run python -m server.verify_static --input .static-export/data
pnpm run lint:py
pnpm run test:backend
pnpm run test:frontend
pnpm exec eslint .
pnpm run verify:static
uv run python -m server.verify_static --input dist/data
git diff --check
```

### 5.2 Production preview smoke test

使用未被占用的 port 啟動：

```powershell
pnpm exec vite preview --host 127.0.0.1 --port 4174
```

若 4174 已被占用，選擇其他未占用 port，不要終止不屬於本任務的程序。

瀏覽器確認：

1. `/cpbl-umpire-scorecard/` 正常載入 manifest 預設場次。
2. 跨場次清單顯示正確場次數與 `generated_at`。
3. 已發布場次可載入。
4. 查詢 manifest 不包含的合法場次編號時，顯示「此場次尚未發布」。
5. 未發布場次不發送 detail JSON request。
6. 已發布但 detail JSON 損壞時，顯示「賽事資料損壞」。
7. 瀏覽器 console 無未處理錯誤。
8. 沒有任何 `/api/*` request。

### 5.3 API mode 回歸

若 5173 已被占用，先確認是否為使用者正在執行的服務；不要擅自終止。可使用臨時 Vite port 並保留 API proxy 驗證。

確認：

1. API mode 不載入 static manifest。
2. `/api/games/cached` 可讀取。
3. 已快取場次可載入。
4. 批次抓取 UI 仍顯示。
5. static-only 的未發布檢查不阻止 API 隨選抓取。

### 5.4 發布腳本安全驗證

- 不執行真實 `pnpm run publish:pages`。
- 使用本機 bare remote 或 mock 驗證 Git 成功／失敗路徑。
- 證明 commit 失敗與 push 失敗都回傳非零，而且不會印出 `[Publish SUCCESS]`。

## 6. 完成定義

只有同時符合下列條件才算完成：

- `pnpm exec eslint .` 在已有 `dist/` 時仍成功。
- static mode 在請求 detail 前以 manifest 判斷是否發布。
- 未發布場次顯示正確訊息，不再被 SPA fallback 誤判為 JSON 損壞。
- detail 頂層型別錯誤會在 data service 被攔截。
- game ID 在任何檔案路徑組合前完成嚴格驗證。
- `database.db-wal` 與 `database.db-shm` 會被 verifier 拒絕。
- snapshot 替換中任一步驟失敗，都能保留或恢復上一份有效版本。
- static build 缺少快照時回傳非零。
- commit 或 push 失敗時發布腳本回傳非零且不誤報成功。
- 所有新增失敗案例都有回歸測試。
- Python、Node、ESLint、contract、build 與 `git diff --check` 全部通過。
- 沒有執行真實 push，沒有修改 analyzer、collector 或 FastAPI 行為。

## 7. Luna 最終回報格式

完成後請回報：

1. 修改檔案清單與各檔案目的。
2. 新增測試案例清單。
3. 所有驗證命令及實際結果。
4. production preview 的未發布場次實測結果。
5. Git commit/push 失敗模擬結果。
6. 是否仍有任何限制或未完成項目。

不要只回報「測試通過」；必須列出測試數量、build 結果及未執行真實發布的說明。
