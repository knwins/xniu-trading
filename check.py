#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本一致性检查脚本
用于快速验证所有.md文件的版本号是否一致
"""

import os
import re
import json
from datetime import datetime

def check_version_consistency():
    """检查版本一致性"""
    print("🔍 版本一致性检查")
    print("=" * 50)
    
    # 读取VERSION文件
    version_file = "VERSION"
    if os.path.exists(version_file):
        with open(version_file, 'r', encoding='utf-8') as f:
            main_version = f.read().strip()
        print(f"📋 主版本号: v{main_version}")
    else:
        print("❌ VERSION文件不存在")
        return False
    
    # 检查.md文件
    md_files = [
        "README.md",
        "README_TRADING.md", 
        "API_TROUBLESHOOTING.md",
        "小额交易测试完整指南.md",
        "量化交易系统完整部署指南.md",
        "CONTROL.md"
    ]
    
    inconsistent_files = []
    consistent_count = 0
    
    for md_file in md_files:
        if os.path.exists(md_file):
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找版本号
            version_match = re.search(r'### v(\d+\.\d+\.\d+)', content)
            if version_match:
                file_version = version_match.group(1)
                if file_version == main_version:
                    print(f"✅ {md_file}: v{file_version}")
                    consistent_count += 1
                else:
                    print(f"❌ {md_file}: v{file_version} (应为 v{main_version})")
                    inconsistent_files.append(md_file)
            else:
                print(f"⚠️  {md_file}: 未找到版本号")
                inconsistent_files.append(md_file)
        else:
            print(f"❌ {md_file}: 文件不存在")
            inconsistent_files.append(md_file)
    
    # 检查info.json
    if os.path.exists("info.json"):
        with open("info.json", 'r', encoding='utf-8') as f:
            version_info = json.load(f)
        
        json_version = version_info.get("version", "")
        if json_version == main_version:
            print(f"✅ info.json: v{json_version}")
            consistent_count += 1
        else:
            print(f"❌ info.json: v{json_version} (应为 v{main_version})")
            inconsistent_files.append("info.json")
    else:
        print("❌ info.json: 文件不存在")
        inconsistent_files.append("info.json")
    
    # 总结
    print("\n" + "=" * 50)
    total_files = len(md_files) + 1  # +1 for info.json
    print(f"📊 检查结果:")
    print(f"   总文件数: {total_files}")
    print(f"   一致文件数: {consistent_count}")
    print(f"   不一致文件数: {len(inconsistent_files)}")
    
    if inconsistent_files:
        print(f"\n❌ 不一致的文件:")
        for file in inconsistent_files:
            print(f"   - {file}")
        return False
    else:
        print(f"\n🎉 所有文件版本一致!")
        return True

def show_version_info():
    """显示版本信息"""
    print("\n📋 版本信息")
    print("=" * 30)
    
    # 读取VERSION文件
    if os.path.exists("VERSION"):
        with open("VERSION", 'r', encoding='utf-8') as f:
            version = f.read().strip()
        print(f"版本号: v{version}")
    else:
        print("版本号: 未设置")
    
    # 读取info.json
    if os.path.exists("info.json"):
        with open("info.json", 'r', encoding='utf-8') as f:
            info = json.load(f)
        
        print(f"发布日期: {info.get('release_date', 'N/A')}")
        print(f"描述: {info.get('description', 'N/A')}")
        
        files = info.get('files', {})
        if files:
            print(f"\n📁 文件统计:")
            print(f"   Python文件: {len(files.get('python_files', []))}")
            print(f"   MD文件: {len(files.get('md_files', []))}")
            print(f"   配置文件: {len(files.get('config_files', []))}")
    else:
        print("info.json: 文件不存在")

def main():
    """主函数"""
    print("🚀 Xniu-trading 版本一致性检查工具")
    print("=" * 50)
    
    # 检查版本一致性
    is_consistent = check_version_consistency()
    
    # 显示版本信息
    show_version_info()
    
    if is_consistent:
        print("\n✅ 所有文件版本一致，可以安全发布!")
    else:
        print("\n❌ 发现版本不一致，请运行 python info.py 更新版本号")

if __name__ == "__main__":
    main() 