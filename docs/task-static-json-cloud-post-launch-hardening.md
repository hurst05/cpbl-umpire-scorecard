# 靜態 JSON 上線後強化任務

## 狀態與用途

本文件記錄試行版上線後再處理的可靠性強化項目。這些問題不會阻止目前最簡單的正常首次發布流程，因此不納入本次最小修正。

已在試行版上線前完成：

- Publisher 不再遞迴執行 `tests/test_publish_script.py`。
- 完整 backend suite 可以正常結束。
- Git command 使用 PowerShell argument array，commit message 不會因空白被拆開。
- 本機 bare remote 已驗證首次與第二次 commit/push。

本文件項目不得與試行版發布混在同一批修改。後續另開實作與 review 回合。

## 1. 拆分 Publisher 與 Deploy Helper

目前以 `test:backend-core` 排除發布整合測試，已消除遞迴，足以支援首次發布。後續可進一步將責任拆分：

```text
publish-pages.ps1
  export → verify → lint → tests → build → dist verify
                                      │
                                      ▼
deploy-gh-pages.ps1
  local dist → temporary checkout → commit → push
```

目標：

- 發布整合測試只呼叫 deploy helper，不重跑完整品質流程。
- deploy helper 單獨執行時仍驗證 `dist/data` contract。
- 正式 `publish:pages` 維持唯一入口。
- 不提供正式流程可跳過品質檢查的危險參數。

## 2. 移除發布測試的外部網路依賴

`tests/test_publish_script.py` 目前以 `invalid.example.com` 測試 remote 失敗。改用：

- 不存在的本機 repository path；或
- 測試專用 Git stub。

所有 subprocess 加入 timeout，且只操作 pytest 暫存目錄。測試不得依賴 DNS、HTTP、認證或真實 origin。

## 3. Push／Pop-Location 成對管理

發布腳本的 `finally` 目前無條件 `Pop-Location`。後續加入 `$locationPushed` 旗標：

```powershell
$locationPushed = $false
try {
    Push-Location $tempDeployDir
    $locationPushed = $true
    # deploy
}
finally {
    if ($locationPushed) {
        Pop-Location
    }
}
```

補測 clone、init 或 Push-Location 前失敗時，呼叫者所在目錄保持不變。

## 4. Hidden Files 與 Dist 精確同步

清理 gh-pages checkout 及複製 dist 時使用 `Get-ChildItem -Force`：

- 保留 `.git`。
- 刪除上一版所有其他可見與 hidden files。
- 複製新版 dist 的所有可見與 hidden files。
- 發布後 gh-pages 內容精確等於 dist。

測試上一版 `.stale-hidden` 會消失，新版 `.nojekyll` 可正確發布。

## 5. Snapshot Rollback 強化

目前正常匯出、驗證與替換路徑可工作；要補強的是檔案鎖定、copy 失敗或 rollback 本身失敗等例外情境。

後續要求：

1. Staging 驗證成功前不更動舊 output。
2. 優先使用 output → backup、staging → output 的兩階段 rename。
3. 每個 rename 目的地必須不存在。
4. Final verify 失敗時 restore backup。
5. Restore 後再次執行 `verify_static_snapshot()`。
6. 只有復原後驗證成功才能輸出「已還原」。
7. 復原失敗時保留 backup，回報絕對 recovery path。
8. 不 suppress 會影響資料完整性的清理或復原錯誤。

必要測試：

- output → backup 失敗，舊 output 不變。
- staging → output 失敗，backup 可還原。
- final verify 失敗，還原後再次驗證。
- rollback 失敗，保留 backup 並正確回報。
- 成功後沒有 staging、backup、failed 或孤兒檔。

## 6. Git 失敗路徑測試

以本機 bare remote 或 Git stub 補齊：

- Commit 失敗：不 push、不顯示 `[Publish SUCCESS]`。
- Push 失敗：回傳非零、不顯示成功。
- Remote path 含空白仍可運作。
- Commit message 含空白、括號及中文仍是單一 argument。
- 無差異時不建立空 commit；測試需固定 `generated_at` 才能真正建立無差異 fixture。

## 7. 移除範圍外 Analyzer Diff

`server/analyzer.py` 目前仍有與上雲無關的換行格式差異。後續修改前還原為 Git 基準，確認：

```powershell
git diff -- server/analyzer.py
```

無輸出。不得改變任何分析公式或輸出。

## 8. 最終驗收

後續強化完成後執行：

```powershell
pnpm run export:static
pnpm run lint:py
pnpm run test:backend
pnpm run test:frontend
pnpm exec eslint .
pnpm run verify:static
uv run python -m server.verify_static --input dist/data
git diff --check
```

並確認：

- 所有發布測試只使用本機資源。
- Publisher 與 deploy helper 無循環依賴。
- 所有 Git 失敗路徑回傳非零。
- Rollback 成功與失敗可清楚區分。
- 沒有執行真實 remote push。
- `server/analyzer.py` 無 diff。
