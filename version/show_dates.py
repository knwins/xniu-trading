#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日期显示脚本
显示所有.md文件中的版本日期信息
"""

import os
import re
import json
from datetime import datetime

def show_all_dates():
    """显示所有文件的日期信息"""
    print("📅 文件日期信息")
    print("=" * 50)
    
    md_files = [
        "README.md",
        "README_TRADING.md", 
        "API_TROUBLESHOOTING.md",
        "小额交易测试完整指南.md",
        "量化交易系统完整部署指南.md",
        "CONTROL.md",
        "版本控制使用说明.md"
    ]
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    print(f"📅 当前日期: {current_date}")
    print()
    
    for md_file in md_files:
        if os.path.exists(md_file):
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找版本号中的日期
            date_match = re.search(r'### v\d+\.\d+\.\d+\s*\(([^)]+)\)', content)
            if date_match:
                date = date_match.group(1)
                status = "✅" if date == current_date else "⚠️"
                print(f"{status} {md_file}: {date}")
            else:
                print(f"❌ {md_file}: 未找到日期")
        else:
            print(f"❌ {md_file}: 文件不存在")
    
    # 检查info.json
    if os.path.exists("info.json"):
        with open("info.json", 'r', encoding='utf-8') as f:
            info = json.load(f)
        json_date = info.get("release_date", "N/A")
        status = "✅" if json_date == current_date else "⚠️"
        print(f"{status} info.json: {json_date}")
    else:
        print("❌ info.json: 文件不存在")
    
    print()
    print("📊 说明:")
    print("   ✅ - 日期与当前日期一致")
    print("   ⚠️  - 日期与当前日期不一致")
    print("   ❌ - 文件不存在或未找到日期")

def main():
    """主函数"""
    print("🚀 Xniu-trading 日期信息查看工具")
    print("=" * 50)
    
    show_all_dates()
    
    print("\n💡 提示:")
    print("   - 运行 python update_dates.py 更新日期")
    print("   - 运行 python info.py 更新版本号")

if __name__ == "__main__":
    main() 