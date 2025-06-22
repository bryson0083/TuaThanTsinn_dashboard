"""
技術指標計算工具
"""

import pandas as pd
import numpy as np
from typing import Optional

class TechnicalIndicators:
    """技術指標計算器"""
    
    @staticmethod
    def moving_average(data: pd.Series, window: int) -> pd.Series:
        """
        計算移動平均線
        
        Args:
            data: 價格資料
            window: 移動平均週期
            
        Returns:
            移動平均線資料
        """
        return data.rolling(window=window).mean()
    
    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """
        計算相對強弱指標 (RSI)
        
        Args:
            data: 價格資料
            period: 計算週期
            
        Returns:
            RSI指標資料
        """
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
        """
        計算MACD指標
        
        Args:
            data: 價格資料
            fast: 快線週期
            slow: 慢線週期
            signal: 信號線週期
            
        Returns:
            包含MACD線、信號線和直方圖的字典
        """
        ema_fast = data.ewm(span=fast).mean()
        ema_slow = data.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def bollinger_bands(data: pd.Series, window: int = 20, num_std: float = 2) -> dict:
        """
        計算布林帶
        
        Args:
            data: 價格資料
            window: 移動平均週期
            num_std: 標準差倍數
            
        Returns:
            包含上軌、中軌、下軌的字典
        """
        rolling_mean = data.rolling(window=window).mean()
        rolling_std = data.rolling(window=window).std()
        
        upper_band = rolling_mean + (rolling_std * num_std)
        lower_band = rolling_mean - (rolling_std * num_std)
        
        return {
            'upper': upper_band,
            'middle': rolling_mean,
            'lower': lower_band
        } 