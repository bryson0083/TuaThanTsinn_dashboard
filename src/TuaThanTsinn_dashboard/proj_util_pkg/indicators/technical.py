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

    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        計算平均真實波動區間 (ATR)

        Args:
            high: 最高價 Series
            low: 最低價 Series
            close: 收盤價 Series
            period: 計算週期（預設 14）

        Returns:
            ATR 指標 Series
        """
        prev_close = close.shift(1)
        tr = pd.concat([
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()

    @staticmethod
    def atr_trailing_stop(close: pd.Series, atr: pd.Series, multiplier: float = 2.0) -> pd.Series:
        """
        計算棘輪式 ATR 移動停損（停損價只會往上調，不會往下）

        Args:
            close: 收盤價 Series
            atr: ATR 指標 Series
            multiplier: ATR 乘數（預設 2.0）

        Returns:
            移動停損價 Series
        """
        candidate_stop = close - atr * multiplier
        trailing_stop = pd.Series(np.nan, index=close.index)
        for i in range(len(close)):
            if pd.isna(candidate_stop.iloc[i]):
                continue
            if i == 0 or pd.isna(trailing_stop.iloc[i - 1]):
                trailing_stop.iloc[i] = candidate_stop.iloc[i]
            elif close.iloc[i] < trailing_stop.iloc[i - 1]:
                trailing_stop.iloc[i] = candidate_stop.iloc[i]
            else:
                trailing_stop.iloc[i] = max(trailing_stop.iloc[i - 1], candidate_stop.iloc[i])
        return trailing_stop