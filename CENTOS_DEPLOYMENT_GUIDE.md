# XNIU.IO 交易系统 CentOS 部署指南

## 概述

本指南将帮助您在 CentOS 服务器上部署 XNIU.IO 交易系统，包括完整的安装、配置、监控和管理功能。

## 系统要求

### 硬件要求
- **CPU**: 2核心以上
- **内存**: 4GB以上
- **存储**: 20GB以上可用空间
- **网络**: 稳定的互联网连接

### 软件要求
- **操作系统**: CentOS 7/8 或 RHEL 7/8
- **Python**: 3.6+
- **权限**: root用户或具有sudo权限的用户

## 部署步骤

### 1. 准备服务器

#### 1.1 连接到服务器
```bash
ssh username@your-server-ip
```

#### 1.2 选择部署方式

**方式一：使用root用户（推荐）**
```bash
# 直接使用root用户登录
sudo su -
```

**方式二：使用普通用户（需要sudo权限）**
```bash
# 创建新用户
sudo useradd -m -s /bin/bash xniu
sudo passwd xniu

# 添加到sudo组
sudo usermod -aG wheel xniu

# 切换到新用户
su - xniu
```

### 2. 上传项目文件

#### 2.1 方法一：使用SCP上传
```bash
# 在本地执行
scp -r xniu-trading/ username@your-server-ip:/tmp/
```

#### 2.2 方法二：使用Git克隆
```bash
# 在服务器上执行
cd /tmp
git clone https://github.com/knwins/xniu-trading.git
```

### 3. 运行部署脚本

#### 3.1 给脚本执行权限
```bash
chmod +x deploy_centos.sh
```

#### 3.2 运行部署脚本
```bash
./deploy_centos.sh
```

### 4. 配置交易参数

#### 4.1 编辑配置文件
```bash
vim /opt/xniu-trading/trader_config.json
```

#### 4.2 配置示例
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

### 5. 启动服务

#### 5.1 启动交易系统
```bash
/opt/xniu-trading/manage.sh start
```

#### 5.2 查看服务状态
```bash
/opt/xniu-trading/manage.sh status
```

#### 5.3 设置开机自启
```bash
sudo systemctl enable xniu-trading
```

## 管理命令

### 服务管理
```bash
# 启动服务
/opt/xniu-trading/manage.sh start

# 停止服务
/opt/xniu-trading/manage.sh stop

# 重启服务
/opt/xniu-trading/manage.sh restart

# 查看状态
/opt/xniu-trading/manage.sh status

# 查看日志
/opt/xniu-trading/manage.sh logs
```

### 配置管理
```bash
# 编辑配置
/opt/xniu-trading/manage.sh config

# 执行备份
/opt/xniu-trading/manage.sh backup
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

## 监控和维护

### 1. 日志监控

#### 1.1 系统日志
```bash
# 查看systemd日志
journalctl -u xniu-trading -f

# 查看应用日志
tail -f /var/log/xniu-trading/*.log
```

#### 1.2 交易日志
```bash
# 查看交易历史
ls -la /opt/xniu-trading/logs/

# 查看最新交易记录
tail -f /opt/xniu-trading/logs/trade_history_*.json
```

### 2. 系统监控

#### 2.1 资源使用
```bash
# 查看CPU和内存使用
htop

# 查看磁盘使用
df -h

# 查看网络连接
netstat -tulpn
```

#### 2.2 自动监控
- 监控脚本每5分钟检查一次服务状态
- 自动重启失败的服务
- 监控磁盘和内存使用率

### 3. 备份策略

#### 3.1 自动备份
- 每天凌晨2点自动备份
- 保留7天的备份文件
- 备份配置文件和日志

#### 3.2 手动备份
```bash
/opt/xniu-trading/backup.sh
```

## 故障排除

### 1. 常见问题

#### 1.1 服务启动失败
```bash
# 查看详细错误信息
journalctl -u xniu-trading -n 50

# 检查配置文件
cat /opt/xniu-trading/trader_config.json

# 检查权限
ls -la /opt/xniu-trading/
```

#### 1.2 API连接失败
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

#### 1.3 权限问题
```bash
# 修复权限
sudo chown -R xniu:xniu /opt/xniu-trading
sudo chmod -R 755 /opt/xniu-trading
```

### 2. 性能优化

#### 2.1 系统优化
```bash
# 调整文件描述符限制
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# 优化内核参数
echo "net.core.somaxconn = 65535" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

#### 2.2 Python优化
```bash
# 安装性能优化包
pip install psutil py-cpuinfo

# 监控Python进程
ps aux | grep python
```

## 安全建议

### 1. 网络安全
- 使用SSH密钥认证
- 配置防火墙规则
- 定期更新系统补丁
- 监控异常登录

### 2. API安全
- 使用最小权限原则
- 定期更换API密钥
- 设置IP白名单
- 监控API使用情况

### 3. 数据安全
- 定期备份重要数据
- 加密敏感配置文件
- 限制文件访问权限
- 监控文件变化

## 更新和维护

### 1. 系统更新
```bash
# 更新系统包
sudo yum update -y

# 更新Python包
cd /opt/xniu-trading
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### 2. 代码更新
```bash
# 备份当前版本
/opt/xniu-trading/backup.sh

# 更新代码
cd /opt/xniu-trading
git pull origin main

# 重启服务
/opt/xniu-trading/manage.sh restart
```

### 3. 配置更新
```bash
# 编辑配置
/opt/xniu-trading/manage.sh config

# 重启服务应用新配置
/opt/xniu-trading/manage.sh restart
```

## 联系支持

如果遇到问题，请：
1. 查看日志文件获取错误信息
2. 检查配置文件是否正确
3. 验证网络连接和API密钥
4. 联系技术支持团队

---

**注意**: 请确保您了解加密货币交易的风险，并只使用您能够承受损失的资金进行交易。 