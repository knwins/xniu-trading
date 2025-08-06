#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版本控制管理脚本
统一管理版本号、日期和文件信息
"""

import os
import re
import json
from datetime import datetime

class SimpleVersionControl:
    def __init__(self):
        self.version_file = "VERSION"
        self.info_file = "version.json"
        self.md_files = [
            "README.md",
            "README_TRADING.md", 
            "API_TROUBLESHOOTING.md",
            "量化交易系统完整部署指南.md"
        ]
        
    def get_version(self):
        """获取当前版本号"""
        if os.path.exists(self.version_file):
            with open(self.version_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        return "1.0.0"
    
    def set_version(self, version):
        """设置版本号"""
        with open(self.version_file, 'w', encoding='utf-8') as f:
            f.write(version)
        print(f"✅ 版本号: {version}")
    
    def update_md_files(self, version):
        """更新所有.md文件的版本号和日期"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        for md_file in self.md_files:
            if os.path.exists(md_file):
                self.update_single_file(md_file, version, current_date)
    
    def update_single_file(self, file_path, version, date):
        """更新单个文件的版本号和日期"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 更新版本号模式
            patterns = [
                r'(### v)(\d+\.\d+\.\d+)(\s*\([^)]+\))',
                r'(## 📝 更新日志\n\n### v)(\d+\.\d+\.\d+)(\s*\([^)]+\))'
            ]
            
            updated = False
            for pattern in patterns:
                if re.search(pattern, content):
                    replacement = rf'\g<1>{version} ({date})'
                    content = re.sub(pattern, replacement, content)
                    updated = True
                    break
            
            # 如果没有找到版本号，添加新的
            if not updated:
                if '## 📝 更新日志' in content:
                    version_section = f'\n### v{version} ({date})\n- 版本更新\n'
                    content = content.replace('## 📝 更新日志', f'## 📝 更新日志{version_section}')
                else:
                    version_section = f'\n\n## 📝 更新日志\n\n### v{version} ({date})\n- 版本更新\n'
                    content += version_section
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ {file_path}")
            
        except Exception as e:
            print(f"❌ {file_path}: {e}")
    
    def create_info_json(self, version):
        """创建version.json文件"""
        info = {
            "version": version,
            "release_date": datetime.now().strftime("%Y-%m-%d"),
            "files": {
                "python_files": [
                    "main.py", "trader.py", "start_trading.py", "data_loader.py",
                    "feature_engineer.py", "strategy.py", "backtester.py",
                    "demo_small_trade.py"
                ],
                "md_files": self.md_files,
                "config_files": [
                    "requirements.txt", "trading_config.json", "centos_setup.sh"
                ]
            },
            "description": "智能量化交易系统 - 统一版本控制"
        }
        
        with open(self.info_file, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        
        print(f"✅ {self.info_file}")
    
    def show_status(self):
        """显示当前状态"""
        version = self.get_version()
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        print(f"📋 当前状态:")
        print(f"   版本号: v{version}")
        print(f"   日期: {current_date}")
        print(f"   文件数: {len(self.md_files)}")
        
        print(f"\n📁 文件状态:")
        for md_file in self.md_files:
            status = "✅" if os.path.exists(md_file) else "❌"
            print(f"   {status} {md_file}")
    
    def update_all(self, new_version=None):
        """更新所有版本信息"""
        if new_version:
            self.set_version(new_version)
            version = new_version
        else:
            version = self.get_version()
        
        print(f"\n🔄 更新文件...")
        self.update_md_files(version)
        self.create_info_json(version)
        print(f"\n🎉 更新完成! 版本: v{version}")

def main():
    """主函数"""
    vc = SimpleVersionControl()
    
    print("🚀 简化版本控制工具")
    print("=" * 40)
    
    # 显示当前状态
    vc.show_status()
    
    # 交互式操作
    print(f"\n选择操作:")
    print("1. 显示状态")
    print("2. 更新版本号")
    print("3. 更新所有文件")
    print("4. 退出")
    
    choice = input("\n请输入选择 (1-4): ").strip()
    
    if choice == "1":
        vc.show_status()
    elif choice == "2":
        new_version = input("请输入新版本号 (格式: x.y.z): ").strip()
        if re.match(r'^\d+\.\d+\.\d+$', new_version):
            vc.update_all(new_version)
        else:
            print("❌ 版本号格式错误")
    elif choice == "3":
        vc.update_all()
    elif choice == "4":
        print("👋 退出")
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main() 