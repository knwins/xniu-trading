#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实盘交易系统
基于回测表现最佳的保守回撤控制策略
"""

import time
import json
import logging
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import threading
from typing import Dict, List, Optional, Tuple
import requests
import hmac
import hashlib
import urllib.parse
from decimal import Decimal, ROUND_DOWN, ROUND_UP, ROUND_HALF_UP

# 添加父目录到Python路径，以便导入根目录中的模块
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入现有模块
from data_loader import DataLoader
from feature_engineer import FeatureEngineer
from strategy import ConservativeDrawdownControlStrategy
from backtester import Backtester

# 配置日志
import os
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'trading.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Trader:
    """
    实盘交易系统
    
    功能特点：
    - 实时数据获取和处理
    - 智能信号生成
    - 风险管理控制
    - 自动交易执行
    - 资金管理
    - 实时监控和报告
    """
    
    def __init__(self, config: Dict):
        """
        初始化实盘交易系统
        
        Args:
            config: 配置字典，包含API密钥、交易参数等
        """
        self.config = config
        self.api_key = config.get('api_key')
        self.secret_key = config.get('secret_key')
        self.base_url = config.get('base_url', 'https://fapi.binance.com')
        self.symbol = config.get('symbol', 'ETHUSDT')
        self.initial_balance = config.get('initial_balance', 1000)
        self.max_position_size = config.get('max_position_size', 0.1)  # 最大仓位比例
        self.stop_loss_pct = config.get('stop_loss_pct', 0.05)  # 止损比例
        self.take_profit_pct = config.get('take_profit_pct', 0.1)  # 止盈比例
        
        # 精度设置 - 动态获取
        self.quantity_precision = None  # 将在API连接后动态设置
        self.price_precision = None     # 将在API连接后动态设置
        self.min_quantity = None        # 将在API连接后动态设置
        
        # 初始化组件
        self.data_loader = DataLoader()
        self.feature_engineer = FeatureEngineer()
        self.strategy = ConservativeDrawdownControlStrategy()
        
        # 交易状态
        self.current_position = 0  # 当前仓位 (1=多仓, -1=空仓, 0=空仓)
        self.position_size = 0  # 仓位大小
        self.entry_price = 0  # 开仓价格
        self.current_balance = self.initial_balance
        self.total_pnl = 0
        self.trade_count = 0
        self.win_count = 0
        
        # 风险控制
        self.max_daily_loss = config.get('max_daily_loss', 0.1)  # 最大日亏损
        self.max_drawdown = config.get('max_drawdown', 0.2)  # 最大回撤
        
        # 信号冷却时间
        self.signal_cooldown = config.get('signal_cooldown', 300)  # 信号冷却时间（秒）
        self.last_signal_time = None  # 上次信号时间
        self.daily_pnl = 0
        self.peak_balance = self.initial_balance
        
        # 交易记录
        self.trade_history = []
        self.signal_history = []
        
        # 线程控制
        self.running = False  # 运行状态
        self._sync_counter = 0  # 同步计数器
        self.stop_event = threading.Event()
        
        # 初始化API连接
        if not self.test_api_connection():
            logger.error("API连接测试失败")
            raise Exception("无法连接到币安API")
        
        # 动态设置精度
        logger.info("正在获取交易对精度信息...")
        self.quantity_precision = self._get_quantity_precision()
        self.price_precision = self._get_price_precision()
        self.min_quantity = self._get_min_quantity()
        
        logger.info(f"精度设置完成 - 数量精度: {self.quantity_precision}, 价格精度: {self.price_precision}, 最小数量: {self.min_quantity}")
        logger.info("实盘交易系统初始化完成")
    
    def _get_quantity_precision(self) -> int:
        """获取数量精度 - 通过读取Binance交易对信息动态设置"""
        try:
            # 获取交易对信息
            endpoint = '/fapi/v1/exchangeInfo'
            response = self._make_request('GET', endpoint)
            
            if response and 'symbols' in response:
                for symbol_info in response['symbols']:
                    if symbol_info['symbol'] == self.symbol:
                        # 优先使用LOT_SIZE过滤器的stepSize计算精度
                        for filter_info in symbol_info['filters']:
                            if filter_info['filterType'] == 'LOT_SIZE':
                                step_size = float(filter_info['stepSize'])
                                precision = self._calculate_precision_from_step_size(step_size)
                                logger.info(f"动态设置 {self.symbol} 数量精度: {precision} (stepSize: {step_size})")
                                return precision
                        
                        # 如果没有LOT_SIZE过滤器，使用baseAssetPrecision
                        if 'baseAssetPrecision' in symbol_info:
                            precision = symbol_info['baseAssetPrecision']
                            logger.info(f"动态设置 {self.symbol} 数量精度: {precision} (baseAssetPrecision)")
                            return precision
                        
                        # 如果都没找到，使用默认值
                        logger.warning(f"未找到 {self.symbol} 的数量精度信息，使用默认精度")
                        return 3
                
                logger.warning(f"未找到交易对 {self.symbol} 的信息，使用默认精度")
                return 3
            else:
                logger.warning("无法获取交易对信息，使用默认精度")
                return 3
                
        except Exception as e:
            logger.error(f"获取数量精度异常: {e}，使用默认精度")
            return 3
    
    def _get_price_precision(self) -> int:
        """获取价格精度 - 通过读取Binance交易对信息动态设置"""
        try:
            # 获取交易对信息
            endpoint = '/fapi/v1/exchangeInfo'
            response = self._make_request('GET', endpoint)
            
            if response and 'symbols' in response:
                for symbol_info in response['symbols']:
                    if symbol_info['symbol'] == self.symbol:
                        # 优先使用PRICE_FILTER过滤器的tickSize计算精度
                        for filter_info in symbol_info['filters']:
                            if filter_info['filterType'] == 'PRICE_FILTER':
                                tick_size = float(filter_info['tickSize'])
                                precision = self._calculate_precision_from_step_size(tick_size)
                                logger.info(f"动态设置 {self.symbol} 价格精度: {precision} (tickSize: {tick_size})")
                                return precision
                        
                        # 如果没有PRICE_FILTER过滤器，使用quotePrecision
                        if 'quotePrecision' in symbol_info:
                            precision = symbol_info['quotePrecision']
                            logger.info(f"动态设置 {self.symbol} 价格精度: {precision} (quotePrecision)")
                            return precision
                        
                        # 如果都没找到，使用默认值
                        logger.warning(f"未找到 {self.symbol} 的价格精度信息，使用默认精度")
                        return 2
                
                logger.warning(f"未找到交易对 {self.symbol} 的信息，使用默认精度")
                return 2
            else:
                logger.warning("无法获取交易对信息，使用默认精度")
                return 2
                
        except Exception as e:
            logger.error(f"获取价格精度异常: {e}，使用默认精度")
            return 2
    
    def _calculate_precision_from_step_size(self, step_size: float) -> int:
        """根据stepSize计算精度位数"""
        if step_size <= 0:
            return 0
        
        # 处理科学计数法
        if 'e' in str(step_size).lower():
            # 科学计数法，如1e-05
            step_str = str(step_size).lower()
            if 'e-' in step_str:
                # 提取指数部分
                exponent = int(step_str.split('e-')[1])
                return exponent
            else:
                return 0
        
        # 将stepSize转换为字符串，计算小数位数
        step_str = str(step_size)
        if '.' in step_str:
            # 去掉末尾的0
            step_str = step_str.rstrip('0')
            precision = len(step_str.split('.')[1])
        else:
            precision = 0
        
        return precision
    
    def _get_min_quantity(self) -> float:
        """获取最小交易数量 - 通过读取Binance交易对信息动态设置"""
        try:
            # 获取交易对信息
            endpoint = '/fapi/v1/exchangeInfo'
            response = self._make_request('GET', endpoint)
            
            if response and 'symbols' in response:
                for symbol_info in response['symbols']:
                    if symbol_info['symbol'] == self.symbol:
                        # 找到对应的交易对
                        for filter_info in symbol_info['filters']:
                            if filter_info['filterType'] == 'LOT_SIZE':
                                # 获取最小数量
                                min_qty = float(filter_info['minQty'])
                                logger.info(f"动态设置 {self.symbol} 最小数量: {min_qty}")
                                return min_qty
                        
                        # 如果没找到LOT_SIZE过滤器，使用默认值
                        logger.warning(f"未找到 {self.symbol} 的LOT_SIZE过滤器，使用默认最小数量")
                        return 0.001
                
                logger.warning(f"未找到交易对 {self.symbol} 的信息，使用默认最小数量")
                return 0.001
            else:
                logger.warning("无法获取交易对信息，使用默认最小数量")
                return 0.001
                
        except Exception as e:
            logger.error(f"获取最小数量异常: {e}，使用默认最小数量")
            return 0.001
    
    def _round_quantity(self, quantity: float, rounding_mode: str = 'DOWN') -> float:
        """
        根据交易所精度要求舍入数量
        
        Args:
            quantity: 原始数量
            rounding_mode: 舍入模式 ('DOWN', 'UP', 'NEAREST')
        
        Returns:
            舍入后的数量
        """
        if quantity <= 0:
            return 0.0
        
        # 确保精度已设置
        if self.quantity_precision is None:
            self.quantity_precision = self._get_quantity_precision()
        
        # 使用Decimal进行精确舍入
        decimal_quantity = Decimal(str(quantity))
        
        # 动态创建舍入格式
        if self.quantity_precision == 0:
            rounding_format = Decimal('1')
        else:
            # 创建对应精度的舍入格式
            format_str = '0.' + '0' * self.quantity_precision
            rounding_format = Decimal(format_str)
        
        # 根据模式选择舍入方式
        if rounding_mode == 'UP':
            rounded_quantity = decimal_quantity.quantize(rounding_format, rounding=ROUND_UP)
        elif rounding_mode == 'NEAREST':
            rounded_quantity = decimal_quantity.quantize(rounding_format, rounding=ROUND_HALF_UP)
        else:  # DOWN
            rounded_quantity = decimal_quantity.quantize(rounding_format, rounding=ROUND_DOWN)
        
        # 确保数量不为0
        if rounded_quantity <= 0:
            return 0.0
            
        return float(rounded_quantity)
    
    def _round_price(self, price: float, rounding_mode: str = 'NEAREST') -> float:
        """
        根据交易所精度要求舍入价格
        
        Args:
            price: 原始价格
            rounding_mode: 舍入模式 ('DOWN', 'UP', 'NEAREST')
        
        Returns:
            舍入后的价格
        """
        if price <= 0:
            return 0.0
        
        # 确保精度已设置
        if self.price_precision is None:
            self.price_precision = self._get_price_precision()
        
        # 使用Decimal进行精确舍入
        decimal_price = Decimal(str(price))
        
        # 动态创建舍入格式
        if self.price_precision == 0:
            rounding_format = Decimal('1')
        else:
            # 创建对应精度的舍入格式
            format_str = '0.' + '0' * self.price_precision
            rounding_format = Decimal(format_str)
        
        # 根据模式选择舍入方式
        if rounding_mode == 'UP':
            rounded_price = decimal_price.quantize(rounding_format, rounding=ROUND_UP)
        elif rounding_mode == 'DOWN':
            rounded_price = decimal_price.quantize(rounding_format, rounding=ROUND_DOWN)
        else:  # NEAREST
            rounded_price = decimal_price.quantize(rounding_format, rounding=ROUND_HALF_UP)
        
        return float(rounded_price)
    
    def refresh_precision_info(self) -> bool:
        """
        动态刷新交易对精度信息
        
        Returns:
            是否刷新成功
        """
        try:
            logger.info("正在刷新交易对精度信息...")
            
            # 重新获取精度信息
            old_qty_precision = self.quantity_precision
            old_price_precision = self.price_precision
            old_min_qty = self.min_quantity
            
            self.quantity_precision = self._get_quantity_precision()
            self.price_precision = self._get_price_precision()
            self.min_quantity = self._get_min_quantity()
            
            # 检查是否有变化
            if (old_qty_precision != self.quantity_precision or 
                old_price_precision != self.price_precision or 
                old_min_qty != self.min_quantity):
                
                logger.info(f"精度信息已更新:")
                logger.info(f"  数量精度: {old_qty_precision} -> {self.quantity_precision}")
                logger.info(f"  价格精度: {old_price_precision} -> {self.price_precision}")
                logger.info(f"  最小数量: {old_min_qty} -> {self.min_quantity}")
                return True
            else:
                logger.info("精度信息无变化")
                return True
                
        except Exception as e:
            logger.error(f"刷新精度信息失败: {e}")
            return False
    
    def _validate_quantity(self, quantity: float) -> bool:
        """验证数量是否符合交易所要求"""
        if quantity <= 0:
            return False
        
        # 使用已缓存的最小数量
        if self.min_quantity is None:
            self.min_quantity = self._get_min_quantity()
        
        if quantity < self.min_quantity:
            logger.warning(f"数量 {quantity} 小于最小数量 {self.min_quantity}")
            return False
        
        return True
    
    def _get_server_time(self) -> int:
        """获取服务器时间戳"""
        try:
            url = f"{self.base_url}/fapi/v1/time"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'serverTime' in data:
                    return data['serverTime']
            
            # 如果获取服务器时间失败，使用本地时间
            logger.warning("获取服务器时间失败，使用本地时间")
            return int(time.time() * 1000)
        except Exception as e:
            logger.warning(f"获取服务器时间异常: {e}，使用本地时间")
            return int(time.time() * 1000)
    
    def _generate_signature(self, params: Dict) -> str:
        """生成API签名"""
        query_string = urllib.parse.urlencode(params)
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, signed: bool = False) -> Dict:
        """发送API请求"""
        url = f"{self.base_url}{endpoint}"
        headers = {
            'X-MBX-APIKEY': self.api_key
        }
        
        if params is None:
            params = {}
        
        if signed:
            # 使用服务器时间戳避免时间同步问题
            server_time = self._get_server_time()
            params['timestamp'] = server_time
            params['signature'] = self._generate_signature(params)
        
        try:
            if method == 'GET':
                response = requests.get(url, params=params, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, params=params, headers=headers, timeout=10)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            # 检查HTTP状态码
            if response.status_code != 200:
                error_msg = f"HTTP错误 {response.status_code}"
                try:
                    error_data = response.json()
                    if 'msg' in error_data:
                        error_msg += f": {error_data['msg']}"
                except:
                    error_msg += f": {response.text}"
                
                logger.error(f"API请求失败: {error_msg}")
                raise requests.exceptions.HTTPError(error_msg)
            
            # 解析响应
            try:
                data = response.json()
                return data
            except json.JSONDecodeError as e:
                logger.error(f"响应解析失败: {e}")
                return None
        
        except requests.exceptions.Timeout:
            logger.error("API请求超时")
            raise
        except requests.exceptions.ConnectionError:
            logger.error("API连接失败")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求异常: {e}")
            raise
        except Exception as e:
            logger.error(f"未知错误: {e}")
            raise
    
    def get_account_info(self) -> Dict:
        """获取账户信息"""
        try:
            endpoint = '/fapi/v2/account'
            response = self._make_request('GET', endpoint, signed=True)
            
            if response:
                # 提取关键账户信息
                account_info = {
                    'totalWalletBalance': response.get('totalWalletBalance', '0'),
                    'availableBalance': response.get('availableBalance', '0'),
                    'totalUnrealizedProfit': response.get('totalUnrealizedProfit', '0'),
                    'totalMarginBalance': response.get('totalMarginBalance', '0'),
                    'totalInitialMargin': response.get('totalInitialMargin', '0'),
                    'totalMaintMargin': response.get('totalMaintMargin', '0'),
                    'totalPositionInitialMargin': response.get('totalPositionInitialMargin', '0'),
                    'totalOpenOrderInitialMargin': response.get('totalOpenOrderInitialMargin', '0'),
                    'totalCrossWalletBalance': response.get('totalCrossWalletBalance', '0'),
                    'totalCrossUnPnl': response.get('totalCrossUnPnl', '0'),
                    'availableBalance': response.get('availableBalance', '0'),
                    'maxWithdrawAmount': response.get('maxWithdrawAmount', '0'),
                    'updateTime': response.get('updateTime', 0)
                }
                
                # 更新当前余额
                try:
                    self.current_balance = float(account_info['availableBalance'])
                except (ValueError, KeyError):
                    self.current_balance = self.initial_balance
                
                logger.info(f"账户余额更新: {self.current_balance:.2f} USDT")
                return account_info
            else:
                logger.error("获取账户信息失败")
                return None
                
        except Exception as e:
            logger.error(f"获取账户信息异常: {e}")
            return None
    
    def test_api_connection(self) -> bool:
        """测试API连接和验证API密钥"""
        try:
            # 1. 测试服务器连接
            print("🔍 测试服务器连接...")
            response = requests.get(f"{self.base_url}/fapi/v1/time", timeout=10)
            if response.status_code != 200:
                logger.error(f"服务器连接失败: {response.status_code}")
                return False
            print("✅ 服务器连接成功")
            
            # 2. 测试API密钥有效性（通过获取账户信息）
            print("🔍 验证API密钥...")
            try:
                account_info = self.get_account_info()
                if account_info:
                    print("✅ API密钥验证成功")
                    logger.info("API连接和密钥验证成功")
                    
                    # 3. 检查持仓模式
                    print("🔍 检查持仓模式...")
                    if self.check_and_fix_position_mode():
                        print("✅ 持仓模式检查通过")
                        return True
                    else:
                        print("❌ 持仓模式检查失败")
                        return False
                else:
                    print("❌ API密钥验证失败")
                    logger.error("API密钥验证失败")
                    return False
            except Exception as e:
                if "Invalid API-key" in str(e) or "Invalid signature" in str(e):
                    print("❌ API密钥无效或签名错误")
                    logger.error("API密钥无效或签名错误")
                else:
                    print(f"❌ API密钥验证异常: {e}")
                    logger.error(f"API密钥验证异常: {e}")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ 连接超时，请检查网络")
            logger.error("API连接超时")
            return False
        except requests.exceptions.ConnectionError:
            print("❌ 网络连接失败，请检查网络设置")
            logger.error("API网络连接失败")
            return False
        except Exception as e:
            print(f"❌ API连接测试异常: {e}")
            logger.error(f"API连接测试异常: {e}")
            return False
    
    def get_current_price(self) -> float:
        """获取当前价格"""
        try:
            endpoint = '/fapi/v2/ticker/price'  # 使用合约API端点
            params = {'symbol': self.symbol}
            response = self._make_request('GET', endpoint, params)
            
            if response and 'price' in response:
                price = float(response['price'])
                # 应用价格精度处理
                return self._round_price(price)
            else:
                logger.error("获取当前价格失败")
                return 0.0
        except Exception as e:
            logger.error(f"获取当前价格异常: {e}")
            return 0.0
    
    def get_position_info(self) -> Dict:
        """获取当前持仓信息"""
        try:
            endpoint = '/fapi/v2/positionRisk'
            params = {'symbol': self.symbol}
            response = self._make_request('GET', endpoint, params, signed=True)
            
            if response and isinstance(response, list):
                for position in response:
                    if position['symbol'] == self.symbol:
                        return {
                            'size': float(position['positionAmt']),
                            'entry_price': float(position['entryPrice']),
                            'unrealized_pnl': float(position['unRealizedProfit']),
                            'side': 'LONG' if float(position['positionAmt']) > 0 else 'SHORT' if float(position['positionAmt']) < 0 else 'NONE'
                        }
            
            return {'size': 0, 'entry_price': 0, 'unrealized_pnl': 0, 'side': 'NONE'}
        except Exception as e:
            logger.error(f"获取持仓信息异常: {e}")
            return {'size': 0, 'entry_price': 0, 'unrealized_pnl': 0, 'side': 'NONE'}
    
    def get_position_mode(self) -> str:
        """获取当前持仓模式"""
        try:
            endpoint = '/fapi/v1/positionSide/dual'
            response = self._make_request('GET', endpoint, params={}, signed=True)
            
            if response and 'dualSidePosition' in response:
                return 'HEDGE' if response['dualSidePosition'] else 'ONE_WAY'
            else:
                logger.warning("无法获取持仓模式信息，默认使用单向模式")
                return 'ONE_WAY'
        except Exception as e:
            logger.error(f"获取持仓模式异常: {e}")
            return 'ONE_WAY'
    
    def set_position_mode(self, mode: str) -> bool:
        """设置持仓模式"""
        try:
            endpoint = '/fapi/v1/positionSide/dual'
            params = {'dualSidePosition': mode == 'HEDGE'}
            response = self._make_request('POST', endpoint, params, signed=True)
            
            if response and response.get('code') == 200:
                logger.info(f"持仓模式设置成功: {mode}")
                return True
            else:
                logger.error(f"持仓模式设置失败: {response}")
                return False
        except Exception as e:
            logger.error(f"设置持仓模式异常: {e}")
            return False
    
    def check_and_fix_position_mode(self) -> bool:
        """检查并修复持仓模式"""
        try:
            current_mode = self.get_position_mode()
            logger.info(f"当前持仓模式: {current_mode}")
            
            if current_mode == 'HEDGE':
                print("\n⚠️  检测到对冲模式 (Hedge Mode)")
                print("本交易系统仅支持单向持仓模式 (One-way Mode)")
                print("对冲模式可能导致持仓冲突和交易错误")
                
                # 获取所有持仓信息
                all_positions = self.get_all_positions()
                if all_positions:
                    print("\n📊 当前持仓情况:")
                    for pos in all_positions:
                        if abs(float(pos['positionAmt'])) > 0:
                            side = "多仓" if float(pos['positionAmt']) > 0 else "空仓"
                            print(f"   {pos['symbol']}: {side} {abs(float(pos['positionAmt']))}")
                
                # 询问用户是否修改为单向模式
                while True:
                    confirm = input("\n是否修改为单向模式并平仓所有持仓? (y/N): ").strip().lower()
                    if confirm in ['y', 'yes', '是']:
                        print("🔄 正在修改为单向模式...")
                        
                        # 1. 平仓所有持仓
                        print("📊 正在平仓所有持仓...")
                        if self.close_all_positions():
                            print("✅ 所有持仓已平仓")
                        else:
                            print("⚠️  部分持仓平仓失败")
                            print("请检查以下可能的原因:")
                            print("1. 持仓数量过小，低于最小交易数量")
                            print("2. 账户余额不足")
                            print("3. 网络连接问题")
                            print("4. API权限不足")
                            
                            retry = input("\n是否继续修改持仓模式? (y/N): ").strip().lower()
                            if retry not in ['y', 'yes', '是']:
                                print("❌ 用户取消操作，交易系统将退出")
                                return False
                        
                        # 2. 修改为单向模式
                        print("🔄 正在修改持仓模式...")
                        if self.set_position_mode('ONE_WAY'):
                            print("✅ 已成功修改为单向模式")
                            logger.info("持仓模式已修改为单向模式")
                            return True
                        else:
                            print("❌ 修改持仓模式失败")
                            print("\n📋 手动修改步骤:")
                            print("1. 登录Binance合约交易界面")
                            print("2. 进入'设置' -> '合约设置'")
                            print("3. 将'持仓模式'从'双向持仓'改为'单向持仓'")
                            print("4. 确认修改")
                            print("\n⚠️  注意: 修改持仓模式前必须先平仓所有持仓")
                            return False
                    elif confirm in ['n', 'no', '否', '']:
                        print("❌ 用户取消操作，交易系统将退出")
                        logger.warning("用户拒绝修改持仓模式，系统退出")
                        return False
                    else:
                        print("请输入 y 或 n")
            else:
                logger.info("持仓模式检查通过，使用单向模式")
                return True
                
        except Exception as e:
            logger.error(f"检查持仓模式异常: {e}")
            return False
    
    def get_all_positions(self) -> List[Dict]:
        """获取所有持仓信息"""
        try:
            endpoint = '/fapi/v2/positionRisk'
            response = self._make_request('GET', endpoint, params={}, signed=True)
            
            if response and isinstance(response, list):
                return response
            else:
                return []
        except Exception as e:
            logger.error(f"获取所有持仓信息异常: {e}")
            return []
    
    def close_all_positions(self) -> bool:
        """平仓所有持仓"""
        try:
            positions = self.get_all_positions()
            success_count = 0
            total_positions = 0
            
            for position in positions:
                symbol = position['symbol']
                position_amt = float(position['positionAmt'])
                
                if abs(position_amt) > 0:
                    total_positions += 1
                    # 确定平仓方向
                    side = 'SELL' if position_amt > 0 else 'BUY'
                    
                    # 使用精度处理后的数量
                    rounded_quantity = self._round_quantity(abs(position_amt))
                    
                    # 验证数量
                    if not self._validate_quantity(rounded_quantity):
                        logger.error(f"平仓数量 {rounded_quantity} 不符合交易所要求: {symbol}")
                        continue
                    
                    # 平仓 - 根据持仓模式决定是否指定持仓方向
                    params = {
                        'symbol': symbol,
                        'side': side,
                        'type': 'MARKET',
                        'quantity': rounded_quantity
                    }
                    
                    # 如果是对冲模式，添加持仓方向参数
                    current_mode = self.get_position_mode()
                    if current_mode == 'HEDGE':
                        params['positionSide'] = 'LONG' if position_amt > 0 else 'SHORT'
                    
                    response = self._make_request('POST', '/fapi/v1/order', params, signed=True)
                    
                    if response and 'orderId' in response:
                        logger.info(f"平仓成功: {symbol} {side} {rounded_quantity}")
                        success_count += 1
                    else:
                        logger.error(f"平仓失败: {symbol} {response}")
                        # 尝试获取更详细的错误信息
                        if response and 'msg' in response:
                            logger.error(f"错误信息: {response['msg']}")
            
            # 如果没有持仓需要平仓，返回成功
            if total_positions == 0:
                logger.info("没有需要平仓的持仓")
                return True
            
            # 如果所有持仓都平仓成功，返回成功
            if success_count == total_positions:
                logger.info(f"所有持仓平仓成功: {success_count}/{total_positions}")
                return True
            else:
                logger.warning(f"部分持仓平仓失败: {success_count}/{total_positions}")
                return False
                
        except Exception as e:
            logger.error(f"平仓所有持仓异常: {e}")
            return False
    
    def sync_position_state(self):
        """同步持仓状态"""
        try:
            position_info = self.get_position_info()
            
            if position_info['side'] == 'NONE':
                # 没有持仓
                self.current_position = 0
                self.position_size = 0
                self.entry_price = 0
                logger.info("同步持仓状态: 无持仓")
            elif position_info['side'] == 'LONG':
                # 多仓
                self.current_position = 1
                self.position_size = abs(position_info['size'])
                self.entry_price = position_info['entry_price']
                logger.info(f"同步持仓状态: 多仓 {self.position_size} @ {self.entry_price}")
            elif position_info['side'] == 'SHORT':
                # 空仓
                self.current_position = -1
                self.position_size = abs(position_info['size'])
                self.entry_price = position_info['entry_price']
                logger.info(f"同步持仓状态: 空仓 {self.position_size} @ {self.entry_price}")
                
        except Exception as e:
            logger.error(f"同步持仓状态异常: {e}")
    
    def get_klines(self, interval: str = '1h', limit: int = 100) -> pd.DataFrame:
        """获取K线数据"""
        try:
            endpoint = '/fapi/v1/klines'  # 使用合约API端点
            params = {
                'symbol': self.symbol,
                'interval': interval,
                'limit': limit
            }
            response = self._make_request('GET', endpoint, params)
            
            if response:
                df = pd.DataFrame(response, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_asset_volume', 'number_of_trades',
                    'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
                ])
                
                # 转换数据类型
                numeric_columns = ['open', 'high', 'low', 'close', 'volume']
                for col in numeric_columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                return df
            else:
                logger.error("获取K线数据失败")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"获取K线数据异常: {e}")
            return pd.DataFrame()
    
    def calculate_position_size(self, price: float, signal_strength: float) -> float:
        """
        智能计算仓位大小，考虑精度要求
        
        Args:
            price: 当前价格
            signal_strength: 信号强度 (0-1)
        
        Returns:
            符合精度要求的仓位大小
        """
        if price <= 0:
            return 0.0
        
        # 计算可用资金
        available_balance = self.current_balance * self.max_position_size
        position_value = available_balance * signal_strength
        
        # 根据信号强度调整仓位
        if signal_strength < 0.3:
            position_value *= 0.5  # 弱信号，减少仓位
        elif signal_strength > 0.7:
            position_value *= 1.2  # 强信号，增加仓位
        
        # 计算原始数量
        raw_quantity = position_value / price
        
        # 应用精度处理（向下舍入确保不超出资金）
        quantity = self._round_quantity(raw_quantity, 'DOWN')
        
        # 验证数量
        if not self._validate_quantity(quantity):
            logger.warning(f"计算出的数量 {quantity} 不符合交易所要求")
            
            # 尝试使用最小数量
            if self.min_quantity and self.min_quantity <= raw_quantity:
                logger.info(f"使用最小数量: {self.min_quantity}")
                return self.min_quantity
            else:
                return 0.0
        
        # 计算实际使用的资金
        actual_value = quantity * price
        logger.info(f"仓位计算: 原始数量={raw_quantity:.6f}, 精度处理后={quantity}, 使用资金={actual_value:.2f}")
        
        return quantity
    
    def place_order(self, side: str, quantity: float, order_type: str = 'MARKET', price: float = None) -> Dict:
        """
        下单
        
        Args:
            side: 交易方向 ('BUY' 或 'SELL')
            quantity: 数量
            order_type: 订单类型 ('MARKET' 或 'LIMIT')
            price: 价格 (限价单需要)
        
        Returns:
            订单响应信息
        """
        try:
            # 根据交易方向选择舍入模式
            # 买入时向下舍入，卖出时向上舍入，确保不会超出资金
            if side == 'BUY':
                rounding_mode = 'DOWN'
            else:  # SELL
                rounding_mode = 'UP'
            
            # 应用精度处理
            rounded_quantity = self._round_quantity(quantity, rounding_mode)
            
            # 验证数量
            if not self._validate_quantity(rounded_quantity):
                logger.error(f"数量 {rounded_quantity} 不符合交易所要求，取消下单")
                return None
            
            endpoint = '/fapi/v1/order'
            params = {
                'symbol': self.symbol,
                'side': side,
                'type': order_type,
                'quantity': rounded_quantity
            }
            
            # 如果是限价单，添加价格参数
            if order_type == 'LIMIT' and price is not None:
                rounded_price = self._round_price(price, 'NEAREST')
                params['price'] = rounded_price
                params['timeInForce'] = 'GTC'  # Good Till Cancel
            
            logger.info(f"下单参数: {side} {rounded_quantity} {self.symbol} @ {price if price else 'MARKET'}")
            
            response = self._make_request('POST', endpoint, params, signed=True)
            
            if response and 'orderId' in response:
                logger.info(f"下单成功: {side} {rounded_quantity} {self.symbol}")
                return response
            else:
                logger.error(f"下单失败: {response}")
                return None
        except Exception as e:
            logger.error(f"下单异常: {e}")
            return None
    
    def close_position(self) -> bool:
        """平仓"""
        if self.current_position == 0:
            return True
        
        try:
            side = 'SELL' if self.current_position > 0 else 'BUY'
            response = self.place_order(side, self.position_size)
            
            if response:
                # 计算盈亏
                current_price = self.get_current_price()
                if current_price > 0:
                    if self.current_position > 0:  # 多仓
                        pnl = (current_price - self.entry_price) * self.position_size
                    else:  # 空仓
                        pnl = (self.entry_price - current_price) * self.position_size
                    
                    self.total_pnl += pnl
                    self.current_balance += pnl
                    
                    # 更新交易统计
                    self.trade_count += 1
                    if pnl > 0:
                        self.win_count += 1
                    
                    # 记录交易
                    trade_record = {
                        'timestamp': datetime.now().isoformat(),
                        'action': 'CLOSE',
                        'side': side,
                        'quantity': self.position_size,
                        'price': current_price,
                        'pnl': pnl,
                        'balance': self.current_balance
                    }
                    self.trade_history.append(trade_record)
                    
                    logger.info(f"平仓成功: {side} {self.position_size} {self.symbol}, PnL: {pnl:.2f}")
                    
                    # 重置仓位
                    self.current_position = 0
                    self.position_size = 0
                    self.entry_price = 0
                    
                    # 同步持仓状态
                    time.sleep(1)  # 等待订单执行
                    self.sync_position_state()
                    
                    return True
            
            return False
        except Exception as e:
            logger.error(f"平仓异常: {e}")
            return False
    
    def open_position(self, signal: int, signal_strength: float) -> bool:
        """开仓"""
        if self.current_position != 0:
            logger.warning("已有持仓，无法开新仓")
            return False
        
        try:
            current_price = self.get_current_price()
            if current_price <= 0:
                logger.error("无法获取有效价格")
                return False
            
            # 计算仓位大小
            quantity = self.calculate_position_size(current_price, signal_strength)
            if quantity <= 0:
                logger.warning("仓位大小计算为0，跳过开仓")
                return False
            
            # 确定交易方向
            side = 'BUY' if signal > 0 else 'SELL'
            
            # 下单
            response = self.place_order(side, quantity)
            
            if response:
                self.current_position = signal
                self.position_size = quantity
                self.entry_price = current_price
                
                # 记录交易
                trade_record = {
                    'timestamp': datetime.now().isoformat(),
                    'action': 'OPEN',
                    'side': side,
                    'quantity': quantity,
                    'price': current_price,
                    'signal_strength': signal_strength,
                    'balance': self.current_balance
                }
                self.trade_history.append(trade_record)
                
                logger.info(f"开仓成功: {side} {quantity} {self.symbol} @ {current_price}")
                
                # 同步持仓状态
                time.sleep(1)  # 等待订单执行
                self.sync_position_state()
                
                return True
            
            return False
        except Exception as e:
            logger.error(f"开仓异常: {e}")
            return False
    
    def check_risk_limits(self) -> bool:
        """检查风险限制"""
        # 检查日亏损限制
        if self.daily_pnl < -self.initial_balance * self.max_daily_loss:
            logger.warning(f"达到日亏损限制: {self.daily_pnl:.2f}")
            return False
        
        # 检查最大回撤
        current_drawdown = (self.peak_balance - self.current_balance) / self.peak_balance
        if current_drawdown > self.max_drawdown:
            logger.warning(f"达到最大回撤限制: {current_drawdown:.2%}")
            return False
        
        # 更新峰值余额
        if self.current_balance > self.peak_balance:
            self.peak_balance = self.current_balance
        
        return True
    
    def generate_signal(self) -> Tuple[int, float]:
        """生成交易信号"""
        try:
            # 获取K线数据
            df = self.get_klines(interval='1h', limit=500)
            if df.empty:
                logger.warning("无法获取K线数据")
                return 0, 0.0
            
            # 计算特征
            logger.info(f"开始计算特征，数据长度: {len(df)}")
            features = self.feature_engineer.calculate_features(df)
            if features is None or features.empty:
                logger.warning("特征计算失败")
                return 0, 0.0
            
            logger.info(f"特征计算成功，特征数据长度: {len(features)}")
            
            # 生成信号
            signal = self.strategy.get_signal(features)
            strength = 0.5  # 默认信号强度
            
            # 记录信号
            signal_record = {
                'timestamp': datetime.now().isoformat(),
                'signal': signal,
                'strength': strength,
                'price': self.get_current_price()
            }
            self.signal_history.append(signal_record)
            
            return signal, strength
        except Exception as e:
            logger.error(f"生成信号异常: {e}")
            return 0, 0.0
    
    def update_balance(self):
        """更新账户余额"""
        try:
            account_info = self.get_account_info()
            if account_info and 'totalWalletBalance' in account_info:
                self.current_balance = float(account_info['totalWalletBalance'])
                logger.info(f"账户余额更新: {self.current_balance:.2f} USDT")
        except Exception as e:
            logger.error(f"更新余额异常: {e}")
    
    def reset_daily_stats(self):
        """重置日统计"""
        self.daily_pnl = 0
        logger.info("日统计已重置")
    
    def print_status(self):
        """打印状态信息"""
        current_price = self.get_current_price()
        win_rate = (self.win_count / self.trade_count * 100) if self.trade_count > 0 else 0
        
        status = f"""
╔══════════════════════════════════════════════════════════════╗
║                    📊 交易状态报告                            ║
╠══════════════════════════════════════════════════════════════╣
║ 当前价格: {current_price:.2f} USDT                           ║
║ 账户余额: {self.current_balance:.2f} USDT                    ║
║ 总盈亏: {self.total_pnl:.2f} USDT                           ║
║ 当前仓位: {self.current_position} ({'多仓' if self.current_position > 0 else '空仓' if self.current_position < 0 else '空仓'}) ║
║ 仓位大小: {self.position_size:.4f}                          ║
║ 开仓价格: {self.entry_price:.2f} USDT                       ║
║ 交易次数: {self.trade_count}                                ║
║ 胜率: {win_rate:.1f}%                                       ║
║ 日盈亏: {self.daily_pnl:.2f} USDT                           ║
║ 最大回撤: {((self.peak_balance - self.current_balance) / self.peak_balance * 100):.1f}% ║
╚══════════════════════════════════════════════════════════════╝
"""
        print(status)
    
    def run(self):
        """运行交易系统"""
        logger.info("启动实盘交易系统...")
        self.running = True
        
        # 重置日统计
        self.reset_daily_stats()
        
        # 同步初始持仓状态
        logger.info("同步初始持仓状态...")
        self.sync_position_state()
        
        try:
            while self.running:
                try:
                    # 检查风险限制
                    if not self.check_risk_limits():
                        logger.warning("触发风险限制，停止交易")
                        break
                    
                    # 定期同步持仓状态（每10次循环同步一次）
                    if hasattr(self, '_sync_counter'):
                        self._sync_counter += 1
                    else:
                        self._sync_counter = 0
                    
                    if self._sync_counter % 10 == 0:
                        self.sync_position_state()
                    
                    # 检查信号冷却时间
                    current_time = time.time()
                    if (self.last_signal_time and 
                        current_time - self.last_signal_time < self.signal_cooldown):
                        time.sleep(1)
                        continue
                    
                    # 生成信号
                    signal, strength = self.generate_signal()
                    self.last_signal_time = current_time
                    
                    if signal != 0 and strength > 0.3:  # 有效信号
                        logger.info(f"生成信号: {signal}, 强度: {strength:.2f}")
                        
                        # 如果有持仓且信号相反，先平仓
                        if ((signal > 0 and self.current_position < 0) or 
                            (signal < 0 and self.current_position > 0)):
                            logger.info("信号反转，平仓")
                            if self.close_position():
                                # 平仓成功后等待一段时间，确保订单完全执行
                                logger.info("等待平仓订单执行...")
                                time.sleep(3)  # 等待3秒
                        
                        # 如果没有持仓，开仓
                        if self.current_position == 0:
                            self.open_position(signal, strength)
                    
                    # 检查止损止盈
                    if self.current_position != 0:
                        current_price = self.get_current_price()
                        if current_price > 0:
                            if self.current_position > 0:  # 多仓
                                # 止损
                                if current_price <= self.entry_price * (1 - self.stop_loss_pct):
                                    logger.info("触发止损")
                                    self.close_position()
                                # 止盈
                                elif current_price >= self.entry_price * (1 + self.take_profit_pct):
                                    logger.info("触发止盈")
                                    self.close_position()
                            else:  # 空仓
                                # 止损
                                if current_price >= self.entry_price * (1 + self.stop_loss_pct):
                                    logger.info("触发止损")
                                    self.close_position()
                                # 止盈
                                elif current_price <= self.entry_price * (1 - self.take_profit_pct):
                                    logger.info("触发止盈")
                                    self.close_position()
                    
                    # 打印状态
                    self.print_status()
                    
                    # 更新余额
                    self.update_balance()
                    
                    # 保存交易历史
                    self.save_trade_history()
                    
                    # 等待
                    time.sleep(60)  # 每分钟检查一次
                    
                except KeyboardInterrupt:
                    logger.info("收到停止信号")
                    break
                except Exception as e:
                    logger.error(f"运行异常: {e}")
                    time.sleep(10)  # 异常后等待10秒再继续
        
        finally:
            # 关闭所有持仓
            if self.current_position != 0:
                logger.info("关闭剩余持仓")
                self.close_position()
            
            # 保存最终交易历史
            self.save_trade_history()
            
            logger.info("实盘交易系统已停止")
            self.running = False
    
    def save_trade_history(self, filename: str = None):
        """保存交易历史"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
            os.makedirs(log_dir, exist_ok=True)
            filename = os.path.join(log_dir, f"trade_history_{timestamp}.json")
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'trade_history': self.trade_history,
                    'signal_history': self.signal_history,
                    'final_stats': {
                        'total_trades': self.trade_count,
                        'win_count': self.win_count,
                        'win_rate': (self.win_count / self.trade_count * 100) if self.trade_count > 0 else 0,
                        'total_pnl': self.total_pnl,
                        'final_balance': self.current_balance
                    }
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"交易历史已保存到: {filename}")
        except Exception as e:
            logger.error(f"保存交易历史失败: {e}")

def create_trader_config():
    """创建交易配置"""
    return {
        'api_key': '',  # 留空，使用公开API
        'secret_key': '',  # 留空，使用公开API
        'base_url': 'https://fapi.binance.com',  # 使用合约API
        'symbol': 'ETHUSDT',
        'initial_balance': 1000,
        'max_position_size': 0.1,
        'stop_loss_pct': 0.05,
        'take_profit_pct': 0.1,
        'max_daily_loss': 0.1,
        'max_drawdown': 0.2,
        'signal_cooldown': 300
    }

if __name__ == "__main__":
    # 测试配置
    config = create_trader_config()
    
    # 创建交易器
    trader = Trader(config)
    
    # 运行交易系统
    trader.run() 