"""
股票資料管理
"""

import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from proj_util_pkg.settings import settings

class StockDataManager:
    """股票資料管理器"""
    
    def __init__(self):
        """初始化"""
        pass
    
    def get_stock_list(self) -> pd.DataFrame:
        """獲取股票清單"""
        # 示例資料，實際應從API或資料庫獲取
        stock_data = {
            'stock_id': ['2330', '2317', '2454', '2382', '3711'],
            'stock_name': ['台積電', '鴻海', '聯發科', '廣達', '日月光投控'],
            'market': ['TSE', 'TSE', 'TSE', 'TSE', 'TSE'],
            'industry': ['半導體業', '電腦及週邊設備業', '半導體業', '電腦及週邊設備業', '半導體業']
        }
        return pd.DataFrame(stock_data)
    
    def get_stock_price(self, stock_id: str, 
                       start_date: Optional[str] = None,
                       end_date: Optional[str] = None) -> pd.DataFrame:
        """
        獲取股票價格資料
        
        Args:
            stock_id: 股票代號
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
        
        Returns:
            包含股價資料的DataFrame
        """
        # 這裡應該連接到實際的股價API (如FinLab、Yahoo Finance等)
        # 目前返回示例資料
        
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=252)).strftime('%Y-%m-%d')
        
        # 生成示例資料
        import numpy as np
        np.random.seed(hash(stock_id) % 2**32)
        
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        dates = [d for d in dates if d.weekday() < 5]  # 僅工作日
        
        base_price = {'2330': 580, '2317': 100, '2454': 1200, '2382': 90, '3711': 130}.get(stock_id, 100)
        
        prices = []
        current_price = base_price
        
        for date in dates:
            # 隨機價格變動
            change_pct = np.random.normal(0, 0.02)  # 2%標準差
            current_price = max(current_price * (1 + change_pct), 1)
            
            high = current_price * (1 + abs(np.random.normal(0, 0.01)))
            low = current_price * (1 - abs(np.random.normal(0, 0.01)))
            volume = int(np.random.normal(10000, 3000))
            volume = max(volume, 1000)
            
            prices.append({
                'date': date,
                'stock_id': stock_id,
                'open': round(current_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(current_price, 2),
                'volume': volume
            })
        
        return pd.DataFrame(prices)
    
    def get_stock_info(self, stock_id: str) -> Dict[str, Any]:
        """
        獲取股票基本資訊
        
        Args:
            stock_id: 股票代號
            
        Returns:
            股票基本資訊字典
        """
        stock_info = {
            '2330': {
                'name': '台積電',
                'market': 'TSE',
                'industry': '半導體業',
                'market_cap': 15000000,  # 市值(百萬)
                'pe_ratio': 18.5,
                'dividend_yield': 2.1
            },
            '2317': {
                'name': '鴻海',
                'market': 'TSE', 
                'industry': '電腦及週邊設備業',
                'market_cap': 1400000,
                'pe_ratio': 12.3,
                'dividend_yield': 3.2
            }
        }
        
        return stock_info.get(stock_id, {
            'name': '未知',
            'market': 'TSE',
            'industry': '其他',
            'market_cap': 0,
            'pe_ratio': 0,
            'dividend_yield': 0
        })
    
    def search_stocks(self, keyword: str) -> pd.DataFrame:
        """
        搜尋股票
        
        Args:
            keyword: 搜尋關鍵字 (股票代號或名稱)
            
        Returns:
            符合搜尋條件的股票清單
        """
        all_stocks = self.get_stock_list()
        
        # 模糊搜尋
        mask = (
            all_stocks['stock_id'].str.contains(keyword, case=False, na=False) |
            all_stocks['stock_name'].str.contains(keyword, case=False, na=False)
        )
        
        return all_stocks[mask] 