"""
DuckDB 資料庫連接管理
"""

import os
import duckdb
from pathlib import Path
from typing import Optional
from proj_util_pkg.settings import settings

class DatabaseConnection:
    """DuckDB 資料庫連接管理器"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化資料庫連接
        
        Args:
            db_path: 資料庫檔案路徑，如果未指定則使用環境變數
        """
        self.db_path = db_path or self._get_default_db_path()
        self.connection = None
        
    def _get_default_db_path(self) -> str:
        """獲取預設資料庫路徑"""
        project_root = os.environ.get('PROJECT_ROOT')
        if project_root:
            db_dir = Path(project_root) / "data"
            db_dir.mkdir(exist_ok=True)
            return str(db_dir / "tuathantsinn.duckdb")
        else:
            # 如果沒有PROJECT_ROOT，使用當前目錄
            return "tuathantsinn.duckdb"
    
    def connect(self) -> duckdb.DuckDBPyConnection:
        """建立資料庫連接"""
        if self.connection is None:
            self.connection = duckdb.connect(self.db_path)
            print(f"✅ 已連接到 DuckDB: {self.db_path}")
        return self.connection
    
    def close(self):
        """關閉資料庫連接"""
        if self.connection:
            self.connection.close()
            self.connection = None
            print("✅ DuckDB 連接已關閉")
    
    def execute(self, query: str, parameters: Optional[tuple] = None):
        """執行SQL查詢"""
        conn = self.connect()
        if parameters:
            return conn.execute(query, parameters)
        else:
            return conn.execute(query)
    
    def fetch_df(self, query: str, parameters: Optional[tuple] = None):
        """查詢並返回DataFrame"""
        conn = self.connect()
        if parameters:
            return conn.execute(query, parameters).df()
        else:
            return conn.execute(query).df()
    
    def __enter__(self):
        """上下文管理器進入"""
        return self.connect()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()

# 全域資料庫連接實例
db_connection = DatabaseConnection() 