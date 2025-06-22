"""
資料庫操作管理
"""

import pandas as pd
from typing import List, Dict, Any, Optional
from .connection import db_connection

class DatabaseOperations:
    """資料庫操作管理器"""
    
    def __init__(self):
        self.db = db_connection
    
    def create_stock_tables(self):
        """建立股票相關資料表"""
        
        # 股票基本資料表
        create_stocks_table = """
        CREATE TABLE IF NOT EXISTS stocks (
            stock_id VARCHAR PRIMARY KEY,
            stock_name VARCHAR NOT NULL,
            market VARCHAR NOT NULL,  -- 'TSE' or 'OTC'
            industry VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # 股價資料表
        create_stock_prices_table = """
        CREATE TABLE IF NOT EXISTS stock_prices (
            id INTEGER PRIMARY KEY,
            stock_id VARCHAR NOT NULL,
            date DATE NOT NULL,
            open DECIMAL(10,2),
            high DECIMAL(10,2),
            low DECIMAL(10,2),
            close DECIMAL(10,2),
            volume BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks(stock_id),
            UNIQUE(stock_id, date)
        );
        """
        
        # 財務資料表
        create_financials_table = """
        CREATE TABLE IF NOT EXISTS financials (
            id INTEGER PRIMARY KEY,
            stock_id VARCHAR NOT NULL,
            year INTEGER NOT NULL,
            quarter INTEGER NOT NULL,
            revenue DECIMAL(15,2),
            net_income DECIMAL(15,2),
            eps DECIMAL(10,2),
            roe DECIMAL(5,2),
            roa DECIMAL(5,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES stocks(stock_id),
            UNIQUE(stock_id, year, quarter)
        );
        """
        
        try:
            self.db.execute(create_stocks_table)
            self.db.execute(create_stock_prices_table)
            self.db.execute(create_financials_table)
            print("✅ 資料表建立成功")
        except Exception as e:
            print(f"❌ 資料表建立失敗: {e}")
    
    def insert_stock_data(self, stock_data: Dict[str, Any]) -> bool:
        """插入股票基本資料"""
        try:
            query = """
            INSERT OR REPLACE INTO stocks 
            (stock_id, stock_name, market, industry, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
            self.db.execute(query, (
                stock_data['stock_id'],
                stock_data['stock_name'], 
                stock_data['market'],
                stock_data.get('industry', '')
            ))
            return True
        except Exception as e:
            print(f"❌ 插入股票資料失敗: {e}")
            return False
    
    def insert_price_data(self, price_data: List[Dict[str, Any]]) -> bool:
        """批量插入股價資料"""
        try:
            query = """
            INSERT OR REPLACE INTO stock_prices 
            (stock_id, date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            for data in price_data:
                self.db.execute(query, (
                    data['stock_id'],
                    data['date'],
                    data['open'],
                    data['high'],
                    data['low'],
                    data['close'],
                    data['volume']
                ))
            return True
        except Exception as e:
            print(f"❌ 插入股價資料失敗: {e}")
            return False
    
    def get_stock_price(self, stock_id: str, 
                       start_date: Optional[str] = None, 
                       end_date: Optional[str] = None) -> pd.DataFrame:
        """查詢股價資料"""
        query = """
        SELECT * FROM stock_prices 
        WHERE stock_id = ?
        """
        params = [stock_id]
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        query += " ORDER BY date"
        
        return self.db.fetch_df(query, tuple(params))
    
    def get_all_stocks(self) -> pd.DataFrame:
        """獲取所有股票清單"""
        query = "SELECT * FROM stocks ORDER BY stock_id"
        return self.db.fetch_df(query)
    
    def get_latest_prices(self, limit: int = 10) -> pd.DataFrame:
        """獲取最新股價資料"""
        query = """
        SELECT s.stock_name, sp.* 
        FROM stock_prices sp
        JOIN stocks s ON sp.stock_id = s.stock_id
        WHERE sp.date = (
            SELECT MAX(date) FROM stock_prices sp2 
            WHERE sp2.stock_id = sp.stock_id
        )
        ORDER BY sp.stock_id
        LIMIT ?
        """
        return self.db.fetch_df(query, (limit,))

# 全域資料庫操作實例
db_ops = DatabaseOperations() 