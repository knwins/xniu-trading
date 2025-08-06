#!/bin/bash
# 快速修复权限问题脚本

echo "=== XNIU.IO 交易系统权限修复脚本 ==="
echo ""

# 检查是否为root用户
if [[ $EUID -eq 0 ]]; then
    echo "✅ 检测到root用户，开始修复权限..."
else
    echo "❌ 请使用root用户运行此脚本"
    echo "使用方法: sudo ./fix_permissions.sh"
    exit 1
fi

# 修复 /opt 目录权限
echo ""
echo "🔧 修复 /opt 目录权限..."
chmod 755 /opt
echo "✅ /opt 目录权限已修复"

# 创建并修复项目目录权限
echo ""
echo "🔧 创建并修复项目目录权限..."
PROJECT_DIR="/opt/xniu-trading"

# 创建目录
mkdir -p $PROJECT_DIR

# 设置权限
chmod 755 $PROJECT_DIR
chown root:root $PROJECT_DIR

echo "✅ 项目目录权限已修复: $PROJECT_DIR"

# 创建日志目录
echo ""
echo "🔧 创建日志目录..."
mkdir -p $PROJECT_DIR/logs
mkdir -p /var/log/xniu-trading

chmod 755 $PROJECT_DIR/logs
chmod 755 /var/log/xniu-trading

echo "✅ 日志目录已创建"

# 检查权限
echo ""
echo "=== 权限检查结果 ==="
echo "项目目录权限:"
ls -ld $PROJECT_DIR
echo ""
echo "日志目录权限:"
ls -ld $PROJECT_DIR/logs
ls -ld /var/log/xniu-trading

echo ""
echo "✅ 权限修复完成！"
echo "现在可以正常运行部署脚本: ./deploy_centos.sh" 