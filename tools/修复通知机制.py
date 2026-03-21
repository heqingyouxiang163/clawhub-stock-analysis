#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复通知机制

问题：23:00 任务执行了但没有发送通知
原因：delivery 配置可能缺失或 mode=none
解决：确保所有任务都有正确的通知配置
"""

import json
import os

CRON_JOBS_FILE = "/home/admin/.openclaw/cron/jobs.json"

# 需要通知的任务
NOTIFY_TASKS = [
    "🦞 每日更新技能记忆表格",
    "自我学习升级 (每日 23:00)",
    "🦞 每日记忆固化 (自动更新 MEMORY.md)"
]

def fix_delivery():
    """修复通知配置"""
    print("🔧 修复通知配置...")
    
    try:
        with open(CRON_JOBS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ 加载失败：{e}")
        return
    
    fixed_count = 0
    for job in data.get('jobs', []):
        name = job.get('name', '')
        
        # 检查是否需要修复
        if any(task_name in name for task_name in NOTIFY_TASKS):
            delivery = job.get('delivery', {})
            
            # 检查通知配置
            if delivery.get('mode') != 'announce':
                print(f"  ⚠️ 修复：{name}")
                print(f"    原配置：mode={delivery.get('mode', 'none')}")
                
                # 修复通知配置
                job['delivery'] = {
                    'mode': 'announce',
                    'channel': 'openim',
                    'to': '779558319'
                }
                
                print(f"    新配置：mode=announce, channel=openim")
                fixed_count += 1
            else:
                print(f"  ✅ 正常：{name}")
    
    # 保存修改
    if fixed_count > 0:
        try:
            with open(CRON_JOBS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"\n✅ 已修复 {fixed_count}个任务的通知配置")
        except Exception as e:
            print(f"❌ 保存失败：{e}")
    else:
        print(f"\n✅ 所有任务通知配置正常")

    # 显示总耗时
    total_elapsed = time.time() - total_start
    if total_elapsed < 1:
        print(f"✅ **总耗时**: {total_elapsed*1000:.0f}ms")
    elif total_elapsed < 60:
        print(f"✅ **总耗时**: {total_elapsed:.1f}秒")
    else:
        print(f"✅ **总耗时**: {total_elapsed/60:.1f}分钟")

if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    fix_delivery()
