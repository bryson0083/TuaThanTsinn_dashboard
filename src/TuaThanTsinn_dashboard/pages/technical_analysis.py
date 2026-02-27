"""
技術分析頁面
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sys
import os

# 添加父目錄到路徑以導入共用模組
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from menu import show_navigation_menu

def generate_sample_data(stock_id: str, days: int = 252):
    """生成示例股價資料"""
    np.random.seed(hash(stock_id) % 2**32)

    dates = pd.date_range(start=datetime.now() - timedelta(days=days),
                         end=datetime.now(), freq='D')

    # 生成OHLC資料
    base_price = 100
    prices = []

    for i in range(len(dates)):
        if i == 0:
            open_price = base_price
        else:
            open_price = prices[-1]['close']

        # 隨機波動
        change = np.random.normal(0, 2)
        close_price = max(open_price + change, 1)

        high_price = max(open_price, close_price) + abs(np.random.normal(0, 1))
        low_price = min(open_price, close_price) - abs(np.random.normal(0, 1))
        low_price = max(low_price, 1)

        volume = int(np.random.normal(10000, 3000))
        volume = max(volume, 1000)

        prices.append({
            'date': dates[i],
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': volume
        })

    return pd.DataFrame(prices)

def calculate_moving_averages(df: pd.DataFrame):
    """計算移動平均線"""
    df['MA5'] = df['close'].rolling(window=5).mean()
    df['MA10'] = df['close'].rolling(window=10).mean()
    df['MA20'] = df['close'].rolling(window=20).mean()
    df['MA60'] = df['close'].rolling(window=60).mean()
    return df

def calculate_rsi(df: pd.DataFrame, period: int = 14):
    """計算RSI指標"""
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def generate_sample_annotations(df: pd.DataFrame):
    """生成示例買賣點標注"""
    annotations = []
    rsi = calculate_rsi(df)

    for i in range(20, len(df) - 5):
        # 示例：RSI 超賣後回升作為買點
        if rsi.iloc[i-1] < 30 and rsi.iloc[i] >= 30:
            annotations.append({
                'date': df.iloc[i]['date'],
                'price': df.iloc[i]['low'],
                'text': '買點',
                'type': 'buy'
            })
        # 示例：RSI 超買後回落作為賣點
        elif rsi.iloc[i-1] > 70 and rsi.iloc[i] <= 70:
            annotations.append({
                'date': df.iloc[i]['date'],
                'price': df.iloc[i]['high'],
                'text': '賣點',
                'type': 'sell'
            })

    return annotations

def create_candlestick_chart(df: pd.DataFrame, title: str, show_ma: bool, show_rsi: bool, show_volume: bool, annotations: list = None):
    """建立K線圖 - 使用 Plotly

    Args:
        annotations: 標注列表，每個標注為 dict，包含:
            - date: 日期
            - price: 價格位置
            - text: 標注文字 (如 "買點"、"賣點")
            - type: 類型 ('buy' 或 'sell')
    """
    # 計算需要的子圖數量和標題
    rows = 1
    row_heights = [0.6]
    subplot_titles = ['']

    if show_volume:
        rows += 1
        row_heights.append(0.2)
        subplot_titles.append('成交量')
    if show_rsi:
        rows += 1
        row_heights.append(0.2)
        subplot_titles.append('RSI')

    # 建立子圖
    fig = make_subplots(
        rows=rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=row_heights,
        subplot_titles=subplot_titles
    )

    # K線圖 (台股慣例：紅漲綠跌)
    fig.add_trace(
        go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='K線',
            increasing_line_color='#ef5350',
            decreasing_line_color='#26a69a',
            increasing_fillcolor='#ef5350',
            decreasing_fillcolor='#26a69a'
        ),
        row=1, col=1
    )

    # 移動平均線
    if show_ma:
        if 'MA5' in df.columns:
            ma5_valid = df[df['MA5'].notna()]
            fig.add_trace(
                go.Scatter(
                    x=ma5_valid['date'],
                    y=ma5_valid['MA5'],
                    mode='lines',
                    name='MA5',
                    line=dict(color='orange', width=1),
                    connectgaps=True
                ),
                row=1, col=1
            )

        if 'MA20' in df.columns:
            ma20_valid = df[df['MA20'].notna()]
            fig.add_trace(
                go.Scatter(
                    x=ma20_valid['date'],
                    y=ma20_valid['MA20'],
                    mode='lines',
                    name='MA20',
                    line=dict(color='blue', width=1),
                    connectgaps=True
                ),
                row=1, col=1
            )

    current_row = 2

    # 成交量
    if show_volume:
        colors = ['#ef5350' if close >= open else '#26a69a'
                  for close, open in zip(df['close'], df['open'])]

        fig.add_trace(
            go.Bar(
                x=df['date'],
                y=df['volume'],
                name='成交量',
                marker_color=colors,
                hovertemplate='成交量: %{y:,.0f}<extra></extra>'
            ),
            row=current_row, col=1
        )
        fig.update_yaxes(title_text="成交量", row=current_row, col=1)
        current_row += 1

    # RSI 指標
    if show_rsi:
        rsi = calculate_rsi(df)
        rsi_valid = rsi.notna()

        fig.add_trace(
            go.Scatter(
                x=df.loc[rsi_valid, 'date'],
                y=rsi[rsi_valid],
                mode='lines',
                name='RSI',
                line=dict(color='purple', width=1.5),
                connectgaps=True,
                hovertemplate='RSI: %{y:.2f}<extra></extra>'
            ),
            row=current_row, col=1
        )

        # RSI 超買超賣線
        fig.add_hline(y=70, line_dash="dash", line_color="red",
                      annotation_text="超買(70)", row=current_row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green",
                      annotation_text="超賣(30)", row=current_row, col=1)

        fig.update_yaxes(title_text="RSI", range=[0, 100], row=current_row, col=1)

    # 加入買賣點標注
    if annotations:
        # 計算價格範圍，用於設定箭頭與K線的間距
        price_range = df['high'].max() - df['low'].min()
        offset = price_range * 0.12  # K線與箭頭尖端的間距（價格的12%）

        for ann in annotations:
            if ann['type'] == 'buy':
                # 買點：藍色箭頭向上，標注在K線下方
                arrow_y = ann['price'] - offset  # 箭頭尖端位置（K線下方留間距）
                fig.add_annotation(
                    x=ann['date'],
                    y=arrow_y,
                    text=ann['text'],
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1.5,
                    arrowwidth=2,
                    arrowcolor='#2196F3',
                    ax=0,
                    ay=45,
                    font=dict(size=11, color='#2196F3', weight='bold'),
                    bgcolor='rgba(33, 150, 243, 0.15)',
                    bordercolor='#2196F3',
                    borderwidth=1,
                    borderpad=3,
                    row=1, col=1
                )
            elif ann['type'] == 'sell':
                # 賣點：橘色箭頭向下，標注在K線上方
                arrow_y = ann['price'] + offset  # 箭頭尖端位置（K線上方留間距）
                fig.add_annotation(
                    x=ann['date'],
                    y=arrow_y,
                    text=ann['text'],
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1.5,
                    arrowwidth=2,
                    arrowcolor='#FF9800',
                    ax=0,
                    ay=-45,
                    font=dict(size=11, color='#FF9800', weight='bold'),
                    bgcolor='rgba(255, 152, 0, 0.15)',
                    bordercolor='#FF9800',
                    borderwidth=1,
                    borderpad=3,
                    row=1, col=1
                )

    # 更新版面配置
    fig.update_layout(
        title=title,
        yaxis_title='價格',
        xaxis_rangeslider_visible=False,
        height=650 if (show_volume and show_rsi) else (550 if (show_volume or show_rsi) else 450),
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    # 計算所有非交易日（週末 + 假期），讓 K 線連續不留空白
    all_dates = pd.date_range(start=df['date'].min(), end=df['date'].max(), freq='D')
    trading_dates = set(pd.to_datetime(df['date']).dt.normalize())
    non_trading_dates = [d for d in all_dates if d not in trading_dates]

    # 設定 X 軸（隱藏非交易日間隙、日期格式、格線）
    fig.update_xaxes(
        rangebreaks=[dict(values=non_trading_dates)],
        tickformat="%m/%d",  # 日期格式：月/日
        dtick=7 * 24 * 60 * 60 * 1000,  # 每週顯示一次刻度（毫秒）
        hoverformat="%Y-%m-%d",  # hover 時顯示完整日期
        showgrid=True,  # 顯示垂直格線
        gridwidth=1,
        gridcolor='rgba(128, 128, 128, 0.2)',  # 淺灰色格線
        griddash='dot',  # 點狀格線
    )

    return fig

def show_technical_analysis():
    """顯示技術分析主頁面"""
    st.title("📈 技術分析")
    st.markdown("### 股票技術分析工具")

    # 股票選擇
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        stock_names = {'2330': '台積電', '2317': '鴻海', '2454': '聯發科', '2382': '廣達', '3711': '日月光投控'}
        stock_id = st.selectbox(
            "選擇股票",
            options=['2330', '2317', '2454', '2382', '3711'],
            format_func=lambda x: f"{x} - {stock_names[x]}"
        )

    with col2:
        period = st.selectbox(
            "分析期間",
            options=[60, 120, 252],
            format_func=lambda x: f"{x}天"
        )

    with col3:
        st.markdown("**分析指標:**")
        col3a, col3b = st.columns(2)
        with col3a:
            show_ma = st.checkbox("移動平均線", True)
            show_rsi = st.checkbox("RSI指標", True)
        with col3b:
            show_volume = st.checkbox("成交量", True)
            show_annotations = st.checkbox("買賣點標注", True)

    return stock_id, period, show_ma, show_rsi, show_volume, show_annotations

def show_price_chart(stock_id: str, period: int, show_ma: bool, show_rsi: bool, show_volume: bool, show_annotations: bool):
    """顯示股價圖表"""
    # 獲取資料
    df = generate_sample_data(stock_id, period)

    if show_ma:
        df = calculate_moving_averages(df)

    # 生成買賣點標注
    annotations = generate_sample_annotations(df) if show_annotations else None

    # K線圖
    stock_names = {'2330': '台積電', '2317': '鴻海', '2454': '聯發科', '2382': '廣達', '3711': '日月光投控'}
    stock_name = stock_names[stock_id]

    fig = create_candlestick_chart(
        df,
        f"{stock_id} {stock_name} - K線圖",
        show_ma,
        show_rsi,
        show_volume,
        annotations
    )

    st.plotly_chart(fig, width="stretch")

    return df

def show_technical_indicators(df: pd.DataFrame):
    """顯示技術指標摘要"""
    st.subheader("📈 技術指標摘要")

    latest = df.iloc[-1]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("最新收盤價", f"{latest['close']:.2f}")

    with col2:
        if 'MA20' in df.columns:
            ma20_diff = latest['close'] - latest['MA20']
            st.metric("MA20差距", f"{ma20_diff:+.2f}")

    with col3:
        rsi = calculate_rsi(df).iloc[-1]
        rsi_status = "超買" if rsi > 70 else "超賣" if rsi < 30 else "正常"
        st.metric("RSI狀態", f"{rsi:.1f} ({rsi_status})")

    with col4:
        volume_avg = df['volume'].tail(20).mean()
        volume_ratio = latest['volume'] / volume_avg
        st.metric("量比", f"{volume_ratio:.2f}")

def main():
    """主程式"""
    # 顯示導航選單
    show_navigation_menu()

    stock_id, period, show_ma, show_rsi, show_volume, show_annotations = show_technical_analysis()

    # 顯示圖表
    df = show_price_chart(stock_id, period, show_ma, show_rsi, show_volume, show_annotations)

    # 顯示技術指標摘要
    if show_ma:
        df = calculate_moving_averages(df)
    show_technical_indicators(df)

if __name__ == "__main__":
    main()
