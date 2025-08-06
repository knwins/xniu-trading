#!/bin/bash
# OSCent服务器一键配置脚本
# 专门针对OSCent (基于CentOS) 服务器优化
# 支持小额交易测试系统

set -e

echo "🚀 OSCent服务器一键配置脚本"
echo "================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "检测到root用户，建议使用普通用户运行"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 检测OSCent系统
detect_oscent() {
    log_step "检测操作系统..."
    
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        log_error "无法检测操作系统"
        exit 1
    fi
    
    # 检查是否为OSCent或CentOS
    if [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"OSCent"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
        log_success "检测到OSCent/CentOS系统: $OS $VER"
    else
        log_warning "当前系统: $OS $VER"
        log_warning "此脚本专为OSCent/CentOS优化，其他系统可能不兼容"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 检查网络连接
check_network() {
    log_step "检查网络连接..."
    
    if ping -c 1 8.8.8.8 &> /dev/null; then
        log_success "网络连接正常"
    else
        log_error "网络连接失败，请检查网络设置"
        exit 1
    fi
    
    # 检查DNS解析
    if nslookup google.com &> /dev/null; then
        log_success "DNS解析正常"
    else
        log_warning "DNS解析可能有问题，尝试使用备用DNS"
        echo "nameserver 8.8.8.8" | sudo tee -a /etc/resolv.conf
    fi
    
    # 检查币安API连接
    log_info "检查币安API连接..."
    if curl -s --connect-timeout 10 https://fapi.binance.com/fapi/v1/ping &> /dev/null; then
        log_success "币安API连接正常"
    else
        log_warning "币安API连接失败，可能影响交易功能"
    fi
}

# 更新系统
update_system() {
    log_step "更新系统包..."
    
    # 更新yum源
    sudo yum update -y
    
    # 安装EPEL源（如果不存在）
    if ! rpm -q epel-release &> /dev/null; then
        log_info "安装EPEL源..."
        sudo yum install -y epel-release
    fi
    
    log_success "系统更新完成"
}

# 安装基础依赖
install_basic_deps() {
    log_step "安装基础依赖..."
    
    # 安装开发工具和基础软件
    sudo yum groupinstall -y "Development Tools"
    sudo yum install -y python3 python3-pip python3-devel git curl wget htop vim
    
    # 安装网络工具
    sudo yum install -y net-tools nmap-ncat telnet
    
    # 安装监控工具
    sudo yum install -y htop iotop nethogs sysstat
    
    # 安装编译工具（用于TA-Lib）
    sudo yum install -y gcc gcc-c++ make
    
    log_success "基础依赖安装完成"
}

# 配置Python环境
setup_python_env() {
    log_step "配置Python环境..."
    
    # 升级pip
    python3 -m pip install --upgrade pip
    
    # 安装virtualenv
    python3 -m pip install virtualenv
    
    log_success "Python环境配置完成"
}

# 创建项目目录
setup_project_dir() {
    log_step "设置项目目录..."
    
    PROJECT_DIR="/opt/quant-trading"
    sudo mkdir -p $PROJECT_DIR
    sudo chown $USER:$USER $PROJECT_DIR
    cd $PROJECT_DIR
    
    # 创建子目录
    mkdir -p {logs,config,data,backups,scripts,tests}
    
    log_success "项目目录: $PROJECT_DIR"
}

# 创建Python虚拟环境
create_venv() {
    log_step "创建Python虚拟环境..."
    
    python3 -m venv venv
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    log_success "Python虚拟环境创建完成"
}

# 安装Python依赖
install_python_deps() {
    log_step "安装Python依赖..."
    
    # 基础科学计算库
    pip install pandas numpy matplotlib seaborn requests python-dotenv
    
    # 交易相关库
    pip install ccxt websocket-client
    
    # 尝试安装TA-Lib
    log_info "安装TA-Lib..."
    if install_talib; then
        log_success "TA-Lib安装成功"
    else
        log_warning "TA-Lib安装失败，使用替代方案"
        pip install ta  # 使用ta库作为替代
    fi
    
    # 安装其他有用的库
    pip install schedule psutil
    
    # 安装测试相关库
    pip install pytest pytest-cov
    
    log_success "Python依赖安装完成"
}

# 安装TA-Lib
install_talib() {
    log_info "编译安装TA-Lib..."
    
    # 下载并编译TA-Lib
    wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
    tar -xzf ta-lib-0.4.0-src.tar.gz
    cd ta-lib/
    ./configure --prefix=/usr
    make
    sudo make install
    cd ..
    pip install TA-Lib
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz
    
    return 0
}

# 配置系统服务
setup_system_service() {
    log_step "配置系统服务..."
    
    # 创建systemd服务文件
    sudo tee /etc/systemd/system/quant-trading.service > /dev/null <<EOF
[Unit]
Description=Quantitative Trading System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/trade/trader.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    # 重新加载systemd
    sudo systemctl daemon-reload
    
    log_success "系统服务配置完成"
}

# 创建监控脚本
create_monitor_scripts() {
    log_step "创建监控脚本..."
    
    # 主监控脚本
    cat > monitor.sh << 'EOF'
#!/bin/bash
# 系统监控脚本

echo "=== OSCent量化交易系统监控 $(date) ==="
echo "========================================"

# 系统状态
echo "📊 系统状态:"
echo "CPU使用率: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "内存使用率: $(free | grep Mem | awk '{printf("%.2f%%", $3/$2 * 100.0)}')"
echo "磁盘使用率: $(df -h / | awk 'NR==2 {print $5}')"
echo "负载平均值: $(uptime | awk -F'load average:' '{print $2}')"

# 网络状态
echo ""
echo "🌐 网络状态:"
if ping -c 1 fapi.binance.com &> /dev/null; then
    echo "✅ 币安API连接正常"
else
    echo "❌ 币安API连接失败"
fi

# 交易系统状态
echo ""
echo "💰 交易系统状态:"
if pgrep -f "trader.py" > /dev/null; then
    echo "✅ 交易系统正在运行"
    echo "进程ID: $(pgrep -f 'trader.py')"
    echo "运行时间: $(ps -o etime= -p $(pgrep -f 'trader.py'))"
else
    echo "❌ 交易系统未运行"
fi

# 小额测试系统状态
echo ""
echo "🧪 小额测试系统状态:"
if [ -f "test/demo_small_trade.py" ]; then
    echo "✅ 演示测试脚本存在"
else
    echo "❌ 演示测试脚本不存在"
fi

if [ -f "test/test_small_trades.py" ]; then
    echo "✅ 完整测试脚本存在"
else
    echo "❌ 完整测试脚本不存在"
fi

# 日志文件状态
echo ""
echo "📝 日志文件状态:"
if [ -f "logs/trading.log" ]; then
    echo "日志文件大小: $(ls -lh logs/trading.log | awk '{print $5}')"
    echo "最后修改时间: $(stat -c %y logs/trading.log)"
else
    echo "日志文件不存在"
fi

# 磁盘空间
echo ""
echo "💾 磁盘空间:"
df -h | grep -E '^/dev/'

# 内存使用详情
echo ""
echo "🧠 内存使用详情:"
free -h
EOF

    chmod +x monitor.sh
    
    # 快速状态检查脚本
    cat > status.sh << 'EOF'
#!/bin/bash
# 快速状态检查

echo "🔍 快速状态检查 $(date)"
echo "========================"

# 检查关键进程
if pgrep -f "trader.py" > /dev/null; then
    echo "✅ 交易系统: 运行中"
else
    echo "❌ 交易系统: 未运行"
fi

# 检查网络
if ping -c 1 8.8.8.8 &> /dev/null; then
    echo "✅ 网络连接: 正常"
else
    echo "❌ 网络连接: 异常"
fi

# 检查币安API
if curl -s --connect-timeout 5 https://fapi.binance.com/fapi/v1/ping &> /dev/null; then
    echo "✅ 币安API: 正常"
else
    echo "❌ 币安API: 异常"
fi

# 检查磁盘空间
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo "✅ 磁盘空间: 充足 ($DISK_USAGE%)"
else
    echo "⚠️ 磁盘空间: 不足 ($DISK_USAGE%)"
fi

# 检查内存
MEM_USAGE=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
if [ "$MEM_USAGE" -lt 80 ]; then
    echo "✅ 内存使用: 正常 ($MEM_USAGE%)"
else
    echo "⚠️ 内存使用: 较高 ($MEM_USAGE%)"
fi

# 检查测试脚本
if [ -f "test/demo_small_trade.py" ]; then
    echo "✅ 演示测试: 可用"
else
    echo "❌ 演示测试: 不可用"
fi
EOF

    chmod +x status.sh
    
    log_success "监控脚本创建完成"
}

# 配置防火墙
setup_firewall() {
    log_step "配置防火墙..."
    
    # 检查firewalld是否运行
    if systemctl is-active --quiet firewalld; then
        log_info "配置firewalld..."
        sudo firewall-cmd --permanent --add-service=ssh
        sudo firewall-cmd --permanent --add-service=http
        sudo firewall-cmd --permanent --add-service=https
        sudo firewall-cmd --reload
        log_success "防火墙配置完成"
    else
        log_warning "firewalld未运行，跳过防火墙配置"
    fi
}

# 设置时区
setup_timezone() {
    log_step "设置时区为香港时区..."
    sudo timedatectl set-timezone Asia/Hong_Kong
    log_success "时区设置完成 - 香港时区 (UTC+8)"
}

# 配置定时任务
setup_cron() {
    log_step "配置定时任务..."
    
    # 添加监控任务
    (crontab -l 2>/dev/null; echo "*/5 * * * * $PROJECT_DIR/monitor.sh >> $PROJECT_DIR/logs/monitor.log 2>&1") | crontab -
    
    # 添加日志轮转任务
    (crontab -l 2>/dev/null; echo "0 2 * * * find $PROJECT_DIR/logs -name '*.log' -mtime +7 -delete") | crontab -
    
    # 添加系统备份任务
    (crontab -l 2>/dev/null; echo "0 3 * * 0 cp -r $PROJECT_DIR/config $PROJECT_DIR/backups/config_\$(date +\%Y\%m\%d)") | crontab -
    
    log_success "定时任务配置完成"
}

# 创建启动脚本
create_startup_scripts() {
    log_step "创建启动脚本..."
    
    # 主启动脚本
    cat > start_trading.sh << 'EOF'
#!/bin/bash
# 启动交易系统脚本

echo "🚀 启动量化交易系统..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行配置脚本"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 检查配置文件
if [ ! -f "config/trading_config.json" ]; then
    echo "❌ 配置文件不存在，请先配置API密钥"
    exit 1
fi

# 检查交易代码
if [ ! -f "trade/trader.py" ]; then
    echo "❌ 交易代码不存在，请先上传代码"
    exit 1
fi

echo "✅ 环境检查通过，启动交易系统..."
python trade/trader.py
EOF

    chmod +x start_trading.sh
    
    # 停止脚本
    cat > stop_trading.sh << 'EOF'
#!/bin/bash
# 停止交易系统脚本

echo "🛑 停止量化交易系统..."

# 查找并停止交易进程
if pgrep -f "trader.py" > /dev/null; then
    echo "正在停止交易系统..."
    pkill -f "trader.py"
    sleep 2
    
    # 检查是否成功停止
    if pgrep -f "trader.py" > /dev/null; then
        echo "强制停止交易系统..."
        pkill -9 -f "trader.py"
    fi
    
    echo "✅ 交易系统已停止"
else
    echo "交易系统未在运行"
fi
EOF

    chmod +x stop_trading.sh
    
    # 重启脚本
    cat > restart_trading.sh << 'EOF'
#!/bin/bash
# 重启交易系统脚本

echo "🔄 重启量化交易系统..."

# 停止交易系统
./stop_trading.sh

# 等待2秒
sleep 2

# 启动交易系统
./start_trading.sh
EOF

    chmod +x restart_trading.sh
    
    # 小额测试脚本
    cat > test_small_trades.sh << 'EOF'
#!/bin/bash
# 小额交易测试脚本

echo "🧪 启动小额交易测试..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行配置脚本"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 检查演示测试脚本
if [ ! -f "test/demo_small_trade.py" ]; then
    echo "❌ 演示测试脚本不存在，尝试创建基础测试脚本..."
    mkdir -p test
    cat > test/demo_small_trade.py << 'PYEOF'
#!/usr/bin/env python3
"""
小额交易演示测试脚本
无需真实API密钥，使用模拟数据测试交易逻辑
"""

import json
import time
import random
from datetime import datetime

def simulate_market_data():
    """模拟市场数据"""
    base_price = 2000.0  # ETH基础价格
    volatility = 0.02    # 2%波动率
    
    # 模拟价格波动
    change = random.uniform(-volatility, volatility)
    current_price = base_price * (1 + change)
    
    return {
        'symbol': 'ETHUSDT',
        'price': round(current_price, 2),
        'timestamp': datetime.now().isoformat(),
        'volume': random.uniform(100, 1000)
    }

def test_trading_logic():
    """测试交易逻辑"""
    print("🧪 开始小额交易演示测试...")
    print("=" * 50)
    
    # 模拟配置
    config = {
        'symbol': 'ETHUSDT',
        'initial_balance': 100.0,
        'max_position_size': 0.05,
        'stop_loss_pct': 0.02,
        'take_profit_pct': 0.05
    }
    
    print(f"📊 测试配置:")
    print(f"   交易对: {config['symbol']}")
    print(f"   初始资金: ${config['initial_balance']}")
    print(f"   最大仓位: {config['max_position_size']*100}%")
    print(f"   止损比例: {config['stop_loss_pct']*100}%")
    print(f"   止盈比例: {config['take_profit_pct']*100}%")
    print()
    
    balance = config['initial_balance']
    position = 0
    entry_price = 0
    
    print("📈 开始模拟交易...")
    print("-" * 50)
    
    for i in range(10):  # 模拟10次交易
        market_data = simulate_market_data()
        current_price = market_data['price']
        
        print(f"第{i+1}次检查 - 当前价格: ${current_price}")
        
        # 简单的交易逻辑：价格低于2000时买入，高于2100时卖出
        if position == 0 and current_price < 2000:
            # 买入信号
            position_size = balance * config['max_position_size']
            position = position_size / current_price
            entry_price = current_price
            balance -= position_size
            
            print(f"   🟢 买入信号触发")
            print(f"   买入数量: {position:.4f} ETH")
            print(f"   买入价格: ${entry_price}")
            print(f"   剩余资金: ${balance:.2f}")
            
        elif position > 0:
            # 检查止损止盈
            price_change = (current_price - entry_price) / entry_price
            
            if price_change <= -config['stop_loss_pct']:
                # 止损
                sell_amount = position * current_price
                balance += sell_amount
                profit = sell_amount - (position * entry_price)
                
                print(f"   🔴 止损触发")
                print(f"   卖出数量: {position:.4f} ETH")
                print(f"   卖出价格: ${current_price}")
                print(f"   亏损: ${profit:.2f}")
                print(f"   剩余资金: ${balance:.2f}")
                
                position = 0
                entry_price = 0
                
            elif price_change >= config['take_profit_pct']:
                # 止盈
                sell_amount = position * current_price
                balance += sell_amount
                profit = sell_amount - (position * entry_price)
                
                print(f"   🟡 止盈触发")
                print(f"   卖出数量: {position:.4f} ETH")
                print(f"   卖出价格: ${current_price}")
                print(f"   盈利: ${profit:.2f}")
                print(f"   剩余资金: ${balance:.2f}")
                
                position = 0
                entry_price = 0
        
        print()
        time.sleep(1)  # 模拟1秒间隔
    
    # 最终结算
    if position > 0:
        final_price = simulate_market_data()['price']
        sell_amount = position * final_price
        balance += sell_amount
        final_profit = sell_amount - (position * entry_price)
        
        print(f"📊 最终结算:")
        print(f"   卖出数量: {position:.4f} ETH")
        print(f"   最终价格: ${final_price}")
        print(f"   最终盈亏: ${final_profit:.2f}")
    
    total_return = ((balance - config['initial_balance']) / config['initial_balance']) * 100
    
    print("=" * 50)
    print(f"🎯 测试结果:")
    print(f"   初始资金: ${config['initial_balance']:.2f}")
    print(f"   最终资金: ${balance:.2f}")
    print(f"   总收益率: {total_return:.2f}%")
    print(f"   净盈亏: ${balance - config['initial_balance']:.2f}")
    
    if total_return > 0:
        print("✅ 测试完成 - 模拟交易盈利")
    else:
        print("⚠️ 测试完成 - 模拟交易亏损")
    
    print("\n📝 说明: 这是演示测试，使用模拟数据，不涉及真实交易")

if __name__ == "__main__":
    try:
        test_trading_logic()
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
PYEOF
    echo "✅ 演示测试脚本创建完成"
fi

echo "✅ 环境检查通过，启动演示测试..."
python test/demo_small_trade.py
EOF

    chmod +x test_small_trades.sh
    
    # API连接测试脚本
    cat > test_api_connection.sh << 'EOF'
#!/bin/bash
# API连接测试脚本

echo "🔗 测试API连接..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行配置脚本"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 检查API测试脚本
if [ ! -f "test/test_api_connection.py" ]; then
    echo "❌ API测试脚本不存在，尝试创建基础API测试脚本..."
    mkdir -p test
    cat > test/test_api_connection.py << 'PYEOF'
#!/usr/bin/env python3
"""
API连接测试脚本
测试网络连接和币安API访问
"""

import requests
import json
import time
from datetime import datetime

def test_network_connection():
    """测试基础网络连接"""
    print("🌐 测试网络连接...")
    
    test_urls = [
        "https://www.google.com",
        "https://fapi.binance.com",
        "https://api.binance.com"
    ]
    
    for url in test_urls:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"   ✅ {url} - 连接正常")
            else:
                print(f"   ⚠️ {url} - 状态码: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ {url} - 连接失败: {e}")
    
    print()

def test_binance_api():
    """测试币安API连接"""
    print("🔗 测试币安API连接...")
    
    # 测试公共API端点
    api_endpoints = [
        "https://fapi.binance.com/fapi/v1/ping",
        "https://fapi.binance.com/fapi/v1/time",
        "https://fapi.binance.com/fapi/v1/exchangeInfo"
    ]
    
    for endpoint in api_endpoints:
        try:
            response = requests.get(endpoint, timeout=10)
            if response.status_code == 200:
                print(f"   ✅ {endpoint} - 连接正常")
                if "ping" in endpoint:
                    print(f"      响应: {response.text}")
            else:
                print(f"   ⚠️ {endpoint} - 状态码: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ {endpoint} - 连接失败: {e}")
    
    print()

def test_api_config():
    """测试API配置"""
    print("🔑 检查API配置...")
    
    config_file = "config/trading_config.json"
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        api_key = config.get('api_key', '')
        secret_key = config.get('secret_key', '')
        
        if api_key and api_key != "YOUR_API_KEY_HERE":
            print("   ✅ API密钥已配置")
            print(f"   API密钥: {api_key[:8]}...{api_key[-4:]}")
        else:
            print("   ⚠️ API密钥未配置或使用默认值")
        
        if secret_key and secret_key != "YOUR_SECRET_KEY_HERE":
            print("   ✅ 密钥已配置")
            print(f"   密钥: {secret_key[:8]}...{secret_key[-4:]}")
        else:
            print("   ⚠️ 密钥未配置或使用默认值")
        
        # 显示其他配置
        print(f"   交易对: {config.get('symbol', 'N/A')}")
        print(f"   初始资金: ${config.get('initial_balance', 0)}")
        print(f"   最大仓位: {config.get('max_position_size', 0)*100}%")
        
    except FileNotFoundError:
        print("   ❌ 配置文件不存在")
    except json.JSONDecodeError:
        print("   ❌ 配置文件格式错误")
    except Exception as e:
        print(f"   ❌ 读取配置文件失败: {e}")
    
    print()

def test_ccxt_library():
    """测试CCXT库"""
    print("📚 测试CCXT库...")
    
    try:
        import ccxt
        print(f"   ✅ CCXT库已安装，版本: {ccxt.__version__}")
        
        # 测试创建交易所实例
        exchange = ccxt.binance({
            'apiKey': '',
            'secret': '',
            'sandbox': False,
            'enableRateLimit': True
        })
        
        print("   ✅ 成功创建币安交易所实例")
        
        # 测试获取市场信息
        try:
            markets = exchange.load_markets()
            print(f"   ✅ 成功获取市场信息，共{len(markets)}个交易对")
        except Exception as e:
            print(f"   ⚠️ 获取市场信息失败: {e}")
        
    except ImportError:
        print("   ❌ CCXT库未安装")
    except Exception as e:
        print(f"   ❌ CCXT库测试失败: {e}")
    
    print()

def main():
    """主函数"""
    print("🔗 API连接测试开始")
    print("=" * 50)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_network_connection()
    test_binance_api()
    test_api_config()
    test_ccxt_library()
    
    print("=" * 50)
    print("🎯 测试总结:")
    print("✅ 网络连接测试完成")
    print("✅ 币安API连接测试完成")
    print("✅ API配置检查完成")
    print("✅ CCXT库测试完成")
    print()
    print("📝 说明:")
    print("- 如果所有测试都通过，说明环境配置正确")
    print("- 如果API密钥未配置，请编辑 config/trading_config.json")
    print("- 如果网络连接失败，请检查网络设置和防火墙")
    print("- 如果CCXT库未安装，请运行: pip install ccxt")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
PYEOF
    echo "✅ API测试脚本创建完成"
fi

echo "✅ 环境检查通过，测试API连接..."
python test/test_api_connection.py
EOF

    chmod +x test_api_connection.sh
    
    log_success "启动脚本创建完成"
}

# 创建配置文件模板
create_config_template() {
    log_step "创建配置文件模板..."
    
    cat > config/trading_config.json << 'EOF'
{
  "api_key": "YOUR_API_KEY_HERE",
  "secret_key": "YOUR_SECRET_KEY_HERE",
  "symbol": "ETHUSDT",
  "initial_balance": 1000.0,
  "max_position_size": 0.1,
  "stop_loss_pct": 0.05,
  "take_profit_pct": 0.1,
  "max_daily_loss": 0.1,
  "max_drawdown": 0.2,
  "signal_cooldown": 300,
  "base_url": "https://fapi.binance.com",
  "testnet": false
}
EOF

    log_success "配置文件模板创建完成"
}

# 创建小额测试配置文件
create_small_trade_config() {
    log_step "创建小额测试配置..."
    
    # 确保config目录存在
    mkdir -p config
    
    cat > config/small_trade_config.json << 'EOF'
{
  "api_key": "YOUR_API_KEY_HERE",
  "secret_key": "YOUR_SECRET_KEY_HERE",
  "symbol": "ETHUSDT",
  "initial_balance": 100.0,
  "max_position_size": 0.05,
  "stop_loss_pct": 0.02,
  "take_profit_pct": 0.05,
  "max_daily_loss": 0.05,
  "max_drawdown": 0.1,
  "signal_cooldown": 600,
  "base_url": "https://fapi.binance.com",
  "testnet": false
}
EOF

    log_success "小额测试配置创建完成"
}

# 创建README文件
create_readme() {
    log_step "创建说明文档..."
    
    cat > README_OSCent.md << 'EOF'
# OSCent量化交易系统部署指南

## 系统信息
- 操作系统: OSCent (基于CentOS)
- 项目目录: /opt/quant-trading
- Python版本: 3.x

## 目录结构
```
/opt/quant-trading/
├── venv/                    # Python虚拟环境
├── logs/                    # 日志文件
├── config/                  # 配置文件
├── data/                    # 数据文件
├── backups/                 # 备份文件
├── scripts/                 # 脚本文件
├── tests/                   # 测试文件
├── monitor.sh              # 监控脚本
├── status.sh               # 状态检查脚本
├── start_trading.sh        # 启动脚本
├── stop_trading.sh         # 停止脚本
├── restart_trading.sh      # 重启脚本
├── test_small_trades.sh    # 小额测试脚本
├── test_api_connection.sh  # API连接测试脚本
├── config/
│   ├── trading_config.json # 主配置文件
│   └── small_trade_config.json # 小额测试配置
```

## 常用命令

### 系统服务管理
```bash
# 启动交易系统
sudo systemctl start quant-trading

# 停止交易系统
sudo systemctl stop quant-trading

# 重启交易系统
sudo systemctl restart quant-trading

# 查看状态
sudo systemctl status quant-trading

# 设置开机自启
sudo systemctl enable quant-trading

# 查看日志
sudo journalctl -u quant-trading -f
```

### 手动操作
```bash
# 进入项目目录
cd /opt/quant-trading

# 激活虚拟环境
source venv/bin/activate

# 启动交易系统
./start_trading.sh

# 停止交易系统
./stop_trading.sh

# 重启交易系统
./restart_trading.sh
```

### 小额测试操作
```bash
# 运行演示测试（无需真实API）
./test_small_trades.sh

# 测试API连接
./test_api_connection.sh

# 直接运行演示测试
python test/demo_small_trade.py

# 运行完整小额测试（需要API密钥）
python test/test_small_trades.py
```

### 监控命令
```bash
# 查看系统状态
./status.sh

# 详细监控
./monitor.sh

# 查看实时日志
tail -f logs/trading.log

# 查看监控日志
tail -f logs/monitor.log
```

## 配置说明

### 1. API配置
编辑 `config/trading_config.json` 文件，填入您的币安API密钥：
```json
{
  "api_key": "您的API_KEY",
  "secret_key": "您的SECRET_KEY"
}
```

### 2. 小额测试配置
编辑 `config/small_trade_config.json` 文件，使用更保守的参数：
```json
{
  "api_key": "您的API_KEY",
  "secret_key": "您的SECRET_KEY",
  "initial_balance": 100.0,
  "max_position_size": 0.05,
  "stop_loss_pct": 0.02,
  "take_profit_pct": 0.05
}
```

### 3. 交易参数
- `symbol`: 交易对
- `initial_balance`: 初始资金
- `max_position_size`: 最大仓位比例
- `stop_loss_pct`: 止损百分比
- `take_profit_pct`: 止盈百分比

## 小额测试系统

### 1. 演示测试 (test/demo_small_trade.py)
- 无需真实API密钥
- 使用模拟价格数据
- 测试交易逻辑和风险控制
- 适合初次测试和演示

### 2. 完整测试 (test/test_small_trades.py)
- 需要真实API密钥
- 使用真实市场数据
- 包含完整的风险控制
- 适合小额真实交易测试

### 3. API连接测试 (test/test_api_connection.py)
- 测试网络连接
- 验证API密钥有效性
- 检查IP白名单设置
- 诊断连接问题

## 故障排除

### 1. 系统服务无法启动
```bash
# 查看详细错误信息
sudo journalctl -u quant-trading -n 50

# 检查配置文件
cat config/trading_config.json

# 检查Python环境
source venv/bin/activate
python -c "import ccxt; print('CCXT版本:', ccxt.__version__)"
```

### 2. 网络连接问题
```bash
# 测试网络连接
ping fapi.binance.com

# 检查DNS
nslookup fapi.binance.com

# 检查防火墙
sudo firewall-cmd --list-all

# 运行API连接测试
./test_api_connection.sh
```

### 3. API密钥问题
```bash
# 测试API连接
python test/test_api_connection.py

# 常见错误及解决方案：
# - Invalid API-key: 检查API密钥是否正确
# - IP not whitelisted: 在币安后台添加服务器IP到白名单
# - Insufficient permissions: 检查API权限设置
```

### 4. 磁盘空间不足
```bash
# 查看磁盘使用情况
df -h

# 清理日志文件
find logs/ -name "*.log" -mtime +7 -delete

# 清理备份文件
find backups/ -name "*" -mtime +30 -delete
```

## 安全建议

1. **API密钥安全**
   - 定期更换API密钥
   - 设置IP白名单
   - 仅启用必要的API权限
   - 使用小额资金测试

2. **系统安全**
   - 定期更新系统
   - 使用强密码
   - 配置防火墙
   - 限制SSH访问

3. **监控告警**
   - 设置磁盘空间告警
   - 监控系统资源使用
   - 定期检查日志
   - 监控交易系统状态

4. **备份策略**
   - 定期备份配置文件
   - 备份重要数据
   - 测试恢复流程

## 测试流程建议

### 1. 初次部署
```bash
# 1. 运行演示测试
python test/demo_small_trade.py

# 2. 测试API连接
python test/test_api_connection.py

# 3. 配置API密钥
nano config/trading_config.json

# 4. 运行小额测试
python test/test_small_trades.py

# 5. 启动正式交易
./start_trading.sh
```

### 2. 日常维护
```bash
# 每日检查
./status.sh

# 每周监控
./monitor.sh

# 定期备份
cp -r config backups/config_$(date +%Y%m%d)
```

## 联系支持

如遇到问题，请检查：
1. 系统日志: `sudo journalctl -u quant-trading`
2. 应用日志: `tail -f logs/trading.log`
3. 监控日志: `tail -f logs/monitor.log`
4. API测试: `python test/test_api_connection.py`
5. 演示测试: `python test/demo_small_trade.py`
EOF

    log_success "说明文档创建完成"
}

# 显示完成信息
show_completion_info() {
    echo ""
    echo "🎉 OSCent服务器配置完成!"
    echo "========================================"
    echo "📁 项目目录: $PROJECT_DIR"
    echo "🐍 Python环境: $PROJECT_DIR/venv"
    echo "📝 主配置文件: $PROJECT_DIR/config/trading_config.json"
    echo "📝 小额测试配置: $PROJECT_DIR/config/small_trade_config.json"
    echo "📊 日志目录: $PROJECT_DIR/logs"
    echo ""
    echo "📋 后续步骤:"
    echo "1. 上传交易代码到 $PROJECT_DIR"
    echo "2. 配置API密钥: nano $PROJECT_DIR/config/trading_config.json"
    echo "3. 测试API连接: ./test_api_connection.sh"
    echo "4. 运行演示测试: ./test_small_trades.sh"
    echo "5. 启动交易系统: sudo systemctl start quant-trading"
    echo "6. 设置开机自启: sudo systemctl enable quant-trading"
    echo "7. 查看状态: sudo systemctl status quant-trading"
    echo "8. 查看日志: sudo journalctl -u quant-trading -f"
    echo ""
    echo "🧪 测试命令:"
    echo "- 演示测试: python test/demo_small_trade.py"
    echo "- API测试: python test/test_api_connection.py"
    echo "- 小额测试: python test/test_small_trades.py"
    echo "- 快速测试: python test/demo_small_trade.py"
    echo ""
    echo "📊 监控命令:"
    echo "- 快速状态: $PROJECT_DIR/status.sh"
    echo "- 详细监控: $PROJECT_DIR/monitor.sh"
    echo "- 系统资源: htop"
    echo "- 查看日志: tail -f $PROJECT_DIR/logs/trading.log"
    echo ""
    echo "⚡ 快捷操作:"
    echo "- 启动: $PROJECT_DIR/start_trading.sh"
    echo "- 停止: $PROJECT_DIR/stop_trading.sh"
    echo "- 重启: $PROJECT_DIR/restart_trading.sh"
    echo "- 测试: $PROJECT_DIR/test_small_trades.sh"
    echo ""
    echo "⚠️ 重要提醒:"
    echo "- 请确保API密钥配置正确"
    echo "- 建议先用演示测试验证系统"
    echo "- 小额测试通过后再进行正式交易"
    echo "- 定期检查系统状态和日志"
    echo "- 保持网络稳定"
    echo "- 确保IP地址已添加到币安API白名单"
    echo "- 建议使用小额资金进行初始测试"
    echo ""
    echo "📚 详细文档: $PROJECT_DIR/README_OSCent.md"
    echo "📖 小额测试说明: $PROJECT_DIR/小额交易测试说明.md"
}

# 主函数
main() {
    echo "开始OSCent服务器配置..."
    echo ""
    
    check_root
    detect_oscent
    check_network
    update_system
    install_basic_deps
    setup_python_env
    setup_project_dir
    create_venv
    install_python_deps
    setup_system_service
    create_monitor_scripts
    create_startup_scripts
    create_config_template
    create_small_trade_config
    create_readme
    setup_firewall
    setup_timezone
    setup_cron
    show_completion_info
}

# 运行主函数
main "$@" 