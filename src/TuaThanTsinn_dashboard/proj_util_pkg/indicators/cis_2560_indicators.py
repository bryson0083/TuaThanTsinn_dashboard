"""
CIS + 2560 戰法技術指標計算工具

提供 CIS 買賣信號判斷與 2560 量能確認過濾的計算邏輯。
信號規則參考：TuaThanTsinn/ANA001_台股選股/twstock_cis_2560選股.ipynb
"""

import pandas as pd
import numpy as np
from typing import Optional


class CIS2560Indicators:
    """CIS + 2560 戰法指標計算器"""

    # --- 技術指標計算 ---

    @staticmethod
    def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        計算 CIS + 2560 所需的所有技術指標

        Args:
            df: 包含 'close', 'open', 'high', 'low', 'vol' 欄位的 DataFrame

        Returns:
            加入 SMA5, SMA25, Vol_SMA5, Vol_SMA60 欄位的 DataFrame
        """
        result = df.copy()
        result['SMA5'] = result['close'].rolling(window=5).mean()
        result['SMA25'] = result['close'].rolling(window=25).mean()
        result['Vol_SMA5'] = result['vol'].rolling(window=5).mean()
        result['Vol_SMA60'] = result['vol'].rolling(window=60).mean()
        return result

    # --- 輔助判斷函式 ---

    @staticmethod
    def is_ma_flat(ma_series: pd.Series, threshold: float = 0.003, periods: int = 3) -> pd.Series:
        """
        判斷均線是否走平

        條件：連續 periods 日，均線日變動率的絕對值都小於 threshold

        Args:
            ma_series: 均線 Series
            threshold: 變動率閾值（預設 0.3%）
            periods: 連續判定天數

        Returns:
            布林 Series
        """
        ma_change_rate = ma_series.pct_change().abs()
        is_flat = (ma_change_rate < threshold).rolling(window=periods).min() == 1
        return is_flat

    @staticmethod
    def is_ma_up(ma_series: pd.Series) -> pd.Series:
        """判斷均線是否向上（今日 > 昨日）"""
        return ma_series > ma_series.shift(1)

    @staticmethod
    def is_ma_down(ma_series: pd.Series) -> pd.Series:
        """判斷均線是否向下（今日 < 昨日）"""
        return ma_series < ma_series.shift(1)

    @staticmethod
    def is_consecutive_bullish(close: pd.Series, open_price: pd.Series, periods: int = 2) -> pd.Series:
        """
        判斷是否連續出現陽線（收盤 > 開盤）

        Args:
            close: 收盤價 Series
            open_price: 開盤價 Series
            periods: 連續天數（預設 2）

        Returns:
            布林 Series
        """
        is_bullish = close > open_price
        return is_bullish.rolling(window=periods).min() == 1

    # --- 信號產生 ---

    @staticmethod
    def generate_signals(df: pd.DataFrame, enable_volume_confirmation: bool = True) -> pd.DataFrame:
        """
        計算 CIS 買賣信號

        Args:
            df: 已透過 compute_indicators() 加入技術指標的 DataFrame，
                需包含 'close', 'open', 'SMA5', 'SMA25', 'Vol_SMA5', 'Vol_SMA60'
            enable_volume_confirmation: 是否啟用 2560 量能確認過濾

        Returns:
            加入 'signal_reverse_buy', 'signal_buy', 'signal_sell' 布林欄位的 DataFrame
        """
        result = df.copy()

        # 預先計算共用條件
        ma25_flat = CIS2560Indicators.is_ma_flat(result['SMA25'])
        ma25_up = CIS2560Indicators.is_ma_up(result['SMA25'])
        ma5_up = CIS2560Indicators.is_ma_up(result['SMA5'])
        ma5_down = CIS2560Indicators.is_ma_down(result['SMA5'])
        consecutive_bullish = CIS2560Indicators.is_consecutive_bullish(result['close'], result['open'])
        vol_confirm = result['Vol_SMA5'] > result['Vol_SMA60']

        # CIS逆買：價格在25MA下方，25MA走平或向上，5MA向上，連續陽線
        signal_reverse_buy = (
            (result['close'] < result['SMA25']) &
            (ma25_flat | ma25_up) &
            ma5_up &
            consecutive_bullish
        )
        if enable_volume_confirmation:
            signal_reverse_buy = signal_reverse_buy & vol_confirm

        # CIS買：25MA走平或向上，5MA在25MA上方，價格在5MA上方
        signal_buy = (
            (ma25_flat | ma25_up) &
            (result['SMA5'] > result['SMA25']) &
            (result['close'] > result['SMA5'])
        )
        if enable_volume_confirmation:
            signal_buy = signal_buy & vol_confirm

        # CIS賣：5MA向下，價格跌破5MA（不加量能過濾，避免錯過停損）
        signal_sell = ma5_down & (result['close'] < result['SMA5'])

        result['signal_reverse_buy'] = signal_reverse_buy
        result['signal_buy'] = signal_buy
        result['signal_sell'] = signal_sell

        return result

    # --- 信號去重 ---

    @staticmethod
    def deduplicate_signals(df: pd.DataFrame) -> pd.DataFrame:
        """
        對信號進行去重，連續相同信號只保留第一次出現

        Args:
            df: 包含 'signal_reverse_buy', 'signal_buy', 'signal_sell' 的 DataFrame

        Returns:
            只包含去重後信號的 DataFrame，新增 'signal_type' 欄位
        """
        def get_signal_type(row):
            signals = []
            if row.get('signal_reverse_buy', False):
                signals.append('CIS逆買')
            if row.get('signal_buy', False):
                signals.append('CIS買')
            if row.get('signal_sell', False):
                signals.append('CIS賣')
            return ', '.join(signals) if signals else None

        df_work = df.copy()
        df_work['signal_type'] = df_work.apply(get_signal_type, axis=1)

        # 篩選有信號的列
        signal_df = df_work[df_work['signal_type'].notna()].copy()

        if signal_df.empty:
            return signal_df

        # 去重：連續相同信號只保留第一次
        prev_signal = None
        prev_idx = None
        keep_mask = []

        for idx, row in signal_df.iterrows():
            is_consecutive = (prev_idx is not None) and (idx - prev_idx == 1)
            is_same = row['signal_type'] == prev_signal
            keep = not (is_consecutive and is_same)
            keep_mask.append(keep)
            prev_signal = row['signal_type']
            prev_idx = idx

        return signal_df[keep_mask].copy()
