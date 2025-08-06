#!/bin/bash
# XNIU.IO 交易系统 CentOS 部署脚本
# 适用于 CentOS 7/8 和 RHEL 7/8

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "请不要使用root用户运行此脚本"
        exit 1
    fi
}

# 检查系统版本
check_system() {
    log_step "检查系统版本..."
    
    if [[ -f /etc/redhat-release ]]; then
        OS_VERSION=$(cat /etc/redhat-release)
        log_info "检测到系统: $OS_VERSION"
    else
        log_error "不支持的操作系统，请使用CentOS或RHEL"
        exit 1
    fi
    
    # 检查是否为CentOS 7+ 或 RHEL 7+
    if [[ $OS_VERSION =~ "CentOS" ]] || [[ $OS_VERSION =~ "Red Hat" ]]; then
        log_info "系统版本支持"
    else
        log_error "请使用CentOS 7+ 或 RHEL 7+"
        exit 1
    fi
}

# 更新系统
update_system() {
    log_step "更新系统包..."
    sudo yum update -y
    log_info "系统更新完成"
}

# 安装基础依赖
install_dependencies() {
    log_step "安装基础依赖..."
    
    # 安装EPEL仓库
    sudo yum install -y epel-release
    
    # 安装基础工具
    sudo yum install -y wget curl git vim unzip
    
    # 安装开发工具
    sudo yum groupinstall -y "Development Tools"
    
    # 安装Python相关
    sudo yum install -y python3 python3-pip python3-devel
    
    # 安装其他必要包
    sudo yum install -y openssl-devel libffi-devel
    
    log_info "基础依赖安装完成"
}

# 安装Python依赖
install_python_deps() {
    log_step "安装Python依赖..."
    
    # 升级pip
    python3 -m pip install --upgrade pip
    
    # 安装虚拟环境
    python3 -m pip install virtualenv
    
    log_info "Python依赖安装完成"
}

# 创建项目目录
create_project_dir() {
    log_step "创建项目目录..."
    
    PROJECT_DIR="/opt/xniu-trading"
    sudo mkdir -p $PROJECT_DIR
    sudo chown $USER:$USER $PROJECT_DIR
    
    log_info "项目目录创建完成: $PROJECT_DIR"
}

# 创建虚拟环境
setup_virtualenv() {
    log_step "设置Python虚拟环境..."
    
    cd $PROJECT_DIR
    python3 -m virtualenv venv
    source venv/bin/activate
    
    log_info "虚拟环境创建完成"
}

# 安装Python包
install_python_packages() {
    log_step "安装Python包..."
    
    source venv/bin/activate
    
    # 安装基础包
    pip install requests pandas numpy scikit-learn matplotlib seaborn
    
    # 安装日志相关
    pip install python-json-logger
    
    # 安装其他可能需要的包
    pip install schedule psutil
    
    log_info "Python包安装完成"
}

# 创建系统服务
create_systemd_service() {
    log_step "创建系统服务..."
    
    SERVICE_FILE="/etc/systemd/system/xniu-trading.service"
    
    sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=XNIU.IO Trading System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python start_trading.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    # 重新加载systemd
    sudo systemctl daemon-reload
    
    log_info "系统服务创建完成"
}

# 创建日志目录
setup_logging() {
    log_step "设置日志目录..."
    
    mkdir -p $PROJECT_DIR/logs
    mkdir -p /var/log/xniu-trading
    
    # 创建日志轮转配置
    sudo tee /etc/logrotate.d/xniu-trading > /dev/null <<EOF
/var/log/xniu-trading/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
}
EOF

    log_info "日志配置完成"
}

# 创建防火墙规则
setup_firewall() {
    log_step "配置防火墙..."
    
    # 检查防火墙状态
    if command -v firewall-cmd &> /dev/null; then
        # 开放SSH端口（如果还没开放）
        sudo firewall-cmd --permanent --add-service=ssh
        
        # 重新加载防火墙
        sudo firewall-cmd --reload
        
        log_info "防火墙配置完成"
    else
        log_warn "未检测到firewalld，跳过防火墙配置"
    fi
}

# 创建监控脚本
create_monitor_script() {
    log_step "创建监控脚本..."
    
    MONITOR_SCRIPT="$PROJECT_DIR/monitor.sh"
    
    tee $MONITOR_SCRIPT > /dev/null <<EOF
#!/bin/bash
# XNIU.IO 交易系统监控脚本

PROJECT_DIR="$PROJECT_DIR"
LOG_FILE="/var/log/xniu-trading/monitor.log"

# 检查服务状态
check_service() {
    if systemctl is-active --quiet xniu-trading; then
        echo "\$(date): 服务运行正常" >> \$LOG_FILE
    else
        echo "\$(date): 服务未运行，尝试重启" >> \$LOG_FILE
        systemctl restart xniu-trading
    fi
}

# 检查磁盘空间
check_disk() {
    DISK_USAGE=\$(df -h \$PROJECT_DIR | awk 'NR==2 {print \$5}' | sed 's/%//')
    if [ \$DISK_USAGE -gt 80 ]; then
        echo "\$(date): 磁盘使用率过高: \${DISK_USAGE}%" >> \$LOG_FILE
    fi
}

# 检查内存使用
check_memory() {
    MEMORY_USAGE=\$(free | awk 'NR==2{printf "%.2f", \$3*100/\$2}')
    if (( \$(echo "\$MEMORY_USAGE > 80" | bc -l) )); then
        echo "\$(date): 内存使用率过高: \${MEMORY_USAGE}%" >> \$LOG_FILE
    fi
}

# 主函数
main() {
    check_service
    check_disk
    check_memory
}

main
EOF

    chmod +x $MONITOR_SCRIPT
    
    # 添加到crontab
    (crontab -l 2>/dev/null; echo "*/5 * * * * $MONITOR_SCRIPT") | crontab -
    
    log_info "监控脚本创建完成"
}

# 创建备份脚本
create_backup_script() {
    log_step "创建备份脚本..."
    
    BACKUP_SCRIPT="$PROJECT_DIR/backup.sh"
    
    tee $BACKUP_SCRIPT > /dev/null <<EOF
#!/bin/bash
# XNIU.IO 交易系统备份脚本

PROJECT_DIR="$PROJECT_DIR"
BACKUP_DIR="/opt/backups/xniu-trading"
DATE=\$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p \$BACKUP_DIR

# 备份配置文件
cp \$PROJECT_DIR/trader_config.json \$BACKUP_DIR/trader_config_\$DATE.json

# 备份日志文件
tar -czf \$BACKUP_DIR/logs_\$DATE.tar.gz -C \$PROJECT_DIR logs/

# 删除7天前的备份
find \$BACKUP_DIR -name "*.json" -mtime +7 -delete
find \$BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "备份完成: \$DATE"
EOF

    chmod +x $BACKUP_SCRIPT
    
    # 添加到crontab（每天凌晨2点备份）
    (crontab -l 2>/dev/null; echo "0 2 * * * $BACKUP_SCRIPT") | crontab -
    
    log_info "备份脚本创建完成"
}

# 创建管理脚本
create_management_script() {
    log_step "创建管理脚本..."
    
    MGMT_SCRIPT="$PROJECT_DIR/manage.sh"
    
    tee $MGMT_SCRIPT > /dev/null <<EOF
#!/bin/bash
# XNIU.IO 交易系统管理脚本

PROJECT_DIR="$PROJECT_DIR"
SERVICE_NAME="xniu-trading"

case "\$1" in
    start)
        echo "启动交易系统..."
        systemctl start \$SERVICE_NAME
        ;;
    stop)
        echo "停止交易系统..."
        systemctl stop \$SERVICE_NAME
        ;;
    restart)
        echo "重启交易系统..."
        systemctl restart \$SERVICE_NAME
        ;;
    status)
        echo "查看服务状态..."
        systemctl status \$SERVICE_NAME
        ;;
    logs)
        echo "查看服务日志..."
        journalctl -u \$SERVICE_NAME -f
        ;;
    config)
        echo "编辑配置文件..."
        vim \$PROJECT_DIR/trader_config.json
        ;;
    backup)
        echo "执行备份..."
        \$PROJECT_DIR/backup.sh
        ;;
    *)
        echo "用法: \$0 {start|stop|restart|status|logs|config|backup}"
        exit 1
        ;;
esac
EOF

    chmod +x $MGMT_SCRIPT
    
    log_info "管理脚本创建完成"
}

# 显示部署信息
show_deployment_info() {
    log_step "部署完成！"
    
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  XNIU.IO 交易系统部署完成${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}项目目录:${NC} $PROJECT_DIR"
    echo -e "${BLUE}配置文件:${NC} $PROJECT_DIR/trader_config.json"
    echo -e "${BLUE}日志目录:${NC} /var/log/xniu-trading"
    echo -e "${BLUE}备份目录:${NC} /opt/backups/xniu-trading"
    echo ""
    echo -e "${YELLOW}管理命令:${NC}"
    echo "  启动服务: $PROJECT_DIR/manage.sh start"
    echo "  停止服务: $PROJECT_DIR/manage.sh stop"
    echo "  重启服务: $PROJECT_DIR/manage.sh restart"
    echo "  查看状态: $PROJECT_DIR/manage.sh status"
    echo "  查看日志: $PROJECT_DIR/manage.sh logs"
    echo "  编辑配置: $PROJECT_DIR/manage.sh config"
    echo "  执行备份: $PROJECT_DIR/manage.sh backup"
    echo ""
    echo -e "${YELLOW}下一步操作:${NC}"
    echo "1. 编辑配置文件: vim $PROJECT_DIR/trader_config.json"
    echo "2. 启动服务: $PROJECT_DIR/manage.sh start"
    echo "3. 查看状态: $PROJECT_DIR/manage.sh status"
    echo ""
    echo -e "${RED}重要提醒:${NC}"
    echo "- 请确保API密钥配置正确"
    echo "- 建议先在测试环境验证"
    echo "- 定期检查日志和备份"
}

# 主函数
main() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  XNIU.IO 交易系统 CentOS 部署脚本${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    
    check_root
    check_system
    update_system
    install_dependencies
    install_python_deps
    create_project_dir
    setup_virtualenv
    install_python_packages
    create_systemd_service
    setup_logging
    setup_firewall
    create_monitor_script
    create_backup_script
    create_management_script
    show_deployment_info
}

# 运行主函数
main "$@" 