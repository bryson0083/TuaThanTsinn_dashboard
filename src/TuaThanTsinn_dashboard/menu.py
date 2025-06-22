"""
共用導航選單模組
"""

import streamlit as st

def show_navigation_menu():
    """顯示自定義導航選單"""
    st.sidebar.title("🧭 導航選單")
    
    # 使用原生 st.page_link 創建頁面連結
    st.sidebar.page_link("app.py", label="首頁", icon="🏠")
    st.sidebar.page_link("pages/market_overview.py", label="市場總覽", icon="📊")
    st.sidebar.page_link("pages/technical_analysis.py", label="技術分析", icon="📈") 
    st.sidebar.page_link("pages/financial_analysis.py", label="財務分析", icon="💰")
    st.sidebar.page_link("pages/portfolio.py", label="投資組合", icon="📱")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    **使用說明:**
    - 點擊上方連結快速切換頁面
    - 每個頁面提供專業的分析工具
    - 支援即時資料更新和互動圖表
    """)
    
    # 版本資訊
    st.sidebar.markdown("---")
    st.sidebar.caption("TuaThanTsinn Dashboard v0.1.0") 