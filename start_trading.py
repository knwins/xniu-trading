#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实盘交易启动脚本

功能：
- 配置交易参数
- 启动实盘交易
- 演示模式
- 配置管理
"""

import os
import sys
import json
from datetime import datetime

# 添加父目录到Python路径，以便导入根目录中的模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入当前目录的模块
from trader import Trader, create_trader_config

def print_banner():
    """打印启动横幅"""
    banner = """
    
╔══════════════════════════════════════════════════════════════╗
║                    🚀 实盘交易系统 XNIU.IO 🚀                    ║
║                                                          ║
║  基于保守回撤控制策略的智能量化交易系统                    ║
║  回测表现: 收益率 160.67%, 胜率 70.0%                  ║
║                                                          ║
║  功能特点:                                               ║
║  ✅ 实时数据获取和处理                                    ║
║  ✅ 智能信号生成                                        ║
║  ✅ 风险管理控制                                        ║
║  ✅ 自动交易执行                                        ║
║  ✅ 资金管理                                           ║
║  ✅ 实时监控和报告                                      ║
║                                                          ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)

def get_user_input(prompt: str, default: str = "") -> str:
    """获取用户输入"""
    if default:
        user_input = input(f"{prompt} (默认: {default}): ").strip()
        return user_input if user_input else default
    else:
        return input(f"{prompt}: ").strip()

def configure_trading():
    """配置交易参数"""
    print("\n📋 配置交易参数")
    print("=" * 50)
    
    config = {}
    
    # API配置
    print("\n🔑 API配置:")
    config['api_key'] = get_user_input("请输入您的API密钥")
    config['secret_key'] = get_user_input("请输入您的密钥")
    
    # 交易参数
    print("\n💰 交易参数:")
    config['symbol'] = get_user_input("交易对", "ETHUSDT")
    config['initial_balance'] = float(get_user_input("初始资金(USDT)", "1000"))
    config['max_position_size'] = float(get_user_input("最大仓位比例(0.1=10%)", "0.1"))
    
    # 风险控制
    print("\n🛡️ 风险控制:")
    config['stop_loss_pct'] = float(get_user_input("止损比例(0.05=5%)", "0.05"))
    config['take_profit_pct'] = float(get_user_input("止盈比例(0.1=10%)", "0.1"))
    config['max_daily_loss'] = float(get_user_input("最大日亏损(0.1=10%)", "0.1"))
    config['max_drawdown'] = float(get_user_input("最大回撤(0.2=20%)", "0.2"))
    
    # 其他设置
    print("\n⚙️ 其他设置:")
    config['signal_cooldown'] = int(get_user_input("信号冷却时间(秒)", "300"))
    config['base_url'] = get_user_input("API基础URL", "https://fapi.binance.com")
    
    return config

def save_config(config: dict, filename: str = None):
    """保存配置"""
    if filename is None:
        filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trading_config.json")
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"✅ 配置已保存到: {filename}")
        return True
    except Exception as e:
        print(f"❌ 保存配置失败: {e}")
        return False

def load_config(filename: str = None) -> dict:
    """加载配置"""
    if filename is None:
        filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trading_config.json")
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✅ 配置已从 {filename} 加载")
            return config
        else:
            print(f"⚠️ 配置文件 {filename} 不存在")
            return None
    except Exception as e:
        print(f"❌ 加载配置失败: {e}")
        return None

def print_config_summary(config: dict):
    """打印配置摘要"""
    print("\n📊 配置摘要:")
    print("=" * 50)
    print(f"交易对: {config['symbol']}")
    print(f"初始资金: {config['initial_balance']} USDT")
    print(f"最大仓位: {config['max_position_size']*100:.1f}%")
    print(f"止损: {config['stop_loss_pct']*100:.1f}%")
    print(f"止盈: {config['take_profit_pct']*100:.1f}%")
    print(f"最大日亏损: {config['max_daily_loss']*100:.1f}%")
    print(f"最大回撤: {config['max_drawdown']*100:.1f}%")
    print(f"信号冷却: {config['signal_cooldown']} 秒")

def confirm_start():
    """确认开始交易"""
    print("\n⚠️ 重要提醒:")
    print("1. 请确保您的API密钥有交易权限")
    print("2. 请确保账户有足够的资金")
    print("3. 实盘交易存在风险，请谨慎操作")
    print("4. 建议先用小额资金测试")
    
    confirm = input("\n是否确认开始实盘交易? (y/N): ").strip().lower()
    return confirm in ['y', 'yes', '是']

def run_demo_mode():
    """运行演示模式"""
    print("\n🎮 演示模式")
    print("=" * 50)
    print("演示模式将模拟交易，不会执行真实交易")
    print("用于测试系统功能和策略表现")
    
    # 创建演示配置
    demo_config = {
        'api_key': 'DEMO_KEY',
        'secret_key': 'DEMO_SECRET',
        'base_url': 'https://fapi.binance.com',
        'symbol': 'ETHUSDT',
        'initial_balance': 1000,
        'max_position_size': 0.1,
        'stop_loss_pct': 0.05,
        'take_profit_pct': 0.1,
        'max_daily_loss': 0.1,
        'max_drawdown': 0.2,
        'signal_cooldown': 300,
        'demo_mode': True
    }
    
    print_config_summary(demo_config)
    
    if confirm_start():
        print("\n🚀 启动演示模式...")
        # 这里可以添加演示模式的逻辑
        print("演示模式功能开发中...")
        print("请使用实盘模式进行测试")

def main():
    """主函数"""
    print_banner()
    
    while True:
        print("\n请选择操作:")
        print("1. 🚀 开始实盘交易")
        print("2. ⚙️ 配置交易参数")
        print("3. 🎮 演示模式")
        print("4. 📊 查看配置")
        print("5. ❌ 退出")
        
        choice = input("\n请输入选择 (1-5): ").strip()
        
        if choice == '1':
            # 开始实盘交易
            config = load_config()
            if not config:
                print("❌ 请先配置交易参数")
                continue
            
            print_config_summary(config)
            
            if confirm_start():
                print("\n🚀 启动实盘交易系统...")
                try:
                    trader = Trader(config)
                    trader.run()
                except KeyboardInterrupt:
                    print("\n⏹️ 收到停止信号")
                except Exception as e:
                    print(f"\n❌ 运行异常: {e}")
                finally:
                    print("实盘交易已结束")
                break
        
        elif choice == '2':
            # 配置交易参数
            config = configure_trading()
            if save_config(config):
                print_config_summary(config)
        
        elif choice == '3':
            # 演示模式
            run_demo_mode()
        
        elif choice == '4':
            # 查看配置
            config = load_config()
            if config:
                print_config_summary(config)
        
        elif choice == '5':
            # 退出
            print("\n👋 感谢使用实盘交易系统!")
            break
        
        else:
            print("❌ 无效选择，请重新输入")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 程序已退出")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        sys.exit(1) 