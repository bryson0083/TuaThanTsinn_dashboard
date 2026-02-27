"""
RSMACD（MACD 強度指標）分析頁面

將 RSI 演算法套用在 MACD 線上，正規化為 0-100 區間的震盪指標，
搭配六種買賣信號進行技術分析。
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
from proj_util_pkg.indicators.rsmacd_indicators import RSMACDIndicators


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
def get_stock_price(symbol: str, days: int = 600) -> pd.DataFrame:
    """
    從 DuckDB 讀取指定股票的歷史價格資料

    Args:
        symbol: 股票代碼
        days: 取最近 N 天的資料（預設 600 天，確保 RSMACD 有足夠暖機數據）
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

def create_rsmacd_chart(
    df: pd.DataFrame,
    signal_df: pd.DataFrame,
    title: str,
    display_days: int = 120,
) -> go.Figure:
    """
    建立 RSMACD 分析圖表

    Args:
        df: 含指標的完整 DataFrame
        signal_df: 去重後的信號 DataFrame
        title: 圖表標題
        display_days: 顯示最近 N 天的資料
    """
    plot_df = df.tail(display_days).copy()

    # 建立子圖：第 1 列 K 線，第 2 列 RSMACD，第 3 列 MACD
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.5, 0.3, 0.2],
        subplot_titles=['', 'RSMACD', 'MACD'],
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
            decreasing_fillcolor='#26a69a',
        ),
        row=1, col=1,
    )

    # --- 第 1 列：MA 均線 ---
    ma_config = [
        ('MA5', '#2196F3', 'MA5'),
        ('MA20', '#FF9800', 'MA20'),
        ('MA60', '#9E9E9E', 'MA60'),
    ]
    for col_name, color, name in ma_config:
        ma_valid = plot_df[plot_df[col_name].notna()]
        if not ma_valid.empty:
            fig.add_trace(
                go.Scatter(
                    x=ma_valid['Date'],
                    y=ma_valid[col_name],
                    mode='lines',
                    name=name,
                    line=dict(color=color, width=1.5),
                    hovertemplate=f'{name}: %{{y:.2f}}<extra></extra>',
                ),
                row=1, col=1,
            )

    # --- 第 1 列：ATR 移動停損線 ---
    if 'atr_trailing_stop' in plot_df.columns:
        stop_valid = plot_df[plot_df['atr_trailing_stop'].notna()]
    else:
        stop_valid = pd.DataFrame()
    if not stop_valid.empty:
        fig.add_trace(
            go.Scatter(
                x=stop_valid['Date'],
                y=stop_valid['atr_trailing_stop'],
                mode='lines',
                name='ATR停損',
                line=dict(color='#E91E63', width=1.5, dash='dot'),
                hovertemplate='ATR停損: %{y:.2f}<extra></extra>',
            ),
            row=1, col=1,
        )

    # --- 第 2 列：RSMACD 曲線 ---
    rsmacd_valid = plot_df[plot_df['rsmacd'].notna()]
    fig.add_trace(
        go.Scatter(
            x=rsmacd_valid['Date'],
            y=rsmacd_valid['rsmacd'],
            mode='lines',
            name='RSMACD',
            line=dict(color='#7B1FA2', width=2),
            hovertemplate='RSMACD: %{y:.2f}<extra></extra>',
        ),
        row=2, col=1,
    )

    # --- 參考線（超買/超賣/中性） ---
    fig.add_hline(
        y=70, line_dash="dash", line_color="#ef5350", line_width=1,
        annotation_text="超買(70)", annotation_position="top left",
        annotation_font_size=10, annotation_font_color="#ef5350",
        row=2, col=1,
    )
    fig.add_hline(
        y=50, line_dash="dash", line_color="gray", line_width=1,
        row=2, col=1,
    )
    fig.add_hline(
        y=30, line_dash="dash", line_color="#26a69a", line_width=1,
        annotation_text="超賣(30)", annotation_position="bottom left",
        annotation_font_size=10, annotation_font_color="#26a69a",
        row=2, col=1,
    )

    # --- 信號標記 ---
    signal_marker_config = {
        'signal_green_arrow': {
            'name': '綠色菱形（翻揚）',
            'symbol': 'diamond',
            'color': '#26a69a',
            'y_pos': 5,
            'size': 12,
        },
        'signal_green_triangle': {
            'name': '綠色三角形（突破30）',
            'symbol': 'triangle-up',
            'color': '#00C853',
            'y_pos': 10,
            'size': 14,
        },
        'signal_green_ball': {
            'name': '綠色小球（翻揚+突破50）',
            'symbol': 'circle',
            'color': '#26a69a',
            'y_pos': 15,
            'size': 10,
        },
        'signal_red_arrow': {
            'name': '紅色菱形（翻落）',
            'symbol': 'diamond',
            'color': '#ef5350',
            'y_pos': 95,
            'size': 12,
        },
        'signal_red_triangle': {
            'name': '紅色倒三角形（跌破70）',
            'symbol': 'triangle-down',
            'color': '#FF1744',
            'y_pos': 90,
            'size': 14,
        },
        'signal_red_ball': {
            'name': '紅色小球（翻落+跌破50）',
            'symbol': 'circle',
            'color': '#ef5350',
            'y_pos': 85,
            'size': 10,
        },
    }

    if not signal_df.empty:
        display_start = plot_df['Date'].min()
        display_signals = signal_df[signal_df['Date'] >= display_start]

        for col_name, config in signal_marker_config.items():
            if col_name not in display_signals.columns:
                continue
            sig_rows = display_signals[display_signals[col_name] == True]
            if sig_rows.empty:
                continue

            fig.add_trace(
                go.Scatter(
                    x=sig_rows['Date'],
                    y=[config['y_pos']] * len(sig_rows),
                    mode='markers',
                    name=config['name'],
                    marker=dict(
                        symbol=config['symbol'],
                        size=config['size'],
                        color=config['color'],
                        line=dict(width=1, color='white'),
                    ),
                    hovertemplate=(
                        f"{config['name']}<br>"
                        "日期: %{x}<br>"
                        "<extra></extra>"
                    ),
                ),
                row=2, col=1,
            )

    # --- 第 3 列：MACD ---
    macd_valid = plot_df[plot_df['macd_line'].notna()]

    # MACD 線
    fig.add_trace(
        go.Scatter(
            x=macd_valid['Date'],
            y=macd_valid['macd_line'],
            mode='lines',
            name='MACD',
            line=dict(color='#2196F3', width=1.5),
            hovertemplate='MACD: %{y:.2f}<extra></extra>',
        ),
        row=3, col=1,
    )

    # Signal 線
    fig.add_trace(
        go.Scatter(
            x=macd_valid['Date'],
            y=macd_valid['macd_signal'],
            mode='lines',
            name='Signal',
            line=dict(color='#FF9800', width=1.5),
            hovertemplate='Signal: %{y:.2f}<extra></extra>',
        ),
        row=3, col=1,
    )

    # Histogram 柱狀圖（正紅負綠）
    hist_colors = [
        '#ef5350' if v >= 0 else '#26a69a'
        for v in macd_valid['macd_histogram']
    ]
    fig.add_trace(
        go.Bar(
            x=macd_valid['Date'],
            y=macd_valid['macd_histogram'],
            name='Histogram',
            marker_color=hist_colors,
            hovertemplate='Histogram: %{y:.2f}<extra></extra>',
        ),
        row=3, col=1,
    )

    # 零軸參考線
    fig.add_hline(
        y=0, line_dash="dash", line_color="gray", line_width=1,
        row=3, col=1,
    )

    # --- 版面配置 ---
    fig.update_layout(
        title=dict(text=title, y=0.98, x=0, xanchor='left'),
        yaxis_title='價格',
        xaxis_rangeslider_visible=False,
        height=850,
        margin=dict(t=120),
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="left", x=0,
        ),
    )

    # 計算所有非交易日（週末 + 假期），讓 K 線連續不留空白
    all_dates = pd.date_range(start=plot_df['Date'].min(), end=plot_df['Date'].max(), freq='D')
    trading_dates = set(plot_df['Date'].dt.normalize())
    non_trading_dates = [d for d in all_dates if d not in trading_dates]

    fig.update_xaxes(
        rangebreaks=[dict(values=non_trading_dates)],
        tickformat="%m/%d",
        dtick=7 * 24 * 60 * 60 * 1000,
        hoverformat="%Y-%m-%d",
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128, 128, 128, 0.2)',
        griddash='dot',
    )

    fig.update_yaxes(title_text="RSMACD", range=[-5, 105], row=2, col=1)
    fig.update_yaxes(title_text="MACD", row=3, col=1)

    return fig


# ===== 頁面 UI 函式 =====

def show_stock_input(stock_list_df: pd.DataFrame):
    """顯示股票輸入區域，回傳 (stock_id, stock_name, display_days, control_ma_period, atr_period, atr_multiplier)"""
    col1, col2, col3 = st.columns([1, 1, 1])

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
            format_func=lambda x: f"近 {x} 個交易日",
        )

    # ATR 移動停損參數
    col_atr1, col_atr2, col_atr3 = st.columns([1, 1, 1])

    with col_atr1:
        control_ma_period = st.number_input("控盤均線", min_value=5, max_value=120, value=20, step=1)

    with col_atr2:
        atr_period = st.number_input("ATR 週期", min_value=5, max_value=50, value=14, step=1)

    with col_atr3:
        atr_multiplier = st.number_input("ATR 乘數", min_value=0.5, max_value=5.0, value=2.0, step=0.1)

    return stock_id.strip(), stock_name, display_days, control_ma_period, atr_period, atr_multiplier


def show_signal_summary(signal_df: pd.DataFrame):
    """顯示信號摘要統計"""
    st.subheader("信號統計")

    if signal_df.empty:
        st.info("此期間無任何 RSMACD 信號")
        return

    signal_counts = {
        'signal_green_arrow': 0,
        'signal_green_triangle': 0,
        'signal_green_ball': 0,
        'signal_red_arrow': 0,
        'signal_red_triangle': 0,
        'signal_red_ball': 0,
    }

    for col in signal_counts:
        if col in signal_df.columns:
            signal_counts[col] = int(signal_df[col].sum())

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric("翻揚", f"{signal_counts['signal_green_arrow']} 次")
    with col2:
        st.metric("突破30", f"{signal_counts['signal_green_triangle']} 次")
    with col3:
        st.metric("翻揚+破50", f"{signal_counts['signal_green_ball']} 次")
    with col4:
        st.metric("翻落", f"{signal_counts['signal_red_arrow']} 次")
    with col5:
        st.metric("跌破70", f"{signal_counts['signal_red_triangle']} 次")
    with col6:
        st.metric("翻落+破50", f"{signal_counts['signal_red_ball']} 次")


def show_signal_table(signal_df: pd.DataFrame):
    """顯示信號明細表格"""
    st.subheader("信號明細")

    if signal_df.empty:
        st.info("此期間無任何 RSMACD 信號")
        return

    display_cols = ['Date', 'close', 'rsmacd', 'signal_type']
    available_cols = [c for c in display_cols if c in signal_df.columns]
    table_df = signal_df[available_cols].copy()

    table_df = table_df.rename(columns={
        'Date': '日期',
        'close': '收盤價',
        'rsmacd': 'RSMACD',
        'signal_type': '信號類型',
    })

    # 最新信號在前
    table_df = table_df.sort_values('日期', ascending=False).reset_index(drop=True)

    st.dataframe(
        table_df.style.format({
            '收盤價': '{:.2f}',
            'RSMACD': '{:.2f}',
        }),
        width="stretch",
    )


# ===== 主程式 =====

def main():
    """主程式"""
    show_navigation_menu()

    st.title("RSMACD 強度指標分析")
    st.markdown("### 將 RSI 套用在 MACD 線上的正規化震盪指標")

    # 讀取股票清單
    stock_list_df = get_stock_list()

    # 使用者輸入
    stock_id, stock_name, display_days, control_ma_period, atr_period, atr_multiplier = show_stock_input(stock_list_df)

    if not stock_id:
        st.warning("請輸入股票代碼")
        return

    if not stock_name:
        st.warning(f"找不到股票代碼 {stock_id} 的資料，請確認代碼是否正確")
        return

    # 取得價格資料（多抓 120 天作為 MACD + RSI 計算緩衝）
    fetch_days = display_days + 120
    price_df = get_stock_price(stock_id, fetch_days)

    if price_df.empty:
        st.error(f"無法取得 {stock_id} 的價格資料")
        return

    # 計算指標
    df_with_indicators = RSMACDIndicators.compute_indicators(
        price_df, control_ma_period=control_ma_period,
        atr_period=atr_period, atr_multiplier=atr_multiplier
    )

    # 產生信號
    df_with_signals = RSMACDIndicators.generate_signals(df_with_indicators)

    # 信號去重
    signal_df = RSMACDIndicators.deduplicate_signals(df_with_signals)

    # 繪製圖表
    chart_title = f"{stock_id} {stock_name} — RSMACD 強度指標分析"
    fig = create_rsmacd_chart(df_with_signals, signal_df, chart_title, display_days)
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
