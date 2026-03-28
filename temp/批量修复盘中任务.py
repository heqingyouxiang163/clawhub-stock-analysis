#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量修复盘中定时任务
"""
import json
import os

CRON_FILE = "/home/admin/.openclaw/cron/jobs.json"

# 读取任务
with open(CRON_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)
    jobs = data.get('jobs', [])

# 修复清单
fixes = {
    # 任务 ID: {name: 新名称，timeoutSeconds: 新超时}
    "47936349-93be-4483-a41b-72c6ff15ac70": {
        "name": "持仓监控 - 通鼎互联",
        "payload_message": "🦞 持仓监控提醒 (10 分钟一次)\n\n📊 通鼎互联 (002491)\n\n成本：¥10.182 | 持仓：1100 股 | 市值：¥12,540\n\n正在获取最新数据..."
    },
    "ead52bff-42ae-4987-8957-f9fbadc8915b": {
        "timeoutSeconds": 90
    },
    "79f2f858-898c-4079-badd-4df3e8616247": {
        "timeoutSeconds": 90
    },
    "1c642957-8dbb-4550-83e1-a155a49d6174": {
        "timeoutSeconds": 180
    },
}

# 应用修复
fixed_count = 0
for job in jobs:
    job_id = job.get('id')
    if job_id in fixes:
        fix = fixes[job_id]
        print(f"🔧 修复任务：{job.get('name', 'Unknown')}")
        
        if 'name' in fix:
            print(f"  名称：{job['name']} → {fix['name']}")
            job['name'] = fix['name']
        
        if 'timeoutSeconds' in fix:
            old_timeout = job.get('payload', {}).get('timeoutSeconds', 'N/A')
            print(f"  超时：{old_timeout}秒 → {fix['timeoutSeconds']}秒")
            job['payload']['timeoutSeconds'] = fix['timeoutSeconds']
        
        if 'payload_message' in fix:
            old_msg = job.get('payload', {}).get('message', '')[:50]
            print(f"  消息：已更新 (原：{old_msg}...)")
            job['payload']['message'] = fix['payload_message']
        
        fixed_count += 1
        print()

# 保存
with open(CRON_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ 修复完成！共修复 {fixed_count} 个任务")
