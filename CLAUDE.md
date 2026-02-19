# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TuaThanTsinn Dashboard (大趨勢台股分析儀表板) — A Taiwan stock market analysis dashboard built with Streamlit. Features market monitoring, technical analysis (K-line charts, MA/RSI/MACD), financial analysis, and portfolio management. Comments and documentation are in Traditional Chinese (繁體中文).

## Build & Run

**Package manager:** UV (not pip). Python 3.12.

```bash
# Install dependencies
uv sync

# Run the dashboard (starts Streamlit on localhost:8501)
python src/TuaThanTsinn_dashboard/start_dashboard.py
```

There is no test suite, linter, or CI/CD configured.

## Architecture

### Entry Points
- `src/TuaThanTsinn_dashboard/start_dashboard.py` — Launch script that runs Streamlit
- `src/TuaThanTsinn_dashboard/app.py` — Streamlit main page (homepage)

### Page Structure
Each page under `pages/` is a standalone Streamlit app that imports `menu.py` for consistent sidebar navigation. Pages use `sys.path` manipulation to access shared modules. Streamlit's built-in sidebar navigation is disabled; a custom menu (`menu.py`) is used instead.

Pages: `market_overview.py`, `technical_analysis.py`, `financial_analysis.py` (stub), `portfolio.py` (stub)

### Data Layer
- **`data/`** — Manager classes (`StockDataManager`, `MarketDataManager`) for data operations
- **`database/`** — DuckDB embedded database (`connection.py` provides a global `db_connection` instance; `operations.py` defines table schemas for stocks, stock_prices, financials)
- DB file location: `{PROJECT_ROOT}/data/tuathantsinn.duckdb`

### Utilities (`proj_util_pkg/`)
- **`settings.py`** — `ProjEnvSettings` class auto-loads `.env` on import, sets `PROJECT_ROOT` and config paths. Importing this module triggers environment initialization.
- **`indicators/`** — `TechnicalIndicators` (MA, RSI, MACD via ta-lib) and `StatisticalIndicators` (volatility, correlation)
- **`finlab_api/finlab_manager.py`** — Wrapper around the `finlab` library for Taiwan stock market data
- **`google_api/gspread_manager.py`** — Google Sheets integration via `gspread`
- **`common/duckdb_tool.py`** — DuckDB helper functions
- **`common/tw_stock_topic.py`** — Reads stock concept/topic data from external Excel file

### Configuration
- `.env` file at `src/TuaThanTsinn_dashboard/proj_util_pkg/config/.env` (see `.env.example` for required variables: `finlab_api_token`, `gspread_wb_key`, data paths)
- `gspread_credentials.json` in the same config directory (Google API service account)
- Streamlit config at `src/TuaThanTsinn_dashboard/.streamlit/config.toml`

## Key Conventions
- Manager classes follow a singleton-like pattern (global instances)
- Type hints are used in function signatures
- Key dependencies: Streamlit, Plotly, Pandas, DuckDB, finlab, ta-lib, gspread

## Notes
- 回覆請使用繁體中文，保持專業且友善的語氣。
