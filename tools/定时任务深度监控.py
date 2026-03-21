#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务深度监控脚本
不仅检查状态，还实际验证任务配置和执行时间
"""

import json
import time
import os
from datetime import datetime


# 配置
CRON_JOBS_FILE = "/home/admin/.openclaw/cron/jobs.json"
RUNS_DIR = "/home/admin/.openclaw/cron/runs"
DEEP_REPORT_FILE = "/home/admin/openclaw/workspace/temp/定时任务深度监控报告.md"


def load_cron_jobs():
    """加载 cron 任务"""
    with open(CRON_JOBS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('jobs', [])


def load_run_history(job_id, limit=5):
    """加载任务执行历史"""
    runs = []
    runs_dir = RUNS_DIR
    
    # 查找该任务的运行记录
    for filename in os.listdir(runs_dir):
        if filename.startswith(job_id.split('-')[0]):
            filepath = os.path.join(runs_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # 读取最后 N 条记录
                    for line in lines[-limit:]:
                        try:
                            run_data = json.loads(line)
                            runs.append(run_data)
                        except:
                            pass
            except:
                pass
    
    return runs


def analyze_task_performance(job, runs):
    """分析任务性能"""
    analysis = {
        'job_id': job.get('id', ''),
        'job_name': job.get('name', ''),
        'state': job.get('state', {}),
        'runs': len(runs),
        'avg_duration': 0,
        'max_duration': 0,
        'min_duration': 0,
        'timeout_setting': job.get('payload', {}).get('timeoutSeconds', 0),
        'issues': []
    }
    
    # 分析执行历史
    if runs:
        durations = [r.get('durationMs', 0) for r in runs if r.get('durationMs')]
        if durations:
            analysis['avg_duration'] = sum(durations) / len(durations)
            analysis['max_duration'] = max(durations)
            analysis['min_duration'] = min(durations)
            
            # 检查是否接近超时
            timeout_ms = analysis['timeout_setting'] * 1000
            if analysis['max_duration'] > timeout_ms * 0.9:
                analysis['issues'].append(f'⚠️ 最大执行时间 ({analysis["max_duration"]/1000:.1f}s) 接近超时 ({analysis["timeout_setting"]}s)')
            
            # 检查执行时间波动
            if analysis['max_duration'] > analysis['avg_duration'] * 3:
                analysis['issues'].append(f'⚠️ 执行时间波动大 (平均{analysis["avg_duration"]/1000:.1f}s, 最大{analysis["max_duration"]/1000:.1f}s)')
    
    # 检查当前状态
    state = analysis['state']
    if state.get('consecutiveErrors', 0) > 0:
        analysis['issues'].append(f'❌ 连续错误：{state.get("consecutiveErrors")}次')
    
    if state.get('lastError'):
        analysis['issues'].append(f'❌ 最后错误：{state.get("lastError")[:50]}')
    
    return analysis


def generate_deep_report(analyses):
    """生成深度监控报告"""
    report = []
    report.append("=" * 80)
    report.append(f"📊 定时任务深度监控报告")
    report.append(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 80)
    report.append("")
    
    # 统计
    total = len(analyses)
    healthy = sum(1 for a in analyses if not a['issues'])
    issues = sum(1 for a in analyses if a['issues'])
    
    report.append(f"📋 监控任务：{total}个")
    report.append(f"✅ 健康：{healthy}个")
    report.append(f"⚠️ 有问题：{issues}个")
    report.append("")
    report.append("-" * 80)
    report.append("")
    
    # 有问题任务详情
    problem_tasks = [a for a in analyses if a['issues']]
    if problem_tasks:
        report.append("⚠️ 问题任务详情:")
        report.append("")
        
        for analysis in problem_tasks:
            report.append(f"📋 {analysis['job_name']}")
            report.append(f"   ID: {analysis['job_id']}")
            report.append(f"   执行次数：{analysis['runs']}次")
            
            if analysis['avg_duration'] > 0:
                report.append(f"   平均耗时：{analysis['avg_duration']/1000:.2f}秒")
                report.append(f"   最大耗时：{analysis['max_duration']/1000:.2f}秒")
                report.append(f"   最小耗时：{analysis['min_duration']/1000:.2f}秒")
                report.append(f"   超时设置：{analysis['timeout_setting']}秒")
            
            if analysis['issues']:
                report.append(f"   问题:")
                for issue in analysis['issues']:
                    report.append(f"     - {issue}")
            
            report.append("")
    
    # 性能统计
    report.append("-" * 80)
    report.append("")
    report.append("📈 性能统计:")
    report.append("")
    
    # 按平均耗时排序
    sorted_by_avg = sorted(analyses, key=lambda x: x['avg_duration'], reverse=True)[:10]
    
    report.append("⏱️ 最慢的 10 个任务:")
    for i, analysis in enumerate(sorted_by_avg, 1):
        if analysis['avg_duration'] > 0:
            report.append(f"   {i}. {analysis['job_name'][:30]:<30} {analysis['avg_duration']/1000:.2f}秒")
    
    report.append("")
    
    # 超时风险
    timeout_risk = [a for a in analyses if a['timeout_setting'] > 0 and a['max_duration'] > a['timeout_setting'] * 1000 * 0.8]
    if timeout_risk:
        report.append("⚠️ 超时风险任务 (执行时间>80% 超时设置):")
        for analysis in timeout_risk:
            ratio = analysis['max_duration'] / (analysis['timeout_setting'] * 1000) * 100
            report.append(f"   - {analysis['job_name'][:30]:<30} {ratio:.0f}%")
    
    report.append("")
    report.append("=" * 80)
    
    return "\n".join(report)


def main():
    """主函数"""
    print("=" * 80)
    print("🔍 定时任务深度监控")
    print("=" * 80)
    print()
    
    start = time.time()
    
    # 1. 加载任务
    print("📂 加载任务...")
    jobs = load_cron_jobs()
    print(f"   ✅ 加载{len(jobs)}个任务")
    print()
    
    # 2. 分析每个任务
    print("🔍 深度分析...")
    analyses = []
    
    for i, job in enumerate(jobs, 1):
        job_name = job.get('name', 'Unknown')[:30]
        job_id = job.get('id', '')
        
        # 加载执行历史
        runs = load_run_history(job_id, limit=10)
        
        # 分析性能
        analysis = analyze_task_performance(job, runs)
        analyses.append(analysis)
        
        if i % 10 == 0:
            print(f"   已分析{i}/{len(jobs)}个任务...")
    
    print(f"   ✅ 分析完成")
    print()
    
    # 3. 生成报告
    print("📝 生成报告...")
    report = generate_deep_report(analyses)
    print()
    
    # 4. 保存报告
    with open(DEEP_REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"   ✅ 报告已保存：{DEEP_REPORT_FILE}")
    print()
    
    # 5. 显示摘要
    print("=" * 80)
    print("📊 监控摘要")
    print("=" * 80)
    print()
    
    total = len(analyses)
    healthy = sum(1 for a in analyses if not a['issues'])
    issues = sum(1 for a in analyses if a['issues'])
    
    print(f"总任务数：{total}个")
    print(f"健康：{healthy}个 ({healthy/total*100:.1f}%)")
    print(f"有问题：{issues}个 ({issues/total*100:.1f}%)")
    print()
    
    # 显示主要问题
    problem_tasks = [a for a in analyses if a['issues']]
    if problem_tasks:
        print("⚠️ 主要问题:")
        for analysis in problem_tasks[:5]:
            print(f"   - {analysis['job_name']}: {len(analysis['issues'])}个问题")
            for issue in analysis['issues'][:2]:
                print(f"     {issue}")
    
    print()
    
    # 显示耗时
    duration = time.time() - start
    print(f"⏱️ 深度监控耗时：{duration:.2f}秒")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
