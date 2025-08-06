#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本信息管理脚本
用于统一管理所有.md文件的版本号
"""

import os
import re
import json
from datetime import datetime

class VersionManager:
    def __init__(self):
        self.version_file = "VERSION"
        self.md_files = [
            "README.md",
            "trade/README_TRADING.md", 
"server/API_TROUBLESHOOTING.md",
"server/小额交易测试完整指南.md",
"server/量化交易系统完整部署指南.md"
        ]
        
    def get_current_version(self):
        """获取当前版本号"""
        if os.path.exists(self.version_file):
            with open(self.version_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        return "1.0.0"
    
    def set_version(self, version):
        """设置版本号"""
        with open(self.version_file, 'w', encoding='utf-8') as f:
            f.write(version)
        print(f"✅ 版本号已更新为: {version}")
    
    def update_md_files_version(self, version):
        """更新所有.md文件的版本号"""
        for md_file in self.md_files:
            if os.path.exists(md_file):
                self.update_single_md_version(md_file, version)
    
    def update_single_md_version(self, file_path, version):
        """更新单个.md文件的版本号"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            # 更新版本号模式1: ### v1.0.0 (2025-08-06)
            pattern1 = r'(### v)(\d+\.\d+\.\d+)(\s*\([^)]+\))'
            replacement1 = rf'\g<1>{version} ({current_date})'
            content = re.sub(pattern1, replacement1, content)
            
            # 更新版本号模式2: ## 📝 更新日志\n\n### v1.0.0 (2025-08-06)
            pattern2 = r'(## 📝 更新日志\n\n### v)(\d+\.\d+\.\d+)(\s*\([^)]+\))'
            replacement2 = rf'\g<1>{version} ({current_date})'
            content = re.sub(pattern2, replacement2, content)
            
            # 如果没有找到版本号，在文件末尾添加
            if not re.search(r'### v\d+\.\d+\.\d+', content):
                # 查找合适的位置插入版本信息
                if '## 📝 更新日志' in content:
                    # 在更新日志部分添加版本信息
                    version_section = f'\n### v{version} ({current_date})\n- 版本更新\n'
                    content = content.replace('## 📝 更新日志', f'## 📝 更新日志{version_section}')
                else:
                    # 在文件末尾添加版本信息
                    version_section = f'\n\n## 📝 更新日志\n\n### v{version} ({current_date})\n- 版本更新\n'
                    content += version_section
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ 已更新 {file_path} 的版本号为 v{version}")
            
        except Exception as e:
            print(f"❌ 更新 {file_path} 时出错: {e}")
    
    def create_version_info(self):
        """创建版本信息文件"""
        version_info = {
            "version": self.get_current_version(),
            "release_date": datetime.now().strftime("%Y-%m-%d"),
            "files": {
                "python_files": [
                    "main.py",
                    "trade/trader.py", 
                    "trade/start.py",
                    "data_loader.py",
                    "feature_engineer.py",
                    "strategy.py",
                    "backtester.py",
                    "test/demo_small_trade.py",
                    "test/test_small_trades.py",
                    "test/test_api_connection.py"
                ],
                "md_files": self.md_files,
                "config_files": [
                    "server/requirements.txt",
                    "config/trading_config.json",
                    "server/centos_setup.sh"
                ]
            },
            "description": "智能量化交易系统 - 统一版本控制"
        }
        
        with open('info.json', 'w', encoding='utf-8') as f:
            json.dump(version_info, f, ensure_ascii=False, indent=2)
        
        print("✅ 已创建 info.json")
    
    def show_version_status(self):
        """显示当前版本状态"""
        current_version = self.get_current_version()
        print(f"\n📋 当前版本状态:")
        print(f"   版本号: v{current_version}")
        print(f"   发布日期: {datetime.now().strftime('%Y-%m-%d')}")
        print(f"   MD文件数量: {len(self.md_files)}")
        print(f"   已配置的文件:")
        for md_file in self.md_files:
            status = "✅" if os.path.exists(md_file) else "❌"
            print(f"     {status} {md_file}")

def main():
    """主函数"""
    vm = VersionManager()
    
    print("🚀 Xniu-trading 版本控制管理工具")
    print("=" * 50)
    
    # 显示当前状态
    vm.show_version_status()
    
    # 获取当前版本
    current_version = vm.get_current_version()
    
    # 询问是否更新版本
    print(f"\n当前版本: v{current_version}")
    choice = input("是否更新版本号? (y/n): ").lower().strip()
    
    if choice == 'y':
        new_version = input("请输入新版本号 (格式: x.y.z): ").strip()
        if re.match(r'^\d+\.\d+\.\d+$', new_version):
            # 更新版本号
            vm.set_version(new_version)
            vm.update_md_files_version(new_version)
            vm.create_version_info()
            print(f"\n🎉 版本更新完成! 新版本: v{new_version}")
        else:
            print("❌ 版本号格式错误，请使用 x.y.z 格式")
    else:
        # 只创建版本信息文件
        vm.create_version_info()
        print("\n✅ 版本信息文件已创建")

if __name__ == "__main__":
    main() 