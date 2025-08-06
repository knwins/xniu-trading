# 🚀 智能量化交易系统

> 安全、简单、高效的量化交易平台

## 📋 项目简介

本项目是一个完整的智能量化交易系统，支持币安期货交易，提供安全的小额交易测试环境，适合新手学习和功能验证。

### ✨ 核心特性
- 🛡️ **安全交易**: 小额测试，严格风控
- 📊 **实时监控**: 详细记录，状态跟踪  
- 🔧 **易于部署**: 一键部署，简化配置
- 📈 **功能完整**: 策略回测，实盘交易

---

## 🚀 快速开始

### 🎯 5分钟快速部署
```bash
# 1. 上传简化部署脚本
scp simple_deploy.sh user@your-server-ip:/home/user/

# 2. 执行部署
ssh user@your-server-ip
chmod +x simple_deploy.sh
./simple_deploy.sh

# 3. 配置API密钥
nano /opt/quant-trading/trading_config.json

# 4. 上传源代码
scp trader.py strategy.py data_loader.py main.py user@your-server-ip:/opt/quant-trading/src/

# 5. 启动系统
sudo systemctl start quant-trading
```

### 🧪 本地测试
```bash
# 演示测试（推荐新手）
python demo_small_trade.py

# API连接诊断
python test_api_connection.py

# 完整功能测试
python test_small_trades.py
```

---

## 📁 项目结构

```
xniu-trading/
├── 📄 文档文件
│   ├── 量化交易系统完整部署指南.md    # 详细部署指南
│   ├── 快速部署指南.md              # 5分钟快速部署
│   ├── 目录结构说明.md              # 项目结构详解
│   ├── API_TROUBLESHOOTING.md      # API故障排除
│   ├── README.md                   # 项目说明
│   └── README_TRADING.md           # 交易系统说明
├── 🔧 部署脚本
│   ├── centos_setup.sh            # 完整部署脚本
│   └── simple_deploy.sh           # 简化部署脚本
├── ⚙️ 配置文件
│   ├── trading_config.json        # 实盘交易配置
│   ├── small_trade_config.json    # 小额测试配置
│   └── requirements.txt           # Python依赖
├── 💻 源代码
│   ├── main.py                    # 主程序入口
│   ├── trader.py                  # 交易核心模块
│   ├── strategy.py                # 交易策略模块
│   ├── data_loader.py             # 数据加载模块
│   ├── backtester.py              # 回测系统
│   ├── feature_engineer.py        # 特征工程
│   └── version_control.py         # 版本控制
├── 🧪 测试文件
│   ├── test_api_connection.py     # API连接测试
│   ├── test_small_trades.py       # 小额交易测试
│   ├── demo_small_trade.py        # 演示交易
│   └── check.py                   # 系统检查
└── 📋 版本控制
    ├── VERSION                    # 版本号
    ├── version.json               # 版本信息
    └── 版本控制简化说明.md          # 版本控制说明
```

---

## ⚙️ 配置说明

### 演示版配置
```python
initial_balance = 1000.0  # 初始资金
max_position_size = 0.1   # 最大仓位10%
stop_loss_pct = 0.05      # 止损5%
take_profit_pct = 0.1     # 止盈10%
```

### 小额测试配置
```python
initial_balance = 100.0   # 初始资金
max_position_size = 0.05  # 最大仓位5%
stop_loss_pct = 0.02      # 止损2%
take_profit_pct = 0.05    # 止盈5%
max_daily_loss = 0.05     # 日亏损限制5%
max_drawdown = 0.1        # 最大回撤10%
```

---

## 🛡️ 安全特性

### 风险控制
- **小额交易**: 最大仓位5%，最小交易10 USDT
- **严格风控**: 日亏损限制5%，最大回撤10%
- **精确计算**: 6位小数精度
- **实时监控**: 详细交易记录

### 监控功能
- 当前价格显示
- 仓位状态监控
- 浮动盈亏计算
- 交易统计（次数、胜率）
- 余额变化跟踪

---

## 📊 使用流程

### 基本测试流程
```bash
# 1. 启动演示测试器
python demo_small_trade.py

# 2. 查看状态 → 选择: 1
# 3. 小额买入 → 选择: 2，输入: 10
# 4. 查看状态 → 选择: 1  
# 5. 平仓测试 → 选择: 4
# 6. 查看结果 → 选择: 1
# 7. 退出系统 → 选择: 6
```

### 进阶测试流程
```bash
# 1. 启动完整测试器
python test_small_trades.py

# 2. 查看初始状态 → 选择: 1
# 3. 自定义买入 → 选择: 2，输入: 20
# 4. 查看状态 → 选择: 1
# 5. 自定义卖出 → 选择: 3，输入: 15
# 6. 平仓 → 选择: 4
# 7. 保存历史 → 选择: 5
# 8. 查看结果 → 选择: 1
# 9. 退出系统 → 选择: 6
```

---

## 🔧 故障排除

### 常见问题

| 问题 | 解决方案 |
|------|----------|
| API连接失败 | 检查API密钥，确认网络稳定 |
| 下单失败 | 检查账户余额，确认交易对正确 |
| 价格获取失败 | 检查网络连接，确认API接口正常 |

### API密钥配置
1. **登录币安账户**
2. **生成API密钥**
   - 进入API管理页面
   - 创建新的API密钥
   - 只启用交易权限（不要启用提现权限）
   - 设置IP白名单（可选）

3. **更新配置文件**
```json
{
  "api_key": "你的新API密钥",
  "secret_key": "你的新密钥", 
  "symbol": "ETHUSDT",
  "initial_balance": 100.0,
  "max_position_size": 0.05
}
```

---

## 📁 日志管理

### 日志文件
- `trading.log` - 实盘交易日志
- `test_small_trades.log` - 小额交易测试日志
- `demo_trade.log` - 演示交易日志
- `demo_trades_history_*.json` - 演示交易历史数据

### 查看日志
```bash
# 查看最新日志
tail -f logs/trading.log

# 查看错误日志
grep "ERROR" logs/trading.log
```

---

## 🔒 安全建议

### ⚠️ 重要提醒
1. **小额测试**: 建议使用10-50 USDT进行测试
2. **实时监控**: 密切关注交易状态和盈亏
3. **及时平仓**: 测试完成后及时平仓
4. **备份配置**: 测试前备份重要配置文件

### 🔒 安全措施
1. **API权限**: 确保API只有交易权限，无提现权限
2. **资金限制**: 使用小额资金进行测试
3. **网络稳定**: 确保网络连接稳定
4. **日志记录**: 所有交易都会记录到日志文件

---

## 🎯 版本控制

### 快速使用
```bash
# 查看当前状态
python version_control.py

# 更新版本号
python version_control.py  # 选择选项 2

# 更新所有文件  
python version_control.py  # 选择选项 3
```

### 核心文件
- `VERSION` - 版本号存储
- `version.json` - 版本信息
- `version_control.py` - 统一管理工具

---

## 📈 使用场景

### 1. 新手学习
- 使用演示版本熟悉界面
- 了解交易流程
- 学习风险控制

### 2. 功能验证
- 测试买入卖出功能
- 验证风控机制
- 检查API连接

### 3. 小额实践
- 真实小额交易练习
- 积累交易经验
- 测试策略效果

---

## 📞 技术支持

如遇到问题，请检查：
1. 系统日志: `tail -f logs/trading.log`
2. 演示测试: `python demo_small_trade.py`
3. API测试: `python test_api_connection.py`
4. 完整测试: `python test_small_trades.py`

**注意**: 本系统仅供学习和测试使用，请谨慎进行真实交易。

---

## 📝 更新日志

### v1.0.1 (2025-08-06)
- 初始版本发布
- 完整的小额交易测试系统
- 演示版和完整版测试工具
- API连接诊断功能
- 统一时区配置 (香港时区)
- 简化版本控制系统
- 整合小额交易测试指南

---

**智能量化交易系统 v1.0.1** - 安全、简单、高效的交易测试平台 