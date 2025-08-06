#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日期更新脚本
将所有.md文件中的"2024-12-19"更新为实际日期
"""

import os
import re
from datetime import datetime

class DateUpdater:
    def __init__(self):
        self.md_files = [
            "README.md",
            "README_TRADING.md", 
            "API_TROUBLESHOOTING.md",
            "小额交易测试完整指南.md",
            "量化交易系统完整部署指南.md",
            "CONTROL.md",
            "版本控制使用说明.md"
        ]
        self.old_date = "2024-12-19"
        self.new_date = datetime.now().strftime("%Y-%m-%d")
        
    def update_file_dates(self, file_path):
        """更新单个文件的日期"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 更新版本号中的日期
            pattern1 = r'(### v\d+\.\d+\.\d+\s*\()' + re.escape(self.old_date) + r'\)'
            replacement1 = rf'\g<1>{self.new_date})'
            content = re.sub(pattern1, replacement1, content)
            
            # 更新其他可能的日期格式
            pattern2 = r'(\d{4}-\d{2}-\d{2})'
            if self.old_date in content:
                content = content.replace(self.old_date, self.new_date)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ 已更新 {file_path} 的日期为 {self.new_date}")
            
        except Exception as e:
            print(f"❌ 更新 {file_path} 时出错: {e}")
    
    def update_all_files(self):
        """更新所有文件的日期"""
        print(f"🔄 开始更新日期: {self.old_date} -> {self.new_date}")
        print("=" * 50)
        
        updated_count = 0
        for md_file in self.md_files:
            if os.path.exists(md_file):
                self.update_file_dates(md_file)
                updated_count += 1
            else:
                print(f"⚠️  {md_file}: 文件不存在")
        
        print(f"\n📊 更新完成:")
        print(f"   更新文件数: {updated_count}")
        print(f"   新日期: {self.new_date}")
    
    def show_current_dates(self):
        """显示当前文件中的日期"""
        print("📅 当前文件中的日期:")
        print("=" * 30)
        
        for md_file in self.md_files:
            if os.path.exists(md_file):
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 查找版本号中的日期
                date_match = re.search(r'### v\d+\.\d+\.\d+\s*\(([^)]+)\)', content)
                if date_match:
                    date = date_match.group(1)
                    print(f"   {md_file}: {date}")
                else:
                    print(f"   {md_file}: 未找到日期")

def main():
    """主函数"""
    updater = DateUpdater()
    
    print("🚀 Xniu-trading 日期更新工具")
    print("=" * 50)
    
    # 显示当前日期
    print(f"📅 当前日期: {updater.new_date}")
    print(f"🔄 将更新: {updater.old_date} -> {updater.new_date}")
    
    # 显示当前文件中的日期
    updater.show_current_dates()
    
    # 询问是否更新
    choice = input(f"\n是否将所有文件中的 '{updater.old_date}' 更新为 '{updater.new_date}'? (y/n): ").lower().strip()
    
    if choice == 'y':
        updater.update_all_files()
        print("\n🎉 日期更新完成!")
    else:
        print("\n❌ 取消更新")

if __name__ == "__main__":
    main() 