#!/bin/bash
# OSCent量化交易系统一键配置脚本 - 精简版
# 专门针对OSCent (基于CentOS) 服务器优化

set -e

echo "🚀 OSCent量化交易系统一键配置脚本"
echo "========================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 检测系统
detect_system() {
    log_info "检测操作系统..."
    
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        log_error "无法检测操作系统"
        exit 1
    fi
    
    if [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"OSCent"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
        log_success "检测到OSCent/CentOS系统: $OS $VER"
    else
        log_warning "当前系统: $OS $VER"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 检查网络连接
check_network() {
    log_info "检查网络连接..."
    
    if ping -c 1 8.8.8.8 &> /dev/null; then
        log_success "网络连接正常"
    else
        log_error "网络连接失败，请检查网络设置"
        exit 1
    fi
    
    if curl -s --connect-timeout 10 https://fapi.binance.com/fapi/v1/ping &> /dev/null; then
        log_success "币安API连接正常"
    else
        log_warning "币安API连接失败，可能影响交易功能"
    fi
}

# 更新系统
update_system() {
    log_info "更新系统包..."
    sudo yum update -y
    
    if ! rpm -q epel-release &> /dev/null; then
        log_info "安装EPEL源..."
        sudo yum install -y epel-release
    fi
    
    log_success "系统更新完成"
}

# 安装基础依赖
install_basic_deps() {
    log_info "安装基础依赖..."
    
    sudo yum groupinstall -y "Development Tools"
    sudo yum install -y python3 python3-pip python3-devel git curl wget vim
    
    log_success "基础依赖安装完成"
}

# 创建项目目录
setup_project_dir() {
    log_info "设置项目目录..."
    
    PROJECT_DIR="/opt/quant-trading"
    sudo mkdir -p $PROJECT_DIR
    sudo chown $USER:$USER $PROJECT_DIR
    cd $PROJECT_DIR
    
    mkdir -p {logs,config,data,scripts}
    
    log_success "项目目录: $PROJECT_DIR"
}

# 创建Python虚拟环境
create_venv() {
    log_info "创建Python虚拟环境..."
    
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    
    log_success "Python虚拟环境创建完成"
}

# 安装Python依赖
install_python_deps() {
    log_info "安装Python依赖..."
    
    pip install pandas numpy matplotlib requests python-dotenv
    pip install ccxt websocket-client
    pip install ta schedule psutil
    
    log_success "Python依赖安装完成"
}

# 配置系统服务
setup_system_service() {
    log_info "配置系统服务..."
    
    sudo tee /etc/systemd/system/quant-trading.service > /dev/null <<EOF
[Unit]
Description=量化交易系统
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/trader.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    log_success "系统服务配置完成"
}

# 创建启动脚本
create_startup_scripts() {
    log_info "创建启动脚本..."
    
    cat > start_trading.sh << 'EOF'
#!/bin/bash
echo "🚀 启动量化交易系统..."
source venv/bin/activate
python trader.py
EOF

    cat > stop_trading.sh << 'EOF'
#!/bin/bash
echo "🛑 停止量化交易系统..."
pkill -f "trader.py"
echo "交易系统已停止"
EOF

    cat > status.sh << 'EOF'
#!/bin/bash
echo "=== 量化交易系统状态 ==="
if pgrep -f "trader.py" > /dev/null; then
    echo "✅ 交易进程: 运行中"
else
    echo "❌ 交易进程: 未运行"
fi
EOF

    chmod +x *.sh
    log_success "启动脚本创建完成"
}

# 创建配置文件
create_config() {
    log_info "创建配置文件..."
    
    cat > trading_config.json << 'EOF'
{
  "api_key": "YOUR_API_KEY_HERE",
  "secret_key": "YOUR_SECRET_KEY_HERE",
  "symbol": "ETHUSDT",
  "initial_balance": 1000.0,
  "max_position_size": 0.1,
  "stop_loss_pct": 0.05,
  "take_profit_pct": 0.1,
  "base_url": "https://fapi.binance.com",
  "testnet": false
}
EOF

    log_success "配置文件创建完成"
}

# 设置时区
setup_timezone() {
    log_info "设置时区为香港时区..."
    sudo timedatectl set-timezone Asia/Hong_Kong
    log_success "时区设置完成"
}

# 显示完成信息
show_completion_info() {
    echo ""
    echo "🎉 OSCent服务器配置完成!"
    echo "========================================"
    echo "📁 项目目录: $PROJECT_DIR"
    echo "🐍 Python环境: $PROJECT_DIR/venv"
    echo "📝 配置文件: $PROJECT_DIR/trading_config.json"
    echo ""
    echo "📋 后续步骤:"
    echo "1. 配置API密钥: nano $PROJECT_DIR/trading_config.json"
    echo "2. 上传交易代码到 $PROJECT_DIR"
    echo "3. 启动系统: sudo systemctl start quant-trading"
    echo "4. 查看状态: sudo systemctl status quant-trading"
    echo ""
    echo "⚡ 快捷操作:"
    echo "- 启动: $PROJECT_DIR/start_trading.sh"
    echo "- 停止: $PROJECT_DIR/stop_trading.sh"
    echo "- 状态: $PROJECT_DIR/status.sh"
    echo ""
    echo "⚠️ 重要提醒:"
    echo "- 请确保API密钥配置正确"
    echo "- 建议先用小额资金测试"
    echo "- 定期检查系统状态和日志"
}

# 主函数
main() {
    echo "开始OSCent服务器配置..."
    echo ""
    
    check_root
    detect_system
    check_network
    update_system
    install_basic_deps
    setup_project_dir
    create_venv
    install_python_deps
    setup_system_service
    create_startup_scripts
    create_config
    setup_timezone
    show_completion_info
}

# 运行主函数
main "$@" 