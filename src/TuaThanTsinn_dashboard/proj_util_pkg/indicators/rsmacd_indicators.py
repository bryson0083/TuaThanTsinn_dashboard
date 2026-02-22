"""
RSMACD（MACD 強度指標）技術指標計算工具

將 RSI 演算法套用在 MACD 線上，將 MACD 正規化至 0-100 範圍。
信號規則參考：TuaThanTsinn/ANA001_台股選股/twstock_rsmacd選股.ipynb
"""

import pandas as pd
import numpy as np

from .technical import TechnicalIndicators


class RSMACDIndicators:
    """RSMACD 指標計算器"""

    # --- 技術指標計算 ---

    @staticmethod
    def compute_indicators(
        df: pd.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        rsi_period: int = 14,
        control_ma_period: int = 20,
        atr_period: int = 14,
        atr_multiplier: float = 2.0,
    ) -> pd.DataFrame:
        """
        計算 RSMACD 所需的所有技術指標

        Args:
            df: 包含 'close' 欄位的 DataFrame
            fast_period: MACD 快線 EMA 週期（預設 12）
            slow_period: MACD 慢線 EMA 週期（預設 26）
            signal_period: MACD 信號線 EMA 週期（預設 9）
            rsi_period: RSI 計算週期（預設 14）
            control_ma_period: 控盤均線週期（預設 20，作為 ATR 移動停損的計算基礎）
            atr_period: ATR 計算週期（預設 14）
            atr_multiplier: ATR 移動停損倍數（預設 2.0）

        Returns:
            加入 macd_line, macd_signal, macd_histogram, rsmacd, control_ma, atr, atr_trailing_stop 欄位的 DataFrame
        """
        result = df.copy()

        # Step 0: 移動平均線
        result['MA5'] = result['close'].rolling(window=5).mean()
        result['MA20'] = result['close'].rolling(window=20).mean()
        result['MA60'] = result['close'].rolling(window=60).mean()

        # 控盤均線（ATR 移動停損的計算基礎）
        result['control_ma'] = result['close'].rolling(window=control_ma_period).mean()

        # Step 0.5: ATR 與棘輪式移動停損（基於控盤均線）
        result['atr'] = TechnicalIndicators.atr(
            result['high'], result['low'], result['close'], period=atr_period
        )
        result['atr_trailing_stop'] = TechnicalIndicators.atr_trailing_stop(
            result['control_ma'], result['atr'], multiplier=atr_multiplier
        )

        # Step 1: MACD 計算
        ema_fast = result['close'].ewm(span=fast_period, adjust=False).mean()
        ema_slow = result['close'].ewm(span=slow_period, adjust=False).mean()
        result['macd_line'] = ema_fast - ema_slow
        result['macd_signal'] = result['macd_line'].ewm(
            span=signal_period, adjust=False
        ).mean()
        result['macd_histogram'] = result['macd_line'] - result['macd_signal']

        # Step 2: 對 MACD 線套用 RSI 演算法（Wilder's smoothing）
        macd_delta = result['macd_line'].diff()
        gain = macd_delta.clip(lower=0)
        loss = (-macd_delta).clip(lower=0)

        avg_gain = gain.ewm(
            alpha=1 / rsi_period, min_periods=rsi_period, adjust=False
        ).mean()
        avg_loss = loss.ewm(
            alpha=1 / rsi_period, min_periods=rsi_period, adjust=False
        ).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsmacd = 100 - (100 / (1 + rs))

        # 邊界處理
        rsmacd = rsmacd.where(avg_loss != 0, 100.0)  # 全漲 → 100
        rsmacd = rsmacd.where(avg_gain != 0, 0.0)    # 全跌 → 0

        result['rsmacd'] = rsmacd
        return result

    # --- 信號產生 ---

    @staticmethod
    def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
        """
        計算 RSMACD 六大買賣信號

        Args:
            df: 已透過 compute_indicators() 加入 'rsmacd' 的 DataFrame

        Returns:
            加入 6 個布林信號欄位的 DataFrame:
            - signal_green_arrow:     RSMACD 曲線翻揚
            - signal_green_triangle:  RSMACD 突破 30（主要選股信號）
            - signal_green_ball:      RSMACD 翻揚且突破 50
            - signal_red_arrow:       RSMACD 曲線翻落
            - signal_red_triangle:    RSMACD 跌破 70
            - signal_red_ball:        RSMACD 翻落且跌破 50
        """
        result = df.copy()
        rsmacd = result['rsmacd']
        rsmacd_prev1 = rsmacd.shift(1)
        rsmacd_prev2 = rsmacd.shift(2)

        # 轉折判斷
        turning_up = (rsmacd > rsmacd_prev1) & (rsmacd_prev1 <= rsmacd_prev2)
        turning_down = (rsmacd < rsmacd_prev1) & (rsmacd_prev1 >= rsmacd_prev2)

        # 買進信號（綠色）
        result['signal_green_arrow'] = turning_up
        result['signal_green_triangle'] = (rsmacd > 30) & (rsmacd_prev1 <= 30)
        result['signal_green_ball'] = (
            (rsmacd > 50) & (rsmacd_prev1 <= 50) & turning_up
        )

        # 賣出信號（紅色）
        result['signal_red_arrow'] = turning_down
        result['signal_red_triangle'] = (rsmacd < 70) & (rsmacd_prev1 >= 70)
        result['signal_red_ball'] = (
            (rsmacd < 50) & (rsmacd_prev1 >= 50) & turning_down
        )

        return result

    # --- 信號去重 ---

    @staticmethod
    def deduplicate_signals(df: pd.DataFrame) -> pd.DataFrame:
        """
        對信號進行去重，連續相同信號只保留第一次出現

        Args:
            df: 包含 6 個信號布林欄位的 DataFrame

        Returns:
            只包含去重後信號的 DataFrame，新增 'signal_type' 欄位
        """
        signal_mapping = {
            'signal_green_arrow': '綠色箭頭',
            'signal_green_triangle': '綠色三角形',
            'signal_green_ball': '綠色小球',
            'signal_red_arrow': '紅色箭頭',
            'signal_red_triangle': '紅色倒三角形',
            'signal_red_ball': '紅色小球',
        }

        def get_signal_type(row):
            signals = []
            for col, label in signal_mapping.items():
                if row.get(col, False):
                    signals.append(label)
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
