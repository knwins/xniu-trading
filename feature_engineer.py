# -*- coding: utf-8 -*-
# feature_engineer.py
import numpy as np
import pandas as pd
from dotenv import load_dotenv
import os
load_dotenv()
RSI_PERIOD = int(os.getenv("RSI_PERIOD", "14"))
LINEWMA_PERIOD = int(os.getenv("LINEWMA_PERIOD", "55"))  # LineWMA周期
OPENEMA_PERIOD = int(os.getenv("OPENEMA_PERIOD", "25"))  # OpenEMA周期
CLOSEEMA_PERIOD = int(os.getenv("CLOSEEMA_PERIOD", "25"))  # CloseEMA周期

class FeatureEngineer:
    @staticmethod
    def calculate_rsi(prices, period=RSI_PERIOD):
        """计算 RSI 指标：RSI = 100 - (100 / (1 + RS))，RS = 平均上涨幅度 / 平均下跌幅度"""
        delta = prices.diff(1)  # 价格变化
        gain = delta.where(delta > 0, 0)  # 上涨幅度（负的取 0）
        loss = -delta.where(delta < 0, 0)  # 下跌幅度（正的取 0）
        
        # 计算平均上涨/下跌幅度（初始用 SMA，后续用 EMA 平滑）
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        # 计算 RS 和 RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_ema(prices, period):
        """计算指数移动平均线 (EMA)"""
        return prices.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_wma(prices, period):
        """计算加权移动平均线 (WMA)"""
        # WMA = (n*P1 + (n-1)*P2 + ... + 2*P(n-1) + Pn) / (n + (n-1) + ... + 2 + 1)
        # 其中 n 是周期，P1 是最新的价格，Pn 是最旧的价格
        
        if len(prices) < period:
            return pd.Series([np.nan] * len(prices), index=prices.index)
        
        weights = np.arange(1, period + 1)
        wma_values = []
        
        for i in range(len(prices)):
            if i < period - 1:
                wma_values.append(np.nan)
            else:
                # 取最近 period 个价格
                recent_prices = prices.iloc[i-period+1:i+1].values
                # 计算加权平均
                wma = np.sum(recent_prices * weights) / np.sum(weights)
                wma_values.append(wma)
        
        return pd.Series(wma_values, index=prices.index)
    
    @staticmethod
    def calculate_macd(prices, fast=12, slow=26, signal=9):
        """计算MACD指标"""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger_bands(prices, period=20, std_dev=2):
        """计算布林带"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return upper_band, sma, lower_band
    
    @staticmethod
    def calculate_atr(high, low, close, period=14):
        """计算ATR（平均真实波动幅度）指标"""
        # 计算真实波动幅度
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        # 真实波动幅度取最大值
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # 计算ATR
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    @staticmethod
    def calculate_stochastic(high, low, close, k_period=14, d_period=3):
        """计算随机指标"""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        return k_percent, d_percent
    
    @staticmethod
    def calculate_cci(high, low, close, period=20):
        """计算商品通道指数 (CCI)"""
        typical_price = (high + low + close) / 3
        sma_tp = typical_price.rolling(window=period).mean()
        mad = typical_price.rolling(window=period).apply(lambda x: np.mean(np.abs(x - x.mean())))
        cci = (typical_price - sma_tp) / (0.015 * mad)
        return cci
    
    @staticmethod
    def calculate_kdj(high, low, close, n=9, m1=3, m2=3):
        """计算KDJ指标"""
        # 计算RSV
        low_n = low.rolling(window=n).min()
        high_n = high.rolling(window=n).max()
        rsv = 100 * ((close - low_n) / (high_n - low_n))
        
        # 计算K值
        k = pd.Series(index=rsv.index, dtype=float)
        k.iloc[0] = 50  # 初始值
        for i in range(1, len(rsv)):
            if pd.isna(rsv.iloc[i]):
                k.iloc[i] = k.iloc[i-1]  # 如果RSV为NaN，保持前一个值
            else:
                k.iloc[i] = (2/3) * k.iloc[i-1] + (1/3) * rsv.iloc[i]
        
        # 计算D值
        d = pd.Series(index=k.index, dtype=float)
        d.iloc[0] = 50  # 初始值
        for i in range(1, len(k)):
            if pd.isna(k.iloc[i]):
                d.iloc[i] = d.iloc[i-1]  # 如果K为NaN，保持前一个值
            else:
                d.iloc[i] = (2/3) * d.iloc[i-1] + (1/3) * k.iloc[i]
        
        # 计算J值
        j = 3 * k - 2 * d
        
        return k, d, j

    @staticmethod
    def calculate_sharpe_ratio(returns, risk_free_rate=0.02, window=30):
        """
        计算夏普比率
        
        参数:
        returns: 收益率序列
        risk_free_rate: 无风险利率（年化，默认2%）
        window: 计算窗口期（默认30个周期）
        
        返回:
        sharpe_ratio: 夏普比率
        """
        # 将年化无风险利率转换为周期利率（假设是小时数据）
        period_risk_free_rate = risk_free_rate / (365 * 24)  # 小时级别的无风险利率
        
        # 计算超额收益
        excess_returns = returns - period_risk_free_rate
        
        # 计算滚动夏普比率
        rolling_mean = excess_returns.rolling(window=window).mean()
        rolling_std = returns.rolling(window=window).std()
        
        # 避免除零错误
        rolling_std = rolling_std.replace(0, np.nan)
        
        # 计算夏普比率
        sharpe_ratio = rolling_mean / rolling_std
        
        return sharpe_ratio
    
    @staticmethod
    def calculate_sortino_ratio(returns, risk_free_rate=0.02, window=30):
        """
        计算索提诺比率（只考虑下行风险）
        
        参数:
        returns: 收益率序列
        risk_free_rate: 无风险利率（年化，默认2%）
        window: 计算窗口期（默认30个周期）
        
        返回:
        sortino_ratio: 索提诺比率
        """
        # 将年化无风险利率转换为周期利率
        period_risk_free_rate = risk_free_rate / (365 * 24)
        
        # 计算超额收益
        excess_returns = returns - period_risk_free_rate
        
        # 计算下行收益（只考虑负收益）
        downside_returns = returns.where(returns < 0, 0)
        
        # 计算下行标准差
        downside_std = downside_returns.rolling(window=window).std()
        
        # 避免除零错误
        downside_std = downside_std.replace(0, np.nan)
        
        # 计算索提诺比率
        sortino_ratio = excess_returns.rolling(window=window).mean() / downside_std
        
        return sortino_ratio
    
    @staticmethod
    def calculate_calmar_ratio(returns, window=30):
        """
        计算卡尔马比率（收益与最大回撤的比值）
        
        参数:
        returns: 收益率序列
        window: 计算窗口期（默认30个周期）
        
        返回:
        calmar_ratio: 卡尔马比率
        """
        # 计算累积收益
        cumulative_returns = (1 + returns).cumprod()
        
        # 计算滚动最大回撤
        rolling_max = cumulative_returns.rolling(window=window).max()
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        
        # 计算最大回撤
        max_drawdown = drawdown.rolling(window=window).min()
        
        # 计算平均收益
        avg_return = returns.rolling(window=window).mean()
        
        # 避免除零错误
        max_drawdown = max_drawdown.replace(0, np.nan)
        
        # 计算卡尔马比率
        calmar_ratio = avg_return / abs(max_drawdown)
        
        return calmar_ratio

    @staticmethod
    def calculate_max_drawdown(returns, window=30):
        """
        计算最大回撤
        
        参数:
        returns: 收益率序列
        window: 计算窗口期（默认30个周期）
        
        返回:
        max_drawdown: 最大回撤（负值，表示损失百分比）
        """
        # 计算累积收益
        cumulative_returns = (1 + returns).cumprod()
        
        # 计算滚动最大值
        rolling_max = cumulative_returns.rolling(window=window).max()
        
        # 计算回撤
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        
        # 计算最大回撤（负值）
        max_drawdown = drawdown.rolling(window=window).min()
        
        return max_drawdown
    
    @staticmethod
    def calculate_drawdown_duration(returns, window=30):
        """
        计算回撤持续时间
        
        参数:
        returns: 收益率序列
        window: 计算窗口期（默认30个周期）
        
        返回:
        drawdown_duration: 回撤持续时间（周期数）
        """
        # 计算累积收益
        cumulative_returns = (1 + returns).cumprod()
        
        # 计算滚动最大值
        rolling_max = cumulative_returns.rolling(window=window).max()
        
        # 计算回撤
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        
        # 计算回撤持续时间
        drawdown_duration = pd.Series(index=returns.index, dtype=float)
        
        for i in range(len(returns)):
            if i < window - 1:
                drawdown_duration.iloc[i] = np.nan
            else:
                # 计算当前回撤持续时间
                current_drawdown = 0
                for j in range(i, max(0, i-window), -1):
                    if drawdown.iloc[j] < 0:
                        current_drawdown += 1
                    else:
                        break
                drawdown_duration.iloc[i] = current_drawdown
        
        return drawdown_duration
    
    @staticmethod
    def calculate_ulcer_index(returns, window=30):
        """
        计算溃疡指数（Ulcer Index）
        衡量价格下跌的深度和持续时间
        
        参数:
        returns: 收益率序列
        window: 计算窗口期（默认30个周期）
        
        返回:
        ulcer_index: 溃疡指数
        """
        # 计算累积收益
        cumulative_returns = (1 + returns).cumprod()
        
        # 计算滚动最大值
        rolling_max = cumulative_returns.rolling(window=window).max()
        
        # 计算回撤
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        
        # 计算溃疡指数（回撤的平方根的平均值）
        ulcer_index = np.sqrt((drawdown ** 2).rolling(window=window).mean())
        
        return ulcer_index
    
    @staticmethod
    def calculate_pain_ratio(returns, window=30):
        """
        计算痛苦比率（Pain Ratio）
        收益与溃疡指数的比值
        
        参数:
        returns: 收益率序列
        window: 计算窗口期（默认30个周期）
        
        返回:
        pain_ratio: 痛苦比率
        """
        # 计算平均收益
        avg_return = returns.rolling(window=window).mean()
        
        # 计算溃疡指数
        ulcer_index = FeatureEngineer.calculate_ulcer_index(returns, window)
        
        # 计算痛苦比率
        pain_ratio = avg_return / (ulcer_index + 1e-8)  # 避免除零
        
        return pain_ratio

    def add_features(self, klines):
        """给 K 线数据添加技术指标特征"""
        df = klines.copy()
        
        # 基础价格数据
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        
        # 计算收益率（用于夏普比率等风险指标）
        df['returns'] = df['close'].pct_change()
        
        # 计算技术指标
        df['lineWMA'] = self.calculate_wma(df['close'], LINEWMA_PERIOD)
        df['openEMA'] = self.calculate_ema(df['open'], OPENEMA_PERIOD)
        df['closeEMA'] = self.calculate_ema(df['close'], CLOSEEMA_PERIOD)
        df['rsi'] = self.calculate_rsi(df['close'])
        
        # 计算MACD
        df['macd'], df['macd_signal'], df['macd_histogram'] = self.calculate_macd(df['close'])
        
        # 计算布林带
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = self.calculate_bollinger_bands(df['close'])
        df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"]  # 布林带宽度
        df["bb_position"] = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])  # 价格在布林带中的位置
        
        # 计算KDJ
        df['kdj_k'], df['kdj_d'], df['kdj_j'] = self.calculate_kdj(df['high'], df['low'], df['close'])
        
        # 计算ATR
        df['atr'] = self.calculate_atr(df['high'], df['low'], df['close'])
        df['atr_ratio'] = df['atr'] / df['atr'].rolling(window=20).mean()  # ATR比率
        
        # 随机指标
        df["stoch_k"], df["stoch_d"] = self.calculate_stochastic(df["high"], df["low"], df["close"])
        
        # CCI
        df["cci"] = self.calculate_cci(df["high"], df["low"], df["close"])
        
        # 价格动量指标
        df["price_momentum_1h"] = df["close"].pct_change(1) * 100
        df["price_momentum_2h"] = df["close"].pct_change(2) * 100
        df["price_momentum_4h"] = df["close"].pct_change(4) * 100
        
        # 成交量指标
        df["volume_sma"] = df["volume"].rolling(window=10).mean()
        df["volume_ratio"] = df["volume"] / df["volume_sma"]
        
        # 波动率指标
        df["volatility"] = df["close"].rolling(window=10).std() / df["close"].rolling(window=10).mean()
        
        # 趋势强度指标
        df["trend_strength"] = abs(df["close"] - df["close"].rolling(window=10).mean()) / df["close"].rolling(window=10).mean()
        
        # 风险调整收益指标
        df["sharpe_ratio_30"] = self.calculate_sharpe_ratio(df["returns"], window=30)
        df["sharpe_ratio_60"] = self.calculate_sharpe_ratio(df["returns"], window=60)
        df["sharpe_ratio_120"] = self.calculate_sharpe_ratio(df["returns"], window=120)
        
        # 索提诺比率（只考虑下行风险）
        df["sortino_ratio_30"] = self.calculate_sortino_ratio(df["returns"], window=30)
        df["sortino_ratio_60"] = self.calculate_sortino_ratio(df["returns"], window=60)
        
        # 卡尔马比率（收益与最大回撤的比值）
        df["calmar_ratio_30"] = self.calculate_calmar_ratio(df["returns"], window=30)
        df["calmar_ratio_60"] = self.calculate_calmar_ratio(df["returns"], window=60)
        
        # 最大回撤指标
        df["max_drawdown_30"] = self.calculate_max_drawdown(df["returns"], window=30)
        df["max_drawdown_60"] = self.calculate_max_drawdown(df["returns"], window=60)
        df["max_drawdown_120"] = self.calculate_max_drawdown(df["returns"], window=120)
        
        # 回撤持续时间
        df["drawdown_duration_30"] = self.calculate_drawdown_duration(df["returns"], window=30)
        df["drawdown_duration_60"] = self.calculate_drawdown_duration(df["returns"], window=60)
        
        # 溃疡指数
        df["ulcer_index_30"] = self.calculate_ulcer_index(df["returns"], window=30)
        df["ulcer_index_60"] = self.calculate_ulcer_index(df["returns"], window=60)
        
        # 痛苦比率
        df["pain_ratio_30"] = self.calculate_pain_ratio(df["returns"], window=30)
        df["pain_ratio_60"] = self.calculate_pain_ratio(df["returns"], window=60)
        
        # 风险指标组合
        df["risk_adjusted_return"] = df["sharpe_ratio_30"] * df["returns"].rolling(window=30).mean()
        df["volatility_adjusted_momentum"] = df["price_momentum_1h"] / (df["volatility"] + 1e-8)
        
        # 回撤风险指标
        df["drawdown_risk_score"] = abs(df["max_drawdown_30"]) * df["drawdown_duration_30"] / 100
        df["recovery_potential"] = df["sharpe_ratio_30"] / (abs(df["max_drawdown_30"]) + 1e-8)
        
        # 删除包含NaN的行
        df = df.dropna()
        
        return df