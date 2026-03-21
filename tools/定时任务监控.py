#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务实时监控工具
每 5 分钟检查一次修复任务的执行状态
"""

import json
import subprocess
import time
from datetime import datetime
from typing import List, Dict


# 监控的任务列表
MONITORED_TASKS = [
    "316140a6-44ad-4a6c-9c11-8a889af6e02a",  # 集合竞价监控
    "f5e618b8-df3f-4105-8b5a-894c8be5e46d",  # 智能分析 -9 点 25
    "79f2f858-898c-4079-badd-4df3e8616247",  # 盘中监控 -14 点
    "ce73ef9b-4bd3-4a88-8706-a2cc904e42e0",  # 智能分析 -14 点
    "b26c6b35-5754-4a7d-bb26-c4a2064396aa",  # 涨停形态每日学习
    "5b179d3f-d374-4cff-84eb-891a6b92c718",  # 龙虎榜分析
    "a7cf3986-ab67-47a3-b4e7-d9710627187e",  # 自我学习升级
]

TASK_NAMES = {
    "316140a6-44ad-4a6c-9c11-8a889af6e02a": "集合竞价监控",
    "f5e618b8-df3f-4105-8b5a-894c8be5e46d": "智能分析 -9:25",
    "79f2f858-898c-4079-badd-4df3e8616247": "盘中监控 -14 点",
    "ce73ef9b-4bd3-4a88-8706-a2cc904e42e0": "智能分析 -14 点",
    "b26c6b35-5754-4a7d-bb26-c4a2064396aa": "涨停形态学习",
    "5b179d3f-d374-4cff-84eb-891a6b92c718": "龙虎榜分析",
    "a7cf3986-ab67-47a3-b4e7-d9710627187e": "自我学习升级",
}

LOG_FILE = "/home/admin/openclaw/workspace/temp/定时任务监控日志.md"


def get_cron_status() -> List[Dict]:
    """获取 cron 任务状态"""
    try:
        result = subprocess.run(
            ["openclaw", "cron", "list", "--json"],
            capture_output=True,
            text=True,
            timeout=30
        )
        data = json.loads(result.stdout)
        return data.get('jobs', [])
    except Exception as e:
        print(f"❌ 获取任务状态失败：{e}")
        return []


def check_tasks(jobs: List[Dict]) -> Dict[str, Dict]:
    """检查任务状态"""
    status = {}
    
    for job in jobs:
        job_id = job.get('id', '')
        if job_id in MONITORED_TASKS:
            state = job.get('state', {})
            payload = job.get('payload', {})
            
            status[job_id] = {
                'name': TASK_NAMES.get(job_id, job.get('name', 'Unknown')),
                'enabled': job.get('enabled', False),
                'timeout': payload.get('timeoutSeconds', 0),
                'last_error': state.get('lastError', '无'),
                'consecutive_errors': state.get('consecutiveErrors', 0),
                'last_status': state.get('lastRunStatus', '未知'),
                'next_run': state.get('nextRunAtMs', 0),
            }
    
    return status


def generate_report(status: Dict[str, Dict]) -> str:
    """生成监控报告"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    report = []
    report.append("=" * 80)
    report.append(f"📊 定时任务监控报告 - {now}")
    report.append("=" * 80)
    report.append("")
    
    # 统计
    total = len(status)
    enabled = sum(1 for s in status.values() if s['enabled'])
    has_errors = sum(1 for s in status.values() if s['consecutive_errors'] > 0)
    
    report.append(f"📋 监控任务：{total}个")
    report.append(f"✅ 已启用：{enabled}个")
    report.append(f"⚠️ 有错误：{has_errors}个")
    report.append("")
    report.append("-" * 80)
    report.append("")
    
    # 详细状态
    for job_id, info in status.items():
        emoji = "✅" if info['enabled'] and info['consecutive_errors'] == 0 else "⚠️"
        
        report.append(f"{emoji} {info['name']}")
        report.append(f"   状态：{'✅ 已启用' if info['enabled'] else '❌ 已禁用'}")
        report.append(f"   超时：{info['timeout']}秒")
        report.append(f"   最后状态：{info['last_status']}")
        report.append(f"   连续错误：{info['consecutive_errors']}次")
        
        if info['last_error'] and info['last_error'] != '无':
            error_short = info['last_error'][:50] + "..." if len(info['last_error']) > 50 else info['last_error']
            report.append(f"   最后错误：{error_short}")
        
        if info['next_run'] > 0:
            next_run = datetime.fromtimestamp(info['next_run'] / 1000).strftime('%Y-%m-%d %H:%M')
            report.append(f"   下次执行：{next_run}")
        
        report.append("")
    
    report.append("-" * 80)
    report.append("")
    
    # 建议
    if has_errors > 0:
        report.append("⚠️ 发现错误，建议:")
        report.append("   1. 检查脚本是否正常")
        report.append("   2. 增加超时时间")
        report.append("   3. 手动触发测试")
        report.append("")
    else:
        report.append("✅ 所有任务状态正常")
        report.append("")
    
    report.append("=" * 80)
    
    return "\n".join(report)


def save_report(report: str):
    """保存报告"""
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"\n---\n{report}\n")


def main():
    """主函数"""
    print("=" * 80)
    print("🔍 定时任务实时监控")
    print("=" * 80)
    print()
    
    # 获取状态
    print("📊 获取任务状态...")
    jobs = get_cron_status()
    
    if not jobs:
        print("❌ 无法获取任务状态")
        return
    
    print(f"✅ 获取到{len(jobs)}个任务")
    print()
    
    # 检查任务
    print("🔍 检查监控任务...")
    status = check_tasks(jobs)
    
    if not status:
        print("❌ 未找到监控任务")
        return
    
    print(f"✅ 检查{len(status)}个任务")
    print()
    
    # 生成报告
    report = generate_report(status)
    
    # 打印报告
    print(report)
    
    # 保存报告
    save_report(report)
    
    print(f"📝 报告已保存：{LOG_FILE}")
    
    # 告警
    has_errors = sum(1 for s in status.values() if s['consecutive_errors'] > 0)
    if has_errors > 0:
        print()
        print(f"🚨 警告：{has_errors}个任务有错误！")
        print("   建议执行：bash /home/admin/openclaw/workspace/tools/深度修复定时任务.sh")


if __name__ == "__main__":
    main()
