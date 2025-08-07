# XNIU.IO 交易系统服务模式说明

## 概述

XNIU.IO 交易系统现在支持两种运行模式：

1. **交互式模式** - 适合手动配置和测试
2. **服务模式** - 适合在CentOS服务器上作为系统服务自动运行

## 服务模式特性

### 新增功能

- ✅ **非交互式启动** - 无需用户输入，自动从配置文件读取参数
- ✅ **系统服务集成** - 支持systemd服务管理
- ✅ **自动重启** - 服务异常时自动重启
- ✅ **开机自启** - 系统启动时自动启动交易服务
- ✅ **配置验证** - 独立的API配置验证功能
- ✅ **日志管理** - 完整的日志记录和轮转
- ✅ **监控脚本** - 自动监控服务状态和系统资源

### 命令行参数

```bash
# 服务模式运行
python start_trading.py --service

# 指定配置文件
python start_trading.py --service --config /path/to/config.json

# 仅验证配置
python start_trading.py --service --validate

# 交互式模式（默认）
python start_trading.py
```

## 部署流程

### 1. 运行部署脚本

```bash
# 给脚本执行权限
chmod +x deploy_centos.sh

# 运行部署脚本
sudo ./deploy_centos.sh
```

部署脚本会自动：
- 安装系统依赖
- 创建Python虚拟环境
- 安装Python包
- 创建系统服务
- 设置日志目录
- 创建管理脚本
- 生成配置文件模板

### 2. 配置API密钥

```bash
# 编辑配置文件
vim /opt/xniu-trading/trader_config.json
```

配置文件示例：
```json
{
  "api_key": "your-binance-api-key-here",
  "secret_key": "your-binance-secret-key-here",
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

### 3. 验证配置

```bash
# 验证API配置
/opt/xniu-trading/manage.sh validate

# 或运行完整测试
./test_service.sh
```

### 4. 启动服务

```bash
# 启动服务
/opt/xniu-trading/manage.sh start

# 设置开机自启
sudo systemctl enable xniu-trading

# 查看服务状态
/opt/xniu-trading/manage.sh status
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

# 验证配置
/opt/xniu-trading/manage.sh validate

# 执行备份
/opt/xniu-trading/manage.sh backup
```

### 系统命令

```bash
# 直接使用systemctl
sudo systemctl start xniu-trading
sudo systemctl stop xniu-trading
sudo systemctl restart xniu-trading
sudo systemctl status xniu-trading
sudo systemctl enable xniu-trading

# 查看日志
sudo journalctl -u xniu-trading -f
```

## 监控和维护

### 自动监控

- 监控脚本每5分钟检查服务状态
- 自动重启失败的服务
- 监控磁盘和内存使用率
- 记录监控日志到 `/var/log/xniu-trading/monitor.log`

### 自动备份

- 每天凌晨2点自动备份
- 保留7天的备份文件
- 备份配置文件和日志

### 日志管理

- 系统日志：`journalctl -u xniu-trading`
- 应用日志：`/opt/xniu-trading/logs/`
- 监控日志：`/var/log/xniu-trading/`

## 故障排除

### 常见问题

#### 1. 服务启动失败

```bash
# 查看详细错误信息
sudo journalctl -u xniu-trading -n 50

# 检查配置文件
cat /opt/xniu-trading/trader_config.json

# 验证API配置
/opt/xniu-trading/manage.sh validate
```

#### 2. API连接失败

```bash
# 测试网络连接
ping api.binance.com

# 检查防火墙
sudo firewall-cmd --list-all

# 验证API密钥
/opt/xniu-trading/manage.sh validate
```

#### 3. 权限问题

```bash
# 修复权限
sudo chown -R root:root /opt/xniu-trading
sudo chmod -R 755 /opt/xniu-trading
```

#### 4. 配置文件问题

```bash
# 检查配置文件格式
python3 -m json.tool /opt/xniu-trading/trader_config.json

# 重新创建配置文件
cp trader_config_template.json /opt/xniu-trading/trader_config.json
```

### 测试脚本

运行测试脚本可以全面检查系统状态：

```bash
chmod +x test_service.sh
./test_service.sh
```

测试脚本会检查：
- 项目目录和文件
- 配置文件格式
- 虚拟环境
- Python依赖
- 服务模式启动
- 系统服务状态
- 日志目录
- 管理脚本

## 安全建议

### 1. API安全

- 使用最小权限原则
- 定期更换API密钥
- 设置IP白名单
- 监控API使用情况

### 2. 系统安全

- 使用SSH密钥认证
- 配置防火墙规则
- 定期更新系统补丁
- 监控异常登录

### 3. 数据安全

- 定期备份重要数据
- 加密敏感配置文件
- 限制文件访问权限
- 监控文件变化

## 性能优化

### 1. 系统优化

```bash
# 调整文件描述符限制
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# 优化内核参数
echo "net.core.somaxconn = 65535" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### 2. Python优化

```bash
# 安装性能优化包
pip install psutil py-cpuinfo

# 监控Python进程
ps aux | grep python
```

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

---

**注意**: 请确保您了解加密货币交易的风险，并只使用您能够承受损失的资金进行交易。 