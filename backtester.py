# -*- coding: utf-8 -*-
# backtester.py
import pandas as pd
from dotenv import load_dotenv
import os
load_dotenv()
LEVERAGE = int(os.getenv("LEVERAGE", "2"))  # 提高杠杆到2倍
STOP_LOSS_RATIO = float(os.getenv("STOP_LOSS_RATIO", "0.05"))  # 提高止损比例到5%

class Backtester:
    def __init__(self):
        self.leverage = LEVERAGE
        self.stop_loss_ratio = STOP_LOSS_RATIO
        self.trading_fee = 0.0006  # Binance 手续费率（0.06%）
        
        # 初始化回测状态
        self.initial_cash = 1000  # 初始资金 10000 USDT
        self.cash = self.initial_cash
        self.position = 0  # 当前仓位：1=多仓，-1=空仓，0=无仓
        self.entry_price = 0  # 开仓价格
        self.position_value = 0  # 开仓时的仓位价值
        self.total_assets = [self.initial_cash]  # 总资产记录
        self.trade_log = []  # 交易日志
        self.strategy = None  # 策略对象
        
        # 动态止损相关
        self.highest_price = 0  # 多仓最高价
        self.lowest_price = float('inf')  # 空仓最低价
        self.trailing_stop_ratio = 0.05  # 追踪止损比例 5%（更宽松）
        
        # 仓位管理 - 更激进的设置
        self.max_position_ratio = 0.7  # 最大仓位比例 70%
        self.min_position_ratio = 0.3  # 最小仓位比例 30%
        
        # 连续亏损控制
        self.consecutive_losses = 0
        self.max_consecutive_losses = 3  # 最大连续亏损次数
        self.position_size_multiplier = 1.0  # 仓位大小倍数
    
    def calculate_position_value(self):
        """计算当前仓位价值（考虑杠杆和动态仓位管理）"""
        # 始终使用初始资金作为基准，确保仓位大小合理
        base_position = self.initial_cash * self.leverage * self.max_position_ratio
        # 根据连续亏损调整仓位大小
        adjusted_position = base_position * self.position_size_multiplier
        
        # 添加边界检查，防止数值溢出
        if adjusted_position > 50000:  # 限制最大仓位价值为5万
            adjusted_position = 50000
        elif adjusted_position < 1000:  # 最小仓位价值为1000
            adjusted_position = 1000
            
        return adjusted_position
    
    def update_position_multiplier(self, pnl):
        """根据盈亏更新仓位倍数"""
        if pnl < 0:  # 亏损
            self.consecutive_losses += 1
            if self.consecutive_losses >= self.max_consecutive_losses:
                self.position_size_multiplier = max(0.3, self.position_size_multiplier * 0.7)
        else:  # 盈利
            self.consecutive_losses = 0
            self.position_size_multiplier = min(1.1, self.position_size_multiplier * 1.05)
    
    def open_position(self, signal, price, current_time=None, timeframe="1h"):
        """开仓：根据信号做多/做空"""
        if self.position != 0:
            return  # 已有仓位则不重复开仓
        
        # 验证价格和信号
        if price <= 0 or signal not in [1, -1]:
            print(f"⚠️ 无效的开仓信号或价格: signal={signal}, price={price}")
            return
        
        position_value = self.calculate_position_value()
        
        # 添加边界检查
        if position_value <= 0:
            print(f"⚠️ 无效的仓位价值: {position_value}")
            return
            
        # 验证现金是否足够支付手续费
        fee = position_value * self.trading_fee
        if self.cash < fee:
            print(f"⚠️ 现金不足支付手续费: 现金={self.cash:.2f}, 手续费={fee:.2f}")
            return
            
        self.position = signal  # 1=多，-1=空
        self.entry_price = price
        self.position_value = position_value  # 记录开仓时的仓位价值
        
        # 初始化动态止损价格
        if signal == 1:  # 多仓
            self.highest_price = price
            self.lowest_price = float('inf')
        else:  # 空仓
            self.lowest_price = price
            self.highest_price = 0
        
        # 扣除开仓手续费
        self.cash -= fee
        
        # 确保现金不为负数
        if self.cash < 0:
            self.cash = 0
        
        # 格式化时间显示
        time_str = current_time.strftime("%Y-%m-%d %H:%M") if current_time else "N/A"
        
        # 记录详细的开仓日志
        action = "开多" if signal == 1 else "开空"
        print(f"📈 [{time_str}] {action} | 价格: {price:.2f} | 仓位价值: {position_value:.2f} | 现金: {self.cash:.2f} | 倍数: {self.position_size_multiplier:.2f} | 时间级别: {timeframe}")
            
        self.trade_log.append({
            "date": current_time,
            "action": action,
            "price": price,
            "cash": self.cash,
            "position_size": position_value,
            "multiplier": self.position_size_multiplier,
            "timeframe": timeframe
        })
    
    def close_position(self, price, reason="信号平仓", current_time=None, timeframe="1h"):
        """平仓：计算盈亏并更新资金"""
        if self.position == 0:
            return
        
        # 验证价格
        if price <= 0:
            print(f"⚠️ 无效的平仓价格: {price}")
            return
        
        # 使用开仓时记录的仓位价值
        position_value = self.position_value
        
        # 添加边界检查
        if position_value <= 0 or self.entry_price <= 0:
            print(f"⚠️ 无效的仓位数据: position_value={position_value}, entry_price={self.entry_price}")
            # 重置仓位状态
            self.position = 0
            self.entry_price = 0
            self.position_value = 0
            self.highest_price = 0
            self.lowest_price = float('inf')
            return
            
        # 计算盈亏：多仓=（平仓价-开仓价）/开仓价 * 仓位价值；空仓相反
        pnl = position_value * (price / self.entry_price - 1) * self.position
        
        # 限制盈亏范围，防止数值溢出
        max_pnl = position_value * 0.5  # 最大盈亏为仓位价值的50%
        if pnl > max_pnl:
            pnl = max_pnl
        elif pnl < -max_pnl:
            pnl = -max_pnl
        
        # 扣除平仓手续费
        fee = position_value * self.trading_fee
        self.cash += pnl - fee
        
        # 确保现金不为负数
        if self.cash < 0:
            self.cash = 0
        
        # 更新仓位倍数
        self.update_position_multiplier(pnl)
        
        # 格式化时间显示
        time_str = current_time.strftime("%Y-%m-%d %H:%M") if current_time else "N/A"
        
        # 记录详细的平仓日志
        action = "平多" if self.position == 1 else "平空"
        pnl_percent = (pnl / position_value) * 100
        profit_loss = "盈利" if pnl > 0 else "亏损"
        
        print(f"📉 [{time_str}] {action} | 价格: {price:.2f} | 盈亏: {pnl:.2f} ({pnl_percent:+.2f}%) | {profit_loss} | 现金: {self.cash:.2f} | 原因: {reason} | 时间级别: {timeframe}")
        
        # 记录交易日志
        self.trade_log.append({
            "date": current_time,
            "action": action,
            "price": price,
            "pnl": pnl,
            "pnl_percent": pnl_percent,
            "cash": self.cash,
            "reason": reason,
            "consecutive_losses": self.consecutive_losses,
            "multiplier": self.position_size_multiplier
        })
        
        # 重置仓位状态
        self.position = 0
        self.entry_price = 0
        self.position_value = 0
        self.highest_price = 0
        self.lowest_price = float('inf')
    
    def check_stop_loss(self, current_price, current_time=None, timeframe="1h"):
        """检查是否触发止损（包括固定止损和追踪止损）"""
        if self.position == 0:
            return
        
        # 更新最高/最低价
        if self.position == 1:  # 多仓
            self.highest_price = max(self.highest_price, current_price)
        else:  # 空仓
            self.lowest_price = min(self.lowest_price, current_price)
        
        # 检查固定止损
        if self.position == 1:  # 多仓：(当前价-开仓价)/开仓价 < -止损比例
            loss_ratio = (current_price - self.entry_price) / self.entry_price
        else:  # 空仓：(开仓价-当前价)/开仓价 < -止损比例（即当前价涨超止损）
            loss_ratio = (self.entry_price - current_price) / self.entry_price
        
        if loss_ratio < -self.stop_loss_ratio:
            self.close_position(current_price, reason="固定止损平仓", current_time=current_time, timeframe=timeframe)
            return
        
        # 检查追踪止损
        if self.position == 1:  # 多仓：从最高价回撤超过追踪止损比例
            drawdown_ratio = (self.highest_price - current_price) / self.highest_price
            if drawdown_ratio > self.trailing_stop_ratio:
                self.close_position(current_price, reason="追踪止损平仓", current_time=current_time, timeframe=timeframe)
        else:  # 空仓：从最低价反弹超过追踪止损比例
            bounce_ratio = (current_price - self.lowest_price) / self.lowest_price
            if bounce_ratio > self.trailing_stop_ratio:
                self.close_position(current_price, reason="追踪止损平仓", current_time=current_time, timeframe=timeframe)
    
    def check_take_profit(self, current_price, current_time=None, timeframe="1h", features=None):
        """检查是否触发止盈"""
        if self.position == 0:
            return
        
        # 计算当前盈利比例
        if self.position == 1:  # 多仓
            profit_ratio = (current_price - self.entry_price) / self.entry_price
        else:  # 空仓
            profit_ratio = (self.entry_price - current_price) / self.entry_price
        
        # 动态止盈策略 - 根据策略类型选择不同的止盈水平
        if hasattr(self.strategy, 'get_dynamic_take_profit_levels'):
            # 使用动态止盈策略
            try:
                # 获取当前市场环境和趋势强度
                market_condition = 1  # 默认正常趋势
                trend_strength = 0   # 默认趋势强度
                
                # 如果有features数据，计算市场环境和趋势强度
                if features is not None and len(features) > 0:
                    # 计算市场环境
                    volatility_5h = features["close"].rolling(window=5).std().iloc[-1] / current_price
                    volatility_10h = features["close"].rolling(window=10).std().iloc[-1] / current_price
                    
                    if volatility_5h > 0.02 and volatility_10h > 0.015:
                        market_condition = 2  # 高波动
                    elif volatility_5h < 0.008 and volatility_10h < 0.01:
                        market_condition = 0  # 震荡
                    else:
                        market_condition = 1  # 正常趋势
                    
                    # 计算趋势强度
                    if len(features) >= 3:
                        current_close = features["close"].iloc[-1]
                        current_linewma = features["lineWMA"].iloc[-1]
                        current_openema = features["openEMA"].iloc[-1]
                        current_closeema = features["closeEMA"].iloc[-1]
                        
                        trend_strength = 0
                        if current_close > current_linewma: trend_strength += 1
                        if current_close > current_openema: trend_strength += 1
                        if current_close > current_closeema: trend_strength += 1
                        
                        if current_linewma > current_openema > current_closeema:
                            trend_strength += 2
                        elif current_linewma < current_openema < current_closeema:
                            trend_strength -= 2
                
                take_profit_levels = self.strategy.get_dynamic_take_profit_levels(
                    features, market_condition, trend_strength
                )
                
                # 优化动态止盈逻辑 - 提高收益潜力
                if profit_ratio >= take_profit_levels.get("full", 0.15):  # 提高完全止盈阈值到15%
                    self.partial_close_position(current_price, 1.0, "完全止盈", current_time, timeframe)
                elif profit_ratio >= take_profit_levels.get("partial_2", 0.10):  # 提高第二次部分止盈阈值到10%
                    self.partial_close_position(current_price, 0.5, "部分止盈", current_time, timeframe)
                elif profit_ratio >= take_profit_levels.get("partial_1", 0.06):  # 提高第一次部分止盈阈值到6%
                    self.partial_close_position(current_price, 0.3, "部分止盈", current_time, timeframe)
                    
            except Exception as e:
                # 如果动态止盈失败，回退到固定止盈
                if profit_ratio >= 0.12:  # 提高盈利阈值到12%，平仓50%
                    self.partial_close_position(current_price, 0.5, "部分止盈", current_time, timeframe)
                elif profit_ratio >= 0.06:  # 提高盈利阈值到6%，平仓30%
                    self.partial_close_position(current_price, 0.3, "部分止盈", current_time, timeframe)
        else:
            # 使用固定止盈策略
            if profit_ratio >= 0.12:  # 提高盈利阈值到12%，平仓50%
                self.partial_close_position(current_price, 0.5, "部分止盈", current_time, timeframe)
            elif profit_ratio >= 0.06:  # 提高盈利阈值到6%，平仓30%
                self.partial_close_position(current_price, 0.3, "部分止盈", current_time, timeframe)
    
    def partial_close_position(self, price, close_ratio, reason, current_time=None, timeframe="1h"):
        """部分平仓"""
        if self.position == 0:
            return
        
        # 验证价格和比例
        if price <= 0 or close_ratio <= 0 or close_ratio > 1:
            print(f"⚠️ 无效的部分平仓参数: price={price}, close_ratio={close_ratio}")
            return
        
        # 使用当前剩余的仓位价值
        current_position_value = self.position_value
        
        # 验证仓位价值
        if current_position_value <= 0:
            print(f"⚠️ 无效的当前仓位价值: {current_position_value}")
            return
            
        partial_value = current_position_value * close_ratio
        
        # 添加边界检查
        if partial_value <= 0:
            print(f"⚠️ 无效的部分平仓价值: {partial_value}")
            return
            
        # 计算部分盈亏
        pnl = partial_value * (price / self.entry_price - 1) * self.position
        
        # 限制盈亏范围，防止数值溢出
        max_pnl = partial_value * 0.5  # 最大盈亏为部分仓位价值的50%
        if pnl > max_pnl:
            pnl = max_pnl
        elif pnl < -max_pnl:
            pnl = -max_pnl
        
        # 扣除平仓手续费
        fee = partial_value * self.trading_fee
        self.cash += pnl - fee
        
        # 确保现金不为负数
        if self.cash < 0:
            self.cash = 0
        
        # 更新剩余仓位价值
        self.position_value = current_position_value - partial_value
        
        # 如果剩余仓位价值太小，则完全平仓
        if self.position_value < 100:  # 小于100则完全平仓
            remaining_pnl = self.position_value * (price / self.entry_price - 1) * self.position
            remaining_fee = self.position_value * self.trading_fee
            self.cash += remaining_pnl - remaining_fee
            self.position_value = 0
            self.position = 0
            self.entry_price = 0
            self.highest_price = 0
            self.lowest_price = float('inf')
        
        # 更新仓位倍数
        self.update_position_multiplier(pnl)
        
        # 格式化时间显示
        time_str = current_time.strftime("%Y-%m-%d %H:%M") if current_time else "N/A"
        
        # 记录部分平仓日志
        action = f"部分平多({close_ratio*100:.0f}%)" if self.position == 1 else f"部分平空({close_ratio*100:.0f}%)"
        pnl_percent = (pnl / partial_value) * 100
        profit_loss = "盈利" if pnl > 0 else "亏损"
        
        print(f"📊 [{time_str}] {action} | 价格: {price:.2f} | 盈亏: {pnl:.2f} ({pnl_percent:+.2f}%) | {profit_loss} | 现金: {self.cash:.2f} | 原因: {reason} | 时间级别: {timeframe}")
        
        # 记录交易日志
        self.trade_log.append({
            "date": current_time,
            "action": action,
            "price": price,
            "pnl": pnl,
            "pnl_percent": pnl_percent,
            "cash": self.cash,
            "reason": reason,
            "consecutive_losses": self.consecutive_losses,
            "multiplier": self.position_size_multiplier,
            "timeframe": timeframe
        })
    
    def run_backtest(self, features, timeframe="1h"):
        """运行回测：遍历 K 线，根据信号交易"""
        print(f"\n🔄 开始回测，共 {len(features)} 条数据...")
        print("=" * 80)
        
        # 添加数据验证
        if len(features) < 50:
            print("⚠️ 数据量过少，可能影响回测准确性")
            return None
        
        # 重置回测状态
        self.cash = self.initial_cash
        self.position = 0
        self.entry_price = 0
        self.position_value = 0
        self.total_assets = [self.initial_cash]
        self.trade_log = []
        self.highest_price = 0
        self.lowest_price = float('inf')
        self.consecutive_losses = 0
        self.position_size_multiplier = 1.0
        
        # 添加交易频率控制
        last_trade_time = None
        min_trade_interval = pd.Timedelta(hours=2)  # 最小交易间隔2小时（增加间隔）
        
        # 添加每日交易次数限制
        daily_trade_count = 0
        current_trade_date = None
        max_daily_trades = 3  # 每日最大交易次数限制
        
        for i in range(len(features)):
            # 使用历史数据生成信号（包括当前K线）
            current_data = features.iloc[:i+1]  # 从开始到当前K线
            current_price = features.iloc[i]["close"]  # 当前收盘价
            current_time = features.index[i]  # 当前时间索引
            
            # 验证价格数据
            if current_price <= 0 or pd.isna(current_price):
                print(f"⚠️ 跳过无效价格数据: {current_time}")
                continue
            
            # 检查止损和止盈（每个 K 线都要判断）
            self.check_stop_loss(current_price, current_time, timeframe)
            self.check_take_profit(current_price, current_time, timeframe, current_data)
            
            # 生成信号并执行交易（只在有信号且无仓位时开仓）
            if self.strategy and len(current_data) >= 20:  # 增加最小数据要求
                signal_result = self.strategy.get_signal(current_data)
                
                # 处理信号结果 - 可能是字典或简单值
                if isinstance(signal_result, dict):
                    signal = signal_result.get('signal', 0)
                else:
                    signal = signal_result
                
                # 添加交易频率控制
                can_trade = True
                
                # 检查时间间隔
                if last_trade_time is not None:
                    time_since_last_trade = current_time - last_trade_time
                    if time_since_last_trade < min_trade_interval:
                        can_trade = False
                
                # 检查每日交易次数限制
                if current_trade_date is None or current_time.date() != current_trade_date:
                    daily_trade_count = 0
                    current_trade_date = current_time.date()
                
                if daily_trade_count >= max_daily_trades:
                    can_trade = False
                
                # 检查现金是否足够
                position_value = self.calculate_position_value()
                fee = position_value * self.trading_fee
                if self.cash < fee * 2:  # 确保有足够现金支付至少2次交易的手续费
                    can_trade = False
                
                if signal != 0 and self.position == 0 and can_trade:
                    self.open_position(signal, current_price, current_time, timeframe)
                    last_trade_time = current_time
                    daily_trade_count += 1
            
            # 记录总资产（现金 + 未平仓浮盈）
            if self.position != 0:
                # 计算未平仓浮盈
                unrealized_pnl = self.calculate_position_value() * (current_price / self.entry_price - 1) * self.position
                
                # 限制浮盈范围，防止数值溢出
                max_unrealized = self.calculate_position_value() * 0.5  # 最大浮盈为仓位价值的50%
                if unrealized_pnl > max_unrealized:
                    unrealized_pnl = max_unrealized
                elif unrealized_pnl < -max_unrealized:
                    unrealized_pnl = -max_unrealized
                    
                total = self.cash + unrealized_pnl
            else:
                total = self.cash
                
            # 限制总资产范围，防止异常值
            if total > 1e6:  # 限制最大总资产为100万
                total = 1e6
            elif total < 0:
                total = 0
                
            self.total_assets.append(total)
        
        # 回测结束后平掉所有仓位
        if self.position != 0:
            final_price = features["close"].iloc[-1]
            if final_price > 0:
                self.close_position(final_price, reason="回测结束平仓", current_time=features.index[-1], timeframe=timeframe)
        
        # 计算最终收益率
        final_cash = self.cash  # 使用实际最终资金
        return_ratio = (final_cash / self.initial_cash - 1) * 100
        
        # 限制收益率范围，防止异常值
        if return_ratio > 500:  # 限制最大收益率为500%
            return_ratio = 500
        elif return_ratio < -100:
            return_ratio = -100
        
        # 打印交易统计摘要
        print("\n" + "=" * 80)
        print("📊 交易统计摘要")
        print("=" * 80)
        trade_df = pd.DataFrame(self.trade_log)
        
        # 初始化变量
        total_trades = 0
        win_rate = 0
        profit_loss_ratio = 0
        
        if len(trade_df) > 0:
            profitable_trades = trade_df[trade_df['pnl'] > 0] if 'pnl' in trade_df.columns else pd.DataFrame()
            loss_trades = trade_df[trade_df['pnl'] < 0] if 'pnl' in trade_df.columns else pd.DataFrame()
            
            total_trades = len(profitable_trades) + len(loss_trades)
            win_rate = len(profitable_trades) / total_trades * 100 if total_trades > 0 else 0
            avg_profit = profitable_trades['pnl'].mean() if len(profitable_trades) > 0 else 0
            avg_loss = loss_trades['pnl'].mean() if len(loss_trades) > 0 else 0
            profit_loss_ratio = abs(avg_profit / avg_loss) if avg_loss != 0 else 0
            
            print(f"总交易次数: {total_trades}")
            print(f"盈利交易: {len(profitable_trades)} 次")
            print(f"亏损交易: {len(loss_trades)} 次")
            print(f"胜率: {win_rate:.1f}%")
            print(f"平均盈利: {avg_profit:.2f}")
            print(f"平均亏损: {avg_loss:.2f}")
            print(f"盈亏比: {profit_loss_ratio:.2f}")
            
            # 添加交易频率分析
            if total_trades > 0:
                trading_days = (features.index[-1] - features.index[0]).days
                trades_per_day = total_trades / max(trading_days, 1)
                print(f"平均每日交易次数: {trades_per_day:.2f}")
                
                if trades_per_day > 2:
                    print("⚠️ 交易频率过高，可能存在过度交易")
        print("=" * 80)
        
        return {
            "total_assets": self.total_assets,
            "trade_log": pd.DataFrame(self.trade_log),
            "final_cash": final_cash,
            "return_ratio": return_ratio,  # 总收益率（%）
            "total_trades": total_trades,
            "win_rate": win_rate,
            "profit_loss_ratio": profit_loss_ratio,
            "timeframe": timeframe
        }