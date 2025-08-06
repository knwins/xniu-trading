# XNIU.IO 智能量化交易系统

[![Python](https://img.shields.io/badge/Python-3.6+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Binance-orange.svg)](https://www.binance.com/)

## 🚀 项目概述

XNIU.IO 是一个基于保守回撤控制策略的智能量化交易系统，专为 Binance 期货交易设计。系统采用先进的机器学习算法和风险管理机制，提供稳定可靠的自动化交易解决方案。

### ✨ 核心特性

- **🎯 智能策略**: 基于保守回撤控制策略，回测收益率 160.67%，胜率 70.0%
- **🛡️ 风险控制**: 多层次风险管理，包括止损、止盈、最大回撤控制
- **📊 实时监控**: 实时数据获取、信号生成、交易执行
- **🔧 灵活配置**: 支持多种参数配置，适应不同市场环境
- **📈 性能优化**: 高效的数据处理和算法实现
- **🔒 安全可靠**: 完善的API验证和错误处理机制

### 📋 功能模块

- **数据获取**: 实时从 Binance API 获取市场数据
- **特征工程**: 计算技术指标和特征数据
- **信号生成**: 基于机器学习模型生成交易信号
- **风险管理**: 多层次风险控制机制
- **交易执行**: 自动下单和平仓
- **监控报告**: 实时状态监控和交易报告

## 🎯 快速开始

### 系统要求

- **操作系统**: CentOS 7/8 或 RHEL 7/8
- **Python**: 3.6 或更高版本
- **内存**: 4GB 以上
- **网络**: 稳定的互联网连接

### 安装步骤

#### 1. 克隆项目
```bash
git clone https://github.com/knwins/xniu-trading.git
cd xniu-trading
```

#### 2. 安装依赖
```bash
pip install -r requirements.txt
```

#### 3. 配置API密钥
编辑 `trader_config.json` 文件，配置您的 Binance API 密钥：
```json
{
  "api_key": "your-binance-api-key",
  "secret_key": "your-binance-secret-key",
  "symbol": "ETHUSDT",
  "initial_balance": 1000.0
}
```

#### 4. 启动系统
```bash
python start_trading.py
```

## 🖥️ 部署选项

### CentOS服务器部署（推荐）
- 生产环境部署
- 完整监控和备份
- 系统服务集成

详细部署指南请参考：[部署文档](README_DEPLOYMENT.md)

## 📊 配置说明

### 交易参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `symbol` | 交易对 | ETHUSDT |
| `initial_balance` | 初始资金 | 1000.0 USDT |
| `max_position_size` | 最大仓位比例 | 10% |
| `stop_loss_pct` | 止损比例 | 5% |
| `take_profit_pct` | 止盈比例 | 10% |
| `max_daily_loss` | 最大日亏损 | 10% |
| `max_drawdown` | 最大回撤 | 20% |

### 风险控制

系统采用多层次风险控制机制：

1. **仓位控制**: 限制单次交易的最大仓位
2. **止损止盈**: 自动设置止损和止盈点位
3. **日亏损限制**: 防止单日过度亏损
4. **回撤控制**: 监控最大回撤，触发保护机制
5. **信号冷却**: 避免频繁交易

## 🔧 管理操作

### 基本命令

```bash
# 启动交易系统
python start_trading.py

# 查看配置
python start_trading.py --config

# 测试API连接
python start_trading.py --test-api
```

### 服务器部署管理

```bash
# 启动服务
/opt/xniu-trading/manage.sh start

# 查看状态
/opt/xniu-trading/manage.sh status

# 查看日志
/opt/xniu-trading/manage.sh logs

# 编辑配置
/opt/xniu-trading/manage.sh config
```

## 📈 监控和维护

### 日志监控

- **系统日志**: 记录系统运行状态
- **交易日志**: 记录所有交易操作
- **错误日志**: 记录异常和错误信息

### 性能监控

- **API连接状态**: 实时监控API连接
- **交易执行情况**: 监控交易成功率
- **系统资源使用**: 监控CPU、内存使用

### 备份策略

- **自动备份**: 每天自动备份配置和日志
- **手动备份**: 支持手动备份重要数据
- **恢复机制**: 提供数据恢复功能

## 🚨 故障排除

### 常见问题

1. **API连接失败**
   - 检查网络连接
   - 验证API密钥
   - 确认IP白名单设置

2. **服务启动失败**
   - 检查配置文件格式
   - 验证依赖安装
   - 查看错误日志

3. **交易执行异常**
   - 检查账户余额
   - 验证交易权限
   - 确认交易参数

### 获取帮助

- 📖 [部署文档](README_DEPLOYMENT.md)
- 🐛 [问题反馈](https://github.com/knwins/xniu-trading/issues)
- 📧 [技术支持](mailto:support@xniu.io)

## 🔒 安全建议

### API安全
- 使用最小权限原则
- 定期更换API密钥
- 设置IP白名单
- 监控API使用情况

### 系统安全
- 使用非root用户运行
- 配置防火墙规则
- 定期更新系统补丁
- 监控异常登录

### 数据安全
- 定期备份重要数据
- 加密敏感配置文件
- 限制文件访问权限
- 监控文件变化

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🤝 贡献

欢迎贡献代码！请查看 [贡献指南](CONTRIBUTING.md) 了解如何参与项目开发。

### 贡献方式

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📞 联系我们

- **官网**: [https://xniu.io](https://xniu.io)
- **邮箱**: support@xniu.io
- **GitHub**: [https://github.com/knwins/xniu-trading](https://github.com/knwins/xniu-trading)

## ⚠️ 免责声明

**重要提醒**: 

1. **风险提示**: 加密货币交易存在高风险，可能导致资金损失
2. **资金安全**: 只使用您能够承受损失的资金进行交易
3. **测试验证**: 建议先在测试环境验证系统功能
4. **定期维护**: 定期检查和维护系统，确保稳定运行
5. **法律合规**: 请确保您的交易活动符合当地法律法规

本软件仅供学习和研究使用，作者不对使用本软件造成的任何损失承担责任。

---

**版本**: v1.0  
**更新时间**: 2025-08-06  
**维护团队**: XNIU.IO Development Team 