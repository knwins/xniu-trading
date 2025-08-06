# -*- coding: utf-8 -*-
# data_loader.py
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import time
import random
load_dotenv()  # 加载环境变量

class DataLoader:
    def __init__(self, timeframe="1h"):
        self.symbol = os.getenv("SYMBOL", "BTCUSDT")
        self.timeframe = timeframe
        
        # 支持的时间级别映射
        self.timeframe_mapping = {
            "MIN15": "15m",
            "MIN30": "30m", 
            "HOUR1": "1h",
            "HOUR2": "2h",
            "HOUR4": "4h"
        }
        
        # 多个API端点，提高可用性
        self.api_endpoints = [
            "https://api.binance.com/api/v3",
            "https://api1.binance.com/api/v3",
            "https://api2.binance.com/api/v3",
            "https://api3.binance.com/api/v3"
        ]
        self.current_endpoint = 0
        
        # 测试连接
        self.use_mock_data = self._test_connection()
    
    def _test_connection(self):
        """测试API连接，返回是否使用模拟数据"""
        for i in range(len(self.api_endpoints)):
            try:
                endpoint = self.api_endpoints[i]
                response = requests.get(f"{endpoint}/time", timeout=5)
                if response.status_code == 200:
                    self.current_endpoint = i
                    print(f"✓ 成功连接到Binance API: {endpoint}")
                    return False
                else:
                    print(f"⚠ API端点 {endpoint} 响应异常: {response.status_code}")
            except Exception as e:
                print(f"⚠ API端点 {endpoint} 连接失败: {e}")
        
        print(f"⚠ 所有API端点连接失败，使用模拟数据")
        return True
    
    def _make_request(self, url, params=None, max_retries=3):
        """发送HTTP请求，带重试机制"""
        for attempt in range(max_retries):
            try:
                # 随机选择API端点，提高成功率
                endpoint = self.api_endpoints[self.current_endpoint]
                full_url = f"{endpoint}{url}"
                
                # 添加随机延迟，避免请求过于频繁
                time.sleep(random.uniform(0.1, 0.5))
                
                response = requests.get(full_url, params=params, timeout=15)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # 请求频率限制
                    print(f"⚠ 请求频率限制，等待后重试...")
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    print(f"⚠ API响应异常: {response.status_code}")
                    # 尝试切换到下一个API端点
                    self.current_endpoint = (self.current_endpoint + 1) % len(self.api_endpoints)
                    
            except requests.exceptions.RequestException as e:
                print(f"⚠ 请求异常 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                    # 尝试切换到下一个API端点
                    self.current_endpoint = (self.current_endpoint + 1) % len(self.api_endpoints)
                else:
                    raise e
        
        return None
    
    def generate_mock_data(self, start_date, end_date):
        """生成模拟的 K 线数据"""
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # 根据时间框架确定时间间隔
        if self.timeframe == "15m":
            freq = "15min"
        elif self.timeframe == "30m":
            freq = "30min"
        elif self.timeframe == "1h":
            freq = "1h"
        elif self.timeframe == "2h":
            freq = "2h"
        elif self.timeframe == "4h":
            freq = "4h"
        else:
            freq = "1h"  # 默认1小时
        
        # 生成时间序列
        date_range = pd.date_range(start=start_dt, end=end_dt, freq=freq)
        
        # 生成模拟价格数据
        np.random.seed(42)  # 固定随机种子，确保结果可重现
        base_price = 3000  # 基础价格
        price_changes = np.random.normal(0, 0.02, len(date_range))  # 价格变化
        
        prices = [base_price]
        for change in price_changes[1:]:
            new_price = prices[-1] * (1 + change)
            prices.append(new_price)
        
        # 生成 OHLCV 数据
        mock_data = []
        for i, (timestamp, price) in enumerate(zip(date_range, prices)):
            # 生成开盘价、最高价、最低价、收盘价
            open_price = price
            close_price = price * (1 + np.random.normal(0, 0.01))
            high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.005)))
            low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.005)))
            volume = np.random.uniform(1000, 10000)
            
            mock_data.append([
                int(timestamp.timestamp() * 1000),  # 时间戳（毫秒）
                open_price,
                high_price,
                low_price,
                close_price,
                volume
            ])
        
        return mock_data
    
    def get_klines(self, start_date, end_date):
        """获取指定时间范围的 K 线数据（开盘价、收盘价等）"""
        
        # 如果使用模拟数据或连接失败，生成模拟数据
        if self.use_mock_data:
            print("📊 使用模拟数据")
            klines = self.generate_mock_data(start_date, end_date)
        else:
            try:
                print("📊 尝试获取真实数据...")
                
                # 转换日期为时间戳
                start_timestamp = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp() * 1000)
                end_timestamp = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp() * 1000)
                
                # 分页获取完整数据
                all_klines = []
                current_start = start_timestamp
                page_count = 0
                
                while current_start < end_timestamp and page_count < 50:  # 限制最大页数
                    try:
                        params = {
                            "symbol": self.symbol,
                            "interval": self.timeframe,
                            "startTime": current_start,
                            "endTime": end_timestamp,
                            "limit": 1000  # Binance API最大限制
                        }
                    
                        print(f"  📡 正在获取第 {page_count + 1} 页数据...")
                        klines_data = self._make_request("/klines", params)
                        
                        if klines_data is None:
                            print("⚠ 获取真实数据失败，切换到模拟数据")
                            break
                        
                        if not klines_data:  # 没有更多数据
                            print("  ✅ 数据获取完成")
                            break
                            
                        # 转换为标准格式并添加到总列表
                        for kline in klines_data:
                            all_klines.append([
                                int(kline[0]),  # 时间戳
                                float(kline[1]),  # open
                                float(kline[2]),  # high
                                float(kline[3]),  # low
                                float(kline[4]),  # close
                                float(kline[5])   # volume
                            ])
                        
                        # 更新下一次请求的开始时间
                        if klines_data:
                            current_start = int(klines_data[-1][0]) + 1
                        else:
                            break
                        
                        page_count += 1
                        print(f"  ✅ 已获取 {len(all_klines)} 条数据...")
                        
                        # 添加短暂延迟避免API限制
                        time.sleep(0.1)
                        
                    except KeyboardInterrupt:
                        print("\n⚠ 用户中断数据获取，使用已获取的数据继续...")
                        break
                    except Exception as e:
                        print(f"⚠ 获取第 {page_count + 1} 页数据失败: {e}")
                        break
                
                if all_klines:
                    print(f"📊 成功获取 {len(all_klines)} 条真实数据")
                    klines = all_klines
                else:
                    print("⚠ 未获取到真实数据，使用模拟数据")
                    klines = self.generate_mock_data(start_date, end_date)
                
            except Exception as e:
                print(f"⚠ 获取真实数据失败，使用模拟数据: {e}")
                klines = self.generate_mock_data(start_date, end_date)
        
        # 转换为 DataFrame 并格式化
        df = pd.DataFrame(
            klines,
            columns=["timestamp", "open", "high", "low", "close", "volume"]
        )
        df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")  # 时间戳转日期
        df = df.set_index("datetime").drop(columns=["timestamp"])
        return df.astype(float)  # 确保数值类型正确