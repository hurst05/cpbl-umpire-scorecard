# 一軍賽事類型與獨立統計

## 目標與驗收

支援一軍例行賽（A）、一軍熱身賽（G）、一軍季後挑戰賽（E）、一軍總冠軍賽（C）。
查詢、批次抓取、場次標籤、跨場次摘要、年度統計與 JSON／CSV 匯出皆依選定類型運作。
預設為 A；「全部年度」只合計選定類型，沒有跨類型統計選項。二軍與未知類型仍排除。
沿用有效 Trackman 判決、完賽批次抓取與安全靜態匯出的既有檢查。
舊版缺少 kind_code 的靜態摘要從 game_id 取得類型，維持例行賽快照相容。

## 範圍與實作順序

1. 測試各類型抓取、儲存、API 與混合資料的統計隔離。
2. server/ 的 collector、app、db 與 stats 共用支援類型，API 的 kind_code 預設 A。
3. 靜態 manifest 保留所有支援類型並加入 kind_code；例行賽 stats/{year}.json 保持原路徑，
   其他類型使用 stats/{kind_code}/{year}.json；更新驗證與匯出測試。
4. src/ 的查詢、跨場次與年度統計共用由 App 管理的類型選擇，沿用現有 Vue 與 Tailwind 樣式。
   切換類型時清空舊統計並防止較慢的舊請求覆蓋新資料。
5. 執行測試、建置、lint 與瀏覽器檢查，再審查完整變更。

## 技術、結構與風格

Vue 3 / Vite、FastAPI / SQLite、Python 3.12+；不新增依賴、不改資料表。
server/ 放後端邏輯，src/services/ 放資料存取，src/utils/ 放前端類型規則，
tests/ 使用 pytest，tests-js/ 使用 Node 內建測試，docs/ 保存規格。
JavaScript 使用兩格縮排、單引號、無分號，例如 `const selectedKindCode = ref('A')`；
Python 使用四格縮排與 snake_case，例如 `kind_code: str = "A"`。

## 指令與驗證

- `pnpm run test:backend`：後端、靜態匯出與驗證。
- `pnpm run test:frontend`：類型辨識、篩選與靜態／API 資料服務。
- `pnpm run lint:py`、`pnpm exec eslint .`：程式檢查。
- `pnpm exec vite build`、`pnpm run build:pages`：兩種模式建置。
- `pnpm run dev`：本機瀏覽器查核類型切換、場次標籤與獨立統計。

## 邊界

必須：以參數化 SQL 與支援類型檢查處理輸入，保留零判決與靜態安全驗證。
另行授權：公開發布、刪除既有資料、大量歷史資料回補。
禁止：混合類型計算統計、引入二軍資料、提交資料庫與機密。
本次需求已由使用者明確指定，依上述範圍直接實作，不新增其他功能。

## 驗證結果（2026-10-10）

後端 64 個測試、前端 22 個測試、Ruff、ESLint、一般與靜態建置全部通過；
發布腳本的本機乾跑與暫存 bare repository 測試通過，未推送公開遠端。
瀏覽器實測並收錄 2026-E-1（133 個主審判決）：例行賽維持 296 場，季後挑戰賽獨立為 1 場，
熱身賽與總冠軍賽目前為 0 場。靜態快照共 297 場，四種類型的統計檔分別驗證。
獨立程式審查未發現需修正問題；未執行大量歷史資料回補。
