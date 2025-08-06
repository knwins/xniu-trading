#!/bin/bash
# 权限测试脚本

echo "=== 权限测试脚本 ==="
echo "当前用户: $(whoami)"
echo "当前用户ID: $EUID"
echo "当前目录: $(pwd)"

# 测试 /opt 目录权限
echo ""
echo "=== 测试 /opt 目录权限 ==="
if [[ -d "/opt" ]]; then
    echo "✅ /opt 目录存在"
    ls -ld /opt
else
    echo "❌ /opt 目录不存在"
fi

# 测试创建项目目录
echo ""
echo "=== 测试创建项目目录 ==="
PROJECT_DIR="/opt/xniu-trading"

if [[ $EUID -eq 0 ]]; then
    echo "🔧 使用root权限创建目录..."
    mkdir -p $PROJECT_DIR
    chmod 755 $PROJECT_DIR
    echo "✅ 目录创建完成"
else
    echo "🔧 使用sudo权限创建目录..."
    sudo mkdir -p $PROJECT_DIR
    sudo chown $USER:$USER $PROJECT_DIR
    echo "✅ 目录创建完成"
fi

# 检查目录权限
echo ""
echo "=== 检查目录权限 ==="
ls -ld $PROJECT_DIR

# 测试写入权限
echo ""
echo "=== 测试写入权限 ==="
TEST_FILE="$PROJECT_DIR/test.txt"
echo "测试内容" > $TEST_FILE 2>/dev/null
if [[ $? -eq 0 ]]; then
    echo "✅ 写入权限正常"
    rm $TEST_FILE
else
    echo "❌ 写入权限失败"
fi

echo ""
echo "=== 测试完成 ===" 