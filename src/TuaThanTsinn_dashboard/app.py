"""
TuaThanTsinn Dashboard - 台股分析儀表板
主應用程式
"""

import streamlit as st
import os
import pandas as pd
from datetime import datetime
from proj_util_pkg.settings import settings
from menu import show_navigation_menu

# 頁面配置
st.set_page_config(
    page_title="TuaThanTsinn Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def show_system_info():
    """顯示系統資訊"""
    with st.expander("🔧 系統資訊", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**專案路徑:**")
            st.code(os.environ.get('PROJECT_ROOT', 'N/A'))
            
            st.write("**Python版本:**")
            import sys
            st.code(f"{sys.version}")
            
        with col2:
            st.write("**當前時間:**")
            st.code(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            st.write("**Streamlit版本:**")
            st.code(st.__version__)

def show_feature_overview():
    """顯示功能概覽"""
    st.subheader("🎯 主要功能")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        ### 📊 市場總覽
        - 即時股價監控
        - 市場指數追蹤
        - 熱門股票排行
        """)
    
    with col2:
        st.markdown("""
        ### 📈 技術分析  
        - K線圖表分析
        - 技術指標計算
        - 趨勢預測模型
        """)
    
    with col3:
        st.markdown("""
        ### 💰 財務分析
        - 財務報表分析
        - 基本面指標
        - 估值模型
        """)
    
    with col4:
        st.markdown("""
        ### 📱 投資組合
        - 持股追蹤管理
        - 績效分析報告
        - 風險評估工具
        """)

def main():
    """主程式"""
    # 顯示導航選單
    show_navigation_menu()
    
    # 頁面標題
    st.title("🏆 TuaThanTsinn Dashboard")
    st.markdown("### 台股分析儀表板")
    
    # 歡迎訊息
    st.success("🎉 歡迎使用台股分析儀表板！系統已成功啟動。")
    
    # 功能概覽
    show_feature_overview()
    
    # 快速統計（示例資料）
    st.subheader("📈 今日市場概況")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="台股加權指數",
            value="17,829.31",
            delta="156.42 (0.88%)"
        )
    
    with col2:
        st.metric(
            label="櫃買指數", 
            value="189.67",
            delta="-2.15 (-1.12%)"
        )
    
    with col3:
        st.metric(
            label="成交量(億)",
            value="2,847.25",
            delta="287.15 (11.22%)"
        )
    
    with col4:
        st.metric(
            label="外資買賣超(億)",
            value="-45.67", 
            delta="-12.34"
        )
    
    # 系統資訊
    show_system_info()
    
    # 頁腳
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666666;'>
            <p>© 2024 TuaThanTsinn Dashboard | 台股分析儀表板 v0.1.0</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main() 