# -*- coding: utf-8 -*-
"""
DuckDB 工具模組

此模組提供了一系列用於操作 DuckDB 資料庫的實用函數。
主要功能包括：
- DataFrame 資料插入
- 表格管理
- 資料查詢
"""

import os
import logging
from typing import Optional, List, Union
import pandas as pd
import duckdb
from datetime import datetime

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def insert_dataframe_to_duckdb(
    conn: duckdb.DuckDBPyConnection,
    df: pd.DataFrame,
    table_name: str,
    date_column: str = 'Date',
    if_exists: str = 'append'
) -> int:
    """
    使用 DuckDB 原生方法插入 DataFrame 資料
    
    Args:
        conn: DuckDB 連接物件
        df: 要插入的 DataFrame
        table_name: 目標表格名稱
        date_column: 日期欄位名稱，用於避免重複插入
        if_exists: 如果表格已存在時的處理方式 ('append', 'replace', 'fail')
        
    Returns:
        插入的資料筆數
    """
    try:
        # 檢查 DataFrame 是否為空
        if df.empty:
            logger.warning(f"DataFrame 為空，跳過插入操作")
            return 0
            
        # 建立表格（如果不存在）
        if if_exists == 'replace':
            conn.execute(f"DROP TABLE IF EXISTS {table_name}")
            
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} AS 
            SELECT * FROM df LIMIT 0
        """)
        
        # 註冊 DataFrame
        conn.register('temp_df', df)
        
        # 嘗試批次插入（避免重複）
        if date_column in df.columns:
            # 先查詢已存在的日期
            existing_dates = conn.execute(f"""
                SELECT DISTINCT {date_column} FROM {table_name}
            """).fetchall()
            existing_dates = [row[0] for row in existing_dates]
            
            # 過濾出新資料
            if existing_dates:
                conn.execute(f"""
                    CREATE OR REPLACE TEMP TABLE new_data AS
                    SELECT * FROM temp_df 
                    WHERE {date_column} NOT IN (
                        SELECT {date_column} FROM {table_name}
                    )
                """)
            else:
                conn.execute(f"""
                    CREATE OR REPLACE TEMP TABLE new_data AS
                    SELECT * FROM temp_df
                """)
            
            # 插入新資料
            conn.execute(f"""
                INSERT INTO {table_name} 
                SELECT * FROM new_data
            """)
            
            # 計算插入的筆數
            new_count = conn.execute("SELECT COUNT(*) FROM new_data").fetchone()[0]
            logger.info(f"成功插入 {new_count} 筆新資料到 {table_name}")
            return new_count
            
        else:
            # 如果沒有日期欄位，直接插入
            conn.execute(f"""
                INSERT INTO {table_name} 
                SELECT * FROM temp_df
            """)
            logger.info(f"成功插入 {len(df)} 筆資料到 {table_name}")
            return len(df)
            
    except Exception as e:
        logger.error(f"插入資料時發生錯誤: {e}")
        raise


def get_table_info(
    conn: duckdb.DuckDBPyConnection,
    table_name: str
) -> dict:
    """
    獲取表格的結構資訊
    
    Args:
        conn: DuckDB 連接物件
        table_name: 表格名稱
        
    Returns:
        包含表格結構資訊的字典
    """
    try:
        # 獲取表格結構
        schema = conn.execute(f"DESCRIBE {table_name}").fetchdf()
        
        # 獲取資料筆數
        count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        
        return {
            "table_name": table_name,
            "schema": schema,
            "row_count": count,
            "columns": schema["column_name"].tolist()
        }
        
    except Exception as e:
        logger.error(f"獲取表格資訊時發生錯誤: {e}")
        raise

