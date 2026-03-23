#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量更新持仓配置文件
将旧的持仓 (贝肯能源、巨力索具等) 替换为国新能源
"""

import os
import re

WORKSPACE = "/home/admin/openclaw/workspace/tools"

# 新持仓配置
NEW_HOLDINGS = '''HOLDINGS = [
    {"code": "600617", "name": "国新能源", "cost": 4.223, "shares": 2433},
]'''

# 需要更新的文件
FILES_TO_UPDATE = [
    "智能分析 - 实时数据版.py",
    "智能分析系统.py",
    "智能分析系统_v2.py",
    "智能分析系统_腾讯版.py",
    "持仓分析自动化.py",
]

def update_file(filepath):
    """更新文件中的 HOLDINGS 配置"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找旧的 HOLDINGS 配置
        old_pattern = r'HOLDINGS\s*=\s*\[[\s\S]*?\]'
        match = re.search(old_pattern, content)
        
        if match:
            # 替换为新配置
            new_content = content[:match.start()] + NEW_HOLDINGS + content[match.end():]
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"✅ 已更新：{filepath}")
            return True
        else:
            print(f"⚠️ 未找到 HOLDINGS 配置：{filepath}")
            return False
            
    except Exception as e:
        print(f"❌ 更新失败 {filepath}: {e}")
        return False

if __name__ == "__main__":
    print("🦞 批量更新持仓配置...\n")
    
    success = 0
    for filename in FILES_TO_UPDATE:
        filepath = os.path.join(WORKSPACE, filename)
        if os.path.exists(filepath):
            if update_file(filepath):
                success += 1
        else:
            print(f"❌ 文件不存在：{filepath}")
    
    print(f"\n✅ 完成：更新 {success}/{len(FILES_TO_UPDATE)} 个文件")
    print("\n新持仓配置:")
    print(NEW_HOLDINGS)
