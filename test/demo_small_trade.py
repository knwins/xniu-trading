#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演示版小额交易测试器
使用模拟数据演示买入卖出功能
"""

import time
import json
import logging
import random
from datetime import datetime
# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/demo_trade.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DemoTradeTester:
    """演示版交易测试器"""
    
    def __init__(self):
        # 模拟配置
        self.symbol = "ETHUSDT"
        self.base_price = 3582.83  # 基础价格
        self.price_volatility = 0.02  # 价格波动率
        
        # 交易状态
        self.current_position = 0  # 当前仓位 (1=多仓, -1=空仓, 0=空仓)
        self.position_size = 0  # 仓位大小
        self.entry_price = 0  # 开仓价格
        self.current_balance = 1000.0  # 初始余额
        self.total_pnl = 0
        self.trade_count = 0
        self.win_count = 0
        
        # 交易记录
        self.trade_history = []
        
        logger.info("演示版交易测试器初始化完成")
        logger.info(f"初始余额: {self.current_balance} USDT")
    
    def get_simulated_price(self) -> float:
        """获取模拟价格"""
        # 模拟价格波动
        change = random.uniform(-self.price_volatility, self.price_volatility)
        current_price = self.base_price * (1 + change)
        return round(current_price, 2)
    
    def simulate_order_execution(self, side: str, quantity: float, price: float) -> dict:
        """模拟订单执行"""
        # 模拟订单执行延迟
        time.sleep(0.5)
        
        # 模拟执行成功
        return {
            'status': 'FILLED',
            'symbol': self.symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'executedQty': quantity,
            'avgPrice': price
        }
    
    def place_order(self, side: str, quantity: float, order_type: str = 'MARKET') -> dict:
        """下单"""
        current_price = self.get_simulated_price()
        quantity = round(quantity, 6)
        
        logger.info(f"模拟下单 - 方向: {side}, 数量: {quantity:.6f}, 价格: {current_price}")
        
        return self.simulate_order_execution(side, quantity, current_price)
    
    def quick_buy(self, amount_usdt: float = 10.0):
        """快速买入"""
        current_price = self.get_simulated_price()
        if not current_price:
            logger.error("无法获取当前价格")
            return False
        
        quantity = amount_usdt / current_price
        logger.info(f"准备买入 - 金额: {amount_usdt} USDT, 数量: {quantity:.6f}, 价格: {current_price}")
        
        result = self.place_order('BUY', quantity)
        
        if result and result.get('status') == 'FILLED':
            self.current_position = 1
            self.position_size = quantity
            self.entry_price = current_price
            self.current_balance -= amount_usdt
            
            # 记录交易
            trade_record = {
                'timestamp': datetime.now(),
                'action': 'BUY',
                'price': current_price,
                'quantity': quantity,
                'amount': amount_usdt,
                'balance': self.current_balance
            }
            self.trade_history.append(trade_record)
            
            logger.info(f"买入成功 - 价格: {current_price}, 数量: {quantity:.6f}")
            return True
        else:
            logger.error(f"买入失败: {result}")
            return False
    
    def quick_sell(self, amount_usdt: float = 10.0):
        """快速卖出"""
        current_price = self.get_simulated_price()
        if not current_price:
            logger.error("无法获取当前价格")
            return False
        
        quantity = amount_usdt / current_price
        logger.info(f"准备卖出 - 金额: {amount_usdt} USDT, 数量: {quantity:.6f}, 价格: {current_price}")
        
        result = self.place_order('SELL', quantity)
        
        if result and result.get('status') == 'FILLED':
            self.current_position = -1
            self.position_size = quantity
            self.entry_price = current_price
            self.current_balance += amount_usdt
            
            # 记录交易
            trade_record = {
                'timestamp': datetime.now(),
                'action': 'SELL',
                'price': current_price,
                'quantity': quantity,
                'amount': amount_usdt,
                'balance': self.current_balance
            }
            self.trade_history.append(trade_record)
            
            logger.info(f"卖出成功 - 价格: {current_price}, 数量: {quantity:.6f}")
            return True
        else:
            logger.error(f"卖出失败: {result}")
            return False
    
    def close_position(self):
        """平仓"""
        if self.current_position == 0:
            logger.info("当前无仓位，无需平仓")
            return True
        
        current_price = self.get_simulated_price()
        side = 'SELL' if self.current_position > 0 else 'BUY'
        
        result = self.place_order(side, self.position_size)
        
        if result and result.get('status') == 'FILLED':
            # 计算盈亏
            pnl = (current_price - self.entry_price) * self.position_size
            if self.current_position < 0:  # 空仓
                pnl = -pnl
            
            self.total_pnl += pnl
            self.current_balance += pnl
            
            # 更新统计
            self.trade_count += 1
            if pnl > 0:
                self.win_count += 1
            
            # 记录交易
            trade_record = {
                'timestamp': datetime.now(),
                'action': 'CLOSE',
                'side': side,
                'price': current_price,
                'quantity': self.position_size,
                'pnl': pnl,
                'balance': self.current_balance,
                'win_rate': self.win_count / self.trade_count if self.trade_count > 0 else 0
            }
            self.trade_history.append(trade_record)
            
            logger.info(f"平仓成功 - 价格: {current_price}, 盈亏: {pnl:.2f}, 余额: {self.current_balance:.2f}")
            logger.info(f"交易统计 - 总交易: {self.trade_count}, 胜率: {self.win_count/self.trade_count*100:.1f}%")
            
            # 重置仓位
            self.current_position = 0
            self.position_size = 0
            self.entry_price = 0
            return True
        else:
            logger.error(f"平仓失败: {result}")
            return False
    
    def print_status(self):
        """打印状态"""
        current_price = self.get_simulated_price()
        pnl = 0
        if self.current_position != 0 and current_price:
            pnl = (current_price - self.entry_price) * self.position_size
            if self.current_position < 0:
                pnl = -pnl
        
        print("\n" + "="*50)
        print("演示版小额交易测试器状态")
        print("="*50)
        print(f"当前价格: {current_price:.2f} USDT")
        print(f"当前余额: {self.current_balance:.2f} USDT")
        print(f"总盈亏: {self.total_pnl:.2f} USDT")
        print(f"当前仓位: {self.current_position}")
        if self.current_position != 0:
            print(f"仓位大小: {self.position_size:.6f}")
            print(f"开仓价格: {self.entry_price:.2f}")
            print(f"浮动盈亏: {pnl:.2f} USDT")
        print(f"总交易次数: {self.trade_count}")
        if self.trade_count > 0:
            print(f"胜率: {self.win_count/self.trade_count*100:.1f}%")
        print("="*50)
    
    def save_trade_history(self, filename: str = None):
        """保存交易历史"""
        if not filename:
            filename = f"../logs/demo_trades_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            # 转换datetime对象为字符串
            serializable_history = []
            for trade in self.trade_history:
                trade_copy = trade.copy()
                if 'timestamp' in trade_copy:
                    trade_copy['timestamp'] = trade_copy['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                serializable_history.append(trade_copy)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(serializable_history, f, ensure_ascii=False, indent=2)
            print(f"✅ 交易历史已保存到: {filename}")
        except Exception as e:
            print(f"❌ 保存交易历史失败: {e}")

def main():
    """主函数"""
    print("演示版小额交易测试器启动...")
    print("注意: 这是一个演示版本，使用模拟数据，不会进行真实交易")
    
    tester = DemoTradeTester()
    tester.print_status()
    
    # 交互式测试
    while True:
        print("\n请选择操作:")
        print("1. 查看状态")
        print("2. 模拟买入 (10 USDT)")
        print("3. 模拟卖出 (10 USDT)")
        print("4. 平仓")
        print("5. 保存交易历史")
        print("6. 退出")
        
        choice = input("请输入选择 (1-6): ").strip()
        
        if choice == '1':
            tester.print_status()
        elif choice == '2':
            amount = input("请输入买入金额 (USDT，直接回车使用10): ").strip()
            if amount:
                try:
                    amount = float(amount)
                    tester.quick_buy(amount)
                except ValueError:
                    print("金额格式错误")
            else:
                tester.quick_buy()
        elif choice == '3':
            amount = input("请输入卖出金额 (USDT，直接回车使用10): ").strip()
            if amount:
                try:
                    amount = float(amount)
                    tester.quick_sell(amount)
                except ValueError:
                    print("金额格式错误")
            else:
                tester.quick_sell()
        elif choice == '4':
            tester.close_position()
        elif choice == '5':
            tester.save_trade_history()
        elif choice == '6':
            print("退出演示测试器")
            break
        else:
            print("无效选择，请重新输入")
        
        time.sleep(1)

if __name__ == "__main__":
    main() 