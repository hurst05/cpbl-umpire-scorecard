# Luna 任務：靜態 JSON 上雲第三輪修正

## 1. 任務背景

第二輪修正已完成下列改善：

- 完整 `pnpm exec eslint .` 可通過。
- static mode 會先用 manifest 判斷場次是否已發布。
- production preview 查詢未發布場次會正確顯示「尚未發布」。
- detail 頂層型別已有純函式驗證與 Node 測試。
- game ID 已在寫檔前驗證。
- verifier 已攔截 `-wal`、`-shm` 與 `.env.*`。
- static build 缺少 snapshot 時會失敗。
- Git 發布流程已有較完整的 exit-code 檢查。

第三輪審查仍發現一個會造成程序無限遞迴的 Critical 問題，以及幾個發布可靠性缺口。本任務只修正這些剩餘問題。

實作前依序閱讀：

1. `docs/spec-static-json-cloud.md`
2. `docs/plan-static-json-cloud-remediation.md`
3. `docs/task-static-json-cloud-review-round2.md`
4. 本文件

## 2. 範圍與安全限制

- 直接在目前工作目錄實作，不建立 worktree。
- 不執行指向真實 `origin` 的 `pnpm run publish:pages`。
- 不執行真實遠端 push。
- Git 發布測試只能使用測試專用本機 bare repository。
- 不連線到 `invalid.example.com` 或其他外部測試 URL。
- 不修改 analyzer、collector、CPBL 抓取、分析公式或 FastAPI 行為。
- 不新增 npm 或 Python runtime dependency。
- 不使用 `git reset --hard`、force push 或歷史重寫。
- 不終止不屬於本任務的使用者程序。
- 最終 `git diff --check` 必須成功。

## 3. 第三輪審查證據

已確認：

- Node tests：9 passed。
- Ruff：通過。
- 完整 ESLint：通過。
- 排除發布腳本測試後的 Python tests：26 passed。
- 靜態匯出：成功，51 場，預設第 297 場。
- Snapshot 驗證與 Vite static build：成功。
- Production preview 查詢 `2026-A-400`：顯示「此場次尚未發布」。

阻擋問題：

```text
pytest
  -> tests/test_publish_script.py::test_publish_script_dry_run
  -> scripts/publish-pages.ps1 -DryRun
  -> pnpm run test:backend
  -> pytest
  -> tests/test_publish_script.py::test_publish_script_dry_run
  -> ... 無限遞迴
```

實測在短時間內產生大量 `pytest`、`uv`、`python` 與 `cmd` 子程序，完整測試無法完成。審查時已終止這次測試產生的遞迴程序。

## 4. 實作順序

### Phase 1：拆開「品質檢查」與「Git 部署」以消除測試遞迴

目前 `tests/test_publish_script.py` 直接執行 `publish-pages.ps1`，而該腳本又執行包含自身測試的 `pnpm run test:backend`。禁止只增加 timeout 或放寬測試；必須消除循環依賴。

#### 1.1 建議結構

將發布流程拆成兩層：

```text
scripts/publish-pages.ps1
  ├─ export
  ├─ verify snapshot
  ├─ Ruff
  ├─ backend tests
  ├─ frontend tests
  ├─ ESLint
  ├─ static build
  ├─ verify dist
  └─ 呼叫 deploy-gh-pages.ps1

scripts/deploy-gh-pages.ps1
  ├─ 驗證 dist
  ├─ 檢查 remote/branch
  ├─ 建立臨時 Git checkout
  ├─ 建立 commit
  └─ push
```

要求：

1. `publish-pages.ps1` 是正式單一入口，保留 `pnpm run publish:pages`。
2. `deploy-gh-pages.ps1` 不執行 pytest、lint、export 或 build。
3. Python 整合測試只呼叫 `deploy-gh-pages.ps1`，不呼叫完整 publisher。
4. 正式 publisher 只有在所有品質檢查成功後才呼叫 deploy helper。
5. deploy helper 必須重新確認 `dist/data` contract，避免被單獨誤用。
6. 不提供會讓正式 publisher 靜默跳過品質檢查的公開 `-SkipTests` 或 `-SkipQualityChecks` 參數。

如果不拆檔，也必須把 Git 部署整理成可獨立測試、且不會再次執行 pytest 的函式模組；但優先採用拆檔方案，控制流較清楚。

#### 1.2 Dry-run 語意

定義清楚兩種 dry-run：

- Publisher dry-run：可執行所有品質檢查與 build，但不能由 backend pytest 測試直接呼叫。
- Deploy dry-run：只驗證 `dist`、remote 與預計操作，不 commit、不 push；整合測試可直接呼叫。

不要以環境變數讓 pytest 自動跳過自身測試，因為這會掩蓋測試集合差異，並保留循環架構。

### Phase 2：重寫發布腳本測試，禁止外部網路與遞迴

修改 `tests/test_publish_script.py`，讓測試只針對 deploy helper。

#### 2.1 測試 fixture

每個測試使用 pytest 暫存目錄建立：

- 最小合法 `dist/index.html`
- 最小合法 `dist/data/manifest.json`
- 對應的 `dist/data/games/{game_id}.json`
- 本機 bare Git repository 作為 remote

不得依賴真實 `.static-export`、真實 `dist`、真實 SQLite 或 `origin`。

#### 2.2 必要測試

至少涵蓋：

1. deploy dry-run 完成且不建立 remote branch。
2. remote 尚無 `gh-pages` 時建立第一個 commit。
3. remote 已有 `gh-pages` 時可更新內容。
4. 內容相同時不建立空 commit。
5. commit 失敗時回傳非零、不執行 push、不輸出 `[Publish SUCCESS]`。
6. push 失敗時回傳非零、不輸出 `[Publish SUCCESS]`。
7. 無效或不存在的本機 remote path 立即失敗。
8. dist contract 損壞時在任何 Git 寫入前失敗。
9. 含空白的 remote path 可正確運作。
10. commit message 含空白、括號與中文時仍作為單一 argument 傳給 Git。

不得再使用：

```text
https://invalid.example.com/non-existent.git
```

這會讓測試依賴 DNS、網路 timeout 與外部狀態。使用不存在的本機路徑或測試 stub 模擬 remote 錯誤。

#### 2.3 Timeout 防護

Python `subprocess.run()` 呼叫 PowerShell 時設定合理 timeout，例如 30 秒。timeout 時測試失敗並清理子程序，不可永久卡住 CI。

若使用 `Popen`，必須在 `finally` 中終止完整子程序樹。優先使用可控且會返回的 deploy-only script，避免需要複雜的 process cleanup。

### Phase 3：修正 PowerShell Git argument 與 location 管理

修改 Git helper，避免 `Start-Process -ArgumentList` 對含空白參數重新切詞。

#### 3.1 Git argument 傳遞

優先使用 PowerShell call operator：

```powershell
& git @GitArgs
$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) {
    throw "git command failed with exit code $exitCode"
}
```

要求：

- `$GitArgs` 是字串陣列。
- commit message 必須保持單一 argument。
- remote path 即使含空白也不能被拆開。
- 不用字串拼接後交給 `Invoke-Expression`。
- 錯誤訊息可顯示安全的命令摘要，但不要洩漏可能存在於 remote URL 的 credential。

若保留 `Start-Process`，必須自行完成正確的 Windows argument escaping，並有含空白／括號測試；基於簡單性，建議改用 `& git @GitArgs`。

#### 3.2 Push/Pop location

目前 `finally` 無條件執行 `Pop-Location`。若錯誤發生在 `Push-Location` 前，可能 pop 掉呼叫者原本的 location。

使用旗標：

```powershell
$locationPushed = $false
try {
    Push-Location $tempDeployDir
    $locationPushed = $true
    # ...
}
finally {
    if ($locationPushed) {
        Pop-Location
    }
}
```

所有 exit/error 路徑都必須保留呼叫者原本位置。

#### 3.3 不在 helper 深層使用 `exit`

Git helper 與 deploy function 內優先 `throw`，由最上層統一捕捉、輸出錯誤並 `exit 1`。這能確保 `finally` 正常執行，也讓測試較容易驗證。

### Phase 4：確保 gh-pages 內容精確等於 dist

目前清理與複製使用未加 `-Force` 的 wildcard，可能漏掉 hidden files。

要求：

1. 清理既有 gh-pages checkout 時，保留 `.git`，其餘可見與 hidden 項目全部移除。
2. 複製 `dist` 時包含 hidden files，例如未來可能加入的 `.nojekyll`。
3. 發布後 checkout 除 `.git` 外的檔案集合必須與 `dist` 一致。
4. 不允許上一版 hidden file 殘留。

建議做法：

```powershell
Get-ChildItem -LiteralPath $tempDeployDir -Force |
    Where-Object { $_.Name -ne '.git' } |
    Remove-Item -Recurse -Force

Get-ChildItem -LiteralPath $distPath -Force |
    Copy-Item -Destination $tempDeployDir -Recurse -Force
```

加入測試：上一版 remote 含 `.stale-hidden`、新版 dist 含 `.nojekyll`，發布後前者消失、後者存在。

### Phase 5：讓 snapshot rollback 可證明成功

目前 exporter 在替換失敗時會嘗試從 backup 複製回 output，但：

- rollback 清理仍使用 `ignore_errors`／例外抑制。
- rollback 後沒有再次執行 `verify_static_snapshot(output_path)`。
- 無論 rollback 是否完整，錯誤訊息固定寫「已還原上一份有效版本」。
- 測試只涵蓋最終 verifier 失敗，未涵蓋 backup、清理、copy 與 restore 本身失敗。

#### 5.1 必要語意

替換失敗後只能出現兩種明確結果：

1. Rollback 成功：舊 output 通過 verifier，錯誤訊息可寫「已還原」。
2. Rollback 失敗：保留 backup，不宣稱已還原，錯誤訊息包含 recovery backup 的絕對路徑，讓使用者可人工復原；發布流程必須停止。

不得 suppress 會影響資料完整性的刪除、restore 或驗證錯誤。

#### 5.2 建議簡化流程

優先使用目錄 rename，而不是先 copy backup 再清空原目錄：

1. staging 驗證成功。
2. 若 output 存在，rename output 到唯一 backup；rename 失敗時原 output 不變並停止。
3. rename staging 到 output。
4. 驗證 output。
5. 成功後刪除 backup。
6. 步驟 3 或 4 失敗時，將失敗的新 output 移到 failed 路徑，再 rename backup 回 output。
7. 驗證復原後的 output，確認成功才刪除 failed 路徑。

每次 rename 的目的地都必須不存在；不要嘗試以 rename 直接覆蓋非空目錄。

#### 5.3 必要測試

擴充 `tests/test_export_static.py`，使用 monkeypatch 精確模擬：

1. output → backup rename 失敗，舊 output 不變。
2. staging → output rename 失敗，backup 可還原。
3. final verify 失敗，backup 可還原且還原後再次驗證。
4. rollback rename 失敗，保留 backup 並回報 recovery path。
5. rollback 後 verifier 失敗，不得宣稱已還原。
6. 成功替換後不存在 backup、failed 或 staging 殘留。

測試要驗證 manifest 與至少一個 detail 檔內容，不只比較 manifest 字串。

### Phase 6：移除範圍外變更

`server/analyzer.py` 再次出現與上雲無關的換行格式變更。將它完整還原為目前 Git 基準版本，不修改分析行為。

確認：

```powershell
git diff -- server/analyzer.py
```

應無輸出。

同時檢查：

- `server/collector.py` 無新增 CLI。
- 沒有 `.github/workflows/deploy-pages.yml`。
- 沒有追蹤 `public/data/`、`.static-export/` 或 `dist/`。

## 5. 測試執行順序

修正遞迴前，不要再次執行完整 `pnpm run test:backend`。

先執行非發布測試：

```powershell
uv run pytest tests/test_analyzer.py tests/test_export_static.py tests/test_verify_static.py
pnpm run test:frontend
pnpm run lint:py
pnpm exec eslint .
```

發布測試架構修正後，單獨執行：

```powershell
uv run pytest tests/test_publish_script.py -vv
```

確認不會再出現巢狀 pytest 後，最後才執行完整測試：

```powershell
pnpm run test:backend
```

完整測試必須在合理時間內結束，不能只依賴人工 Ctrl+C。

## 6. 最終驗收矩陣

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

另外確認：

1. 完整 backend pytest 只出現單一 pytest 測試樹，不遞迴啟動自己。
2. `test_publish_script.py` 不呼叫 `publish-pages.ps1` 的品質檢查入口。
3. 所有 Git 測試使用本機 bare remote，無外部 DNS／HTTP request。
4. commit message 與含空白 remote path 測試通過。
5. commit／push 失敗都回傳非零且沒有 `[Publish SUCCESS]`。
6. deploy 測試不修改真實 origin 或 gh-pages。
7. snapshot rollback 成功時有二次驗證。
8. snapshot rollback 失敗時保留 recovery backup 且不誤報已還原。
9. `git diff -- server/analyzer.py` 無輸出。

## 7. Production preview 回歸

啟動 production preview：

```powershell
pnpm exec vite preview --host 127.0.0.1 --port 4174
```

若 port 已被占用，使用其他未占用 port，不終止使用者程序。

確認：

- 預設第 297 場可載入。
- 跨場次清單顯示 51 場與產生時間。
- 查詢第 400 場顯示「此場次尚未發布」。
- 未發布場次不請求 detail JSON。
- 靜態模式不請求 `/api/*`。
- console 無未處理錯誤。

## 8. 完成定義

只有同時符合下列條件才算完成：

- Critical pytest 遞迴已從架構上消除。
- 完整 `pnpm run test:backend` 可正常結束。
- 發布整合測試不使用真實 publisher preflight，也不連外。
- Git argument、commit、push、location 與 hidden file 行為都有測試。
- Snapshot rollback 成功與失敗都能被準確區分。
- Rollback 後重新驗證舊 snapshot。
- Static export、contract、build、ESLint、Python 與 Node tests 全部通過。
- `server/analyzer.py` 沒有範圍外 diff。
- 沒有執行真實遠端發布。

## 9. Luna 最終回報格式

請回報：

1. 如何消除 pytest → publisher → pytest 的循環依賴。
2. 發布腳本與 deploy helper 的責任分界。
3. 發布測試數量、使用的本機 remote 方法及執行時間。
4. Commit/push 失敗測試結果。
5. Snapshot rollback 成功與 rollback 失敗測試結果。
6. 完整 Python、Node、Ruff、ESLint、contract 與 build 結果。
7. Production preview 結果。
8. 明確聲明未執行真實 push。
