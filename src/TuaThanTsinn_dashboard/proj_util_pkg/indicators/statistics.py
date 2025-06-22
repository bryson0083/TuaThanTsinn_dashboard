"""
統計指標計算工具
"""

import pandas as pd
import numpy as np
from typing import Optional

class StatisticalIndicators:
    """統計指標計算器"""
    
    @staticmethod
    def volatility(data: pd.Series, window: int = 20) -> pd.Series:
        """
        計算波動率
        
        Args:
            data: 價格資料
            window: 計算週期
            
        Returns:
            波動率資料
        """
        returns = data.pct_change()
        volatility = returns.rolling(window=window).std() * np.sqrt(252)  # 年化波動率
        return volatility
    
    @staticmethod
    def correlation(data1: pd.Series, data2: pd.Series, window: int = 20) -> pd.Series:
        """
        計算相關係數
        
        Args:
            data1: 第一組資料
            data2: 第二組資料
            window: 計算週期
            
        Returns:
            相關係數資料
        """
        return data1.rolling(window=window).corr(data2)
    
    @staticmethod
    def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
        """
        計算夏普比率
        
        Args:
            returns: 報酬率資料
            risk_free_rate: 無風險利率
            
        Returns:
            夏普比率
        """
        excess_returns = returns - risk_free_rate
        return excess_returns.mean() / excess_returns.std() * np.sqrt(252)
    
    @staticmethod
    def max_drawdown(data: pd.Series) -> dict:
        """
        計算最大回撤
        
        Args:
            data: 價格或淨值資料
            
        Returns:
            包含最大回撤和相關資訊的字典
        """
        # 計算累積最高點
        cumulative_max = data.cummax()
        
        # 計算回撤
        drawdown = (data - cumulative_max) / cumulative_max
        
        # 找出最大回撤
        max_dd = drawdown.min()
        max_dd_date = drawdown.idxmin()
        
        return {
            'max_drawdown': max_dd,
            'max_drawdown_date': max_dd_date,
            'drawdown_series': drawdown
        } 