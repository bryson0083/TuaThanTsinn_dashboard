# TuaThanTsinn Dashboard

大趨勢台股分析儀表板 — 基於 Streamlit 的台灣股市分析工具，提供市場總覽、技術分析、CIS + 2560 戰法分析、財務分析與投資組合管理等功能。

## 功能頁面

- **市場總覽** — 台股市場即時概況與類股表現
- **技術分析** — K 線圖搭配 MA / RSI / MACD 等技術指標
- **CIS + 2560 戰法** — 結合 CIS 選股策略與 2560 量能確認的買賣信號分析
- **財務分析** — 個股財務數據查詢（開發中）
- **投資組合** — 持股管理與績效追蹤（開發中）

## 環境需求

- Python >= 3.12
- [UV](https://docs.astral.sh/uv/) 套件管理工具
- TA-Lib C 函式庫（技術指標計算所需）

## 安裝與啟動

```bash
# 1. 安裝相依套件
uv sync

# 2. 設定環境變數
#    複製範本並填入實際設定值
cp src/TuaThanTsinn_dashboard/proj_util_pkg/config/.env.example \
   src/TuaThanTsinn_dashboard/proj_util_pkg/config/.env

# 3. 啟動儀表板（預設於 http://localhost:8501）
python src/TuaThanTsinn_dashboard/start_dashboard.py
```

## 環境變數說明

編輯 `src/TuaThanTsinn_dashboard/proj_util_pkg/config/.env`，設定以下參數：

| 變數名稱 | 說明 |
|----------|------|
| `duckdb_file_path` | 外部 DuckDB 資料庫路徑（台股歷史資料） |
| `finlab_api_token` | FinLab API 存取金鑰 |
| `gspread_wb_key` | Google Sheets 活頁簿金鑰 |

> Google Sheets 整合另需將服務帳戶憑證檔放置於 `src/TuaThanTsinn_dashboard/proj_util_pkg/config/gspread_credentials.json`。

## 技術架構

- **前端框架：** Streamlit
- **圖表引擎：** Plotly
- **資料處理：** Pandas, DuckDB
- **技術指標：** TA-Lib
- **套件管理：** UV
