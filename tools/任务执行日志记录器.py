#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务执行日志记录器
记录每次任务执行的详细信息，用于性能分析和优化
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List


# 配置
LOG_DIR = "/home/admin/openclaw/workspace/temp/任务执行日志"
os.makedirs(LOG_DIR, exist_ok=True)

# 需要重点监控的任务
MONITORED_TASKS = {
    "316140a6-44ad-4a6c-9c11-8a889af6e02a": "集合竞价监控 (交易日 9:20)",
    "f5e618b8-df3f-4105-8b5a-894c8be5e46d": "智能分析 -9 点 25",
    "ce73ef9b-4bd3-4a88-8706-a2cc904e42e0": "智能分析 -14 点",
    "79f2f858-898c-4079-badd-4df3e8616247": "盘中监控 -14 点",
    "47936349-93be-4483-a41b-72c6ff15ac70": "持仓监控 - 贝肯能源",
    "2ae843de-6ad7-4fff-b57c-c2721b9d7300": "持仓分析每日自动运行",
}


def load_cron_runs(job_id: str) -> List[Dict]:
    """加载任务执行历史"""
    runs_dir = "/home/admin/.openclaw/cron/runs"
    runs = []
    
    # 查找该任务的运行记录
    for filename in os.listdir(runs_dir):
        if filename.startswith(job_id.split('-')[0]):
            filepath = os.path.join(runs_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines:
                        try:
                            run_data = json.loads(line)
                            runs.append(run_data)
                        except:
                            pass
            except:
                pass
    
    return runs


def analyze_execution_time(runs: List[Dict]) -> Dict:
    """分析执行时间"""
    if not runs:
        return {}
    
    durations = [r.get('durationMs', 0) for r in runs if r.get('durationMs')]
    
    if not durations:
        return {}
    
    # 统计
    avg_duration = sum(durations) / len(durations)
    max_duration = max(durations)
    min_duration = min(durations)
    
    # 分位数
    sorted_durations = sorted(durations)
    p50 = sorted_durations[len(sorted_durations)//2]
    p90 = sorted_durations[int(len(sorted_durations)*0.9)]
    p95 = sorted_durations[int(len(sorted_durations)*0.95)]
    
    # 超时统计
    timeout_count = sum(1 for d in durations if d > 120000)  # >2 分钟
    timeout_ratio = timeout_count / len(durations) * 100
    
    return {
        'count': len(durations),
        'avg_ms': avg_duration,
        'max_ms': max_duration,
        'min_ms': min_duration,
        'p50_ms': p50,
        'p90_ms': p90,
        'p95_ms': p95,
        'timeout_count': timeout_count,
        'timeout_ratio': timeout_ratio,
        '波动倍数': max_duration / min_duration if min_duration > 0 else 0
    }


def generate_task_log(job_id: str, job_name: str, runs: List[Dict]) -> str:
    """生成任务执行日志"""
    log = []
    log.append("=" * 80)
    log.append(f"📊 任务执行日志 - {job_name}")
    log.append(f"ID: {job_id}")
    log.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.append("=" * 80)
    log.append("")
    
    # 执行时间分析
    stats = analyze_execution_time(runs)
    if stats:
        log.append("⏱️ 执行时间统计:")
        log.append(f"   执行次数：{stats['count']}次")
        log.append(f"   平均耗时：{stats['avg_ms']/1000:.2f}秒")
        log.append(f"   最大耗时：{stats['max_ms']/1000:.2f}秒")
        log.append(f"   最小耗时：{stats['min_ms']/1000:.2f}秒")
        log.append(f"   中位数：{stats['p50_ms']/1000:.2f}秒")
        log.append(f"   P90: {stats['p90_ms']/1000:.2f}秒")
        log.append(f"   P95: {stats['p95_ms']/1000:.2f}秒")
        log.append(f"   波动倍数：{stats['波动倍数']:.1f}倍")
        log.append(f"   超时次数：{stats['timeout_count']}次 ({stats['timeout_ratio']:.1f}%)")
        log.append("")
        
        # 风险评估
        risk_level = "✅ 低风险"
        if stats['波动倍数'] > 100:
            risk_level = "🔴 高风险 (波动>100 倍)"
        elif stats['波动倍数'] > 50:
            risk_level = "🟡 中风险 (波动>50 倍)"
        elif stats['timeout_ratio'] > 20:
            risk_level = "🟠 超时风险 (超时>20%)"
        
        log.append(f"风险等级：{risk_level}")
        log.append("")
    
    # 最近执行记录
    log.append("-" * 80)
    log.append("📝 最近执行记录:")
    log.append("")
    
    recent_runs = runs[-10:] if len(runs) > 10 else runs
    for i, run in enumerate(recent_runs, 1):
        ts = run.get('ts', 0)
        if ts:
            exec_time = datetime.fromtimestamp(ts/1000).strftime('%Y-%m-%d %H:%M')
        else:
            exec_time = '未知'
        
        duration = run.get('durationMs', 0)
        status = run.get('status', 'unknown')
        error = run.get('error', '')
        
        emoji = "✅" if status == 'ok' else "❌"
        
        log.append(f"{i}. {exec_time} {emoji} {duration/1000:.2f}秒")
        if error:
            error_short = error[:80] if len(error) > 80 else error
            log.append(f"   错误：{error_short}")
    
    log.append("")
    
    # 优化建议
    log.append("-" * 80)
    log.append("💡 优化建议:")
    log.append("")
    
    if stats:
        if stats['波动倍数'] > 100:
            log.append("   ⚠️ 执行时间波动极大 (>100 倍)")
            log.append("   建议:")
            log.append("     1. 检查数据源稳定性")
            log.append("     2. 添加超时重试机制")
            log.append("     3. 使用缓存减少网络请求")
            log.append("")
        
        if stats['timeout_ratio'] > 10:
            log.append("   ⚠️ 超时率高 (>10%)")
            log.append("   建议:")
            log.append("     1. 增加超时时间")
            log.append("     2. 优化脚本性能")
            log.append("     3. 检查网络延迟")
            log.append("")
        
        if stats['max_ms'] > 180000:
            log.append("   ⚠️ 最大执行时间超过 3 分钟")
            log.append("   建议:")
            log.append("     1. 设置超时限制")
            log.append("     2. 分解复杂任务")
            log.append("     3. 添加进度监控")
            log.append("")
    
    log.append("=" * 80)
    
    return "\n".join(log)


def main():
    """主函数"""
    print("=" * 80)
    print("📊 定时任务执行日志生成")
    print("=" * 80)
    print()
    
    for job_id, job_name in MONITORED_TASKS.items():
        print(f"📋 {job_name[:40]:<40}", end=" ")
        
        # 加载执行历史
        runs = load_cron_runs(job_id)
        
        if not runs:
            print("⚠️ 无执行记录")
            continue
        
        # 生成日志
        log = generate_task_log(job_id, job_name, runs)
        
        # 保存日志
        date_str = datetime.now().strftime('%Y%m%d')
        log_file = os.path.join(LOG_DIR, f"{job_name[:20]}_{date_str}.md")
        # 简化文件名
        safe_name = job_name.replace('(', '').replace(')', '').replace(' ', '_')[:30]
        log_file = os.path.join(LOG_DIR, f"{safe_name}_{date_str}.md")
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(log)
        
        # 显示摘要
        stats = analyze_execution_time(runs)
        if stats:
            print(f"✅ {stats['count']}次 平均{stats['avg_ms']/1000:.2f}秒 最大{stats['max_ms']/1000:.2f}秒")
        else:
            print("✅ 已生成日志")
    
    print()
    print("=" * 80)
    print(f"📁 日志目录：{LOG_DIR}")
    print("=" * 80)


if __name__ == "__main__":
    main()
