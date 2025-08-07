#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实盘交易启动脚本

功能：
- 配置交易参数
- 启动实盘交易
- 演示模式
- 配置管理
- 支持非交互式模式（用于系统服务）
"""

import os
import sys
import json
import argparse
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
    
    # 加载现有配置
    existing_config = load_config()
    if existing_config:
        print("📋 检测到现有配置，输入为空时将保持原值")
    
    config = {}
    
    # API配置
    print("\n🔑 API配置:")
    
    # API key 格式验证
    while True:
        current_api_key = existing_config.get('api_key', '') if existing_config else ''
        api_key = get_user_input("请输入您的API密钥", current_api_key)
        if not api_key:
            print("❌ API密钥不能为空")
            continue
        
        # 验证API key格式
        if len(api_key) < 20:
            print("❌ API密钥长度不足，请检查是否正确")
            continue
        
        if not api_key.isalnum():
            print("❌ API密钥格式不正确，应只包含字母和数字")
            continue
        
        config['api_key'] = api_key
        break
    
    # Secret key 格式验证
    while True:
        current_secret_key = existing_config.get('secret_key', '') if existing_config else ''
        secret_key = get_user_input("请输入您的密钥", current_secret_key)
        if not secret_key:
            print("❌ 密钥不能为空")
            continue
        
        # 验证Secret key格式
        if len(secret_key) < 20:
            print("❌ 密钥长度不足，请检查是否正确")
            continue
        
        if not secret_key.isalnum():
            print("❌ 密钥格式不正确，应只包含字母和数字")
            continue
        
        config['secret_key'] = secret_key
        break
    
    # 测试API连接
    print("\n🔍 测试API连接...")
    try:
        from trader import Trader
        test_trader = Trader(config)
        if test_trader.test_api_connection():
            print("✅ API连接测试成功")
        else:
            print("❌ API连接测试失败，请检查网络连接")
    except Exception as e:
        print(f"❌ API连接测试异常: {e}")
    
    # 交易参数
    print("\n💰 交易参数:")
    current_symbol = existing_config.get('symbol', 'ETHUSDT') if existing_config else 'ETHUSDT'
    config['symbol'] = get_user_input("交易对", current_symbol)
    
    current_balance = existing_config.get('initial_balance', 1000) if existing_config else 1000
    balance_input = get_user_input("初始资金(USDT)", str(current_balance))
    config['initial_balance'] = float(balance_input) if balance_input else current_balance
    
    current_position = existing_config.get('max_position_size', 0.1) if existing_config else 0.1
    position_input = get_user_input("最大仓位比例(0.1=10%)", str(current_position))
    config['max_position_size'] = float(position_input) if position_input else current_position
    
    # 风险控制
    print("\n🛡️ 风险控制:")
    current_stop_loss = existing_config.get('stop_loss_pct', 0.05) if existing_config else 0.05
    stop_loss_input = get_user_input("止损比例(0.05=5%)", str(current_stop_loss))
    config['stop_loss_pct'] = float(stop_loss_input) if stop_loss_input else current_stop_loss
    
    current_take_profit = existing_config.get('take_profit_pct', 0.1) if existing_config else 0.1
    take_profit_input = get_user_input("止盈比例(0.1=10%)", str(current_take_profit))
    config['take_profit_pct'] = float(take_profit_input) if take_profit_input else current_take_profit
    
    current_daily_loss = existing_config.get('max_daily_loss', 0.1) if existing_config else 0.1
    daily_loss_input = get_user_input("最大日亏损(0.1=10%)", str(current_daily_loss))
    config['max_daily_loss'] = float(daily_loss_input) if daily_loss_input else current_daily_loss
    
    current_drawdown = existing_config.get('max_drawdown', 0.2) if existing_config else 0.2
    drawdown_input = get_user_input("最大回撤(0.2=20%)", str(current_drawdown))
    config['max_drawdown'] = float(drawdown_input) if drawdown_input else current_drawdown
    
    # 其他设置
    print("\n⚙️ 其他设置:")
    current_cooldown = existing_config.get('signal_cooldown', 300) if existing_config else 300
    cooldown_input = get_user_input("信号冷却时间(秒)", str(current_cooldown))
    config['signal_cooldown'] = int(cooldown_input) if cooldown_input else current_cooldown
    
    current_url = existing_config.get('base_url', 'https://fapi.binance.com') if existing_config else 'https://fapi.binance.com'
    config['base_url'] = get_user_input("API基础URL", current_url)
    
    return config

def save_config(config: dict, filename: str = None):
    """保存配置"""
    if filename is None:
        filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trader_config.json")
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
        filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trader_config.json")
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

def validate_api_credentials(config: dict) -> bool:
    """验证API凭据"""
    print("\n🔍 API凭据验证")
    print("=" * 50)
    
    # 检查配置完整性
    required_fields = ['api_key', 'secret_key', 'base_url']
    for field in required_fields:
        if field not in config or not config[field]:
            print(f"❌ 缺少必要配置: {field}")
            return False
    
    # 验证API key格式
    api_key = config['api_key']
    secret_key = config['secret_key']
    
    print(f"📋 API Key: {api_key[:8]}...{api_key[-4:]}")
    print(f"📋 Secret Key: {secret_key[:8]}...{secret_key[-4:]}")
    print(f"🌐 API URL: {config['base_url']}")
    
    # 格式验证
    if len(api_key) < 20:
        print("❌ API Key长度不足")
        return False
    
    if len(secret_key) < 20:
        print("❌ Secret Key长度不足")
        return False
    
    if not api_key.isalnum():
        print("❌ API Key格式不正确")
        return False
    
    if not secret_key.isalnum():
        print("❌ Secret Key格式不正确")
        return False
    
    print("✅ 格式验证通过")
    
    # 连接测试
    try:
        from trader import Trader
        trader = Trader(config)
        
        print("\n🔍 测试网络连接...")
        import requests
        response = requests.get(f"{config['base_url']}/fapi/v1/time", timeout=5)
        if response.status_code == 200:
            print("✅ 网络连接正常")
        else:
            print(f"❌ 网络连接失败: {response.status_code}")
            return False
        
        print("\n🔍 验证API密钥...")
        if trader.test_api_connection():
            print("✅ API密钥验证成功")
            return True
        else:
            print("❌ API密钥验证失败")
            return False
            
    except Exception as e:
        print(f"❌ 验证过程异常: {e}")
        return False

def run_trading_service(config: dict):
    """运行交易服务（非交互式模式）"""
    print("🚀 启动交易服务（非交互式模式）...")
    print(f"📊 使用配置: {config.get('symbol', 'Unknown')}")
    
    try:
        # 验证配置
        if not validate_api_credentials(config):
            print("❌ API凭据验证失败，服务启动失败")
            return False
        
        # 启动交易器
        trader = Trader(config)
        trader.run()
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️ 收到停止信号")
        return True
    except Exception as e:
        print(f"\n❌ 服务运行异常: {e}")
        return False

def interactive_main():
    """交互式主函数"""
    print_banner()
    
    while True:
        print("\n请选择操作:")
        print("1. 🚀 开始实盘交易")
        print("2. ⚙️ 配置交易参数")
        print("3. 📊 查看配置")
        print("4. 🔍 测试API连接")
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
            # 查看配置
            config = load_config()
            if config:
                print_config_summary(config)
        
        elif choice == '4':
            # 测试API连接
            config = load_config()
            if not config:
                print("❌ 请先配置交易参数")
                continue
            
            if validate_api_credentials(config):
                print("\n✅ API凭据验证完全通过！")
            else:
                print("\n❌ API凭据验证失败，请检查配置")
        
        elif choice == '5':
            # 退出
            print("\n👋 感谢使用实盘交易系统!")
            break
        
        else:
            print("❌ 无效选择，请重新输入")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='XNIU.IO 实盘交易系统')
    parser.add_argument('--service', action='store_true', help='以服务模式运行（非交互式）')
    parser.add_argument('--config', type=str, help='指定配置文件路径')
    parser.add_argument('--validate', action='store_true', help='仅验证API配置')
    
    args = parser.parse_args()
    
    if args.service:
        # 服务模式运行
        config_file = args.config or os.path.join(os.path.dirname(os.path.abspath(__file__)), "trader_config.json")
        config = load_config(config_file)
        
        if not config:
            print(f"❌ 配置文件不存在或无法加载: {config_file}")
            sys.exit(1)
        
        if args.validate:
            # 仅验证配置
            if validate_api_credentials(config):
                print("✅ API配置验证成功")
                sys.exit(0)
            else:
                print("❌ API配置验证失败")
                sys.exit(1)
        else:
            # 运行交易服务
            success = run_trading_service(config)
            sys.exit(0 if success else 1)
    else:
        # 交互式模式运行
        try:
            interactive_main()
        except KeyboardInterrupt:
            print("\n\n👋 程序已退出")
        except Exception as e:
            print(f"\n❌ 程序异常: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main() 