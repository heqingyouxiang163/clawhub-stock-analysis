#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接修改 cron 配置文件来更新超时时间
"""

import json
import os
from datetime import datetime

# 配置文件路径
CRON_JOBS_FILE = "/home/admin/.openclaw/cron/jobs.json"
BACKUP_FILE = "/home/admin/.openclaw/cron/jobs.json.backup"

# 目标任务和新的超时设置 (秒)
TARGET_UPDATES = {
    "316140a6-44ad-4a6c-9c11-8a889af6e02a": 120,  # 集合竞价监控
    "f5e618b8-df3f-4105-8b5a-894c8be5e46d": 180,  # 智能分析 -9:25
    "79f2f858-898c-4079-badd-4df3e8616247": 180,  # 盘中监控 -14 点
    "ce73ef9b-4bd3-4a88-8706-a2cc904e42e0": 180,  # 智能分析 -14 点
    "b26c6b35-5754-4a7d-bb26-c4a2064396aa": 300,  # 涨停形态学习
    "5b179d3f-d374-4cff-84eb-891a6b92c718": 180,  # 龙虎榜分析
    "a7cf3986-ab67-47a3-b4e7-d9710627187e": 300,  # 自我学习升级
}

TASK_NAMES = {
    "316140a6-44ad-4a6c-9c11-8a889af6e02a": "集合竞价监控",
    "f5e618b8-df3f-4105-8b5a-894c8be5e46d": "智能分析 -9:25",
    "79f2f858-898c-4079-badd-4df3e8616247": "盘中监控 -14 点",
    "ce73ef9b-4bd3-4a88-8706-a2cc904e42e0": "智能分析 -14 点",
    "b26c6b35-5754-4a7d-bb26-c4a2064396aa": "涨停形态学习",
    "5b179d3f-d374-4cff-84eb-891a6b92c718": "龙虎榜分析",
    "a7cf3986-ab67-47a3-b4e7-d9710627187e": "自我学习升级",
}


def main():
    print("=" * 80)
    print("🔧 直接修改 cron 配置 - 更新超时时间")
    print("=" * 80)
    print()
    
    # 检查文件
    if not os.path.exists(CRON_JOBS_FILE):
        print(f"❌ 配置文件不存在：{CRON_JOBS_FILE}")
        return
    
    # 备份
    print("📦 备份配置文件...")
    with open(CRON_JOBS_FILE, 'r', encoding='utf-8') as f:
        original_data = f.read()
    
    with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
        f.write(original_data)
    print(f"   ✅ 备份完成：{BACKUP_FILE}")
    print()
    
    # 加载配置
    print("📂 加载配置...")
    with open(CRON_JOBS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    jobs = data.get('jobs', [])
    print(f"   ✅ 加载{len(jobs)}个任务")
    print()
    
    # 更新超时
    print("⏰ 更新超时时间...")
    updated_count = 0
    
    for job in jobs:
        job_id = job.get('id', '')
        if job_id in TARGET_UPDATES:
            name = TASK_NAMES.get(job_id, job.get('name', 'Unknown'))
            current_timeout = job.get('payload', {}).get('timeoutSeconds', 0)
            target_timeout = TARGET_UPDATES[job_id]
            
            # 更新超时
            if 'payload' not in job:
                job['payload'] = {}
            
            job['payload']['timeoutSeconds'] = target_timeout
            
            # 更新 updatedAtMs
            job['updatedAtMs'] = int(datetime.now().timestamp() * 1000)
            
            status = "✅" if current_timeout != target_timeout else "⚠️"
            print(f"   {status} {name[:30]:<30} {current_timeout:3}秒 → {target_timeout:3}秒")
            updated_count += 1
    
    print()
    print(f"✅ 更新{updated_count}个任务")
    print()
    
    # 保存配置
    print("💾 保存配置...")
    with open(CRON_JOBS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"   ✅ 保存完成：{CRON_JOBS_FILE}")
    print()
    
    # 验证
    print("🔍 验证修改...")
    with open(CRON_JOBS_FILE, 'r', encoding='utf-8') as f:
        verify_data = json.load(f)
    
    verify_jobs = verify_data.get('jobs', [])
    for job in verify_jobs:
        job_id = job.get('id', '')
        if job_id in TARGET_UPDATES:
            name = TASK_NAMES.get(job_id, 'Unknown')
            new_timeout = job.get('payload', {}).get('timeoutSeconds', 0)
            target_timeout = TARGET_UPDATES[job_id]
            
            status = "✅" if new_timeout == target_timeout else "❌"
            print(f"   {status} {name[:30]:<30} {new_timeout:3}秒 (目标：{target_timeout:3}秒)")
    
    print()
    print("=" * 80)
    print("✅ 配置修改完成")
    print()
    print("💡 提示:")
    print("   1. 配置已直接修改")
    print("   2. 建议重启 Gateway 使配置生效")
    print("   3. 或者等待下次自动刷新")
    print()
    print("📦 备份文件：tools/定时任务监控.py")
    print("=" * 80)


if __name__ == "__main__":
    main()
