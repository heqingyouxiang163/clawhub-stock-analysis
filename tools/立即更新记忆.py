#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
立即更新 MEMORY.md 工具

用途：
1. 重大配置变更时立即更新 MEMORY.md
2. 避免等到 23:00 固化任务导致配置丢失
3. 支持增量更新，保留历史配置

使用方式：
    python3 立即更新记忆.py "配置变更内容"
    
示例：
    python3 立即更新记忆.py "优化缓存清理机制，添加自动清理脚本"
    python3 立即更新记忆.py "修复路径问题，所有脚本改用绝对路径"
"""

import sys
import os
import time  # 修复：添加 time 模块导入
from datetime import datetime

MEMORY_FILE = "/home/admin/openclaw/workspace/MEMORY.md"
TIMESTAMP = datetime.now().strftime('%Y-%m-%d %H:%M')


def update_memory(change_description):
    """立即更新 MEMORY.md"""
    
    # 检查文件是否存在
    if not os.path.exists(MEMORY_FILE):
        print(f"⚠️ MEMORY.md 不存在：{MEMORY_FILE}")
        return False
    
    # 读取现有内容
    with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 构建更新内容
    update_section = f"""

---

## 🆕 实时更新 ({TIMESTAMP})

{change_description}

**状态**: ✅ 已立即更新
**下次固化**: 今日 23:00 自动归档

"""
    
    # 找到合适的位置插入 (在文件开头或"最后更新"后)
    if "**最后更新**:" in content:
        # 更新最后更新时间
        old_timestamp = content.split("**最后更新**:")[1].split("\n")[0].strip()
        content = content.replace(
            f"**最后更新**: {old_timestamp}",
            f"**最后更新**: {TIMESTAMP}"
        )
    
    # 在文件开头插入更新
    lines = content.split("\n")
    insert_pos = 0
    
    # 找到第一个大标题后的位置
    for i, line in enumerate(lines):
        if line.startswith("---") and i > 5:
            insert_pos = i + 1
            break
    
    if insert_pos > 0:
        lines.insert(insert_pos, update_section)
        new_content = "\n".join(lines)
    else:
        new_content = update_section + content
    
    # 写回文件
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ MEMORY.md 已更新")
    print(f"📝 变更内容：{change_description}")
    print(f"⏰ 更新时间：{TIMESTAMP}")
    
    return True


def quick_update(change_type, details):
    """快速更新模板"""
    
    templates = {
        "任务优化": f"⚡ 任务频率优化：{details}",
        "数据源": f"📊 数据源变更：{details}",
        "脚本修复": f"🔧 脚本修复：{details}",
        "配置变更": f"⚙️ 配置变更：{details}",
        "Bug 修复": f"🐛 Bug 修复：{details}",
    }
    
    change_text = templates.get(change_type, f"配置变更：{details}")
    return update_memory(change_text)


if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    print("=" * 60)
    print("📝 立即更新 MEMORY.md")
    print(f"时间：{TIMESTAMP}")
    print("=" * 60)
    print()
    
    if len(sys.argv) < 2:
        print("❌ 用法：python3 立即更新记忆.py \"配置变更内容\"")
        print()
        print("示例:")
        print('  python3 立即更新记忆.py "优化缓存清理机制"')
        print('  python3 立即更新记忆.py "修复路径问题"')
        sys.exit(1)
    
    change_description = sys.argv[1]
    success = update_memory(change_description)
    
    print()
    print("=" * 60)
    
    if success:
        print("✅ 更新完成")
    else:
        print("❌ 更新失败")
        sys.exit(1)
