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
from decimal import Decimal, ROUND_DOWN

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
        self.daily_pnl = 0
        self.peak_balance = self.initial_balance
        
        # 交易记录
        self.trade_history = []
        self.signal_history = []
        
        # 运行状态
        self.is_running = False
        self.last_signal_time = None
        self.signal_cooldown = config.get('signal_cooldown', 300)  # 信号冷却时间（秒）
        
        # 初始化API连接
        if not self.test_api_connection():
            logger.error("API连接测试失败")
            raise Exception("无法连接到币安API")
        
        logger.info("实盘交易系统初始化完成")
    
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
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)
        
        try:
            if method == 'GET':
                response = requests.get(url, params=params, headers=headers)
            elif method == 'POST':
                response = requests.post(url, params=params, headers=headers)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {e}")
            return None
    
    def get_account_info(self) -> Dict:
        """获取账户信息"""
        endpoint = '/fapi/v2/account'
        return self._make_request('GET', endpoint, signed=True)
    
    def test_api_connection(self) -> bool:
        """测试API连接"""
        try:
            # 测试服务器时间
            response = requests.get(f"{self.base_url}/fapi/v1/time")
            if response.status_code == 200:
                logger.info("API连接测试成功")
                return True
            else:
                logger.error(f"API连接测试失败: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"API连接测试异常: {e}")
            return False
    
    def get_current_price(self) -> float:
        """获取当前价格"""
        try:
            endpoint = '/fapi/v1/ticker/price'
            params = {'symbol': self.symbol}
            response = self._make_request('GET', endpoint, params)
            
            if response and 'price' in response:
                return float(response['price'])
            else:
                logger.error("获取当前价格失败")
                return 0.0
        except Exception as e:
            logger.error(f"获取当前价格异常: {e}")
            return 0.0
    
    def get_klines(self, interval: str = '1h', limit: int = 100) -> pd.DataFrame:
        """获取K线数据"""
        try:
            endpoint = '/fapi/v1/klines'
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
        """计算仓位大小"""
        available_balance = self.current_balance * self.max_position_size
        position_value = available_balance * signal_strength
        
        # 根据信号强度调整仓位
        if signal_strength < 0.3:
            position_value *= 0.5  # 弱信号，减少仓位
        elif signal_strength > 0.7:
            position_value *= 1.2  # 强信号，增加仓位
        
        quantity = position_value / price
        return quantity
    
    def place_order(self, side: str, quantity: float, order_type: str = 'MARKET') -> Dict:
        """下单"""
        try:
            endpoint = '/fapi/v1/order'
            params = {
                'symbol': self.symbol,
                'side': side,
                'type': order_type,
                'quantity': quantity
            }
            
            response = self._make_request('POST', endpoint, params, signed=True)
            
            if response and 'orderId' in response:
                logger.info(f"下单成功: {side} {quantity} {self.symbol}")
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
            df = self.get_klines(interval='1h', limit=100)
            if df.empty:
                logger.warning("无法获取K线数据")
                return 0, 0.0
            
            # 计算特征
            features = self.feature_engineer.calculate_features(df)
            if features is None or features.empty:
                logger.warning("特征计算失败")
                return 0, 0.0
            
            # 生成信号
            signal, strength = self.strategy.generate_signal(features)
            
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
        self.is_running = True
        
        # 重置日统计
        self.reset_daily_stats()
        
        try:
            while self.is_running:
                try:
                    # 检查风险限制
                    if not self.check_risk_limits():
                        logger.warning("触发风险限制，停止交易")
                        break
                    
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
                            self.close_position()
                        
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
            self.is_running = False
    
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
        'api_key': 'your_api_key',
        'secret_key': 'your_secret_key',
        'base_url': 'https://fapi.binance.com',
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