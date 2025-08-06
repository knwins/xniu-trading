# 🔧 API故障排除指南

## 常见错误及解决方案

### 1. 400 Bad Request 错误

**错误信息**: `400 Client Error: Bad Request for url: https://fapi.binance.com/fapi/v2/account`

**可能原因**:
- API密钥格式错误
- 签名生成错误
- 参数格式错误

**解决方案**:
1. 检查API密钥和密钥是否正确
2. 确保时间戳格式正确
3. 验证签名算法

### 2. 401 Unauthorized 错误

**错误信息**: `{"code":-2015,"msg":"Invalid API-key, IP, or permissions for action"}`

**可能原因**:
- API密钥错误
- IP白名单限制
- API权限不足

**解决方案**:

#### 2.1 检查API密钥
```bash
# 运行API测试脚本
python test/test_api_connection.py
```

#### 2.2 配置IP白名单
1. 登录币安账户
2. 进入"API管理"
3. 找到您的API密钥
4. 点击"编辑限制"
5. 在"IP白名单"中添加您的IP地址

**获取当前IP地址**:
```bash
# Windows
curl ifconfig.me

# Linux/Mac
curl ifconfig.me
# 或者
wget -qO- ifconfig.me
```

#### 2.3 检查API权限
确保API密钥有以下权限：
- ✅ 读取信息
- ✅ 现货及杠杆交易
- ✅ 合约交易

### 3. 403 Forbidden 错误

**错误信息**: `403 Forbidden`

**可能原因**:
- API密钥被禁用
- 账户被限制
- 权限不足

**解决方案**:
1. 检查API密钥状态
2. 确认账户状态
3. 联系币安客服

### 4. 429 Too Many Requests 错误

**错误信息**: `429 Too Many Requests`

**可能原因**:
- API调用频率过高
- 超出请求限制

**解决方案**:
1. 降低请求频率
2. 增加请求间隔
3. 使用更高级别的API密钥

## 🔍 诊断步骤

### 步骤1: 运行API测试
```bash
python test/test_api_connection.py
```

### 步骤2: 检查网络连接
```bash
# 测试币安服务器连接
ping fapi.binance.com

# 测试API端点
curl https://fapi.binance.com/fapi/v1/ping
```

### 步骤3: 验证配置
```bash
# 检查配置文件
cat config/trading_config.json
```

### 步骤4: 检查时间同步
```bash
# 获取币安服务器时间
curl https://fapi.binance.com/fapi/v1/time

# 检查本地时间
date
```

## 🛠️ 修复工具

### 1. API测试脚本
```bash
python test/test_api_connection.py
```

### 2. 配置验证脚本
```python
import json
import os

def validate_config():
    config_file = 'config/trading_config.json'
    if not os.path.exists(config_file):
        print("❌ 配置文件不存在")
        return False
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    required_fields = ['api_key', 'secret_key', 'base_url']
    for field in required_fields:
        if field not in config:
            print(f"❌ 缺少必要字段: {field}")
            return False
    
    print("✅ 配置文件格式正确")
    return True

if __name__ == "__main__":
    validate_config()
```

## 📋 检查清单

### API配置检查
- [ ] API密钥格式正确（64位字符）
- [ ] 密钥格式正确（64位字符）
- [ ] Base URL正确（https://fapi.binance.com）
- [ ] 配置文件存在且可读

### 权限检查
- [ ] API密钥已启用
- [ ] 具有读取权限
- [ ] 具有交易权限（如需要）
- [ ] IP白名单配置正确

### 网络检查
- [ ] 网络连接正常
- [ ] 可以访问币安服务器
- [ ] 防火墙未阻止请求
- [ ] 代理设置正确（如使用）

### 时间同步检查
- [ ] 本地时间与服务器时间同步
- [ ] 时间差小于5秒
- [ ] 时区设置正确 (香港时区 - Asia/Hong_Kong)

## 🚨 紧急处理

### 如果API密钥泄露
1. 立即禁用API密钥
2. 创建新的API密钥
3. 更新配置文件
4. 检查账户安全

### 如果账户被限制
1. 联系币安客服
2. 提供必要信息
3. 等待处理结果
4. 考虑使用新账户

## 📞 获取帮助

### 币安官方支持
- 客服邮箱: support@binance.com
- 在线客服: https://www.binance.com/zh-CN/support
- API文档: https://binance-docs.github.io/apidocs/

### 项目支持
- GitHub Issues: [项目Issues页面](https://github.com/knwins/xniu-trading/issues)
- 文档: [项目Wiki页面](https://github.com/knwins/xniu-trading/wiki)

## ⚠️ 安全提醒

1. **保护API密钥**
   - 不要分享API密钥
   - 定期更换API密钥
   - 使用最小权限原则

2. **网络安全**
   - 使用安全的网络连接
   - 避免在公共WiFi使用
   - 定期检查账户活动

3. **监控异常**
   - 定期检查API调用记录
   - 监控账户余额变化
   - 关注异常登录活动

---

**重要**: 如果问题持续存在，请先检查币安官方状态页面，确认服务是否正常。

## 📝 版本信息

### v1.0.1 (2025-08-06)
- 初始版本发布
- 完整的API故障排除指南
- 详细的错误诊断步骤
- 安全检查清单
- 统一时区配置 (香港时区) 