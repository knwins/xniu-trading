# XNIU.IO 交易系统部署文档

## 📋 目录

- [系统概述](#系统概述)
- [CentOS服务器部署](#centos服务器部署)
- [配置说明](#配置说明)
- [管理操作](#管理操作)
- [监控维护](#监控维护)
- [故障排除](#故障排除)
- [安全建议](#安全建议)

## 🚀 系统概述

XNIU.IO 是一个基于保守回撤控制策略的智能量化交易系统，具有以下特点：

- **回测表现**: 收益率 160.67%, 胜率 70.0%
- **功能特点**: 实时数据获取、智能信号生成、风险管理控制、自动交易执行
- **支持平台**: Binance 期货交易
- **部署方式**: CentOS 服务器部署

## 🖥️ CentOS服务器部署

### 系统要求

#### 硬件要求
- **CPU**: 2核心以上
- **内存**: 4GB以上
- **存储**: 20GB以上可用空间
- **网络**: 稳定的互联网连接

#### 软件要求
- **操作系统**: CentOS 7/8 或 RHEL 7/8
- **Python**: 3.6+
- **权限**: 具有sudo权限的非root用户

### 部署步骤

#### 1. 准备服务器
```bash
# 连接到服务器
ssh username@your-server-ip

# 创建部署用户（可选）
sudo useradd -m -s /bin/bash xniu
sudo passwd xniu
sudo usermod -aG wheel xniu
su - xniu
```

#### 2. 上传项目文件
```bash
# 方法一：使用SCP上传
scp -r xniu-trading/ username@your-server-ip:/tmp/

# 方法二：使用Git克隆
cd /tmp
git clone https://github.com/knwins/xniu-trading.git
```

#### 3. 运行部署脚本
```bash
# 进入项目目录
cd /tmp/xniu-trading

# 给脚本执行权限
chmod +x deploy_centos.sh

# 运行部署脚本
./deploy_centos.sh
```

#### 4. 配置交易参数
```bash
# 编辑配置文件
vim /opt/xniu-trading/trader_config.json
```

配置示例：
```json
{
  "api_key": "your-binance-api-key",
  "secret_key": "your-binance-secret-key",
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

#### 5. 启动服务
```bash
# 启动交易系统
/opt/xniu-trading/manage.sh start

# 查看服务状态
/opt/xniu-trading/manage.sh status

# 设置开机自启
sudo systemctl enable xniu-trading
```

## ⚙️ 配置说明

### 配置文件结构
```json
{
  "api_key": "Binance API密钥",
  "secret_key": "Binance 密钥",
  "symbol": "交易对",
  "initial_balance": "初始资金",
  "max_position_size": "最大仓位比例",
  "stop_loss_pct": "止损比例",
  "take_profit_pct": "止盈比例",
  "max_daily_loss": "最大日亏损",
  "max_drawdown": "最大回撤",
  "signal_cooldown": "信号冷却时间",
  "base_url": "API基础URL"
}
```

### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| api_key | string | - | Binance API密钥 |
| secret_key | string | - | Binance密钥 |
| symbol | string | ETHUSDT | 交易对 |
| initial_balance | float | 1000.0 | 初始资金(USDT) |
| max_position_size | float | 0.1 | 最大仓位比例(10%) |
| stop_loss_pct | float | 0.05 | 止损比例(5%) |
| take_profit_pct | float | 0.1 | 止盈比例(10%) |
| max_daily_loss | float | 0.1 | 最大日亏损(10%) |
| max_drawdown | float | 0.2 | 最大回撤(20%) |
| signal_cooldown | int | 300 | 信号冷却时间(秒) |
| base_url | string | https://fapi.binance.com | API基础URL |

## 🔧 管理操作

### 服务管理命令

```bash
# 服务管理
/opt/xniu-trading/manage.sh start    # 启动服务
/opt/xniu-trading/manage.sh stop     # 停止服务
/opt/xniu-trading/manage.sh restart  # 重启服务
/opt/xniu-trading/manage.sh status   # 查看状态
/opt/xniu-trading/manage.sh logs     # 查看日志
/opt/xniu-trading/manage.sh config   # 编辑配置
/opt/xniu-trading/manage.sh backup   # 执行备份
```

### 手动操作
```bash
# 进入项目目录
cd /opt/xniu-trading

# 激活虚拟环境
source venv/bin/activate

# 手动运行
python start_trading.py
```

## 📊 监控维护

### 日志监控

#### 系统日志
```bash
# 查看systemd日志
journalctl -u xniu-trading -f

# 查看应用日志
tail -f /var/log/xniu-trading/*.log
```

#### 交易日志
```bash
# 查看交易历史
ls -la /opt/xniu-trading/logs/

# 查看最新交易记录
tail -f /opt/xniu-trading/logs/trade_history_*.json
```

### 系统监控

#### 资源使用
```bash
# 查看CPU和内存使用
htop

# 查看磁盘使用
df -h

# 查看网络连接
netstat -tulpn
```

#### 自动监控
- 监控脚本每5分钟检查一次服务状态
- 自动重启失败的服务
- 监控磁盘和内存使用率

### 备份策略

#### 自动备份
- 每天凌晨2点自动备份
- 保留7天的备份文件
- 备份配置文件和日志

#### 手动备份
```bash
/opt/xniu-trading/backup.sh
```

## 🚨 故障排除

### 常见问题

#### 1. 服务启动失败
```bash
# 查看详细错误信息
journalctl -u xniu-trading -n 50

# 检查配置文件
cat /opt/xniu-trading/trader_config.json

# 检查权限
ls -la /opt/xniu-trading/
```

#### 2. API连接失败
```bash
# 测试网络连接
ping api.binance.com

# 检查防火墙
sudo firewall-cmd --list-all

# 验证API密钥
cd /opt/xniu-trading
source venv/bin/activate
python -c "from trader import Trader; import json; config=json.load(open('trader_config.json')); t=Trader(config); print(t.test_api_connection())"
```

#### 3. 权限问题
```bash
# 修复权限
sudo chown -R xniu:xniu /opt/xniu-trading
sudo chmod -R 755 /opt/xniu-trading
```

### 性能优化

#### 系统优化
```bash
# 调整文件描述符限制
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# 优化内核参数
echo "net.core.somaxconn = 65535" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

#### Python优化
```bash
# 安装性能优化包
pip install psutil py-cpuinfo

# 监控Python进程
ps aux | grep python
```

## 🔒 安全建议

### 网络安全
- 使用SSH密钥认证
- 配置防火墙规则
- 定期更新系统补丁
- 监控异常登录

### API安全
- 使用最小权限原则
- 定期更换API密钥
- 设置IP白名单
- 监控API使用情况

### 数据安全
- 定期备份重要数据
- 加密敏感配置文件
- 限制文件访问权限
- 监控文件变化

## 📈 更新和维护

### 系统更新
```bash
# 更新系统包
sudo yum update -y

# 更新Python包
cd /opt/xniu-trading
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### 代码更新
```bash
# 备份当前版本
/opt/xniu-trading/backup.sh

# 更新代码
cd /opt/xniu-trading
git pull origin main

# 重启服务
/opt/xniu-trading/manage.sh restart
```

### 配置更新
```bash
# 编辑配置
/opt/xniu-trading/manage.sh config

# 重启服务应用新配置
/opt/xniu-trading/manage.sh restart
```

## 📞 技术支持

### 获取帮助
1. 查看部署指南文档
2. 检查日志文件
3. 验证配置文件
4. 联系技术支持

### 联系方式
- **文档**: 查看项目README
- **问题**: 提交GitHub Issue
- **支持**: 联系开发团队

## 📋 部署检查清单

### 部署前检查
- [ ] 确认系统要求满足
- [ ] 准备API密钥
- [ ] 检查网络连接
- [ ] 确认用户权限

### 部署后检查
- [ ] 服务启动成功
- [ ] API连接正常
- [ ] 配置文件正确
- [ ] 日志输出正常
- [ ] 监控脚本运行
- [ ] 备份功能正常

### 安全检查
- [ ] 防火墙配置
- [ ] 文件权限设置
- [ ] API密钥安全
- [ ] 日志监控启用

---

## ⚠️ 重要提醒

1. **风险提示**: 请确保您了解加密货币交易的风险
2. **资金安全**: 只使用您能够承受损失的资金进行交易
3. **测试验证**: 建议先在测试环境验证系统功能
4. **定期维护**: 定期检查和维护系统，确保稳定运行
5. **备份重要**: 定期备份配置文件和交易数据

---

**版本**: v1.0  
**更新时间**: 2025-08-06  
**维护团队**: XNIU.IO Development Team 