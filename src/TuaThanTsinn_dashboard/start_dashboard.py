#!/usr/bin/env python3
"""
TuaThanTsinn Dashboard 啟動腳本
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """啟動 Streamlit 儀表板"""
    
    # 設定工作目錄
    dashboard_dir = Path(__file__).parent
    os.chdir(dashboard_dir)
    
    print("🚀 正在啟動 TuaThanTsinn Dashboard...")
    print(f"📁 工作目錄: {dashboard_dir}")
    print(f"🐍 Python 版本: {sys.version}")
    print("-" * 50)
    
    try:
        # 啟動 Streamlit 應用
        cmd = [
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port=8501",
            "--server.address=localhost",
            "--browser.gatherUsageStats=false"
        ]
        
        print("🌐 啟動網址: http://localhost:8501")
        print("⏹️  停止服務: 按 Ctrl+C")
        print("-" * 50)
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n👋 TuaThanTsinn Dashboard 已停止")
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")

if __name__ == "__main__":
    main() 