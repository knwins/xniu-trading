# 🚀 Xniu-trading - 智能量化交易系统

一个基于Python的智能量化交易系统，集成了多种交易策略、风险管理和实盘交易功能。

## 📋 项目概述

本项目是一个完整的量化交易系统，包含以下核心功能：

- **多策略回测**: 支持多种交易策略的回测和性能分析
- **实时交易**: 基于币安API的实盘交易功能
- **风险管理**: 多层次风险控制机制
- **数据获取**: 自动获取和处理市场数据
- **特征工程**: 丰富的技术指标和特征计算
- **可视化分析**: 详细的图表和报告生成

## 🎯 策略表现

基于回测结果，系统包含以下策略：

1. **保守回撤控制策略**: 收益率 160.67%, 胜率 70.0%
2. **高频自适应止盈策略**: 高频交易，自适应止盈
3. **加强版稳健风险调整策略**: 稳健策略的加强版
4. **趋势跟踪风险管理策略**: 趋势跟踪结合风险管理

## 🛠️ 系统要求

- Python 3.7+
- 稳定的网络连接
- 币安账户和API密钥（实盘交易需要）
- 系统时区：香港时区 (Asia/Hong_Kong) - 通过 `server/centos_setup.sh` 统一配置

## 📦 安装依赖

```bash
pip install -r server/requirements.txt
```

## 🚀 快速开始

### 1. 回测模式

运行策略回测：

```bash
python main.py
```

这将执行完整的策略回测，包括：
- 数据加载和特征工程
- 多策略回测
- 风险控制测试
- 生成分析报告和图表

### 2. 实盘交易

启动实盘交易系统：

```bash
cd trade
python trade/start.py
```

或者直接运行：

```bash
cd trade
python trade/trader.py
```

### 3. 小额交易测试

运行小额交易测试：

```bash
cd trade
python test/test_small_trades.py
```

## 📁 项目结构

```
xniu-trading/
├── main.py                      # 主回测程序
├── strategy.py                  # 交易策略
├── data_loader.py              # 数据加载器
├── feature_engineer.py         # 特征工程
├── backtester.py              # 回测引擎
├── README.md                  # 项目说明
├── .gitignore                 # Git忽略文件
│
├── trade/                     # 实盘交易相关
│   ├── trader.py              # 实盘交易系统
│   ├── start.py               # 实盘交易启动脚本
│   └── README_TRADING.md      # 实盘交易指南
│
├── config/                    # 配置文件
│   ├── trading_config.json    # 实盘交易配置
│   └── small_trade_config.json # 小额交易测试配置
│
├── server/                    # 服务器部署
│   ├── centos_setup.sh       # 服务器设置脚本
│   ├── requirements.txt      # Python依赖
│   ├── 量化交易系统完整部署指南.md
│   └── API_TROUBLESHOOTING.md
│
├── test/                     # 测试相关
│   ├── test_small_trades.py   # 小额交易测试
│   ├── demo_small_trade.py    # 演示交易
│   ├── test_api_connection.py # API连接测试
│   └── 小额交易测试完整指南.md # 小额交易测试指南
│
├── version/                   # 版本控制
│   ├── info.py               # 版本管理脚本
│   ├── check.py              # 版本检查脚本
│   ├── info.json             # 版本信息配置
│   ├── CONTROL.md            # 版本控制说明
│   ├── 版本控制使用说明.md
│   ├── update_dates.py       # 日期更新
│   └── show_dates.py         # 显示日期
│
└── logs/                     # 日志文件目录
    ├── trading.log           # 实盘交易日志
    ├── test_small_trades.log # 小额交易测试日志
    ├── demo_trade.log        # 演示交易日志
    ├── demo_trades_history_*.json # 演示交易历史数据
    └── README.md             # 日志说明文档
```

## 🔧 核心模块

### 数据加载器 (data_loader.py)
- 从币安API获取K线数据
- 支持多个时间框架
- 自动重试和错误处理
- 模拟数据生成

### 特征工程 (feature_engineer.py)
- 技术指标计算（RSI, MACD, 布林带等）
- 风险指标计算（夏普比率, 索提诺比率等）
- 多维度特征提取

### 交易策略 (strategy.py)
- 高频自适应止盈策略
- 加强版稳健风险调整策略
- 保守回撤控制策略
- 趋势跟踪风险管理策略

### 回测引擎 (backtester.py)
- 完整的回测框架
- 动态止损止盈
- 仓位管理
- 交易记录

### 实盘交易 (trade/trader.py)
- 实时数据获取
- 自动交易执行
- 风险控制
- 资金管理

## ⚙️ 配置说明

### API配置
在 `config/trading_config.json` 中配置：

```json
{
  "api_key": "your_api_key",
  "secret_key": "your_secret_key",
  "symbol": "ETHUSDT",
  "initial_balance": 1000.0,
  "max_position_size": 0.1,
  "stop_loss_pct": 0.05,
  "take_profit_pct": 0.1,
  "max_daily_loss": 0.1,
  "max_drawdown": 0.2,
  "signal_cooldown": 300,
  "base_url": "https://fapi.binance.com"
}
```

### 环境变量
创建 `.env` 文件：

```
SYMBOL=BTCUSDT
RSI_PERIOD=14
LINEWMA_PERIOD=55
OPENEMA_PERIOD=25
CLOSEEMA_PERIOD=25
LEVERAGE=2
STOP_LOSS_RATIO=0.05
```

## 🔒 安全建议

1. **API安全**
   - 使用IP白名单限制API访问
   - 定期更换API密钥
   - 设置最小权限原则
   - 监控API调用频率

2. **网络安全**
   - 使用安全的网络连接
   - 定期更新系统
   - 使用VPN或专线连接

3. **数据安全**
   - 定期备份重要数据
   - 加密敏感配置文件
   - 监控异常访问
   - 使用安全的日志记录

## ⚠️ 风险提示

1. **实盘交易存在风险**，可能导致资金损失
2. **建议先用小额资金测试**，熟悉系统后再增加资金
3. **定期检查系统状态**，确保正常运行
4. **保持网络稳定**，避免断线影响交易
5. **遵守相关法律法规**和交易所规则
6. **定期检查日志**，及时发现和处理问题

## 📞 技术支持

如遇到问题，请：
1. 查看 `logs/` 目录中的日志文件
2. 检查 `config/` 目录中的配置参数
3. 确认网络连接
4. 参考 `server/API_TROUBLESHOOTING.md` 故障排除指南

## 🔧 版本控制

本项目使用统一的版本控制系统管理所有文档的版本号：

### 版本管理工具
- `cd version && python info.py` - 版本管理脚本
- `cd version && python check.py` - 版本一致性检查
- `version/info.json` - 版本信息配置
- `version/CONTROL.md` - 版本控制说明

### 快速检查
```bash
# 检查版本一致性
cd version
python check.py

# 更新版本号
cd version
python info.py
```

## 📝 更新日志

### v1.0.1 (2025-08-06)
- 初始版本发布
- 完整的回测和实盘交易功能
- 多种交易策略
- 风险控制机制
- 统一时区配置 (香港时区)
- 添加版本控制系统
- 重新组织项目结构，提高模块化程度

## 📄 许可证

本项目仅供学习和研究使用，不构成投资建议。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目。

---

**免责声明**: 本系统仅供学习和研究使用，不构成投资建议。实盘交易存在风险，请谨慎操作。 