# CPBL 比賽時間抓取機制與 CDN 308 重定向異常記錄

## 問題背景

在系統抓取或回填賽事資料時，發現部分場次（例如 301、303 等）的比賽時間（\game_duration_minutes\）為 \NULL\，導致跨場次數據庫與賽事分析頁面無法正確顯示比賽費時（時/分）。

## 根本原因分析

1. **HiNet CDN 的 HTTP 308 重新導向挑戰**：
   - 官方網站 \https://www.cpbl.com.tw/box/getlive\ 位在 HiNet CDN 防護後方。
   - 當發出 POST 請求時，若 client 沒有攜帶有效的 session / cookie，CDN 會回應 \HTTP 308 Permanent Redirect\ 並附帶 \Set-Cookie: __chtcdn=...\。
   - Python 原生 \urllib.request\ 預設的 \HTTPRedirectHandler\ 僅支援 301/302/303/307，遇到 HTTP 308 或 POST 重定向時會拋出 \urllib.error.HTTPError: HTTP Error 308: Permanent Redirect\。
   - 先前程式中未妥善處理 308，且捕獲異常後直接回傳 \None\，導致時間抓取失敗。

2. **延賽／雙重賽的 \GameDetailJson\ 陣列多筆紀錄問題**：
   - 中職 API 在遇到曾延賽、改期或補賽的場次（如 15、16、81、159、198、285）時，\GameDetailJson\ 會回傳多筆物件（陣列）。
   - 陣列第 0 筆往往是延賽的暫存紀錄（\GameStatus=6\，\GameDuringTime='      '\ 為空白）。
   - 若程式只取 \gd[0]\，會抓到空白字串而誤判為沒有比賽時間，忽略了後續真正完賽（\GameStatus=3\）的紀錄。

3. **302 場次為延賽**：
   - 302 場次（2026-09-01 兄弟 vs 台鋼）因雨延賽（\POSTPONED\），原本即無完賽比賽時間。

## 解決方案與防護措施

1. **改用 \httpx\ 並開啟 \ollow_redirects=True\**：
   - 在 \server/collector.py\ 中的 \etch_game_duration()\ 改用 \httpx.Client(headers=CPBL_HEADERS, follow_redirects=True, timeout=10)\。
   - 自動跟隨 308 重新導向並保留 Cookie，順利取得 \getlive\ 回應。

2. **倒序遍歷 \GameDetailJson\ 陣列**：
   - 在解析 \GameDetailJson\ 時，使用 \
eversed(gd)\ 倒序遍歷，優先讀取最新且已完賽（\GameStatus=3\）或具有有效費時字串的紀錄。

3. **回填工具同步升級**：
   - 更新 \scripts/backfill_durations.py\，全面修復既有 SQLite 資料庫中缺少 \game_duration_minutes\ 的歷史場次。
