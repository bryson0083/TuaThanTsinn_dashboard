"""
CIS + 2560 戰法分析頁面

結合 CIS 選股策略與 2560 量能確認的技術分析視覺化工具。
使用者輸入股票代碼後，顯示 K 線圖、CIS 買賣信號及 2560 量能分析。
"""

import streamlit as st
import pandas as pd
import duckdb
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import sys

# 添加父目錄到路徑以導入共用模組
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from menu import show_navigation_menu

# 載入環境設定
from proj_util_pkg.settings import settings
from proj_util_pkg.indicators.cis_2560_indicators import CIS2560Indicators


# ===== 資料存取函式 =====

@st.cache_data(ttl=300)
def get_stock_list() -> pd.DataFrame:
    """從 DuckDB 讀取 tw_stock_list 取得股票清單"""
    db_path = os.environ.get('duckdb_file_path')
    if not db_path:
        return pd.DataFrame(columns=['stock_id', 'stock_name'])

    conn = duckdb.connect(db_path, read_only=True)
    try:
        df = conn.execute(
            "SELECT stock_id, stock_name FROM tw_stock_list ORDER BY stock_id"
        ).fetchdf()
    finally:
        conn.close()
    return df


@st.cache_data(ttl=300)
def get_stock_price(symbol: str, days: int = 500) -> pd.DataFrame:
    """
    從 DuckDB 讀取指定股票的歷史價格資料

    Args:
        symbol: 股票代碼
        days: 取最近 N 天的資料（預設 500 天，確保 60 日均線有足夠數據）
    """
    db_path = os.environ.get('duckdb_file_path')
    if not db_path:
        return pd.DataFrame()

    conn = duckdb.connect(db_path, read_only=True)
    try:
        df = conn.execute("""
            SELECT Date, open, high, low, close, vol
            FROM tw_stock_daily_txn
            WHERE symbol = ?
            ORDER BY Date DESC
            LIMIT ?
        """, [symbol, days]).fetchdf()
    finally:
        conn.close()

    # 依日期升冪排序
    df = df.sort_values('Date').reset_index(drop=True)
    return df


def lookup_stock_name(stock_list_df: pd.DataFrame, stock_id: str) -> str:
    """查詢股票名稱，找不到則回傳空字串"""
    match = stock_list_df[stock_list_df['stock_id'] == stock_id]
    if not match.empty:
        return match.iloc[0]['stock_name']
    return ''


# ===== 圖表建立函式 =====

def create_cis_2560_chart(
    df: pd.DataFrame,
    signal_df: pd.DataFrame,
    title: str,
    display_days: int = 120
) -> go.Figure:
    """
    建立 CIS + 2560 K 線圖

    Args:
        df: 含指標的完整 DataFrame
        signal_df: 去重後的信號 DataFrame
        title: 圖表標題
        display_days: 顯示最近 N 天的資料
    """
    plot_df = df.tail(display_days).copy()

    # 建立子圖：第 1 列 K 線 + 均線，第 2 列成交量
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.7, 0.3],
        subplot_titles=['', '成交量']
    )

    # --- 第 1 列：K 線 ---
    fig.add_trace(
        go.Candlestick(
            x=plot_df['Date'],
            open=plot_df['open'],
            high=plot_df['high'],
            low=plot_df['low'],
            close=plot_df['close'],
            name='K線',
            increasing_line_color='#ef5350',
            decreasing_line_color='#26a69a',
            increasing_fillcolor='#ef5350',
            decreasing_fillcolor='#26a69a'
        ),
        row=1, col=1
    )

    # SMA5（藍色）
    sma5_valid = plot_df[plot_df['SMA5'].notna()]
    fig.add_trace(
        go.Scatter(
            x=sma5_valid['Date'], y=sma5_valid['SMA5'],
            mode='lines', name='MA5',
            line=dict(color='#2196F3', width=1.5)
        ),
        row=1, col=1
    )

    # SMA25（橘色）
    sma25_valid = plot_df[plot_df['SMA25'].notna()]
    fig.add_trace(
        go.Scatter(
            x=sma25_valid['Date'], y=sma25_valid['SMA25'],
            mode='lines', name='MA25',
            line=dict(color='#FF9800', width=1.5)
        ),
        row=1, col=1
    )

    # --- 第 2 列：成交量 ---
    vol_colors = [
        '#ef5350' if c >= o else '#26a69a'
        for c, o in zip(plot_df['close'], plot_df['open'])
    ]
    fig.add_trace(
        go.Bar(
            x=plot_df['Date'], y=plot_df['vol'],
            name='成交量', marker_color=vol_colors,
            hovertemplate='成交量: %{y:,.0f}<extra></extra>'
        ),
        row=2, col=1
    )

    # Vol_SMA5（藍色虛線）
    vol_sma5_valid = plot_df[plot_df['Vol_SMA5'].notna()]
    fig.add_trace(
        go.Scatter(
            x=vol_sma5_valid['Date'], y=vol_sma5_valid['Vol_SMA5'],
            mode='lines', name='Vol MA5',
            line=dict(color='#2196F3', width=1, dash='dot')
        ),
        row=2, col=1
    )

    # Vol_SMA60（橘色虛線）
    vol_sma60_valid = plot_df[plot_df['Vol_SMA60'].notna()]
    fig.add_trace(
        go.Scatter(
            x=vol_sma60_valid['Date'], y=vol_sma60_valid['Vol_SMA60'],
            mode='lines', name='Vol MA60',
            line=dict(color='#FF9800', width=1, dash='dot')
        ),
        row=2, col=1
    )

    # --- 信號標註 ---
    if not signal_df.empty:
        display_start = plot_df['Date'].min()
        display_signals = signal_df[signal_df['Date'] >= display_start]

        price_range = plot_df['high'].max() - plot_df['low'].min()
        offset = price_range * 0.05

        signal_config = {
            'CIS買':   {'color': '#2196F3', 'ay': 40,  'price_col': 'low',  'offset_sign': -1},
            'CIS逆買': {'color': '#9C27B0', 'ay': 40,  'price_col': 'low',  'offset_sign': -1},
            'CIS賣':   {'color': '#FF5722', 'ay': -40, 'price_col': 'high', 'offset_sign': 1},
        }

        for _, row in display_signals.iterrows():
            signal_type_str = row['signal_type']
            for sig_name, config in signal_config.items():
                if sig_name in signal_type_str:
                    price_val = row[config['price_col']]
                    fig.add_annotation(
                        x=row['Date'],
                        y=price_val + config['offset_sign'] * offset,
                        text=sig_name,
                        showarrow=True,
                        arrowhead=2,
                        arrowsize=1.5,
                        arrowwidth=2,
                        arrowcolor=config['color'],
                        ax=0,
                        ay=config['ay'],
                        font=dict(size=10, color=config['color']),
                        bgcolor='rgba(255, 255, 255, 0.8)',
                        bordercolor=config['color'],
                        borderwidth=1,
                        borderpad=3,
                        row=1, col=1
                    )

    # --- 版面配置 ---
    fig.update_layout(
        title=title,
        yaxis_title='價格',
        xaxis_rangeslider_visible=False,
        height=650,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right", x=1
        )
    )

    fig.update_xaxes(
        rangebreaks=[dict(bounds=["sat", "mon"])],
        tickformat="%m/%d",
        dtick=7 * 24 * 60 * 60 * 1000,
        hoverformat="%Y-%m-%d",
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128, 128, 128, 0.2)',
        griddash='dot',
    )

    fig.update_yaxes(title_text="成交量", row=2, col=1)

    return fig


# ===== 頁面 UI 函式 =====

def show_stock_input(stock_list_df: pd.DataFrame):
    """顯示股票輸入區域，回傳 (stock_id, stock_name, display_days, enable_vol_confirm)"""
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    with col1:
        stock_id = st.text_input("股票代碼", value="2330", max_chars=10)

    with col2:
        stock_name = lookup_stock_name(stock_list_df, stock_id.strip())
        st.text_input("股票名稱", value=stock_name, disabled=True)

    with col3:
        display_days = st.selectbox(
            "顯示期間",
            options=[60, 120, 250, 500],
            index=1,
            format_func=lambda x: f"近 {x} 個交易日"
        )

    with col4:
        enable_vol_confirm = st.checkbox("啟用 2560 量能確認", value=True)

    return stock_id.strip(), stock_name, display_days, enable_vol_confirm


def show_signal_summary(signal_df: pd.DataFrame):
    """顯示信號摘要統計"""
    st.subheader("信號統計")

    if signal_df.empty:
        st.info("此期間無任何 CIS 信號")
        return

    buy_count = signal_df['signal_type'].str.contains('CIS買').sum()
    rev_buy_count = signal_df['signal_type'].str.contains('CIS逆買').sum()
    sell_count = signal_df['signal_type'].str.contains('CIS賣').sum()
    # CIS買 計數中扣除同時包含 CIS逆買 的列（避免雙重計算）
    pure_buy = buy_count - rev_buy_count

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("CIS買", f"{pure_buy} 次")
    with col2:
        st.metric("CIS逆買", f"{rev_buy_count} 次")
    with col3:
        st.metric("CIS賣", f"{sell_count} 次")
    with col4:
        st.metric("信號總數", f"{len(signal_df)} 次")


def show_signal_table(signal_df: pd.DataFrame):
    """顯示信號明細表格"""
    st.subheader("信號明細")

    if signal_df.empty:
        st.info("此期間無任何 CIS 信號")
        return

    display_cols = ['Date', 'close', 'SMA5', 'SMA25', 'Vol_SMA5', 'Vol_SMA60', 'signal_type']
    available_cols = [c for c in display_cols if c in signal_df.columns]
    table_df = signal_df[available_cols].copy()

    table_df = table_df.rename(columns={
        'Date': '日期', 'close': '收盤價',
        'SMA5': '5MA', 'SMA25': '25MA',
        'Vol_SMA5': '5日均量', 'Vol_SMA60': '60日均量',
        'signal_type': '信號類型'
    })

    # 最新信號在前
    table_df = table_df.sort_values('日期', ascending=False).reset_index(drop=True)

    st.dataframe(
        table_df.style.format({
            '收盤價': '{:.2f}',
            '5MA': '{:.2f}',
            '25MA': '{:.2f}',
            '5日均量': '{:,.0f}',
            '60日均量': '{:,.0f}',
        }),
        width="stretch"
    )


# ===== 主程式 =====

def main():
    """主程式"""
    show_navigation_menu()

    st.title("CIS + 2560 戰法分析")
    st.markdown("### 結合 CIS 選股策略與 2560 量能確認的技術分析工具")

    # 讀取股票清單
    stock_list_df = get_stock_list()

    # 使用者輸入
    stock_id, stock_name, display_days, enable_vol_confirm = show_stock_input(stock_list_df)

    if not stock_id:
        st.warning("請輸入股票代碼")
        return

    if not stock_name:
        st.warning(f"找不到股票代碼 {stock_id} 的資料，請確認代碼是否正確")
        return

    # 取得價格資料（多抓 80 天作為均線計算緩衝）
    fetch_days = display_days + 80
    price_df = get_stock_price(stock_id, fetch_days)

    if price_df.empty:
        st.error(f"無法取得 {stock_id} 的價格資料")
        return

    # 計算指標
    df_with_indicators = CIS2560Indicators.compute_indicators(price_df)

    # 產生信號
    df_with_signals = CIS2560Indicators.generate_signals(
        df_with_indicators,
        enable_volume_confirmation=enable_vol_confirm
    )

    # 信號去重
    signal_df = CIS2560Indicators.deduplicate_signals(df_with_signals)

    # 繪製圖表
    chart_title = f"{stock_id} {stock_name} — CIS + 2560 戰法分析"
    fig = create_cis_2560_chart(df_with_signals, signal_df, chart_title, display_days)
    st.plotly_chart(fig, width="stretch")

    # 信號統計
    show_signal_summary(signal_df)

    # 信號明細
    show_signal_table(signal_df)

    # 頁尾
    st.markdown("---")
    st.caption(f"最後更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
