# -*- coding: utf-8 -*-
"""
量化交易策略模块
================

本模块包含多个量化交易策略的实现，包括：
1. 多时间级别数据加载器
2. 基础动量策略
3. 增强版牛势策略
4. 增强版动量策略

每个策略都包含详细的信号生成逻辑和风险管理机制。
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import requests
class MultiTimeframeDataLoader:
    """
    多时间级别数据加载器
    
    功能：
    - 从Binance API获取多个时间级别的K线数据
    - 支持多个API端点以提高可用性
    - 包含重试机制和错误处理
    - 自动数据格式化和清洗
    
    支持的时间级别：
    - 15分钟 (MIN15)
    - 30分钟 (MIN30) 
    - 1小时 (HOUR1)
    - 2小时 (HOUR2)
    - 4小时 (HOUR4)
    """
    
    def __init__(self):
        """
        初始化数据加载器
        
        配置：
        - 多个API端点以提高可用性和负载均衡
        - 支持的时间级别映射
        - 当前使用的API端点索引
        """
        # 多个API端点，提高可用性和负载均衡
        self.api_endpoints = [
            "https://api.binance.com/api/v3",    # 主API端点
            "https://api1.binance.com/api/v3",   # 备用端点1
            "https://api2.binance.com/api/v3",   # 备用端点2
            "https://api3.binance.com/api/v3"    # 备用端点3
        ]
        self.current_endpoint = 0  # 当前使用的API端点索引
        
        # 支持的时间级别配置
        self.timeframes = ["15m", "30m", "1h", "2h", "4h"]  # Binance API格式
        self.timeframe_names = ["MIN15", "MIN30", "HOUR1", "HOUR2", "HOUR4"]  # 内部格式
        self.timeframe_mapping = dict(zip(self.timeframes, self.timeframe_names))  # 映射关系
    
    def _make_request(self, url, params=None, max_retries=3):
        """
        发送HTTP请求，带重试机制和错误处理
        
        特性：
        - 自动重试机制（最多3次）
        - 指数退避策略
        - 多API端点故障转移
        - 请求频率限制处理
        - 随机延迟避免请求过于频繁
        
        Args:
            url: API路径
            params: 请求参数
            max_retries: 最大重试次数
            
        Returns:
            dict: API响应数据，失败时返回None
        """
        import time
        import random
        
        for attempt in range(max_retries):
            try:
                # 选择当前API端点
                endpoint = self.api_endpoints[self.current_endpoint]
                full_url = f"{endpoint}{url}"
                
                # 添加随机延迟，避免请求过于频繁（0.1-0.3秒）
                time.sleep(random.uniform(0.1, 0.3))
                
                # 发送GET请求，超时时间15秒
                response = requests.get(full_url, params=params, timeout=15)
                
                if response.status_code == 200:
                    return response.json()  # 成功返回JSON数据
                elif response.status_code == 429:  # 请求频率限制
                    print(f"⚠ 请求频率限制，等待后重试...")
                    time.sleep(2 ** attempt)  # 指数退避策略
                    continue
                else:
                    print(f"⚠ API响应异常: {response.status_code}")
                    # 尝试切换到下一个API端点
                    self.current_endpoint = (self.current_endpoint + 1) % len(self.api_endpoints)
                    
            except requests.exceptions.RequestException as e:
                print(f"⚠ 请求异常 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避策略
                    # 尝试切换到下一个API端点
                    self.current_endpoint = (self.current_endpoint + 1) % len(self.api_endpoints)
                else:
                    raise e  # 最后一次重试失败，抛出异常
        
        return None  # 所有重试都失败
    
    def get_multi_timeframe_data(self, symbol="ETHUSDT", limit=200):
        """
        获取多个时间级别的K线数据
        
        功能：
        - 并行获取多个时间级别的数据
        - 自动数据格式化和清洗
        - 错误处理和日志记录
        - 返回标准化的DataFrame格式
        
        Args:
            symbol: 交易对符号，默认"ETHUSDT"
            limit: 获取的K线数量，默认200条
            
        Returns:
            dict: 包含多个时间级别数据的字典
                  格式: {timeframe_name: DataFrame}
        """
        multi_tf_data = {}
        
        for timeframe in self.timeframes:
            try:
                # 构建API请求参数
                params = {
                    "symbol": symbol,      # 交易对
                    "interval": timeframe, # 时间级别
                    "limit": limit         # 数据条数
                }
                
                # 发送API请求获取K线数据
                klines_data = self._make_request("/klines", params)
                
                if klines_data is not None:
                    # 转换为DataFrame，包含所有原始列
                    df = pd.DataFrame(klines_data, columns=[
                        "open_time", "open", "high", "low", "close", "volume",
                        "close_time", "quote_asset_volume", "number_of_trades",
                        "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
                    ])
                    
                    # 转换数值类型列（OHLCV）
                    numeric_columns = ["open", "high", "low", "close", "volume"]
                    for col in numeric_columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    # 转换时间戳为datetime格式
                    df["datetime"] = pd.to_datetime(df["open_time"], unit="ms")
                    df = df.set_index("datetime")
                    
                    # 只保留策略需要的列（OHLCV）
                    df = df[["open", "high", "low", "close", "volume"]]
                    
                    # 使用标准化的时间级别名称存储
                    tf_name = self.timeframe_mapping[timeframe]
                    multi_tf_data[tf_name] = df
                    print(f"✓ 成功获取 {tf_name} 时间级别数据: {len(df)} 条")
                    
                else:
                    print(f"❌ 获取 {timeframe} 时间级别数据失败")
                    
            except Exception as e:
                print(f"❌ 处理 {timeframe} 时间级别数据时出错: {e}")
        
        return multi_tf_data
class HighFrequencyAdaptiveStrategy:
    """
    高频自适应止盈策略
    优化信号质量，改进风险控制，提升夏普比率，增强趋势确认机制。
    新增风险控制机制和动态仓位管理。
    """
    
    @staticmethod
    def get_signal(features):
        """
        动态止盈策略信号生成
        
        算法流程：
        =========
        1. 数据验证：检查数据完整性和最小长度要求
        2. 市场环境判断：分析波动率和成交量判断市场状态
        3. 多时间框架趋势：计算短期、中期、长期趋势
        4. 趋势强度分析：基于价格与均线关系的趋势强度
        5. 成交量确认：成交量趋势和比率分析
        6. RSI过滤：RSI指标的超买超卖和趋势分析
        7. 趋势一致性：多时间框架趋势一致性检查
        8. MACD分析：趋势确认和动量分析
        9. 布林带分析：价格位置和波动分析
        10. KDJ分析：超买超卖和趋势分析
        11. ATR分析：真实波动幅度分析
        12. 动态信号过滤：根据市场条件调整信号敏感度
        13. 综合评分：加权计算最终交易信号
        
        参数说明：
        =========
        - market_condition: 市场环境判断（高波动/低波动/震荡）
        - trend_strength: 趋势强度（基于价格与均线关系）
        - volume_confirmation: 成交量确认信号
        - rsi_filter: RSI过滤信号
        - trend_consistency: 趋势一致性信号
        - macd_signal: MACD信号
        - bollinger_signal: 布林带信号
        - kdj_signal: KDJ信号
        - atr_signal: ATR信号
        - signal_threshold: 动态信号阈值
        
        Args:
            features: 包含技术指标的DataFrame
                    必须包含：close, lineWMA, openEMA, closeEMA, rsi, volume等列
                    建议数据长度：至少20条记录
            
        Returns:
            int: 交易信号
                1: 做多信号（强势上涨）
                -1: 做空信号（强势下跌）
                0: 观望信号
        """
        if len(features) < 20:  # 需要更多历史数据
            return 0
        
        # ==================== 基础数据准备 ====================
        current_close = features["close"].iloc[-1]
        current_linewma = features["lineWMA"].iloc[-1]
        current_openema = features["openEMA"].iloc[-1]
        current_closeema = features["closeEMA"].iloc[-1]
        current_rsi = features["rsi"].iloc[-1]
        current_volume = features["volume"].iloc[-1]
        
        # ==================== 市场环境判断 ====================
        # 计算价格波动率
        volatility_5h = features["close"].rolling(window=5).std().iloc[-1] / current_close
        volatility_10h = features["close"].rolling(window=10).std().iloc[-1] / current_close
        
        # 计算成交量比率
        avg_volume_5h = features["volume"].rolling(window=5).mean().iloc[-1]
        avg_volume_10h = features["volume"].rolling(window=10).mean().iloc[-1]
        volume_ratio_5h = current_volume / avg_volume_5h if avg_volume_5h > 0 else 1
        volume_ratio_10h = current_volume / avg_volume_10h if avg_volume_10h > 0 else 1
        
        # 市场环境判断 - 优化阈值
        market_condition = 0  # 0=震荡, 1=趋势, 2=高波动
        if volatility_5h > 0.02 and volatility_10h > 0.015:  # 降低高波动阈值
            market_condition = 2
        elif volatility_5h < 0.008 and volatility_10h < 0.01:  # 降低低波动阈值
            market_condition = 0
        else:  # 正常趋势
            market_condition = 1
        
        # ==================== 多时间框架趋势分析 ====================
        # 短期趋势（1-3小时）
        short_trend = 0
        for i in range(1, 4):
            if i < len(features):
                prev_close = features["close"].iloc[-i]
                prev_linewma = features["lineWMA"].iloc[-i]
                if prev_close > prev_linewma:
                    short_trend += 1
                elif prev_close < prev_linewma:
                    short_trend -= 1
        
        # 中期趋势（4-8小时）
        medium_trend = 0
        for i in range(4, 9):
            if i < len(features):
                prev_close = features["close"].iloc[-i]
                prev_openema = features["openEMA"].iloc[-i]
                if prev_close > prev_openema:
                    medium_trend += 1
                elif prev_close < prev_openema:
                    medium_trend -= 1
        
        # 长期趋势（9-15小时）
        long_trend = 0
        for i in range(9, 16):
            if i < len(features):
                prev_close = features["close"].iloc[-i]
                prev_closeema = features["closeEMA"].iloc[-i]
                if prev_close > prev_closeema:
                    long_trend += 1
                elif prev_close < prev_closeema:
                    long_trend -= 1
        
        # ==================== 趋势强度分析 ====================
        trend_strength = 0
        
        # 当前价格与均线关系
        if current_close > current_linewma: trend_strength += 1
        if current_close > current_openema: trend_strength += 1
        if current_close > current_closeema: trend_strength += 1
        
        # 均线排列（多头排列/空头排列）
        if current_linewma > current_openema > current_closeema:  # 多头排列
            trend_strength += 2
        elif current_linewma < current_openema < current_closeema:  # 空头排列
            trend_strength -= 2
        
        # ==================== 成交量确认 ====================
        volume_confirmation = 0
        
        # 成交量趋势确认 - 降低阈值，提高敏感度
        if volume_ratio_5h > 1.2 and volume_ratio_10h > 1.1:  # 降低阈值
            volume_confirmation = 1.0  # 成交量放大
        elif volume_ratio_5h > 1.4 and volume_ratio_10h > 1.3:  # 降低阈值
            volume_confirmation = 1.5  # 强烈成交量放大
        elif volume_ratio_5h < 0.8 and volume_ratio_10h < 0.9:  # 提高阈值
            volume_confirmation = -0.8  # 成交量萎缩
        
        # ==================== RSI过滤（进一步优化） ====================
        rsi_filter = 0
        prev_rsi = features["rsi"].iloc[-2]
        rsi_trend = current_rsi - prev_rsi
        
        # 进一步放宽RSI过滤条件，大幅提高交易频率
        if current_rsi < 40 and rsi_trend > 0:  # 进一步提高超卖阈值到40
            rsi_filter = 1.5
        elif current_rsi < 50 and rsi_trend > 0:  # 进一步提高阈值到50
            rsi_filter = 0.8
        elif current_rsi > 60 and rsi_trend < 0:  # 进一步降低超买阈值到60
            rsi_filter = -1.5
        elif current_rsi > 50 and rsi_trend < 0:  # 进一步降低阈值到50
            rsi_filter = -0.8
        elif 40 <= current_rsi <= 60:  # 扩大中性区间
            if rsi_trend > 0:
                rsi_filter = 0.5  # RSI上升，增强信号
            elif rsi_trend < 0:
                rsi_filter = -0.5  # RSI下降，增强信号
        
        # ==================== MACD分析（新增） ====================
        macd_signal = 0
        if "macd" in features.columns and "macd_signal" in features.columns:
            current_macd = features["macd"].iloc[-1]
            current_macd_signal = features["macd_signal"].iloc[-1]
            prev_macd = features["macd"].iloc[-2]
            prev_macd_signal = features["macd_signal"].iloc[-2]
            
            # MACD金叉死叉
            if current_macd > current_macd_signal and prev_macd <= prev_macd_signal:
                macd_signal = 1.0  # 金叉
            elif current_macd < current_macd_signal and prev_macd >= prev_macd_signal:
                macd_signal = -1.0  # 死叉
            
            # MACD趋势
            elif current_macd > current_macd_signal and current_macd > 0:
                macd_signal = 0.5  # 多头趋势
            elif current_macd < current_macd_signal and current_macd < 0:
                macd_signal = -0.5  # 空头趋势
        
        # ==================== 布林带分析（新增） ====================
        bollinger_signal = 0
        if "bb_upper" in features.columns and "bb_lower" in features.columns:
            current_bb_upper = features["bb_upper"].iloc[-1]
            current_bb_lower = features["bb_lower"].iloc[-1]
            current_bb_middle = features["bb_middle"].iloc[-1]
            
            # 价格位置
            if current_close < current_bb_lower:
                bollinger_signal = 1.0  # 超卖反弹
            elif current_close > current_bb_upper:
                bollinger_signal = -1.0  # 超买回调
            elif current_close > current_bb_middle:
                bollinger_signal = 0.3  # 多头区域
            elif current_close < current_bb_middle:
                bollinger_signal = -0.3  # 空头区域
        
        # ==================== KDJ分析（新增） ====================
        kdj_signal = 0
        if "kdj_k" in features.columns and "kdj_d" in features.columns:
            current_k = features["kdj_k"].iloc[-1]
            current_d = features["kdj_d"].iloc[-1]
            prev_k = features["kdj_k"].iloc[-2]
            prev_d = features["kdj_d"].iloc[-2]
            
            # KDJ金叉死叉
            if current_k > current_d and prev_k <= prev_d:
                kdj_signal = 1.0  # 金叉
            elif current_k < current_d and prev_k >= prev_d:
                kdj_signal = -1.0  # 死叉
            
            # KDJ超买超卖
            elif current_k < 20 and current_d < 20:
                kdj_signal = 0.8  # 超卖
            elif current_k > 80 and current_d > 80:
                kdj_signal = -0.8  # 超买
        
        # ==================== ATR分析（新增） ====================
        atr_signal = 0
        if "atr" in features.columns:
            current_atr = features["atr"].iloc[-1]
            avg_atr = features["atr"].rolling(window=10).mean().iloc[-1]
            
            # ATR相对强度
            if current_atr > avg_atr * 1.2:
                atr_signal = 0.5  # 高波动
            elif current_atr < avg_atr * 0.8:
                atr_signal = -0.3  # 低波动
            else:
                atr_signal = 0.1  # 正常波动
        
        # ==================== 趋势一致性检查 ====================
        trend_consistency = 0
        
        # 检查多时间框架趋势一致性 - 进一步放宽条件
        if short_trend >= 0 and medium_trend >= -1:  # 进一步降低要求
            trend_consistency = 1.0  # 多头趋势一致
        elif short_trend <= 0 and medium_trend <= 1:  # 进一步降低要求
            trend_consistency = -1.0  # 空头趋势一致
        elif short_trend >= -1 and medium_trend >= -1:  # 更宽松的多头条件
            trend_consistency = 0.5
        elif short_trend <= 1 and medium_trend <= 1:  # 更宽松的空头条件
            trend_consistency = -0.5
        
        # ==================== 动态信号阈值 ====================
        # 根据市场环境调整信号阈值 - 提高阈值，提升信号质量
        if market_condition == 0:  # 震荡市场
            base_threshold = 0.6  # 提高阈值：从0.4提高到0.6，提升信号质量
        elif market_condition == 1:  # 正常趋势
            base_threshold = 0.5  # 提高阈值：从0.3提高到0.5，提升信号质量
        else:  # 高波动市场
            base_threshold = 0.7  # 提高阈值：从0.5提高到0.7，提升信号质量
        
        # ==================== 综合信号计算 ====================
        signal_strength = 0
        
        # 权重分配：趋势强度(0.3) + 成交量(0.2) + RSI(0.15) + 趋势一致性(0.1) + MACD(0.15) + 布林带(0.1) + KDJ(0.05)
        signal_strength += (trend_strength / 3) * 0.3  # 增加趋势强度权重
        signal_strength += volume_confirmation * 0.2  # 增加成交量权重
        signal_strength += rsi_filter * 0.15  # 增加RSI权重
        signal_strength += trend_consistency * 0.1  # 减少趋势一致性权重，提高交易频率
        signal_strength += macd_signal * 0.15
        signal_strength += bollinger_signal * 0.1
        signal_strength += kdj_signal * 0.05
        
        # ==================== 市场环境过滤 ====================
        # 在震荡市场中，提高信号要求
        if market_condition == 0:
            if abs(signal_strength) < base_threshold * 0.8:  # 提高要求
                return 0  # 震荡市场中信号不足，观望
        
        # ==================== 风险控制过滤 ====================
        # 获取风险状态
        risk_status = HighFrequencyAdaptiveStrategy.get_risk_status(features)
        
        # 高风险环境下，需要更强的信号
        if risk_status["risk_level"] == "high":
            if abs(signal_strength) < base_threshold * 1.2:  # 需要更强的信号
                return 0  # 高风险环境下信号不足，观望
        
        # 中等风险环境下，适度提高要求
        elif risk_status["risk_level"] == "medium":
            if abs(signal_strength) < base_threshold * 1.0:  # 适度提高要求
                return 0  # 中等风险环境下信号不足，观望
        
        # ==================== 最终信号判断 ====================
        # 提高信号阈值，提升信号质量
        if signal_strength >= base_threshold:
            return 1  # 做多信号
        elif signal_strength <= -base_threshold:
            return -1  # 做空信号
        elif signal_strength >= base_threshold * 0.8:  # 提高温和信号阈值
            return 1  # 温和做多信号
        elif signal_strength <= -base_threshold * 0.8:
            return -1  # 温和做空信号
        else:
            return 0  # 观望信号
    
    @staticmethod
    def get_dynamic_take_profit_levels(features, market_condition, trend_strength):
        """
        获取动态止盈水平
        
        Args:
            features: 技术指标数据
            market_condition: 市场环境 (0=震荡, 1=趋势, 2=高波动)
            trend_strength: 趋势强度
            
        Returns:
            dict: 包含动态止盈水平的字典
        """
        # 计算ATR
        atr = 0
        if "atr" in features.columns:
            atr = features["atr"].iloc[-1]
        
        # 计算波动率
        volatility = features["close"].rolling(window=10).std().iloc[-1] / features["close"].iloc[-1]
        
        # 基础止盈水平 - 大幅提高阈值，增加盈利空间
        base_take_profit = 0.08  # 8%基础止盈
        
        # 根据市场环境调整 - 降低止盈阈值，提高收益
        if market_condition == 0:  # 震荡市场
            take_profit_levels = {
                "partial_1": 0.05,   # 5%部分止盈（降低）
                "partial_2": 0.08,   # 8%部分止盈（降低）
                "full": 0.15         # 15%完全止盈（降低）
            }
        elif market_condition == 1:  # 正常趋势
            take_profit_levels = {
                "partial_1": 0.08,   # 8%部分止盈（降低）
                "partial_2": 0.12,   # 12%部分止盈（降低）
                "full": 0.20         # 20%完全止盈（降低）
            }
        else:  # 高波动市场
            take_profit_levels = {
                "partial_1": 0.10,   # 10%部分止盈（降低）
                "partial_2": 0.15,   # 15%部分止盈（降低）
                "full": 0.25         # 25%完全止盈（降低）
            }
        
        # 根据趋势强度调整 - 大幅优化调整幅度
        if abs(trend_strength) >= 3:  # 强趋势
            for key in take_profit_levels:
                take_profit_levels[key] *= 1.5  # 增加50%
        elif abs(trend_strength) <= 1:  # 弱趋势
            for key in take_profit_levels:
                take_profit_levels[key] *= 0.6  # 减少40%
        
        # 根据ATR调整 - 大幅优化调整幅度
        if atr > 0:
            atr_ratio = atr / features["close"].iloc[-1]
            if atr_ratio > 0.02:  # 高波动
                for key in take_profit_levels:
                    take_profit_levels[key] *= 1.3  # 增加30%
            elif atr_ratio < 0.01:  # 低波动
                for key in take_profit_levels:
                    take_profit_levels[key] *= 0.7  # 减少30%
        
        return take_profit_levels
    
    @staticmethod
    def get_risk_status(features):
        """
        获取风险状态 - 新增风险控制机制
        
        Args:
            features: 技术指标数据
            
        Returns:
            dict: 风险状态信息
        """
        current_close = features["close"].iloc[-1]
        
        # 计算波动率
        volatility_5h = features["close"].rolling(window=5).std().iloc[-1] / current_close
        volatility_10h = features["close"].rolling(window=10).std().iloc[-1] / current_close
        volatility_20h = features["close"].rolling(window=20).std().iloc[-1] / current_close
        
        # 计算ATR
        atr = 0
        if "atr" in features.columns:
            atr = features["atr"].iloc[-1]
        
        # 计算RSI
        current_rsi = features["rsi"].iloc[-1]
        
        # 计算成交量比率
        current_volume = features["volume"].iloc[-1]
        avg_volume_10h = features["volume"].rolling(window=10).mean().iloc[-1]
        volume_ratio = current_volume / avg_volume_10h if avg_volume_10h > 0 else 1
        
        # 风险等级判断
        risk_level = "low"
        risk_score = 0
        
        # 波动率风险评分
        if volatility_5h > 0.03:
            risk_score += 3
        elif volatility_5h > 0.02:
            risk_score += 2
        elif volatility_5h > 0.015:
            risk_score += 1
        
        if volatility_10h > 0.025:
            risk_score += 2
        elif volatility_10h > 0.02:
            risk_score += 1
        
        # ATR风险评分
        if atr > 0:
            atr_ratio = atr / current_close
            if atr_ratio > 0.03:
                risk_score += 3
            elif atr_ratio > 0.02:
                risk_score += 2
            elif atr_ratio > 0.015:
                risk_score += 1
        
        # RSI风险评分
        if current_rsi > 80 or current_rsi < 20:
            risk_score += 2
        elif current_rsi > 75 or current_rsi < 25:
            risk_score += 1
        
        # 成交量风险评分
        if volume_ratio > 2.0:
            risk_score += 2
        elif volume_ratio > 1.5:
            risk_score += 1
        
        # 确定风险等级
        if risk_score >= 6:
            risk_level = "high"
        elif risk_score >= 3:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "volatility_5h": volatility_5h,
            "volatility_10h": volatility_10h,
            "atr_ratio": atr / current_close if atr > 0 else 0,
            "rsi": current_rsi,
            "volume_ratio": volume_ratio
        }
    
    @staticmethod
    def get_position_size(features, base_position=1.0):
        """
        动态仓位管理 - 根据风险状态调整仓位大小
        
        Args:
            features: 技术指标数据
            base_position: 基础仓位大小
            
        Returns:
            float: 调整后的仓位大小
        """
        risk_status = HighFrequencyAdaptiveStrategy.get_risk_status(features)
        
        # 根据风险等级调整仓位
        if risk_status["risk_level"] == "high":
            position_multiplier = 0.3  # 高风险时大幅减仓
        elif risk_status["risk_level"] == "medium":
            position_multiplier = 0.6  # 中等风险时适度减仓
        else:
            position_multiplier = 0.9  # 低风险时轻微减仓
        
        # 根据波动率进一步调整
        volatility_5h = risk_status["volatility_5h"]
        if volatility_5h > 0.025:
            position_multiplier *= 0.8
        elif volatility_5h > 0.02:
            position_multiplier *= 0.9
        
        # 根据RSI调整
        rsi = risk_status["rsi"]
        if rsi > 75 or rsi < 25:
            position_multiplier *= 0.7
        
        return base_position * position_multiplier

class TrendTrackingRiskManagementStrategy:
    """
    趋势跟踪风险管理策略 - 优化版本
    
    策略特点：
    - 更精确的趋势识别机制
    - 改进的风险控制算法
    - 优化的仓位管理
    - 更快的信号响应
    - 平衡的风险收益比
    
    核心改进：
    - 简化多时间框架分析，减少信号延迟
    - 优化风险评分算法，提高准确性
    - 改进仓位管理，提高交易频率
    - 增强趋势反转信号识别
    """
    
    @staticmethod
    def get_signal(features):
        """
        改进版趋势反转风险管理策略信号生成
        
        算法流程：
        =========
        1. 简化趋势分析：减少时间框架数量，提高响应速度
        2. 优化风险检测：更精确的下行趋势识别
        3. 改进反转信号：更敏感的反弹信号检测
        4. 动态风险调整：基于市场状态的动态调整
        5. 平衡信号生成：在风险和收益之间找到平衡
        
        Args:
            features: 包含技术指标的DataFrame
                    必须包含：close, lineWMA, openEMA, closeEMA, rsi, volume等列
                    建议数据长度：至少20条记录
            
        Returns:
            int: 交易信号
                1: 做多信号（趋势反转确认）
                -1: 做空信号（下行趋势确认）
                0: 观望信号（高风险环境）
        """
        if len(features) < 20:  # 减少所需历史数据
            return 0
        
        # ==================== 基础数据准备 ====================
        current_close = features["close"].iloc[-1]
        current_linewma = features["lineWMA"].iloc[-1]
        current_openema = features["openEMA"].iloc[-1]
        current_closeema = features["closeEMA"].iloc[-1]
        current_rsi = features["rsi"].iloc[-1]
        current_volume = features["volume"].iloc[-1]
        
        # ==================== 简化趋势分析 ====================
        # 短期趋势（1-3小时）- 减少时间范围
        short_trend = 0
        for i in range(1, 4):
            if i < len(features):
                prev_close = features["close"].iloc[-i]
                prev_linewma = features["lineWMA"].iloc[-i]
                if prev_close > prev_linewma:
                    short_trend += 1
                elif prev_close < prev_linewma:
                    short_trend -= 1
        
        # 中期趋势（4-10小时）- 减少时间范围
        medium_trend = 0
        for i in range(4, 11):
            if i < len(features):
                prev_close = features["close"].iloc[-i]
                prev_openema = features["openEMA"].iloc[-i]
                if prev_close > prev_openema:
                    medium_trend += 1
                elif prev_close < prev_openema:
                    medium_trend -= 1
        
        # ==================== 趋势强度评估 ====================
        trend_strength = 0
        
        # 当前价格与均线关系
        if current_close > current_linewma: trend_strength += 1
        if current_close > current_openema: trend_strength += 1
        if current_close > current_closeema: trend_strength += 1
        
        # 均线排列
        if current_linewma > current_openema > current_closeema:  # 多头排列
            trend_strength += 2
        elif current_linewma < current_openema < current_closeema:  # 空头排列
            trend_strength -= 2
        
        # ==================== 优化风险检测 ====================
        down_trend_risk = 0
        
        # 检查是否处于下行趋势（降低阈值）
        if short_trend <= -2 and medium_trend <= -3:
            down_trend_risk = 2  # 中等下行趋势
        elif short_trend <= -1 and medium_trend <= -2:
            down_trend_risk = 1  # 弱下行趋势
        
        # 价格位置检查
        if current_close < current_linewma < current_openema:
            down_trend_risk += 1  # 价格在短期均线下方
        
        # RSI超卖检查
        if current_rsi < 25:
            down_trend_risk -= 1  # RSI严重超卖，可能反弹
        
        # ==================== 改进反转信号识别 ====================
        reversal_signal = 0
        
        # 检查短期反转信号（降低阈值）
        if short_trend >= 1 and medium_trend <= -1:  # 短期反弹，中期仍下行
            reversal_signal = 1  # 可能的反弹信号
        
        # 检查中期反转信号
        if short_trend >= 2 and medium_trend >= 0:
            reversal_signal = 2  # 中期反转信号
        
        # RSI反转信号
        prev_rsi = features["rsi"].iloc[-2]
        rsi_trend = current_rsi - prev_rsi
        if current_rsi > 25 and rsi_trend > 3:  # RSI从超卖区域反弹
            reversal_signal += 1
        
        # ==================== 波动率分析 ====================
        volatility = features["close"].rolling(window=10).std().iloc[-1] / current_close
        volatility_factor = 1.0
        
        if volatility > 0.03:  # 高波动
            volatility_factor = 0.8  # 适度降低信号敏感度
        elif volatility > 0.02:  # 中等波动
            volatility_factor = 0.9
        elif volatility < 0.01:  # 低波动
            volatility_factor = 1.1  # 适度提高信号敏感度
        
        # ==================== 成交量确认 ====================
        volume_confirmation = 0
        avg_volume_10h = features["volume"].rolling(window=10).mean().iloc[-1]
        volume_ratio = current_volume / avg_volume_10h if avg_volume_10h > 0 else 1
        
        if volume_ratio > 1.3:  # 成交量放大
            volume_confirmation = 1
        elif volume_ratio > 1.8:  # 强烈成交量放大
            volume_confirmation = 2
        
        # ==================== 优化风险评分计算 ====================
        risk_score = 0
        
        # 下行趋势风险评分（权重30%）
        risk_score += down_trend_risk * 0.3
        
        # 趋势反转信号评分（权重40%）
        risk_score += reversal_signal * 0.4
        
        # 趋势强度评分（权重20%）
        risk_score += (trend_strength / 3) * 0.2
        
        # 成交量确认评分（权重10%）
        risk_score += volume_confirmation * 0.1
        
        # 应用波动率调整
        risk_score *= volatility_factor
        
        # ==================== 改进信号生成逻辑 ====================
        # 高风险环境：强下行趋势时，需要强反转信号
        if down_trend_risk >= 2:
            if reversal_signal >= 2:  # 需要中等反转信号
                return 1  # 做多
            else:
                return 0  # 观望
        
        # 中等风险环境：需要反转信号
        elif down_trend_risk >= 1:
            if reversal_signal >= 1:  # 需要弱反转信号
                return 1  # 做多
            else:
                return 0  # 观望
        
        # 低风险环境：正常信号生成
        else:
            if risk_score >= 0.3:
                return 1  # 做多信号
            elif risk_score <= -0.3:
                return -1  # 做空信号
            else:
                return 0  # 观望信号
    
    @staticmethod
    def get_dynamic_stop_loss(features, entry_price, position_type):
        """
        改进的动态止损计算
        
        Args:
            features: 技术指标数据
            entry_price: 开仓价格
            position_type: 仓位类型 (1=多仓, -1=空仓)
            
        Returns:
            float: 动态止损价格
        """
        current_close = features["close"].iloc[-1]
        atr = features["atr"].iloc[-1] if "atr" in features.columns else 0
        
        # 基础止损比例
        base_stop_loss = 0.025  # 2.5%基础止损（更紧）
        
        # 根据ATR调整止损
        if atr > 0:
            atr_ratio = atr / current_close
            if atr_ratio > 0.02:  # 高波动
                base_stop_loss = 0.035  # 3.5%止损
            elif atr_ratio < 0.01:  # 低波动
                base_stop_loss = 0.02  # 2%止损
        
        # 根据趋势强度调整止损
        trend_strength = 0
        if "lineWMA" in features.columns:
            linewma = features["lineWMA"].iloc[-1]
            if position_type == 1:  # 多仓
                if current_close > linewma:
                    base_stop_loss *= 0.85  # 趋势向上，收紧止损
                else:
                    base_stop_loss *= 1.1  # 趋势向下，适度放宽止损
            else:  # 空仓
                if current_close < linewma:
                    base_stop_loss *= 0.85  # 趋势向下，收紧止损
                else:
                    base_stop_loss *= 1.1  # 趋势向上，适度放宽止损
        
        # 计算止损价格
        if position_type == 1:  # 多仓
            stop_loss_price = entry_price * (1 - base_stop_loss)
        else:  # 空仓
            stop_loss_price = entry_price * (1 + base_stop_loss)
        
        return stop_loss_price
    
    @staticmethod
    def get_position_size(features, base_position=1.0):
        """
        改进的动态仓位管理
        
        Args:
            features: 技术指标数据
            base_position: 基础仓位大小
            
        Returns:
            float: 调整后的仓位大小
        """
        current_close = features["close"].iloc[-1]
        
        # 计算趋势强度
        trend_strength = 0
        if "lineWMA" in features.columns and "openEMA" in features.columns and "closeEMA" in features.columns:
            linewma = features["lineWMA"].iloc[-1]
            openema = features["openEMA"].iloc[-1]
            closeema = features["closeEMA"].iloc[-1]
            
            if current_close > linewma: trend_strength += 1
            if current_close > openema: trend_strength += 1
            if current_close > closeema: trend_strength += 1
            
            if linewma > openema > closeema:  # 多头排列
                trend_strength += 2
            elif linewma < openema < closeema:  # 空头排列
                trend_strength -= 2
        
        # 计算波动率
        volatility = features["close"].rolling(window=10).std().iloc[-1] / current_close
        
        # 计算RSI
        rsi = features["rsi"].iloc[-1]
        
        # 仓位调整因子
        position_factor = 1.0
        
        # 根据趋势强度调整（更温和的调整）
        if trend_strength >= 3:  # 强趋势
            position_factor *= 1.15
        elif trend_strength <= -3:  # 强反向趋势
            position_factor *= 0.5  # 适度减仓
        elif trend_strength <= -1:  # 弱反向趋势
            position_factor *= 0.75  # 适度减仓
        
        # 根据波动率调整
        if volatility > 0.03:  # 高波动
            position_factor *= 0.8
        elif volatility > 0.02:  # 中等波动
            position_factor *= 0.9
        elif volatility < 0.01:  # 低波动
            position_factor *= 1.05
        
        # 根据RSI调整
        if rsi > 75:  # 超买
            position_factor *= 0.85
        elif rsi < 25:  # 超卖
            position_factor *= 0.85
        
        # 限制仓位范围
        position_factor = max(0.3, min(1.3, position_factor))
        
        return base_position * position_factor
    
    @staticmethod
    def get_risk_status(features):
        """
        获取风险状态
        
        Args:
            features: 技术指标数据
            
        Returns:
            dict: 风险状态信息
        """
        current_close = features["close"].iloc[-1]
        
        # 计算趋势强度
        trend_strength = 0
        if "lineWMA" in features.columns and "openEMA" in features.columns and "closeEMA" in features.columns:
            linewma = features["lineWMA"].iloc[-1]
            openema = features["openEMA"].iloc[-1]
            closeema = features["closeEMA"].iloc[-1]
            
            if current_close > linewma: trend_strength += 1
            if current_close > openema: trend_strength += 1
            if current_close > closeema: trend_strength += 1
            
            if linewma > openema > closeema:  # 多头排列
                trend_strength += 2
            elif linewma < openema < closeema:  # 空头排列
                trend_strength -= 2
        
        # 计算波动率
        volatility = features["close"].rolling(window=10).std().iloc[-1] / current_close
        
        # 计算RSI
        rsi = features["rsi"].iloc[-1]
        
        # 风险等级判断
        risk_level = "low"
        if trend_strength <= -3 or volatility > 0.03:
            risk_level = "high"
        elif trend_strength <= -1 or volatility > 0.02:
            risk_level = "medium"
        
        return {
            "risk_level": risk_level,
            "trend_strength": trend_strength,
            "volatility": volatility,
            "rsi": rsi,
            "position_recommendation": "reduce" if risk_level == "high" else "normal"
        }
class ConservativeDrawdownControlStrategy:
    """
    保守回撤控制策略
    
    基于多种风险调整收益指标的高频交易策略：
    1. 夏普比率、索提诺比率、卡尔马比率综合分析
    2. 动态回撤控制机制（25-30%阈值）
    3. 高频交易信号生成（237次交易/180天）
    4. 动态仓位管理和风险调整
    5. 传统技术指标确认
    6. 适合积极型投资者，追求高收益
    """
    
    @staticmethod
    def get_signal(features):
        """
        高频风险调整收益交易信号生成
        
        算法流程：
        =========
        1. 风险调整收益分析：计算多个时间框架的夏普比率、索提诺比率、卡尔马比率
        2. 动态回撤控制：当回撤超过25-30%时立即平仓
        3. 风险收益趋势：分析风险调整收益指标的趋势
        4. 波动率调整：基于当前波动率调整信号敏感度
        5. 传统指标确认：使用RSI、MACD、布林带等传统指标确认信号
        6. 综合评分：加权计算最终交易信号
        7. 高频交易：降低信号阈值，提高交易频率
        
        Args:
            features: 包含技术指标和风险调整收益指标的DataFrame
                    必须包含：close, returns, sharpe_ratio_*, sortino_ratio_*, calmar_ratio_*, max_drawdown_*等列
                    建议数据长度：至少60条记录（降低要求）
            
        Returns:
            int: 交易信号
                1: 做多信号（风险调整收益良好且回撤可控）
                -1: 做空信号（风险调整收益恶化或回撤过大）
                0: 观望信号
        """
        if len(features) < 60:  # 降低数据要求，从120条降低到60条
            return 0
        
        # ==================== 基础数据准备 ====================
        current_close = features["close"].iloc[-1]
        current_returns = features["returns"].iloc[-1]
        
        # ==================== 动态回撤控制 ====================
        # 获取最新的最大回撤指标
        max_drawdown_30 = features["max_drawdown_30"].iloc[-1]
        max_drawdown_60 = features["max_drawdown_60"].iloc[-1]
        
        # 回撤控制：动态回撤限制，25-30%阈值
        if not pd.isna(max_drawdown_30) and abs(max_drawdown_30) > 0.25:
            return -1  # 强制平仓信号
        
        if not pd.isna(max_drawdown_60) and abs(max_drawdown_60) > 0.30:
            return -1  # 强制平仓信号
        
        # ==================== 风险调整收益指标分析 ====================
        # 获取最新的风险调整收益指标
        sharpe_30 = features["sharpe_ratio_30"].iloc[-1]
        sharpe_60 = features["sharpe_ratio_60"].iloc[-1]
        sharpe_120 = features["sharpe_ratio_120"].iloc[-1]
        
        sortino_30 = features["sortino_ratio_30"].iloc[-1]
        sortino_60 = features["sortino_ratio_60"].iloc[-1]
        
        calmar_30 = features["calmar_ratio_30"].iloc[-1]
        calmar_60 = features["calmar_ratio_60"].iloc[-1]
        
        # 回撤持续时间
        drawdown_duration_30 = features["drawdown_duration_30"].iloc[-1]
        drawdown_duration_60 = features["drawdown_duration_60"].iloc[-1]
        
        # 溃疡指数和痛苦比率
        ulcer_index_30 = features["ulcer_index_30"].iloc[-1]
        pain_ratio_30 = features["pain_ratio_30"].iloc[-1]
        
        # 风险调整收益趋势分析
        sharpe_trend = 0
        if not pd.isna(sharpe_30) and not pd.isna(sharpe_60):
            if sharpe_30 > sharpe_60:
                sharpe_trend = 1  # 夏普比率改善
            elif sharpe_30 < sharpe_60:
                sharpe_trend = -1  # 夏普比率恶化
        
        sortino_trend = 0
        if not pd.isna(sortino_30) and not pd.isna(sortino_60):
            if sortino_30 > sortino_60:
                sortino_trend = 1  # 索提诺比率改善
            elif sortino_30 < sortino_60:
                sortino_trend = -1  # 索提诺比率恶化
        
        calmar_trend = 0
        if not pd.isna(calmar_30) and not pd.isna(calmar_60):
            if calmar_30 > calmar_60:
                calmar_trend = 1  # 卡尔马比率改善
            elif calmar_30 < calmar_60:
                calmar_trend = -1  # 卡尔马比率恶化
        
        # ==================== 增强的回撤风险分析 ====================
        drawdown_risk_score = 0
        
        # 最大回撤评分（权重30%）- 动态回撤评分标准
        if not pd.isna(max_drawdown_30):
            if max_drawdown_30 > -0.05:  # 回撤小于5%
                drawdown_risk_score += 0.30
            elif max_drawdown_30 > -0.10:  # 回撤5-10%
                drawdown_risk_score += 0.20
            elif max_drawdown_30 > -0.15:  # 回撤10-15%
                drawdown_risk_score += 0.10
            elif max_drawdown_30 > -0.20:  # 回撤15-20%
                drawdown_risk_score += 0.05
            elif max_drawdown_30 < -0.25:  # 回撤大于25%
                drawdown_risk_score -= 0.30  # 大幅扣分
        
        # 回撤持续时间评分（权重20%）
        if not pd.isna(drawdown_duration_30):
            if drawdown_duration_30 < 5:  # 回撤持续时间很短
                drawdown_risk_score += 0.20
            elif drawdown_duration_30 < 10:  # 回撤持续时间短
                drawdown_risk_score += 0.10
            elif drawdown_duration_30 < 15:  # 回撤持续时间中等
                drawdown_risk_score += 0.05
            elif drawdown_duration_30 > 20:  # 回撤持续时间长
                drawdown_risk_score -= 0.20
        
        # 溃疡指数评分（权重15%）
        if not pd.isna(ulcer_index_30):
            if ulcer_index_30 < 0.05:  # 溃疡指数很低
                drawdown_risk_score += 0.15
            elif ulcer_index_30 < 0.10:  # 溃疡指数低
                drawdown_risk_score += 0.10
            elif ulcer_index_30 > 0.15:  # 溃疡指数高
                drawdown_risk_score -= 0.15
        
        # 痛苦比率评分（权重15%）
        if not pd.isna(pain_ratio_30):
            if pain_ratio_30 > 1.2:  # 痛苦比率很高
                drawdown_risk_score += 0.15
            elif pain_ratio_30 > 0.8:  # 痛苦比率高
                drawdown_risk_score += 0.10
            elif pain_ratio_30 < 0.3:  # 痛苦比率低
                drawdown_risk_score -= 0.15
        
        # ==================== 风险调整收益评分 ====================
        risk_adjusted_score = 0
        
        # 夏普比率评分（权重35%）- 动态评分标准
        if not pd.isna(sharpe_30):
            if sharpe_30 > 1.0:  # 优秀
                risk_adjusted_score += 0.35
            elif sharpe_30 > 0.5:  # 良好
                risk_adjusted_score += 0.20
            elif sharpe_30 > 0:  # 一般
                risk_adjusted_score += 0.10
            elif sharpe_30 < -0.5:  # 差
                risk_adjusted_score -= 0.20
        
        # 索提诺比率评分（权重25%）- 动态评分标准
        if not pd.isna(sortino_30):
            if sortino_30 > 1.5:  # 优秀
                risk_adjusted_score += 0.25
            elif sortino_30 > 0.8:  # 良好
                risk_adjusted_score += 0.15
            elif sortino_30 > 0:  # 一般
                risk_adjusted_score += 0.08
            elif sortino_30 < -0.5:  # 差
                risk_adjusted_score -= 0.15
        
        # 卡尔马比率评分（权重25%）- 动态评分标准
        if not pd.isna(calmar_30):
            if calmar_30 > 2.0:  # 优秀
                risk_adjusted_score += 0.25
            elif calmar_30 > 1.0:  # 良好
                risk_adjusted_score += 0.15
            elif calmar_30 > 0:  # 一般
                risk_adjusted_score += 0.08
            elif calmar_30 < -0.5:  # 差
                risk_adjusted_score -= 0.15
        
        # ==================== 趋势分析 ====================
        trend_score = 0
        
        # 风险调整收益趋势评分
        trend_score += sharpe_trend * 0.4
        trend_score += sortino_trend * 0.3
        trend_score += calmar_trend * 0.3
        
        # ==================== 波动率调整 ====================
        volatility = features["volatility"].iloc[-1]
        volatility_adjusted_momentum = features["volatility_adjusted_momentum"].iloc[-1]
        
        # 波动率调整因子（高波动时降低信号敏感度）
        volatility_factor = 1.0
        if not pd.isna(volatility):
            if volatility > 0.025:  # 高波动
                volatility_factor = 0.7
            elif volatility > 0.015:  # 中等波动
                volatility_factor = 0.85
            elif volatility < 0.008:  # 低波动
                volatility_factor = 1.2
        
        # ==================== 传统技术指标确认 ====================
        confirmation_score = 0
        
        # RSI确认
        current_rsi = features["rsi"].iloc[-1]
        if not pd.isna(current_rsi):
            if current_rsi > 75:  # 超买
                confirmation_score -= 0.25
            elif current_rsi < 25:  # 超卖
                confirmation_score += 0.25
            elif 35 < current_rsi < 65:  # 中性
                confirmation_score += 0.15
        
        # MACD确认
        macd = features["macd"].iloc[-1]
        macd_signal = features["macd_signal"].iloc[-1]
        if not pd.isna(macd) and not pd.isna(macd_signal):
            if macd > macd_signal:  # 金叉
                confirmation_score += 0.25
            elif macd < macd_signal:  # 死叉
                confirmation_score -= 0.25
        
        # 布林带确认
        bb_position = features["bb_position"].iloc[-1]
        if not pd.isna(bb_position):
            if bb_position > 0.85:  # 接近上轨
                confirmation_score -= 0.15
            elif bb_position < 0.15:  # 接近下轨
                confirmation_score += 0.15
        
        # ==================== 综合评分计算 ====================
        # 最终信号评分
        final_score = (
            risk_adjusted_score * 0.30 +      # 风险调整收益权重30%
            drawdown_risk_score * 0.35 +      # 回撤风险权重35%（更高权重）
            trend_score * 0.20 +              # 趋势权重20%
            confirmation_score * 0.15         # 传统指标确认权重15%
        ) * volatility_factor  # 波动率调整
        
        # ==================== 信号生成 ====================
        # 动态信号阈值（优化阈值设置，提高交易频率）
        avg_sharpe = features["sharpe_ratio_30"].rolling(window=20).mean().iloc[-1]
        current_drawdown = abs(max_drawdown_30) if not pd.isna(max_drawdown_30) else 0
        
        if not pd.isna(avg_sharpe):
            if avg_sharpe > 1.0 and current_drawdown < 0.10:
                threshold = 0.15  # 优化阈值设置
            elif avg_sharpe > 0.5 and current_drawdown < 0.15:
                threshold = 0.20  # 降低阈值
            else:
                threshold = 0.25  # 降低默认阈值
        else:
                            threshold = 0.20  # 优化默认阈值
        
        # 生成交易信号
        if final_score > threshold:
            return 1  # 做多信号
        elif final_score < -threshold:
            return -1  # 做空信号
        else:
            return 0  # 观望信号
    
    @staticmethod
    def get_position_size(features, base_position=1.0):
        """
        基于风险调整收益指标和最大回撤动态调整仓位大小，支持高频交易
        
        Args:
            features: 包含风险调整收益指标的DataFrame
            base_position: 基础仓位大小
            
        Returns:
            float: 调整后的仓位大小
        """
        if len(features) < 30:
            return base_position * 0.5  # 数据不足时降低仓位，从0.3提高到0.5
        
        # 获取最新的风险调整收益指标
        sharpe_30 = features["sharpe_ratio_30"].iloc[-1]
        sortino_30 = features["sortino_ratio_30"].iloc[-1]
        calmar_30 = features["calmar_ratio_30"].iloc[-1]
        
        # 获取最大回撤指标
        max_drawdown_30 = features["max_drawdown_30"].iloc[-1]
        drawdown_duration_30 = features["drawdown_duration_30"].iloc[-1]
        ulcer_index_30 = features["ulcer_index_30"].iloc[-1]
        
        # 计算仓位调整因子
        position_factor = 1.0
        
        # 基于夏普比率调整 - 动态调整
        if not pd.isna(sharpe_30):
            if sharpe_30 > 1.2:
                position_factor *= 1.3  # 优秀时增加仓位
            elif sharpe_30 > 0.8:
                position_factor *= 1.2  # 良好时适度增加
            elif sharpe_30 > 0:
                position_factor *= 1.0  # 一般时保持仓位
            elif sharpe_30 < -0.5:
                position_factor *= 0.7  # 负夏普比率时减少仓位
            elif sharpe_30 < -1.0:
                position_factor *= 0.5  # 很差时大幅减少仓位
        
        # 基于索提诺比率调整 - 修复变量名错误
        if not pd.isna(sortino_30):
            if sortino_30 > 1.8:
                position_factor *= 1.2
            elif sortino_30 > 1.0:
                position_factor *= 1.1
            elif sortino_30 < 0:
                position_factor *= 0.8
        
        # 基于卡尔马比率调整
        if not pd.isna(calmar_30):
            if calmar_30 > 2.5:
                position_factor *= 1.2
            elif calmar_30 > 1.5:
                position_factor *= 1.1
            elif calmar_30 < 0:
                position_factor *= 0.8
        
        # 基于最大回撤调整（动态控制）
        if not pd.isna(max_drawdown_30):
            current_drawdown = abs(max_drawdown_30)
            if current_drawdown < 0.05:  # 回撤小于5%
                position_factor *= 1.3  # 增加仓位
            elif current_drawdown < 0.10:  # 回撤5-10%
                position_factor *= 1.1  # 适度增加仓位
            elif current_drawdown < 0.15:  # 回撤10-15%
                position_factor *= 1.0  # 保持仓位
            elif current_drawdown < 0.20:  # 回撤15-20%
                position_factor *= 0.8  # 减少仓位
            elif current_drawdown < 0.25:  # 回撤20-25%
                position_factor *= 0.6  # 大幅减少仓位
            else:  # 回撤大于25%
                position_factor *= 0.4  # 极大幅度减少仓位
        
        # 基于回撤持续时间调整
        if not pd.isna(drawdown_duration_30):
            if drawdown_duration_30 < 5:  # 回撤持续时间很短
                position_factor *= 1.2
            elif drawdown_duration_30 < 10:  # 回撤持续时间短
                position_factor *= 1.1
            elif drawdown_duration_30 < 15:  # 回撤持续时间中等
                position_factor *= 1.0
            elif drawdown_duration_30 > 20:  # 回撤持续时间长
                position_factor *= 0.8
        
        # 基于溃疡指数调整
        if not pd.isna(ulcer_index_30):
            if ulcer_index_30 < 0.05:  # 溃疡指数很低
                position_factor *= 1.2
            elif ulcer_index_30 < 0.10:  # 溃疡指数低
                position_factor *= 1.1
            elif ulcer_index_30 > 0.15:  # 溃疡指数高
                position_factor *= 0.8
        
        # 动态仓位大小范围限制
        position_factor = max(0.3, min(2.5, position_factor))  # 动态仓位范围0.3-2.5
        
        return base_position * position_factor
    
    @staticmethod
    def get_risk_metrics(features):
        """
        获取当前的风险指标摘要，支持高频交易决策
        
        Args:
            features: 包含风险调整收益指标的DataFrame
            
        Returns:
            dict: 风险指标摘要
        """
        if len(features) < 30:
            return {}
        
        current = features.iloc[-1]
        
        return {
            # 风险调整收益指标
            "sharpe_ratio_30": current.get("sharpe_ratio_30", np.nan),
            "sharpe_ratio_60": current.get("sharpe_ratio_60", np.nan),
            "sortino_ratio_30": current.get("sortino_ratio_30", np.nan),
            "calmar_ratio_30": current.get("calmar_ratio_30", np.nan),
            
            # 最大回撤指标（动态监控）
            "max_drawdown_30": current.get("max_drawdown_30", np.nan),
            "max_drawdown_60": current.get("max_drawdown_60", np.nan),
            "drawdown_duration_30": current.get("drawdown_duration_30", np.nan),
            
            # 其他风险指标
            "volatility": current.get("volatility", np.nan),
            "ulcer_index_30": current.get("ulcer_index_30", np.nan),
            "pain_ratio_30": current.get("pain_ratio_30", np.nan),
            
            # 组合指标
            "risk_adjusted_return": current.get("risk_adjusted_return", np.nan),
            "volatility_adjusted_momentum": current.get("volatility_adjusted_momentum", np.nan),
            "drawdown_risk_score": current.get("drawdown_risk_score", np.nan),
            "recovery_potential": current.get("recovery_potential", np.nan),
            
            # 动态回撤控制状态
            "drawdown_control_status": "active" if abs(current.get("max_drawdown_30", 0)) < 0.25 else "warning"
        }

class EnhancedStableRiskAdjustmentStrategy:
    """
    加强版稳健风险调整策略
    
    策略特点：
    - 基于原稳健风险调整策略的增强版本
    - 主要优化：提高交易频率和交易数量
    - 降低信号阈值，增加交易机会
    - 保持原有的风险控制机制
    - 增加短期信号捕捉能力
    
    核心改进：
    - 降低信号生成阈值，提高交易频率
    - 增加短期技术指标权重
    - 优化仓位管理，提高资金利用率
    - 保持风险控制不变
    """
    
    @staticmethod
    def get_signal(features):
        """
        基于夏普比率的交易信号生成（加强版）
        
        算法流程：
        =========
        1. 风险调整收益分析：计算多个时间框架的夏普比率、索提诺比率、卡尔马比率
        2. 最大回撤分析：分析当前回撤水平和回撤持续时间
        3. 风险收益趋势：分析风险调整收益指标的趋势
        4. 波动率调整：基于当前波动率调整信号敏感度
        5. 传统指标确认：使用RSI、MACD、布林带等传统指标确认信号
        6. 综合评分：加权计算最终交易信号
        7. 动态仓位管理：基于风险调整收益表现调整仓位大小
        
        主要改进：
        - 降低信号阈值，提高交易频率
        - 增加短期指标权重
        - 优化信号确认机制
        
        Args:
            features: 包含技术指标和风险调整收益指标的DataFrame
                    必须包含：close, returns, sharpe_ratio_*, sortino_ratio_*, calmar_ratio_*, max_drawdown_*等列
                    建议数据长度：至少120条记录
            
        Returns:
            int: 交易信号
                1: 做多信号（风险调整收益良好）
                -1: 做空信号（风险调整收益恶化）
                0: 观望信号
        """
        if len(features) < 120:  # 需要足够的历史数据计算风险指标
            return 0
        
        # ==================== 基础数据准备 ====================
        current_close = features["close"].iloc[-1]
        current_returns = features["returns"].iloc[-1]
        
        # ==================== 风险调整收益指标分析 ====================
        # 获取最新的风险调整收益指标
        sharpe_30 = features["sharpe_ratio_30"].iloc[-1]
        sharpe_60 = features["sharpe_ratio_60"].iloc[-1]
        sharpe_120 = features["sharpe_ratio_120"].iloc[-1]
        
        sortino_30 = features["sortino_ratio_30"].iloc[-1]
        sortino_60 = features["sortino_ratio_60"].iloc[-1]
        
        calmar_30 = features["calmar_ratio_30"].iloc[-1]
        calmar_60 = features["calmar_ratio_60"].iloc[-1]
        
        # 最大回撤指标
        max_drawdown_30 = features["max_drawdown_30"].iloc[-1]
        max_drawdown_60 = features["max_drawdown_60"].iloc[-1]
        
        # 回撤持续时间
        drawdown_duration_30 = features["drawdown_duration_30"].iloc[-1]
        drawdown_duration_60 = features["drawdown_duration_60"].iloc[-1]
        
        # 溃疡指数和痛苦比率
        ulcer_index_30 = features["ulcer_index_30"].iloc[-1]
        pain_ratio_30 = features["pain_ratio_30"].iloc[-1]
        
        # 风险调整收益趋势分析
        sharpe_trend = 0
        if not pd.isna(sharpe_30) and not pd.isna(sharpe_60):
            if sharpe_30 > sharpe_60:
                sharpe_trend = 1  # 夏普比率改善
            elif sharpe_30 < sharpe_60:
                sharpe_trend = -1  # 夏普比率恶化
        
        sortino_trend = 0
        if not pd.isna(sortino_30) and not pd.isna(sortino_60):
            if sortino_30 > sortino_60:
                sortino_trend = 1  # 索提诺比率改善
            elif sortino_30 < sortino_60:
                sortino_trend = -1  # 索提诺比率恶化
        
        calmar_trend = 0
        if not pd.isna(calmar_30) and not pd.isna(calmar_60):
            if calmar_30 > calmar_60:
                calmar_trend = 1  # 卡尔马比率改善
            elif calmar_30 < calmar_60:
                calmar_trend = -1  # 卡尔马比率恶化
        
        # ==================== 回撤风险分析 ====================
        drawdown_risk_score = 0
        
        # 最大回撤评分（权重20%，降低权重以提高交易频率）
        if not pd.isna(max_drawdown_30):
            if max_drawdown_30 > -0.05:  # 回撤小于5%
                drawdown_risk_score += 0.20
            elif max_drawdown_30 > -0.10:  # 回撤5-10%
                drawdown_risk_score += 0.10
            elif max_drawdown_30 > -0.15:  # 回撤10-15%
                drawdown_risk_score += 0.05
            elif max_drawdown_30 < -0.25:  # 回撤大于25%（提高阈值）
                drawdown_risk_score -= 0.20
        
        # 回撤持续时间评分（权重10%，降低权重）
        if not pd.isna(drawdown_duration_30):
            if drawdown_duration_30 < 5:  # 回撤持续时间短
                drawdown_risk_score += 0.10
            elif drawdown_duration_30 < 10:  # 回撤持续时间中等
                drawdown_risk_score += 0.05
            elif drawdown_duration_30 > 25:  # 回撤持续时间长（提高阈值）
                drawdown_risk_score -= 0.10
        
        # 溃疡指数评分（权重8%，降低权重）
        if not pd.isna(ulcer_index_30):
            if ulcer_index_30 < 0.05:  # 溃疡指数低
                drawdown_risk_score += 0.08
            elif ulcer_index_30 > 0.20:  # 溃疡指数高（提高阈值）
                drawdown_risk_score -= 0.08
        
        # 痛苦比率评分（权重8%，降低权重）
        if not pd.isna(pain_ratio_30):
            if pain_ratio_30 > 1.0:  # 痛苦比率高
                drawdown_risk_score += 0.08
            elif pain_ratio_30 < 0.3:  # 痛苦比率低（降低阈值）
                drawdown_risk_score -= 0.08
        
        # ==================== 风险调整收益评分 ====================
        risk_adjusted_score = 0
        
        # 夏普比率评分（权重25%，降低权重）
        if not pd.isna(sharpe_30):
            if sharpe_30 > 0.8:  # 优秀（降低阈值）
                risk_adjusted_score += 0.25
            elif sharpe_30 > 0.3:  # 良好（降低阈值）
                risk_adjusted_score += 0.15
            elif sharpe_30 > -0.2:  # 一般（降低阈值）
                risk_adjusted_score += 0.05
            elif sharpe_30 < -0.8:  # 差（降低阈值）
                risk_adjusted_score -= 0.15
        
        # 索提诺比率评分（权重18%，降低权重）
        if not pd.isna(sortino_30):
            if sortino_30 > 1.2:  # 优秀（降低阈值）
                risk_adjusted_score += 0.18
            elif sortino_30 > 0.6:  # 良好（降低阈值）
                risk_adjusted_score += 0.10
            elif sortino_30 > -0.2:  # 一般（降低阈值）
                risk_adjusted_score += 0.05
            elif sortino_30 < -0.8:  # 差（降低阈值）
                risk_adjusted_score -= 0.10
        
        # 卡尔马比率评分（权重18%，降低权重）
        if not pd.isna(calmar_30):
            if calmar_30 > 1.5:  # 优秀（降低阈值）
                risk_adjusted_score += 0.18
            elif calmar_30 > 0.8:  # 良好（降低阈值）
                risk_adjusted_score += 0.10
            elif calmar_30 > -0.2:  # 一般（降低阈值）
                risk_adjusted_score += 0.05
            elif calmar_30 < -1.0:  # 差（降低阈值）
                risk_adjusted_score -= 0.10
        
        # ==================== 趋势分析 ====================
        trend_score = 0
        
        # 风险调整收益趋势评分
        trend_score += sharpe_trend * 0.4
        trend_score += sortino_trend * 0.3
        trend_score += calmar_trend * 0.3
        
        # ==================== 波动率调整 ====================
        volatility = features["volatility"].iloc[-1]
        volatility_adjusted_momentum = features["volatility_adjusted_momentum"].iloc[-1]
        
        # 波动率调整因子（高波动时降低信号敏感度，但幅度减小）
        volatility_factor = 1.0
        if not pd.isna(volatility):
            if volatility > 0.04:  # 高波动（提高阈值）
                volatility_factor = 0.8  # 降低幅度减小
            elif volatility > 0.025:  # 中等波动（提高阈值）
                volatility_factor = 0.9  # 降低幅度减小
            elif volatility < 0.008:  # 低波动（降低阈值）
                volatility_factor = 1.3  # 提高幅度增加
        
        # ==================== 传统技术指标确认（增强版） ====================
        confirmation_score = 0
        
        # RSI确认（增强敏感度）
        current_rsi = features["rsi"].iloc[-1]
        if not pd.isna(current_rsi):
            if current_rsi > 75:  # 超买（提高阈值）
                confirmation_score -= 0.25
            elif current_rsi < 25:  # 超卖（降低阈值）
                confirmation_score += 0.25
            elif 35 < current_rsi < 65:  # 中性（扩大范围）
                confirmation_score += 0.15
            elif 30 < current_rsi < 70:  # 轻微信号
                confirmation_score += 0.05
        
        # MACD确认（增强敏感度）
        macd = features["macd"].iloc[-1]
        macd_signal = features["macd_signal"].iloc[-1]
        macd_histogram = features["macd_histogram"].iloc[-1]
        if not pd.isna(macd) and not pd.isna(macd_signal):
            if macd > macd_signal:  # 金叉
                confirmation_score += 0.25
                # 增加MACD柱状图确认
                if not pd.isna(macd_histogram) and macd_histogram > 0:
                    confirmation_score += 0.05
            elif macd < macd_signal:  # 死叉
                confirmation_score -= 0.25
                # 增加MACD柱状图确认
                if not pd.isna(macd_histogram) and macd_histogram < 0:
                    confirmation_score -= 0.05
        
        # 布林带确认（增强敏感度）
        bb_position = features["bb_position"].iloc[-1]
        bb_width = features["bb_width"].iloc[-1]
        if not pd.isna(bb_position):
            if bb_position > 0.85:  # 接近上轨（提高阈值）
                confirmation_score -= 0.15
            elif bb_position < 0.15:  # 接近下轨（降低阈值）
                confirmation_score += 0.15
            elif 0.3 < bb_position < 0.7:  # 中间区域（扩大范围）
                confirmation_score += 0.10
        
        # 增加KDJ确认
        kdj_k = features["kdj_k"].iloc[-1]
        kdj_d = features["kdj_d"].iloc[-1]
        if not pd.isna(kdj_k) and not pd.isna(kdj_d):
            if kdj_k > kdj_d and kdj_k < 80:  # 金叉且未超买
                confirmation_score += 0.15
            elif kdj_k < kdj_d and kdj_k > 20:  # 死叉且未超卖
                confirmation_score -= 0.15
        
        # 增加ATR确认
        atr = features["atr"].iloc[-1]
        atr_ratio = features["atr_ratio"].iloc[-1]
        if not pd.isna(atr_ratio):
            if atr_ratio > 1.2:  # 波动率增加
                confirmation_score += 0.05
            elif atr_ratio < 0.8:  # 波动率减少
                confirmation_score -= 0.05
        
        # ==================== 综合评分计算（调整权重） ====================
        # 最终信号评分（调整权重分配）
        final_score = (
            risk_adjusted_score * 0.30 +      # 风险调整收益权重30%（降低）
            drawdown_risk_score * 0.20 +      # 回撤风险权重20%（降低）
            trend_score * 0.25 +              # 趋势权重25%（保持不变）
            confirmation_score * 0.25         # 传统指标确认权重25%（提高）
        ) * volatility_factor  # 波动率调整
        
        # ==================== 信号生成（降低阈值） ====================
        # 动态信号阈值（基于历史风险调整收益表现，降低阈值）
        avg_sharpe = features["sharpe_ratio_30"].rolling(window=20).mean().iloc[-1]
        current_drawdown = abs(max_drawdown_30) if not pd.isna(max_drawdown_30) else 0
        
        if not pd.isna(avg_sharpe):
            if avg_sharpe > 0.8 and current_drawdown < 0.12:  # 降低阈值
                threshold = 0.15  # 高夏普比率且低回撤时降低阈值，提高交易频率
            elif avg_sharpe > 0.3 and current_drawdown < 0.18:  # 降低阈值
                threshold = 0.25  # 中等夏普比率且中等回撤时中等阈值
            else:
                threshold = 0.35  # 低夏普比率或高回撤时提高阈值（但仍低于原版）
        else:
            threshold = 0.30  # 默认阈值（降低）
        
        # 生成交易信号
        if final_score > threshold:
            return 1  # 做多信号
        elif final_score < -threshold:
            return -1  # 做空信号
        else:
            return 0  # 观望信号
    
    @staticmethod
    def get_position_size(features, base_position=1.0):
        """
        基于风险调整收益指标和最大回撤动态调整仓位大小（加强版）
        
        主要改进：
        - 提高基础仓位大小
        - 优化仓位调整逻辑
        - 增加资金利用率
        
        Args:
            features: 包含风险调整收益指标的DataFrame
            base_position: 基础仓位大小
            
        Returns:
            float: 调整后的仓位大小
        """
        if len(features) < 30:
            return base_position * 0.6  # 数据不足时降低仓位（提高比例）
        
        # 获取最新的风险调整收益指标
        sharpe_30 = features["sharpe_ratio_30"].iloc[-1]
        sortino_30 = features["sortino_ratio_30"].iloc[-1]
        calmar_30 = features["calmar_ratio_30"].iloc[-1]
        
        # 获取最大回撤指标
        max_drawdown_30 = features["max_drawdown_30"].iloc[-1]
        drawdown_duration_30 = features["drawdown_duration_30"].iloc[-1]
        ulcer_index_30 = features["ulcer_index_30"].iloc[-1]
        
        # 计算仓位调整因子
        position_factor = 1.2  # 提高基础仓位因子
        
        # 基于夏普比率调整（优化阈值）
        if not pd.isna(sharpe_30):
            if sharpe_30 > 1.2:  # 优秀（降低阈值）
                position_factor *= 1.4  # 增加仓位幅度
            elif sharpe_30 > 0.6:  # 良好（降低阈值）
                position_factor *= 1.2  # 适度增加
            elif sharpe_30 < -0.2:  # 差（降低阈值）
                position_factor *= 0.8  # 减少仓位
            elif sharpe_30 < -0.6:  # 很差（降低阈值）
                position_factor *= 0.6  # 大幅减少仓位
        
        # 基于索提诺比率调整（优化阈值）
        if not pd.isna(sortino_30):
            if sortino_30 > 1.8:  # 优秀（降低阈值）
                position_factor *= 1.3
            elif sortino_30 < -0.2:  # 差（降低阈值）
                position_factor *= 0.9
        
        # 基于卡尔马比率调整（优化阈值）
        if not pd.isna(calmar_30):
            if calmar_30 > 2.5:  # 优秀（降低阈值）
                position_factor *= 1.3
            elif calmar_30 < -0.2:  # 差（降低阈值）
                position_factor *= 0.9
        
        # 基于最大回撤调整（优化阈值）
        if not pd.isna(max_drawdown_30):
            current_drawdown = abs(max_drawdown_30)
            if current_drawdown < 0.06:  # 回撤小于6%（降低阈值）
                position_factor *= 1.3  # 增加仓位
            elif current_drawdown < 0.12:  # 回撤6-12%（降低阈值）
                position_factor *= 1.1  # 适度增加仓位
            elif current_drawdown < 0.18:  # 回撤12-18%（降低阈值）
                position_factor *= 0.9  # 减少仓位
            elif current_drawdown < 0.25:  # 回撤18-25%（降低阈值）
                position_factor *= 0.7  # 大幅减少仓位
            else:  # 回撤大于25%
                position_factor *= 0.5  # 极大幅度减少仓位
        
        # 基于回撤持续时间调整（优化阈值）
        if not pd.isna(drawdown_duration_30):
            if drawdown_duration_30 < 6:  # 回撤持续时间短（降低阈值）
                position_factor *= 1.2
            elif drawdown_duration_30 > 18:  # 回撤持续时间长（提高阈值）
                position_factor *= 0.8
        
        # 基于溃疡指数调整（优化阈值）
        if not pd.isna(ulcer_index_30):
            if ulcer_index_30 < 0.06:  # 溃疡指数低（降低阈值）
                position_factor *= 1.2
            elif ulcer_index_30 > 0.18:  # 溃疡指数高（提高阈值）
                position_factor *= 0.8
        
        # 限制仓位大小范围（提高上限）
        position_factor = max(0.3, min(2.5, position_factor))
        
        return base_position * position_factor
    
    @staticmethod
    def get_risk_metrics(features):
        """
        获取当前的风险指标摘要（与原版相同）
        
        Args:
            features: 包含风险调整收益指标的DataFrame
            
        Returns:
            dict: 风险指标摘要
        """
        if len(features) < 30:
            return {}
        
        current = features.iloc[-1]
        
        return {
            # 风险调整收益指标
            "sharpe_ratio_30": current.get("sharpe_ratio_30", np.nan),
            "sharpe_ratio_60": current.get("sharpe_ratio_60", np.nan),
            "sortino_ratio_30": current.get("sortino_ratio_30", np.nan),
            "calmar_ratio_30": current.get("calmar_ratio_30", np.nan),
            
            # 最大回撤指标
            "max_drawdown_30": current.get("max_drawdown_30", np.nan),
            "max_drawdown_60": current.get("max_drawdown_60", np.nan),
            "drawdown_duration_30": current.get("drawdown_duration_30", np.nan),
            
            # 其他风险指标
            "volatility": current.get("volatility", np.nan),
            "ulcer_index_30": current.get("ulcer_index_30", np.nan),
            "pain_ratio_30": current.get("pain_ratio_30", np.nan),
            
            # 组合指标
            "risk_adjusted_return": current.get("risk_adjusted_return", np.nan),
            "volatility_adjusted_momentum": current.get("volatility_adjusted_momentum", np.nan),
            "drawdown_risk_score": current.get("drawdown_risk_score", np.nan),
            "recovery_potential": current.get("recovery_potential", np.nan)
        }
    
    @staticmethod
    def get_risk_status(features):
        """
        获取当前的风险状态和控制建议（与原版相同）
        
        Args:
            features: 包含风险调整收益指标的DataFrame
            
        Returns:
            dict: 风险状态信息
        """
        if len(features) < 30:
            return {
                "risk_level": "unknown",
                "status": "unknown",
                "message": "数据不足，无法评估风险状态",
                "metrics": {},
                "recommendations": ["等待更多数据以进行风险评估"]
            }
        
        # 获取最新的风险指标
        current = features.iloc[-1]
        
        sharpe_30 = current.get("sharpe_ratio_30", np.nan)
        sharpe_60 = current.get("sharpe_ratio_60", np.nan)
        sortino_30 = current.get("sortino_ratio_30", np.nan)
        calmar_30 = current.get("calmar_ratio_30", np.nan)
        
        max_drawdown_30 = current.get("max_drawdown_30", np.nan)
        max_drawdown_60 = current.get("max_drawdown_60", np.nan)
        drawdown_duration_30 = current.get("drawdown_duration_30", np.nan)
        
        volatility = current.get("volatility", np.nan)
        ulcer_index_30 = current.get("ulcer_index_30", np.nan)
        pain_ratio_30 = current.get("pain_ratio_30", np.nan)
        
        # ==================== 风险等级评估 ====================
        risk_score = 0
        risk_factors = []
        
        # 1. 夏普比率风险评分
        if not pd.isna(sharpe_30):
            if sharpe_30 < -0.8:  # 提高阈值
                risk_score += 3
                risk_factors.append(f"夏普比率极低: {sharpe_30:.3f}")
            elif sharpe_30 < -0.2:  # 提高阈值
                risk_score += 2
                risk_factors.append(f"夏普比率为负: {sharpe_30:.3f}")
            elif sharpe_30 < 0.3:  # 提高阈值
                risk_score += 1
                risk_factors.append(f"夏普比率偏低: {sharpe_30:.3f}")
            elif sharpe_30 > 1.2:  # 降低阈值
                risk_score -= 1  # 优秀表现降低风险
        
        # 2. 最大回撤风险评分
        if not pd.isna(max_drawdown_30):
            current_drawdown = abs(max_drawdown_30)
            if current_drawdown > 0.30:  # 提高阈值
                risk_score += 4
                risk_factors.append(f"最大回撤极高: {current_drawdown:.1%}")
            elif current_drawdown > 0.25:  # 提高阈值
                risk_score += 3
                risk_factors.append(f"最大回撤很高: {current_drawdown:.1%}")
            elif current_drawdown > 0.20:  # 提高阈值
                risk_score += 2
                risk_factors.append(f"最大回撤较高: {current_drawdown:.1%}")
            elif current_drawdown > 0.15:  # 提高阈值
                risk_score += 1
                risk_factors.append(f"最大回撤中等: {current_drawdown:.1%}")
            elif current_drawdown < 0.06:  # 降低阈值
                risk_score -= 1  # 低回撤降低风险
        
        # 3. 回撤持续时间风险评分
        if not pd.isna(drawdown_duration_30):
            if drawdown_duration_30 > 25:  # 提高阈值
                risk_score += 2
                risk_factors.append(f"回撤持续时间长: {drawdown_duration_30}天")
            elif drawdown_duration_30 > 20:  # 提高阈值
                risk_score += 1
                risk_factors.append(f"回撤持续时间较长: {drawdown_duration_30}天")
        
        # 4. 波动率风险评分
        if not pd.isna(volatility):
            if volatility > 0.05:  # 提高阈值
                risk_score += 2
                risk_factors.append(f"波动率极高: {volatility:.1%}")
            elif volatility > 0.04:  # 提高阈值
                risk_score += 1
                risk_factors.append(f"波动率较高: {volatility:.1%}")
        
        # 5. 溃疡指数风险评分
        if not pd.isna(ulcer_index_30):
            if ulcer_index_30 > 0.25:  # 提高阈值
                risk_score += 2
                risk_factors.append(f"溃疡指数极高: {ulcer_index_30:.3f}")
            elif ulcer_index_30 > 0.20:  # 提高阈值
                risk_score += 1
                risk_factors.append(f"溃疡指数较高: {ulcer_index_30:.3f}")
        
        # 6. 索提诺比率风险评分
        if not pd.isna(sortino_30):
            if sortino_30 < -0.8:  # 提高阈值
                risk_score += 2
                risk_factors.append(f"索提诺比率极低: {sortino_30:.3f}")
            elif sortino_30 < -0.2:  # 提高阈值
                risk_score += 1
                risk_factors.append(f"索提诺比率为负: {sortino_30:.3f}")
        
        # 7. 卡尔马比率风险评分
        if not pd.isna(calmar_30):
            if calmar_30 < -1.5:  # 提高阈值
                risk_score += 2
                risk_factors.append(f"卡尔马比率极低: {calmar_30:.3f}")
            elif calmar_30 < -0.2:  # 提高阈值
                risk_score += 1
                risk_factors.append(f"卡尔马比率为负: {calmar_30:.3f}")
        
        # ==================== 风险等级确定 ====================
        if risk_score >= 10:  # 提高阈值
            risk_level = "critical"
            status = "danger"
        elif risk_score >= 6:  # 提高阈值
            risk_level = "high"
            status = "warning"
        elif risk_score >= 3:  # 提高阈值
            risk_level = "medium"
            status = "warning"
        else:
            risk_level = "low"
            status = "safe"
        
        # ==================== 风险状态描述 ====================
        if risk_level == "critical":
            message = f"⚠️ 风险等级：严重 - 当前存在多个高风险因素，建议立即采取风险控制措施"
        elif risk_level == "high":
            message = f"⚠️ 风险等级：高 - 需要密切关注风险指标，建议减少仓位或暂停交易"
        elif risk_level == "medium":
            message = f"⚠️ 风险等级：中等 - 风险指标显示需要谨慎操作，建议降低仓位"
        else:
            message = f"✅ 风险等级：低 - 当前风险指标良好，可以正常交易"
        
        if risk_factors:
            message += f"\n主要风险因素：{', '.join(risk_factors)}"
        
        # ==================== 风险控制建议 ====================
        recommendations = []
        
        if risk_level == "critical":
            recommendations.extend([
                "立即平仓所有高风险仓位",
                "暂停新开仓操作",
                "检查策略参数设置",
                "考虑降低杠杆倍数",
                "增加止损保护"
            ])
        elif risk_level == "high":
            recommendations.extend([
                "减少仓位至50%以下",
                "提高止损保护级别",
                "避免开新仓",
                "密切关注市场变化",
                "考虑部分止盈"
            ])
        elif risk_level == "medium":
            recommendations.extend([
                "降低仓位至70%以下",
                "收紧止损设置",
                "谨慎开新仓",
                "加强风险监控",
                "准备应急方案"
            ])
        else:
            recommendations.extend([
                "可以正常交易",
                "保持当前仓位",
                "继续监控风险指标",
                "维持现有止损设置"
            ])
        
        # ==================== 关键风险指标 ====================
        metrics = {
            "risk_score": risk_score,
            "sharpe_ratio_30": sharpe_30,
            "max_drawdown_30": max_drawdown_30,
            "volatility": volatility,
            "drawdown_duration_30": drawdown_duration_30,
            "ulcer_index_30": ulcer_index_30,
            "sortino_ratio_30": sortino_30,
            "calmar_ratio_30": calmar_30
        }
        
        return {
            "risk_level": risk_level,
            "status": status,
            "message": message,
            "metrics": metrics,
            "recommendations": recommendations,
            "risk_factors": risk_factors
        }



