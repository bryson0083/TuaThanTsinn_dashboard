"""
投資組合頁面
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# 添加父目錄到路徑以導入共用模組
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from menu import show_navigation_menu

def main():
    """主程式"""
    # 顯示導航選單
    show_navigation_menu()
    
    st.title("📱 投資組合")
    st.markdown("### 個人投資組合管理")
    
    st.info("🚧 此頁面正在開發中，敬請期待！")
    
    # 基本功能框架
    st.subheader("🎯 主要功能")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📊 投資追蹤**
        - 持股明細管理
        - 損益計算分析
        - 績效評估報告
        - 風險評估工具
        """)
    
    with col2:
        st.markdown("""
        **📈 投資策略**
        - 資產配置建議
        - 再平衡提醒
        - 投資目標設定
        - 定期定額規劃
        """)

if __name__ == "__main__":
    main() 