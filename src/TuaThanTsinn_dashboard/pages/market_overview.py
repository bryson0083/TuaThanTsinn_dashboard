"""
市場總覽頁面

從 DuckDB 讀取加權指數與櫃買指數資料，以 Metric Cards 與走勢圖呈現。
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


# ===== 資料存取函式 =====

@st.cache_data(ttl=300)
def get_barometer_data(days: int = 130) -> pd.DataFrame:
    """
    從 DuckDB 讀取大盤溫度計資料（加權指數 + 櫃買指數）

    Args:
        days: 取最近 N 天的資料（預設 130 天）
    """
    db_path = os.environ.get('duckdb_file_path')
    if not db_path:
        return pd.DataFrame()

    try:
        conn = duckdb.connect(db_path, read_only=True)
        try:
            df = conn.execute("""
                SELECT "Date",
                       "TAIEX指數", "TAIEX_漲跌數", "TAIEX_漲跌幅",
                       "TAIEX成交金額",
                       "OTC指數", "OTC_漲跌數", "OTC_漲跌幅",
                       "OTC成交金額"
                FROM tw_sotck_barometer_part_01
                ORDER BY "Date" DESC
                LIMIT ?
            """, [days]).fetchdf()
        finally:
            conn.close()
    except Exception as e:
        st.warning(f"讀取大盤資料時發生錯誤: {e}")
        return pd.DataFrame()

    df = df.sort_values('Date').reset_index(drop=True)
    return df


@st.cache_data(ttl=300)
def get_chips_data(days: int = 130) -> pd.DataFrame:
    """
    從 DuckDB 讀取大盤籌碼資料（多表合併）

    Args:
        days: 取最近 N 天的資料（預設 130 天）
    """
    db_path = os.environ.get('duckdb_file_path')
    if not db_path:
        return pd.DataFrame()

    try:
        conn = duckdb.connect(db_path, read_only=True)
        try:
            # 加權指數
            df_taiex = conn.execute("""
                SELECT "Date", "TAIEX指數"
                FROM tw_sotck_barometer_part_01
                ORDER BY "Date" DESC
                LIMIT ?
            """, [days]).fetchdf()

            # 外資期貨淨空單口數
            df_futures = conn.execute("""
                SELECT "Date", "臺股期貨_外資"
                FROM tw_futures_institutional_investors_trading_summary
                ORDER BY "Date" DESC
                LIMIT ?
            """, [days]).fetchdf()

            # 自營商選擇權淨未平倉
            df_option = conn.execute("""
                SELECT "Date", "net_oi"
                FROM tw_option_proprietary_traders_oi
                ORDER BY "Date" DESC
                LIMIT ?
            """, [days]).fetchdf()

            # Put/Call Ratio
            df_pcr = conn.execute("""
                SELECT "Date", "PutCallOIRatio%"
                FROM tw_pc_ratio
                ORDER BY "Date" DESC
                LIMIT ?
            """, [days]).fetchdf()

            # 散戶小台 / 微台淨未平倉口數
            df_retail = conn.execute("""
                SELECT "Date", "散戶小台淨未平倉口數", "散戶微台淨未平倉口數"
                FROM tw_retail_investors_net_open_interest
                ORDER BY "Date" DESC
                LIMIT ?
            """, [days]).fetchdf()
        finally:
            conn.close()
    except Exception as e:
        st.warning(f"讀取籌碼資料時發生錯誤: {e}")
        return pd.DataFrame()

    # 以 Date 為 key 合併所有資料
    df = df_taiex
    for other in [df_futures, df_option, df_pcr, df_retail]:
        if not other.empty:
            df = pd.merge(df, other, on='Date', how='outer')

    df = df.sort_values('Date').reset_index(drop=True)
    return df


# ===== UI 顯示函式 =====

def show_metric_cards(df: pd.DataFrame):
    """顯示主要指數與成交金額 Metric Cards（四欄水平排列）"""
    latest = df.iloc[-1]
    previous = df.iloc[-2] if len(df) > 1 else None
    trade_date = pd.to_datetime(latest['Date']).strftime('%Y-%m-%d')

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        taiex_change = latest['TAIEX_漲跌數']
        taiex_pct = latest['TAIEX_漲跌幅']
        st.metric(
            label=f"加權指數（{trade_date}）",
            value=f"{latest['TAIEX指數']:,.2f}",
            delta=f"{taiex_change:+,.2f} ({taiex_pct:+.2f}%)",
            delta_color="inverse",
            help="台灣證券交易所加權股價指數",
        )

    with col2:
        otc_change = latest['OTC_漲跌數']
        otc_pct = latest['OTC_漲跌幅']
        st.metric(
            label=f"櫃買指數（{trade_date}）",
            value=f"{latest['OTC指數']:,.2f}",
            delta=f"{otc_change:+,.2f} ({otc_pct:+.2f}%)",
            delta_color="inverse",
            help="櫃買中心股價指數",
        )

    with col3:
        taiex_vol = latest['TAIEX成交金額']
        delta_str = None
        if previous is not None:
            delta_val = taiex_vol - previous['TAIEX成交金額']
            delta_str = f"{delta_val:+,.2f} 億"
        st.metric(
            label="加權成交金額（億）",
            value=f"{taiex_vol:,.2f}",
            delta=delta_str,
            delta_color="inverse",
            help="台灣證券交易所成交金額（億元）",
        )

    with col4:
        otc_vol = latest['OTC成交金額']
        delta_str = None
        if previous is not None:
            delta_val = otc_vol - previous['OTC成交金額']
            delta_str = f"{delta_val:+,.2f} 億"
        st.metric(
            label="櫃買成交金額（億）",
            value=f"{otc_vol:,.2f}",
            delta=delta_str,
            delta_color="inverse",
            help="櫃買中心成交金額（億元）",
        )


def show_chips_metric_cards(df: pd.DataFrame):
    """顯示籌碼 Metric Cards（五欄水平排列）"""
    latest = df.iloc[-1]
    previous = df.iloc[-2] if len(df) > 1 else None

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        val = latest.get('臺股期貨_外資', 0) or 0
        delta_str = None
        if previous is not None:
            prev_val = previous.get('臺股期貨_外資', 0) or 0
            delta_str = f"{val - prev_val:+,.0f}"
        st.metric(
            label="外資期貨",
            value=f"{val:,.0f}",
            delta=delta_str,
            delta_color="inverse",
        )

    with col2:
        val = latest.get('net_oi', 0) or 0
        delta_str = None
        if previous is not None:
            prev_val = previous.get('net_oi', 0) or 0
            delta_str = f"{val - prev_val:+,.0f}"
        st.metric(
            label="自營商選擇權",
            value=f"{val:,.0f}",
            delta=delta_str,
            delta_color="inverse",
        )

    with col3:
        val = latest.get('PutCallOIRatio%', 0) or 0
        delta_str = None
        if previous is not None:
            prev_val = previous.get('PutCallOIRatio%', 0) or 0
            delta_str = f"{val - prev_val:+.2f}%"
        st.metric(
            label="P/C Ratio",
            value=f"{val:.2f}%",
            delta=delta_str,
        )

    with col4:
        val = latest.get('散戶小台淨未平倉口數', 0) or 0
        delta_str = None
        if previous is not None:
            prev_val = previous.get('散戶小台淨未平倉口數', 0) or 0
            delta_str = f"{val - prev_val:+,.0f}"
        st.metric(
            label="小台散戶",
            value=f"{val:,.0f}",
            delta=delta_str,
            delta_color="inverse",
        )

    with col5:
        val = latest.get('散戶微台淨未平倉口數', 0) or 0
        delta_str = None
        if previous is not None:
            prev_val = previous.get('散戶微台淨未平倉口數', 0) or 0
            delta_str = f"{val - prev_val:+,.0f}"
        st.metric(
            label="微台散戶",
            value=f"{val:,.0f}",
            delta=delta_str,
            delta_color="inverse",
        )


def show_chips_charts(df: pd.DataFrame, display_days: int):
    """顯示大盤籌碼分析圖表（6 列子圖）"""
    plot_df = df.tail(display_days).copy()

    fig = make_subplots(
        rows=6, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.25, 0.15, 0.15, 0.15, 0.15, 0.15],
        subplot_titles=[
            '加權指數', '外資期貨淨空單口數',
            '自營商選擇權淨未平倉', 'Put/Call Ratio（OI）',
            '小台期貨淨空單口數（散戶）', '微台期貨淨空單口數（散戶）',
        ],
    )

    # Row 1：加權指數（折線圖）
    fig.add_trace(
        go.Scatter(
            x=plot_df['Date'], y=plot_df['TAIEX指數'],
            mode='lines', name='加權指數',
            line=dict(color='#ef5350', width=2),
            hovertemplate='加權: %{y:,.2f}<extra></extra>',
        ),
        row=1, col=1,
    )

    # Row 2：外資期貨淨空單口數（柱狀圖，紅漲綠跌）
    foreign_vals = plot_df['臺股期貨_外資'].fillna(0)
    fig.add_trace(
        go.Bar(
            x=plot_df['Date'], y=foreign_vals,
            name='外資期貨',
            marker_color=['#ef5350' if v >= 0 else '#26a69a' for v in foreign_vals],
            hovertemplate='外資期貨: %{y:,.0f}<extra></extra>',
        ),
        row=2, col=1,
    )

    # Row 3：自營商選擇權淨未平倉（柱狀圖，紅漲綠跌）
    option_vals = plot_df['net_oi'].fillna(0)
    fig.add_trace(
        go.Bar(
            x=plot_df['Date'], y=option_vals,
            name='自營商選擇權',
            marker_color=['#ef5350' if v >= 0 else '#26a69a' for v in option_vals],
            hovertemplate='自營商選擇權: %{y:,.0f}<extra></extra>',
        ),
        row=3, col=1,
    )

    # Row 4：Put/Call Ratio（柱狀圖，單一顏色）
    pcr_vals = plot_df['PutCallOIRatio%'].fillna(0)
    fig.add_trace(
        go.Bar(
            x=plot_df['Date'], y=pcr_vals,
            name='P/C Ratio',
            marker_color='#2196F3',
            hovertemplate='P/C Ratio: %{y:.2f}%<extra></extra>',
        ),
        row=4, col=1,
    )

    # Row 5：小台期貨淨空單口數（柱狀圖，紅漲綠跌）
    mini_vals = plot_df['散戶小台淨未平倉口數'].fillna(0)
    fig.add_trace(
        go.Bar(
            x=plot_df['Date'], y=mini_vals,
            name='小台散戶',
            marker_color=['#ef5350' if v >= 0 else '#26a69a' for v in mini_vals],
            hovertemplate='小台散戶: %{y:,.0f}<extra></extra>',
        ),
        row=5, col=1,
    )

    # Row 6：微台期貨淨空單口數（柱狀圖，紅漲綠跌）
    micro_vals = plot_df['散戶微台淨未平倉口數'].fillna(0)
    fig.add_trace(
        go.Bar(
            x=plot_df['Date'], y=micro_vals,
            name='微台散戶',
            marker_color=['#ef5350' if v >= 0 else '#26a69a' for v in micro_vals],
            hovertemplate='微台散戶: %{y:,.0f}<extra></extra>',
        ),
        row=6, col=1,
    )

    # 移除非交易日空白
    all_dates = pd.date_range(
        start=plot_df['Date'].min(),
        end=plot_df['Date'].max(),
        freq='D',
    )
    trading_dates = set(plot_df['Date'].dt.normalize())
    non_trading_dates = [d for d in all_dates if d not in trading_dates]

    fig.update_xaxes(
        rangebreaks=[dict(values=non_trading_dates)],
        tickformat="%m/%d",
        hoverformat="%Y-%m-%d",
        showgrid=True, gridwidth=1,
        gridcolor='rgba(128, 128, 128, 0.2)', griddash='dot',
    )

    # Y 軸標題
    fig.update_yaxes(title_text="指數", row=1, col=1)
    fig.update_yaxes(title_text="口數", row=2, col=1)
    fig.update_yaxes(title_text="口數", row=3, col=1)
    fig.update_yaxes(title_text="%", row=4, col=1)
    fig.update_yaxes(title_text="口數", row=5, col=1)
    fig.update_yaxes(title_text="口數", row=6, col=1)

    fig.update_layout(
        height=900,
        hovermode='x unified',
        xaxis_rangeslider_visible=False,
        showlegend=False,
    )

    st.plotly_chart(fig, width='stretch')


def show_trend_charts(df: pd.DataFrame, display_days: int):
    """顯示市場走勢圖（雙 Y 軸子圖）"""
    st.subheader("市場走勢圖")

    plot_df = df.tail(display_days).copy()

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.6, 0.4],
        subplot_titles=['指數走勢', '成交金額（億）'],
        specs=[[{"secondary_y": True}], [{"secondary_y": True}]],
    )

    # 上圖：加權指數（左 Y 軸）
    fig.add_trace(
        go.Scatter(
            x=plot_df['Date'], y=plot_df['TAIEX指數'],
            mode='lines', name='加權指數',
            line=dict(color='#ef5350', width=2),
            hovertemplate='加權: %{y:,.2f}<extra></extra>',
        ),
        row=1, col=1, secondary_y=False,
    )

    # 上圖：櫃買指數（右 Y 軸）
    fig.add_trace(
        go.Scatter(
            x=plot_df['Date'], y=plot_df['OTC指數'],
            mode='lines', name='櫃買指數',
            line=dict(color='#2196F3', width=2),
            hovertemplate='櫃買: %{y:,.2f}<extra></extra>',
        ),
        row=1, col=1, secondary_y=True,
    )

    # 下圖：加權成交金額（柱狀）
    fig.add_trace(
        go.Bar(
            x=plot_df['Date'], y=plot_df['TAIEX成交金額'],
            name='加權成交金額',
            marker_color='rgba(239, 83, 80, 0.5)',
            hovertemplate='加權成交: %{y:,.2f} 億<extra></extra>',
        ),
        row=2, col=1, secondary_y=False,
    )

    # 下圖：櫃買成交金額（折線）
    fig.add_trace(
        go.Scatter(
            x=plot_df['Date'], y=plot_df['OTC成交金額'],
            mode='lines', name='櫃買成交金額',
            line=dict(color='#2196F3', width=1.5),
            hovertemplate='櫃買成交: %{y:,.2f} 億<extra></extra>',
        ),
        row=2, col=1, secondary_y=True,
    )

    # 移除非交易日空白
    all_dates = pd.date_range(
        start=plot_df['Date'].min(),
        end=plot_df['Date'].max(),
        freq='D',
    )
    trading_dates = set(plot_df['Date'].dt.normalize())
    non_trading_dates = [d for d in all_dates if d not in trading_dates]

    fig.update_xaxes(
        rangebreaks=[dict(values=non_trading_dates)],
        tickformat="%m/%d",
        hoverformat="%Y-%m-%d",
        showgrid=True, gridwidth=1,
        gridcolor='rgba(128, 128, 128, 0.2)', griddash='dot',
    )

    # Y 軸標題
    fig.update_yaxes(title_text="加權指數", row=1, col=1, secondary_y=False)
    fig.update_yaxes(title_text="櫃買指數", row=1, col=1, secondary_y=True)
    fig.update_yaxes(title_text="加權（億）", row=2, col=1, secondary_y=False)
    fig.update_yaxes(title_text="櫃買（億）", row=2, col=1, secondary_y=True)

    fig.update_layout(
        height=550,
        hovermode='x unified',
        xaxis_rangeslider_visible=False,
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right", x=1,
        ),
    )

    st.plotly_chart(fig, width='stretch')


# ===== 主程式 =====

def main():
    """主程式"""
    show_navigation_menu()

    st.title("市場總覽")

    tab_market, tab_chips = st.tabs(["台股大盤", "大盤籌碼"])

    with tab_market:
        # 顯示期間選擇器
        display_days = st.selectbox(
            "顯示期間",
            options=[30, 60, 120, 250],
            index=2,
            format_func=lambda x: f"近 {x} 個交易日",
        )

        # 多取一些資料供成交金額 delta 計算
        df = get_barometer_data(days=display_days + 10)

        if df.empty:
            st.error("無法取得市場資料，請確認 DuckDB 資料庫路徑設定是否正確。")
            st.info("請確認環境變數 `duckdb_file_path` 已正確設定，"
                    "並且資料庫中包含 `tw_sotck_barometer_part_01` 資料表。")
        else:
            # Metric Cards
            show_metric_cards(df)

            # 走勢圖
            show_trend_charts(df, display_days)

    with tab_chips:
        # 顯示期間選擇器
        chips_days = st.selectbox(
            "顯示期間",
            options=[30, 60, 120, 250],
            index=2,
            format_func=lambda x: f"近 {x} 個交易日",
            key="chips_display_days",
        )

        chips_df = get_chips_data(days=chips_days + 10)

        if chips_df.empty:
            st.error("無法取得籌碼資料，請確認 DuckDB 資料庫路徑設定是否正確。")
        else:
            show_chips_metric_cards(chips_df)
            show_chips_charts(chips_df, chips_days)

    # 頁尾
    st.markdown("---")
    st.caption(f"最後更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
