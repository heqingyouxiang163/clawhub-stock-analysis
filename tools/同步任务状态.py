#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步任务状态工具

功能:
1. 从 cron jobs.json 读取最新状态
2. 更新监控缓存
3. 清除旧的错误报告
"""

import json
import os
from datetime import datetime

CRON_JOBS_FILE = "/home/admin/.openclaw/cron/jobs.json"
STATUS_FILE = "/home/admin/openclaw/workspace/temp/cron 监控状态.json"

def sync_status():
    """同步任务状态"""
    print("🔄 同步任务状态...")
    
    # 加载 cron 任务
    try:
        with open(CRON_JOBS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ 加载失败：{e}")
        return
    
    jobs = data.get('jobs', [])
    healthy = 0
    problematic = 0
    unknown = []
    
    for job in jobs:
        name = job.get('name', 'Unknown')
        state = job.get('state', {})
        status = state.get('lastStatus', 'unknown')
        errors = state.get('consecutiveErrors', 0)
        
        if status == 'ok' and errors == 0:
            healthy += 1
        elif status == 'unknown':
            unknown.append(name)
        else:
            problematic += 1
    
    print(f"  总计：{len(jobs)}个任务")
    print(f"  健康：{healthy}个")
    print(f"  问题：{problematic}个")
    print(f"  未知：{len(unknown)}个")
    
    # 更新监控状态
    status_data = {
        "last_check": datetime.now().isoformat(),
        "last_update": datetime.now().strftime('%Y-%m-%d %H:%M'),
        "total_jobs": len(jobs),
        "healthy": healthy,
        "problematic": problematic,
        "unknown": len(unknown),
        "status": "ok" if problematic == 0 else "warning",
        "success_rate": healthy / len(jobs) * 100 if len(jobs) > 0 else 0,
        "note": f"健康{healthy}个 | 问题{problematic}个 | 未知{len(unknown)}个",
        "alerts": [],
        "retried": [],
        "optimized": [],
        "reset_suggestions": unknown
    }
    
    try:
        os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
        with open(STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 状态已同步到：{STATUS_FILE}")
    except Exception as e:
        print(f"❌ 保存失败：{e}")
    
    print()
    if unknown:
        print("⚠️ 未知状态任务 (可能是首次执行或状态未更新):")
        for name in unknown:
            print(f"  - {name}")
    else:
        print("✅ 所有任务状态正常！")

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
    sync_status()
