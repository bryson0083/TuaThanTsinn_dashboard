"""
市場總覽頁面
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 添加父目錄到路徑以導入共用模組
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from menu import show_navigation_menu

def show_market_overview():
    """顯示市場總覽"""
    st.title("📊 市場總覽")
    st.markdown("### 台股市場即時概況")
    
    # 市場指數概況
    st.subheader("🏛️ 主要指數")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="加權股價指數",
            value="17,829.31",
            delta="156.42 (0.88%)",
            help="台灣證券交易所加權股價指數"
        )
    
    with col2:
        st.metric(
            label="櫃買指數",
            value="189.67", 
            delta="-2.15 (-1.12%)",
            help="櫃買中心股價指數"
        )
    
    with col3:
        st.metric(
            label="高股息指數",
            value="1,234.56",
            delta="12.34 (1.01%)",
            help="台灣高股息指數"
        )
    
    # 市場統計
    st.subheader("📈 交易統計")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("成交金額(億)", "2,847.25", "287.15")
    
    with col2:
        st.metric("成交筆數(萬)", "145.67", "15.23")
        
    with col3:
        st.metric("上漲家數", "876", "45")
        
    with col4:
        st.metric("下跌家數", "634", "-23")
    
    # 外資動向
    st.subheader("🌐 外資動向")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("外資買賣超(億)", "-45.67", "-12.34")
    
    with col2:
        st.metric("投信買賣超(億)", "23.45", "5.67")
        
    with col3:
        st.metric("自營商買賣超(億)", "12.34", "-2.11")

def show_top_stocks():
    """顯示熱門股票"""
    st.subheader("🔥 熱門股票")
    
    # 示例資料
    top_stocks_data = {
        '股票代號': ['2330', '2317', '2454', '2382', '3711'],
        '股票名稱': ['台積電', '鴻海', '聯發科', '廣達', '日月光投控'],
        '收盤價': [582.0, 101.5, 1205.0, 89.7, 127.5],
        '漲跌': [8.0, -1.5, 35.0, 2.1, -2.5],
        '漲跌幅(%)': [1.39, -1.46, 2.99, 2.40, -1.92],
        '成交量(張)': [45678, 23456, 12345, 34567, 15678]
    }
    
    df = pd.DataFrame(top_stocks_data)
    
    # 設定顏色格式
    def color_negative_red(value):
        if isinstance(value, (int, float)):
            if value < 0:
                return 'color: red'
            elif value > 0:
                return 'color: green'
        return 'color: black'
    
    # 顯示表格
    styled_df = df.style.map(
        color_negative_red, 
        subset=['漲跌', '漲跌幅(%)']
    ).format({
        '收盤價': '{:.1f}',
        '漲跌': '{:+.1f}',
        '漲跌幅(%)': '{:+.2f}%',
        '成交量(張)': '{:,}'
    })
    
    st.dataframe(styled_df, use_container_width=True)

def show_market_charts():
    """顯示市場圖表"""
    st.subheader("📊 市場走勢圖")
    
    # 生成示例資料
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    np.random.seed(42)
    prices = 17000 + np.cumsum(np.random.randn(len(dates)) * 10)
    
    chart_data = pd.DataFrame({
        'Date': dates,
        'Price': prices
    }).set_index('Date')
    
    # 顯示線性圖
    st.line_chart(chart_data['Price'])
    
    # 顯示區域圖
    st.subheader("📈 成交量走勢")
    volume_data = pd.DataFrame({
        'Date': dates[-30:],  # 最近30天
        'Volume': np.random.randint(1000, 5000, 30)
    }).set_index('Date')
    
    st.area_chart(volume_data['Volume'])

def main():
    """主程式"""
    # 顯示導航選單
    show_navigation_menu()
    
    show_market_overview()
    
    # 兩欄布局
    col1, col2 = st.columns([2, 1])
    
    with col1:
        show_market_charts()
    
    with col2:
        show_top_stocks()
    
    # 更新時間
    st.markdown("---")
    st.caption(f"📅 最後更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 