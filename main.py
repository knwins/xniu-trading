
# -*- coding: utf-8 -*-
# main.py
from data_loader import DataLoader
from feature_engineer import FeatureEngineer
from strategy import (
    HighFrequencyAdaptiveStrategy,
    EnhancedStableRiskAdjustmentStrategy,
    TrendTrackingRiskManagementStrategy,
    ConservativeDrawdownControlStrategy
)
from backtester import Backtester
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def run_comprehensive_backtest():
    """运行完整的策略回测系统"""
    print("🚀 开始量化交易策略全面回测系统...")
    print("=" * 80)
    
    # 1. 数据加载和特征工程
    features, kline_data = load_and_process_data()
    if features is None:
        return
    
    # 2. 定义所有策略
    strategies = define_strategies()
    
    # 3. 运行多时间框架回测
    all_results = run_multi_timeframe_backtest(features, strategies)
    
    # 4. 运行风险控制测试
    risk_test_results = run_risk_control_tests(features, strategies)
    
    # 5. 生成详细报告
    generate_comprehensive_report(all_results, risk_test_results)
    
    # 6. 绘制分析图表
    create_analysis_charts(all_results, risk_test_results, kline_data)
    
    print("\n✅ 量化交易策略全面回测完成!")

def load_and_process_data():
    """加载和处理数据"""
    print("📊 正在加载和处理历史数据...")
    
    # 数据加载器配置
    data_loader = DataLoader(timeframe="1h")
    
    # 修复时间范围计算 - 确保使用正确的时间范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)  # 减少到180天，更合理的时间范围
    
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    print(f"📅 回测时间范围: {start_date_str} 至 {end_date_str} (最近180天)")
    
    try:
        # 尝试获取真实数据
        historical_data = data_loader.get_klines(start_date_str, end_date_str)
        
        if historical_data is None or len(historical_data) == 0:
            print("⚠️ 无法获取真实数据，使用模拟数据...")
            data_loader.use_mock_data = True
            historical_data = data_loader.get_klines(start_date_str, end_date_str)
        
        if historical_data is None or len(historical_data) == 0:
            print("❌ 数据加载失败")
            return None
        
        # 添加数据验证
        print(f"✅ 成功加载 {len(historical_data)} 条历史数据")
        print(f"📊 数据时间范围: {historical_data.index[0]} 至 {historical_data.index[-1]}")
        print(f"📈 价格范围: {historical_data['close'].min():.2f} - {historical_data['close'].max():.2f}")
        
        # 验证数据完整性
        if len(historical_data) < 100:
            print("⚠️ 数据量过少，可能影响回测准确性")
        
        # 检查数据异常值
        price_changes = historical_data['close'].pct_change().dropna()
        if price_changes.abs().max() > 0.5:  # 单日价格变化超过50%
            print("⚠️ 检测到异常价格变化，可能存在数据问题")
        
    except Exception as e:
        print(f"❌ 数据加载异常: {e}")
        print("🔄 使用模拟数据...")
        data_loader.use_mock_data = True
        historical_data = data_loader.get_klines(start_date_str, end_date_str)
        
        if historical_data is None or len(historical_data) == 0:
            print("❌ 模拟数据也加载失败")
            return None
    
    # 特征工程
    print("🔧 正在进行特征工程...")
    try:
        feature_engineer = FeatureEngineer()
        features = feature_engineer.add_features(historical_data)
        
        if features is None or len(features) == 0:
            print("❌ 特征工程失败")
            return None
        
        print(f"✅ 特征工程完成，共 {len(features)} 条特征数据")
        print(f"📈 包含技术指标: RSI, MACD, 布林带, KDJ, ATR等")
        print(f"📊 包含风险指标: 夏普比率, 索提诺比率, 最大回撤等")
        
        return features, historical_data
        
    except Exception as e:
        print(f"❌ 特征工程异常: {e}")
        return None

def define_strategies():
    """定义所有要测试的策略"""
    strategies = {
        "高频自适应止盈策略": {
            "class": HighFrequencyAdaptiveStrategy,
            "description": "高频交易，自适应止盈，高胜率但回撤较大"
        },

        "加强版稳健风险调整策略": {
            "class": EnhancedStableRiskAdjustmentStrategy,
            "description": "稳健策略的加强版，降低信号阈值提高交易频率，保持风险控制"
        },
        "保守回撤控制策略": {
            "class": ConservativeDrawdownControlStrategy,
            "description": "高频交易策略，基于风险调整收益指标，严格控制回撤，适合积极型投资者"
        },
        "趋势跟踪风险管理策略": {
            "class": TrendTrackingRiskManagementStrategy,
            "description": "趋势跟踪结合风险管理，中等频率交易"
        },

    }
    
    print(f"📋 已定义 {len(strategies)} 个策略:")
    for name, info in strategies.items():
        print(f"   • {name}: {info['description']}")
    
    return strategies

def run_multi_timeframe_backtest(features, strategies):
    """运行1小时时间框架回测"""
    print("\n🔄 开始1小时时间框架回测...")
    
    all_results = {}
    
    print(f"\n⏰ 测试 1小时 时间框架...")
    
    # 使用已加载的1小时数据，无需重新加载
    print(f"✅ 1小时时间框架数据准备完成，共 {len(features)} 条数据")
    
    # 测试所有策略
    tf_results = []
    for strategy_name, strategy_info in strategies.items():
        result = run_single_strategy_backtest(
            strategy_info["class"], 
            strategy_name, 
            features, 
            "1小时"
        )
        if result:
            tf_results.append(result)
    
    all_results["1小时"] = tf_results
    
    return all_results

def run_single_strategy_backtest(strategy_class, strategy_name, features, timeframe):
    """运行单个策略的回测"""
    try:
        print(f"  📊 测试策略: {strategy_name}")
        
        # 创建回测器
        backtester = Backtester()
        backtester.strategy = strategy_class
        
        # 执行回测
        result = backtester.run_backtest(features)
        
        if result:
            # 计算额外指标
            trade_df = result['trade_log']
            if len(trade_df) > 0 and 'pnl' in trade_df.columns:
                profitable_trades = trade_df[trade_df['pnl'] > 0]
                loss_trades = trade_df[trade_df['pnl'] < 0]
                
                win_rate = len(profitable_trades) / len(trade_df) * 100
                avg_profit = profitable_trades['pnl'].mean() if len(profitable_trades) > 0 else 0
                avg_loss = loss_trades['pnl'].mean() if len(loss_trades) > 0 else 0
                profit_loss_ratio = abs(avg_profit / avg_loss) if avg_loss != 0 else 0
                
                # 计算最大回撤
                total_assets = result['total_assets']
                if len(total_assets) > 0:
                    max_drawdown = calculate_max_drawdown(total_assets)
                else:
                    max_drawdown = 0
                
                # 计算夏普比率
                if len(total_assets) > 1:
                    returns = np.diff(total_assets) / total_assets[:-1]
                    sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
                else:
                    sharpe_ratio = 0
                
                enhanced_result = {
                    'strategy_name': strategy_name,
                    'timeframe': timeframe,
                    'final_cash': result['final_cash'],
                    'return_ratio': result['return_ratio'],
                    'total_trades': result['total_trades'],
                    'win_rate': win_rate,
                    'avg_profit': avg_profit,
                    'avg_loss': avg_loss,
                    'profit_loss_ratio': profit_loss_ratio,
                    'max_drawdown': max_drawdown,
                    'sharpe_ratio': sharpe_ratio,
                    'total_assets': total_assets,
                    'ohlc_data': features
                }
                
                print(f"    ✅ 完成 - 收益率: {result['return_ratio']:.2f}%, 胜率: {win_rate:.1f}%, 交易次数: {result['total_trades']}")
                return enhanced_result
            else:
                print(f"    ❌ 失败 - 无交易记录")
                return None
        else:
            print(f"    ❌ 失败 - 回测异常")
            return None
            
    except Exception as e:
        print(f"    ❌ 异常: {e}")
        return None

def run_risk_control_tests(features, strategies):
    """运行风险控制测试"""
    print("\n🛡️ 开始风险控制测试...")
    
    risk_results = {}
    
    for strategy_name, strategy_info in strategies.items():
        print(f"\n📊 测试 {strategy_name} 风险控制...")
        
        try:
            # 获取风险状态
            if hasattr(strategy_info["class"], 'get_risk_status'):
                risk_status = strategy_info["class"].get_risk_status(features)
                risk_results[strategy_name] = risk_status
                print(f"  风险等级: {risk_status.get('risk_level', 'unknown')}")
                print(f"  状态: {risk_status.get('status', 'unknown')}")
                print(f"  消息: {risk_status.get('message', 'N/A')}")
            else:
                print(f"  ⚠️ 策略无风险控制功能")
                
        except Exception as e:
            print(f"  ❌ 风险控制测试失败: {e}")
    
    return risk_results

def calculate_max_drawdown(total_assets):
    """计算最大回撤"""
    if len(total_assets) < 2:
        return 0
    
    peak = total_assets[0]
    max_dd = 0
    
    for value in total_assets:
        if value > peak:
            peak = value
        dd = (peak - value) / peak
        if dd > max_dd:
            max_dd = dd
    
    return max_dd

def generate_comprehensive_report(all_results, risk_test_results):
    """生成综合报告"""
    print("\n" + "="*80)
    print("📊 量化交易策略综合回测报告")
    print("="*80)
    
    # 1. 策略性能排名
    print("\n🏆 策略性能排名:")
    print("-" * 60)
    
    all_strategy_results = []
    for timeframe, results in all_results.items():
        for result in results:
            all_strategy_results.append(result)
    
    # 按收益率排序
    sorted_results = sorted(all_strategy_results, key=lambda x: x['return_ratio'], reverse=True)
    
    for i, result in enumerate(sorted_results[:10], 1):  # 显示前10名
        print(f"{i:2d}. {result['strategy_name']} ({result['timeframe']})")
        print(f"    收益率: {result['return_ratio']:6.2f}% | 胜率: {result['win_rate']:5.1f}% | "
              f"交易次数: {result['total_trades']:3d} | 最大回撤: {result['max_drawdown']:5.1%} | "
              f"夏普比率: {result['sharpe_ratio']:5.2f}")
    
    # 2. 最优策略分析
    if sorted_results:
        best_strategy = sorted_results[0]
        print(f"\n🎯 全局最优策略: {best_strategy['strategy_name']}")
        print(f"   时间框架: {best_strategy['timeframe']}")
        print(f"   收益率: {best_strategy['return_ratio']:.2f}%")
        print(f"   胜率: {best_strategy['win_rate']:.1f}%")
        print(f"   交易次数: {best_strategy['total_trades']}")
        print(f"   盈亏比: {best_strategy['profit_loss_ratio']:.2f}")
        print(f"   最大回撤: {best_strategy['max_drawdown']:.1%}")
        print(f"   夏普比率: {best_strategy['sharpe_ratio']:.2f}")
    
    # 3. 风险控制分析
    print(f"\n🛡️ 风险控制分析:")
    print("-" * 40)
    for strategy_name, risk_status in risk_test_results.items():
        print(f"{strategy_name}: {risk_status.get('risk_level', 'unknown')} - {risk_status.get('message', 'N/A')}")
    
    # 4. 时间框架分析
    print(f"\n⏰ 时间框架分析:")
    print("-" * 40)
    for timeframe, results in all_results.items():
        if results:
            avg_return = np.mean([r['return_ratio'] for r in results])
            avg_trades = np.mean([r['total_trades'] for r in results])
            print(f"{timeframe}: 平均收益率 {avg_return:.2f}%, 平均交易次数 {avg_trades:.0f}")

def create_analysis_charts(all_results, risk_test_results, kline_data=None, symbol="BTCUSDT"):
    """创建分析图表"""
    print("\n📈 正在生成分析图表...")
    
    # 1. 策略性能对比图
    create_performance_comparison_chart(all_results, symbol)
    
    # 2. 资金曲线图（带K线数据）
    create_equity_curves_with_kline(all_results, kline_data, symbol)
    


def create_performance_comparison_chart(all_results, symbol="BTCUSDT"):
    """创建策略性能对比图"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'{symbol} 量化交易策略性能对比分析', fontsize=16, fontweight='bold')
    
    # 提取数据
    strategies = []
    returns = []
    win_rates = []
    trade_counts = []
    sharpe_ratios = []
    
    for timeframe, results in all_results.items():
        for result in results:
            strategies.append(f"{result['strategy_name']}\n({result['timeframe']})")
            returns.append(result['return_ratio'])
            win_rates.append(result['win_rate'])
            trade_counts.append(result['total_trades'])
            sharpe_ratios.append(result['sharpe_ratio'])
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
    
    # 收益率对比
    ax1 = axes[0, 0]
    bars1 = ax1.bar(strategies, returns, color=colors[:len(strategies)])
    ax1.set_title('策略收益率对比', fontweight='bold')
    ax1.set_ylabel('收益率 (%)')
    ax1.tick_params(axis='x', rotation=45)
    
    # 添加数值标签
    for bar, val in zip(bars1, returns):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + max(0.5, abs(height) * 0.02),
                f'{val:.1f}%', ha='center', va='bottom', fontweight='bold')
    
    # 胜率对比
    ax2 = axes[0, 1]
    bars2 = ax2.bar(strategies, win_rates, color=colors[:len(strategies)])
    ax2.set_title('策略胜率对比', fontweight='bold')
    ax2.set_ylabel('胜率 (%)')
    ax2.tick_params(axis='x', rotation=45)
    
    for bar, val in zip(bars2, win_rates):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + max(0.2, height * 0.02),
                f'{val:.1f}%', ha='center', va='bottom', fontweight='bold')
    
    # 交易次数对比
    ax3 = axes[1, 0]
    bars3 = ax3.bar(strategies, trade_counts, color=colors[:len(strategies)])
    ax3.set_title('策略交易次数对比', fontweight='bold')
    ax3.set_ylabel('交易次数')
    ax3.tick_params(axis='x', rotation=45)
    
    for bar, val in zip(bars3, trade_counts):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + max(1, height * 0.02),
                f'{val}', ha='center', va='bottom', fontweight='bold')
    
    # 夏普比率对比
    ax4 = axes[1, 1]
    bars4 = ax4.bar(strategies, sharpe_ratios, color=colors[:len(strategies)])
    ax4.set_title('策略夏普比率对比', fontweight='bold')
    ax4.set_ylabel('夏普比率')
    ax4.tick_params(axis='x', rotation=45)
    
    for bar, val in zip(bars4, sharpe_ratios):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + max(0.01, abs(height) * 0.02),
                f'{val:.2f}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('strategy_performance_comparison.png', dpi=300, bbox_inches='tight')
    print("📊 策略性能对比图已保存为: strategy_performance_comparison.png")
    plt.show()

def create_equity_curves_chart(all_results):
    """创建资金曲线图（不包含买入卖出标注）"""
    fig, ax = plt.subplots(figsize=(15, 8))
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
    color_idx = 0
    
    for timeframe, results in all_results.items():
        for result in results:
            if len(result['total_assets']) > 0:
                # 生成时间轴
                time_points = pd.date_range(
                    start=datetime.now() - timedelta(days=180),
                    periods=len(result['total_assets']),
                    freq='H'
                )
                
                # 绘制资金曲线（仅显示资金变化，不标注交易点）
                ax.plot(time_points, result['total_assets'], 
                       label=f"{result['strategy_name']} ({result['timeframe']})",
                       color=colors[color_idx % len(colors)], linewidth=2, alpha=0.8)
                color_idx += 1
    
    ax.set_title('策略资金曲线对比', fontsize=16, fontweight='bold')
    ax.set_xlabel('时间')
    ax.set_ylabel('资金 (USDT)')
    ax.grid(True, alpha=0.3)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # 添加初始资金线
    ax.axhline(y=1000, color='black', linestyle='--', alpha=0.5, label='初始资金')
    
    plt.tight_layout()
    plt.savefig('equity_curves_comparison.png', dpi=300, bbox_inches='tight')
    print("📊 资金曲线图已保存为: equity_curves_comparison.png（不包含买入卖出标注）")
    plt.show()

def create_equity_curves_with_kline(all_results, kline_data=None, symbol="BTCUSDT"):
    """创建带有K线数据的资金曲线图（不包含买入卖出标注）"""
    if kline_data is None:
        print("⚠ 未提供K线数据，使用标准资金曲线图")
        create_equity_curves_chart(all_results)
        return
    
    # 创建子图：上方显示K线，下方显示资金曲线
    # 注意：此图表不包含买入卖出点的标注，只显示价格走势和资金曲线
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12), height_ratios=[2, 1])
    
    # 上方子图：绘制K线图（不标注交易点）
    ax1.set_title(f'{symbol} 价格走势 (K线图)', fontsize=14, fontweight='bold')
    
    # 如果K线数据太多，进行采样以提高显示效果
    if len(kline_data) > 1000:
        # 每10个数据点取1个，减少显示密度
        sample_interval = len(kline_data) // 1000
        kline_sample = kline_data.iloc[::sample_interval]
        print(f"📊 K线数据采样: 从 {len(kline_data)} 条数据采样到 {len(kline_sample)} 条")
    else:
        kline_sample = kline_data
    
    # 绘制K线图（仅显示价格走势，不标注买入卖出点）
    for i in range(len(kline_sample)):
        # 获取当前K线数据
        open_price = kline_sample.iloc[i]['open']
        high_price = kline_sample.iloc[i]['high']
        low_price = kline_sample.iloc[i]['low']
        close_price = kline_sample.iloc[i]['close']
        current_time = kline_sample.index[i]
        
        # 确定K线颜色（红涨绿跌）
        if close_price >= open_price:
            color = '#FF4444'  # 红色，上涨
            body_color = '#FF6666'
        else:
            color = '#44FF44'  # 绿色，下跌
            body_color = '#66FF66'
        
        # 绘制影线（最高价到最低价）
        ax1.plot([current_time, current_time], [low_price, high_price], 
                color=color, linewidth=1)
        
        # 绘制实体（开盘价到收盘价）
        body_height = abs(close_price - open_price)
        if body_height > 0:
            ax1.bar(current_time, body_height, bottom=min(open_price, close_price),
                   color=body_color, width=pd.Timedelta(hours=0.8), alpha=0.8)
    
    ax1.set_ylabel('价格 (USDT)')
    ax1.grid(True, alpha=0.3)
    
    # 下方子图：绘制资金曲线（不标注买入卖出点）
    ax2.set_title(f'{symbol} 策略资金曲线对比', fontsize=14, fontweight='bold')
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
    color_idx = 0
    
    for timeframe, results in all_results.items():
        for result in results:
            if len(result['total_assets']) > 0:
                # 生成时间轴
                time_points = pd.date_range(
                    start=kline_data.index[0],
                    periods=len(result['total_assets']),
                    freq='H'
                )
                
                # 绘制资金曲线（仅显示资金变化，不标注交易点）
                ax2.plot(time_points, result['total_assets'], 
                       label=f"{result['strategy_name']} ({result['timeframe']})",
                       color=colors[color_idx % len(colors)], linewidth=2, alpha=0.8)
                color_idx += 1
    
    ax2.set_xlabel('时间')
    ax2.set_ylabel('资金 (USDT)')
    ax2.grid(True, alpha=0.3)
    ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # 添加初始资金线
    ax2.axhline(y=1000, color='black', linestyle='--', alpha=0.5, label='初始资金')
    
    # 同步两个子图的x轴
    ax1.set_xlim(kline_data.index[0], kline_data.index[-1])
    ax2.set_xlim(kline_data.index[0], kline_data.index[-1])
    
    plt.tight_layout()
    plt.savefig('equity_curves_with_kline.png', dpi=300, bbox_inches='tight')
    print("📊 带K线数据的资金曲线图已保存为: equity_curves_with_kline.png（不包含买入卖出标注）")
    plt.show()





def main():
    """主函数 - 回测所有策略，1小时框架"""
    print("🚀 开始量化交易策略回测 - 1小时时间框架")
    print("=" * 80)
    
    # 加载和处理数据
    features, kline_data = load_and_process_data()
    if features is None:
        print("❌ 数据加载失败，程序退出")
        return
    
    # 获取交易对信息
    data_loader = DataLoader(timeframe="1h")
    symbol = data_loader.symbol
    
    # 定义策略
    strategies = define_strategies()
    
    print("\n🔄 开始1小时时间框架回测...")
    
    # 运行1小时时间框架回测
    all_results = run_multi_timeframe_backtest(features, strategies)
    
    # 运行风险控制测试
    risk_test_results = run_risk_control_tests(features, strategies)
    
    # 生成综合报告
    generate_comprehensive_report(all_results, risk_test_results)
    
    # 创建分析图表
    create_analysis_charts(all_results, risk_test_results, kline_data, symbol)
    
    print("\n✅ 1小时时间框架回测完成!")

if __name__ == "__main__":
    main()