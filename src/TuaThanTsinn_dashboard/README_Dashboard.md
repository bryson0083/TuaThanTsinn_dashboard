# TuaThanTsinn Dashboard - 台股分析儀表板

## 專案概述

TuaThanTsinn Dashboard 是一個基於 Streamlit 構建的台股分析儀表板，提供全面的股票市場分析工具。

## 功能特色

### 📊 市場總覽
- 即時股價監控
- 市場指數追蹤 
- 熱門股票排行
- 外資動向分析

### 📈 技術分析
- K線圖表分析
- 技術指標計算 (RSI、移動平均線)
- 趨勢預測模型
- 成交量分析

### 💰 財務分析 (開發中)
- 財務報表分析
- 基本面指標
- 估值模型

### 📱 投資組合 (開發中)
- 持股追蹤管理
- 績效分析報告
- 風險評估工具

## 技術架構

### 核心技術棧
- **前端框架**: Streamlit >= 1.46.0
- **資料庫**: DuckDB >= 1.3.1
- **圖表庫**: Plotly >= 5.17.0
- **資料處理**: Pandas >= 2.3.0
- **程式語言**: Python >= 3.12

### 專案結構

```
src/TuaThanTsinn_dashboard/
├── .streamlit/
│   └── config.toml              # Streamlit 配置檔案
├── pages/                       # 頁面檔案 (英文檔名)
│   ├── market_overview.py       # 📊 市場總覽
│   ├── technical_analysis.py    # 📈 技術分析
│   ├── financial_analysis.py    # 💰 財務分析
│   └── portfolio.py             # 📱 投資組合
├── database/                    # 資料庫相關
│   ├── connection.py            # DuckDB 連接管理
│   └── operations.py            # 資料庫操作
├── data/                        # 資料處理
│   ├── stock_data.py            # 股票資料管理
│   └── market_data.py           # 市場資料管理
├── components/                  # UI 元件
│   ├── charts.py                # 圖表元件
│   └── widgets.py               # 小工具元件
├── proj_util_pkg/               # 工具套件
│   ├── config/                  # 配置檔案
│   │   └── .env                 # 環境變數
│   ├── common/                  # 通用工具
│   ├── indicators/              # 技術指標
│   ├── finlab_api/              # FinLab API
│   └── google_api/              # Google API
├── app.py                       # 主應用程式
├── menu.py                      # 共用導航選單
├── start_dashboard.py           # 啟動腳本
└── README_Dashboard.md          # 說明文件
```

## 安裝與設定

### 1. 安裝相依套件

```bash
cd /Users/bryson0083/projects/TuaThanTsinn_dashboard
uv sync
```

### 2. 設定環境變數

環境變數設定檔案位於: `src/TuaThanTsinn_dashboard/proj_util_pkg/config/.env`

主要設定項目：
- `finlab_api_token`: FinLab API 金鑰
- `gspread_wb_key`: Google Sheets 工作簿金鑰

### 3. 資料庫設定

DuckDB 資料庫將自動建立於 `PROJECT_ROOT/data/tuathantsinn.duckdb`

## 啟動方式

### 方法一: 使用啟動腳本 (推薦)

```bash
cd /Users/bryson0083/projects/TuaThanTsinn_dashboard/src/TuaThanTsinn_dashboard
python start_dashboard.py
```

### 方法二: 直接使用 Streamlit

```bash
cd /Users/bryson0083/projects/TuaThanTsinn_dashboard/src/TuaThanTsinn_dashboard
streamlit run app.py
```

### 方法三: 使用 uv 執行

```bash
cd /Users/bryson0083/projects/TuaThanTsinn_dashboard/src/TuaThanTsinn_dashboard
uv run streamlit run app.py
```

## 訪問網址

啟動成功後，請前往: http://localhost:8501

## 導航功能

### 原生 st.page_link 導航
- 使用 Streamlit 原生的 `st.page_link` 功能
- 英文檔名搭配中文顯示標籤
- 自動高亮當前頁面
- 圖標支援

### 導航選單特色
- 🏠 首頁 - 系統總覽和快速統計
- 📊 市場總覽 - 市場指數和熱門股票
- 📈 技術分析 - K線圖和技術指標
- 💰 財務分析 - 財務報表和基本面 (開發中)
- 📱 投資組合 - 投資組合管理 (開發中)

## 配置檔案

### Streamlit 配置 (.streamlit/config.toml)
```toml
[client]
showSidebarNavigation = false  # 隱藏預設導航，使用自定義導航
```

## 開發說明

### 頁面開發規範
1. 檔案名稱使用英文 (如: `market_overview.py`)
2. 顯示名稱使用中文 (透過 `label` 參數)
3. 每個頁面都要引入 `show_navigation_menu()`
4. 避免在子頁面中使用 `st.set_page_config()`

### 新增頁面步驟
1. 在 `pages/` 目錄下建立新的 `.py` 檔案
2. 在 `menu.py` 中新增對應的 `st.page_link`
3. 在頁面中引入並呼叫 `show_navigation_menu()`

## 疑難排解

### 常見問題

**Q: 頁面無法正常顯示導航選單？**
A: 確認在頁面中有正確引入並呼叫 `show_navigation_menu()`

**Q: 技術分析頁面的圖表無法顯示？**
A: 確認已安裝 `plotly` 套件：`uv add plotly`

**Q: 資料庫連接失敗？**
A: 檢查 `PROJECT_ROOT` 環境變數是否正確設定

## 版本資訊

- **版本**: v0.1.0
- **Python**: >= 3.12
- **Streamlit**: >= 1.46.0
- **最後更新**: 2024年12月

## 授權

Apache License 2.0

## 支援

如有問題，請聯繫開發團隊或查看專案文檔。 