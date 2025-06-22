"""
技術分析頁面
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
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

def create_candlestick_chart(df: pd.DataFrame, title: str):
    """建立K線圖"""
    fig = go.Figure()
    
    # K線圖
    fig.add_trace(go.Candlestick(
        x=df['date'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='K線'
    ))
    
    # 移動平均線
    if 'MA5' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'], y=df['MA5'],
            mode='lines', name='MA5',
            line=dict(color='orange', width=1)
        ))
    
    if 'MA20' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'], y=df['MA20'],
            mode='lines', name='MA20',
            line=dict(color='blue', width=1)
        ))
    
    fig.update_layout(
        title=title,
        yaxis_title='價格',
        xaxis_title='日期',
        height=500
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
        show_ma = st.checkbox("移動平均線", True)
        show_rsi = st.checkbox("RSI指標", True)
        show_volume = st.checkbox("成交量", True)
    
    return stock_id, period, show_ma, show_rsi, show_volume

def show_price_chart(stock_id: str, period: int, show_ma: bool, show_rsi: bool, show_volume: bool):
    """顯示股價圖表"""
    # 獲取資料
    df = generate_sample_data(stock_id, period)
    
    if show_ma:
        df = calculate_moving_averages(df)
    
    # K線圖
    stock_names = {'2330': '台積電', '2317': '鴻海', '2454': '聯發科', '2382': '廣達', '3711': '日月光投控'}
    stock_name = stock_names[stock_id]
    fig = create_candlestick_chart(df, f"{stock_id} {stock_name} - K線圖")
    st.plotly_chart(fig, use_container_width=True)
    
    # RSI 指標
    if show_rsi:
        st.subheader("📊 RSI 相對強弱指標")
        rsi = calculate_rsi(df)
        
        rsi_fig = go.Figure()
        rsi_fig.add_trace(go.Scatter(
            x=df['date'], y=rsi,
            mode='lines', name='RSI',
            line=dict(color='purple')
        ))
        
        # RSI 超買超賣線
        rsi_fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="超買線(70)")
        rsi_fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="超賣線(30)")
        
        rsi_fig.update_layout(
            title="RSI 指標",
            yaxis_title="RSI",
            xaxis_title="日期",
            height=300
        )
        
        st.plotly_chart(rsi_fig, use_container_width=True)
    
    # 成交量
    if show_volume:
        st.subheader("📊 成交量分析")
        volume_fig = go.Figure()
        volume_fig.add_trace(go.Bar(
            x=df['date'], y=df['volume'],
            name='成交量',
            marker_color='lightblue'
        ))
        
        volume_fig.update_layout(
            title="成交量",
            yaxis_title="成交量",
            xaxis_title="日期",
            height=300
        )
        
        st.plotly_chart(volume_fig, use_container_width=True)
    
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
    
    stock_id, period, show_ma, show_rsi, show_volume = show_technical_analysis()
    
    # 顯示圖表
    df = show_price_chart(stock_id, period, show_ma, show_rsi, show_volume)
    
    # 顯示技術指標摘要
    if show_ma:
        df = calculate_moving_averages(df)
    show_technical_indicators(df)

if __name__ == "__main__":
    main() 