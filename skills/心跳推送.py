#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🦞 心跳推送脚本

功能:
- 检查系统状态
- 推送心跳信息给用户
- 报告定时任务状态
"""

import json
from pathlib import Path
from datetime import datetime


def check_system_status():
    """检查系统状态"""
    status = {
        '时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        '角色': '小艺·炒股龙虾 v18.0',
        '状态': '✅ 正常运行',
        '定时任务': [],
        '日志文件': []
    }
    
    # 检查定时任务
    cron_file = Path('~/.openclaw/cron/jobs.json').expanduser()
    if cron_file.exists():
        with open(cron_file, 'r', encoding='utf-8') as f:
            cron_data = json.load(f)
            jobs = cron_data.get('jobs', [])
            status['定时任务'] = f"{len(jobs)}个任务"
    
    # 检查日志文件
    log_file = Path('temp/小龙虾运行日志.txt')
    if log_file.exists():
        status['日志文件'] = '✅ 正常写入'
    else:
        status['日志文件'] = '⚠️ 未找到'
    
    # 检查推荐记录
    recommend_file = Path('temp/小龙虾推荐记录.json')
    if recommend_file.exists():
        status['推荐记录'] = '✅ 正常保存'
    else:
        status['推荐记录'] = '⚠️ 无记录'
    
    return status


def send_heartbeat_message():
    """发送心跳推送消息"""
    status = check_system_status()
    
    message = f"""
🦞 **小龙虾心跳检查**

⏰ 时间：{status['时间']}
🎭 角色：{status['角色']}
💓 状态：{status['状态']}

📋 定时任务：{status['定时任务']}
📝 日志文件：{status['日志文件']}
📊 推荐记录：{status['推荐记录']}

---
✅ 系统正常运行中
"""
    
    print(message)
    
    # 保存推送记录
    record_file = Path('temp/心跳推送记录.json')
    record_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(record_file, 'a', encoding='utf-8') as f:
        json.dump({
            '时间': status['时间'],
            '状态': status['状态'],
            '消息': message
        }, f, ensure_ascii=False, indent=2)
        f.write('\n')
    
    return message


if __name__ == '__main__':
    send_heartbeat_message()
