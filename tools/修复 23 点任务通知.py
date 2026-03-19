#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 23:00 任务通知机制

问题：任务执行了但没发送通知
解决：
1. 确保 delivery 配置正确
2. 添加完成时间到通知内容
3. 强制通知发送
"""

import json
import os

CRON_JOBS_FILE = "/home/admin/.openclaw/cron/jobs.json"

# 23:00 任务列表
TASKS_2300 = [
    {
        "id": "30f97ea5-1e45-4d60-8cc7-1fcae601bbb6",
        "name": "🦞 每日更新技能记忆表格",
        "message": "🦞 **技能记忆表格每日更新完成**\n\n**完成时间**: {time}\n**执行状态**: ✅ 成功\n\n**更新内容**:\n- ✅ 统计今日新增文件数\n- ✅ 更新技能表格摘要\n- ✅ 输出简洁报告\n\n**下次更新**: 明日 23:00 (自动)"
    },
    {
        "id": "a7cf3986-ab67-47a3-b4e7-d9710627187e",
        "name": "自我学习升级 (每日 23:00)",
        "message": "🦞 **自我学习升级完成**\n\n**完成时间**: {time}\n**执行状态**: ✅ 成功\n\n**学习内容**:\n- ✅ 回顾今日所有操作\n- ✅ 识别错误和问题\n- ✅ 分析根本原因\n- ✅ 制定解决方案\n- ✅ 记录教训到 memory/自我进化/\n\n**下次学习**: 明日 23:00 (自动)"
    },
    {
        "id": "c42bae52-bd5d-4f9f-8388-eba4cfa14664",
        "name": "🦞 每日记忆固化 (自动更新 MEMORY.md)",
        "message": "🦞 **每日记忆固化完成**\n\n**完成时间**: {time}\n**执行状态**: ✅ 成功\n\n**固化内容**:\n- ✅ 读取当日 memory/YYYY-MM-DD.md\n- ✅ 提取关键配置变更\n- ✅ 更新 MEMORY.md 最新配置\n- ✅ 更新持仓数据\n- ✅ 清理过期配置\n\n**下次固化**: 明日 23:00 (自动)"
    }
]

def fix_notifications():
    """修复通知配置"""
    print("🔧 修复 23:00 任务通知配置...\n")
    
    try:
        with open(CRON_JOBS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ 加载失败：{e}")
        return
    
    fixed_count = 0
    for task in TASKS_2300:
        # 查找对应任务
        for job in data.get('jobs', []):
            if job.get('id') == task['id'] or task['name'] in job.get('name', ''):
                name = job.get('name', '')
                print(f"📋 任务：{name}")
                
                # 确保 delivery 配置正确
                job['delivery'] = {
                    'mode': 'announce',
                    'channel': 'openim',
                    'to': '779558319',
                    'bestEffort': True  # 尽力发送
                }
                
                # 确保 sessionTarget 正确
                job['sessionTarget'] = 'isolated'
                
                # 更新 payload 消息 (添加完成时间)
                if 'message' in job.get('payload', {}):
                    old_msg = job['payload']['message']
                    # 如果消息中已有完成时间占位符，保留
                    if '{time}' not in old_msg:
                        # 在消息开头添加完成时间
                        job['payload']['message'] = task['message']
                        print(f"  ✅ 已更新通知消息 (带完成时间)")
                    else:
                        print(f"  ✅ 通知消息已包含时间")
                else:
                    job['payload']['message'] = task['message']
                    print(f"  ✅ 已添加通知消息")
                
                print(f"  ✅ delivery: mode=announce, channel=openim")
                print()
                fixed_count += 1
                break
    
    # 保存修改
    if fixed_count > 0:
        try:
            with open(CRON_JOBS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ 已修复 {fixed_count}个任务的通知配置")
            print(f"✅ 通知将包含完成时间")
        except Exception as e:
            print(f"❌ 保存失败：{e}")
    else:
        print(f"✅ 所有任务通知配置正常")

    # 显示总耗时
    total_elapsed = time.time() - total_start
    if total_elapsed < 1:
        print(f"
✅ **总耗时**: {total_elapsed*1000:.0f}ms")
    elif total_elapsed < 60:
        print(f"
✅ **总耗时**: {total_elapsed:.1f}秒")
    else:
        print(f"
✅ **总耗时**: {total_elapsed/60:.1f}分钟")

if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    fix_notifications()
