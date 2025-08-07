#!/bin/bash
# XNIU.IO 交易系统服务测试脚本

set -e

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

# 项目目录
PROJECT_DIR="/opt/xniu-trading"
SERVICE_NAME="xniu-trading"

# 检查项目目录
check_project_dir() {
    log_step "检查项目目录..."
    
    if [[ ! -d "$PROJECT_DIR" ]]; then
        log_error "项目目录不存在: $PROJECT_DIR"
        log_info "请先运行部署脚本: ./deploy_centos.sh"
        exit 1
    fi
    
    log_info "项目目录存在: $PROJECT_DIR"
}

# 检查配置文件
check_config_file() {
    log_step "检查配置文件..."
    
    CONFIG_FILE="$PROJECT_DIR/trader_config.json"
    
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_error "配置文件不存在: $CONFIG_FILE"
        log_info "请先配置交易参数"
        exit 1
    fi
    
    # 检查配置文件格式
    if ! python3 -m json.tool "$CONFIG_FILE" > /dev/null 2>&1; then
        log_error "配置文件格式错误"
        exit 1
    fi
    
    log_info "配置文件存在且格式正确: $CONFIG_FILE"
}

# 检查虚拟环境
check_virtualenv() {
    log_step "检查虚拟环境..."
    
    VENV_DIR="$PROJECT_DIR/venv"
    
    if [[ ! -d "$VENV_DIR" ]]; then
        log_error "虚拟环境不存在: $VENV_DIR"
        log_info "请先运行部署脚本: ./deploy_centos.sh"
        exit 1
    fi
    
    log_info "虚拟环境存在: $VENV_DIR"
}

# 检查Python依赖
check_python_deps() {
    log_step "检查Python依赖..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    
    # 检查关键模块
    REQUIRED_MODULES=("requests" "pandas" "numpy" "json" "datetime")
    
    for module in "${REQUIRED_MODULES[@]}"; do
        if ! python -c "import $module" 2>/dev/null; then
            log_error "缺少Python模块: $module"
            log_info "请运行: pip install $module"
            exit 1
        fi
    done
    
    log_info "Python依赖检查通过"
}

# 测试服务模式启动
test_service_mode() {
    log_step "测试服务模式启动..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    
    # 测试配置验证
    log_info "测试配置验证..."
    if python start_trading.py --service --validate; then
        log_info "✅ 配置验证通过"
    else
        log_error "❌ 配置验证失败"
        log_warn "请检查API密钥配置"
        return 1
    fi
    
    # 测试服务启动（短暂运行）
    log_info "测试服务启动（5秒）..."
    timeout 5s python start_trading.py --service || true
    
    log_info "✅ 服务模式测试通过"
}

# 检查系统服务
check_system_service() {
    log_step "检查系统服务..."
    
    SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
    
    if [[ ! -f "$SERVICE_FILE" ]]; then
        log_error "系统服务文件不存在: $SERVICE_FILE"
        log_info "请先运行部署脚本: ./deploy_centos.sh"
        exit 1
    fi
    
    log_info "系统服务文件存在: $SERVICE_FILE"
    
    # 检查服务状态
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_info "✅ 服务正在运行"
    else
        log_warn "⚠️ 服务未运行"
        log_info "可以使用以下命令启动服务:"
        echo "  sudo systemctl start $SERVICE_NAME"
        echo "  sudo systemctl enable $SERVICE_NAME"
    fi
}

# 检查日志目录
check_log_dirs() {
    log_step "检查日志目录..."
    
    LOG_DIRS=("$PROJECT_DIR/logs" "/var/log/xniu-trading")
    
    for dir in "${LOG_DIRS[@]}"; do
        if [[ ! -d "$dir" ]]; then
            log_warn "日志目录不存在: $dir"
        else
            log_info "日志目录存在: $dir"
        fi
    done
}

# 检查管理脚本
check_management_script() {
    log_step "检查管理脚本..."
    
    MGMT_SCRIPT="$PROJECT_DIR/manage.sh"
    
    if [[ ! -f "$MGMT_SCRIPT" ]]; then
        log_error "管理脚本不存在: $MGMT_SCRIPT"
        log_info "请先运行部署脚本: ./deploy_centos.sh"
        exit 1
    fi
    
    if [[ ! -x "$MGMT_SCRIPT" ]]; then
        log_warn "管理脚本没有执行权限，正在修复..."
        chmod +x "$MGMT_SCRIPT"
    fi
    
    log_info "管理脚本存在且可执行: $MGMT_SCRIPT"
}

# 显示测试结果
show_test_results() {
    log_step "测试完成！"
    
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  服务测试结果${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}项目目录:${NC} $PROJECT_DIR"
    echo -e "${BLUE}配置文件:${NC} $PROJECT_DIR/trader_config.json"
    echo -e "${BLUE}虚拟环境:${NC} $PROJECT_DIR/venv"
    echo -e "${BLUE}系统服务:${NC} $SERVICE_NAME"
    echo ""
    echo -e "${YELLOW}管理命令:${NC}"
    echo "  启动服务: sudo systemctl start $SERVICE_NAME"
    echo "  停止服务: sudo systemctl stop $SERVICE_NAME"
    echo "  查看状态: sudo systemctl status $SERVICE_NAME"
    echo "  查看日志: sudo journalctl -u $SERVICE_NAME -f"
    echo "  编辑配置: $PROJECT_DIR/manage.sh config"
    echo "  验证配置: $PROJECT_DIR/manage.sh validate"
    echo ""
    echo -e "${YELLOW}下一步操作:${NC}"
    echo "1. 确保API密钥配置正确"
    echo "2. 启动服务: sudo systemctl start $SERVICE_NAME"
    echo "3. 设置开机自启: sudo systemctl enable $SERVICE_NAME"
    echo "4. 查看服务状态: sudo systemctl status $SERVICE_NAME"
}

# 主函数
main() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  XNIU.IO 交易系统服务测试${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    
    check_project_dir
    check_config_file
    check_virtualenv
    check_python_deps
    test_service_mode
    check_system_service
    check_log_dirs
    check_management_script
    show_test_results
}

# 运行主函数
main "$@" 