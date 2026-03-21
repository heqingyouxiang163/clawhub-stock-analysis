#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务自动监控守护进程
每分钟检查一次任务执行情况，自动生成日志和告警
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List


# 配置
CHECK_INTERVAL = 60  # 检查间隔 (秒)
LOG_DIR = "/home/admin/openclaw/workspace/temp/任务执行日志"
ALERT_LOG = "/home/admin/openclaw/workspace/temp/任务告警日志.md"
os.makedirs(LOG_DIR, exist_ok=True)

# 监控的任务和超时阈值 (秒)
MONITORED_TASKS = {
    "316140a6-44ad-4a6c-9c11-8a889af6e02a": ("集合竞价监控", 360),
    "f5e618b8-df3f-4105-8b5a-894c8be5e46d": ("智能分析 -9:25", 300),
    "ce73ef9b-4bd3-4a88-8706-a2cc904e42e0": ("智能分析 -14 点", 300),
    "79f2f858-898c-4079-badd-4df3e8616247": ("盘中监控 -14 点", 300),
    "47936349-93be-4483-a41b-72c6ff15ac70": ("持仓监控", 300),
    "2ae843de-6ad7-4fff-b57c-c2721b9d7300": ("持仓分析", 120),
}


def load_last_check_time() -> Dict[str, int]:
    """加载上次检查时间"""
    cache_file = os.path.join(LOG_DIR, "last_check.json")
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}


def save_last_check_time(data: Dict[str, int]):
    """保存上次检查时间"""
    cache_file = os.path.join(LOG_DIR, "last_check.json")
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def check_new_runs(job_id: str, last_check: int) -> List[Dict]:
    """检查是否有新的执行记录"""
    runs_dir = "/home/admin/.openclaw/cron/runs"
    new_runs = []
    
    for filename in os.listdir(runs_dir):
        if filename.startswith(job_id.split('-')[0]):
            filepath = os.path.join(runs_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines:
                        try:
                            run_data = json.loads(line)
                            ts = run_data.get('ts', 0)
                            # 只检查上次检查后的新记录
                            if ts > last_check:
                                new_runs.append(run_data)
                        except:
                            pass
            except:
                pass
    
    return new_runs


def analyze_run(run: Dict, timeout_threshold: int) -> Dict:
    """分析单次执行"""
    duration = run.get('durationMs', 0)
    status = run.get('status', 'unknown')
    error = run.get('error', '')
    
    issues = []
    
    # 检查超时
    if duration > timeout_threshold * 1000:
        issues.append(f"❌ 超时 ({duration/1000:.1f}秒 > {timeout_threshold}秒)")
    elif duration > timeout_threshold * 1000 * 0.8:
        issues.append(f"⚠️ 接近超时 ({duration/1000:.1f}秒)")
    
    # 检查错误
    if status == 'error' and error:
        if 'timed out' in error:
            issues.append("❌ 执行超时")
        elif 'Jwt' in error:
            issues.append("❌ JWT 认证失败")
        elif 'Token' in error:
            issues.append("❌ Token 余额不足")
        elif 'Message failed' in error:
            issues.append("❌ 消息发送失败")
        else:
            issues.append(f"❌ 执行错误：{error[:50]}")
    
    return {
        'duration': duration,
        'status': status,
        'error': error,
        'issues': issues,
        'timestamp': run.get('ts', 0)
    }


def generate_alert(job_name: str, analysis: Dict) -> str:
    """生成告警"""
    alert = []
    alert.append(f"🚨 **任务告警** - {job_name}")
    alert.append(f"**时间**: {datetime.fromtimestamp(analysis['timestamp']/1000).strftime('%Y-%m-%d %H:%M:%S')}")
    alert.append(f"**耗时**: {analysis['duration']/1000:.2f}秒")
    alert.append(f"**状态**: {analysis['status']}")
    
    if analysis['issues']:
        alert.append("**问题**:")
        for issue in analysis['issues']:
            alert.append(f"- {issue}")
    
    return "\n".join(alert)


def main():
    """主循环"""
    print("=" * 80)
    print("🔍 定时任务自动监控启动")
    print("=" * 80)
    print()
    
    last_check_time = load_last_check_time()
    current_time = int(datetime.now().timestamp() * 1000)
    
    alerts = []
    
    for job_id, (job_name, timeout) in MONITORED_TASKS.items():
        # 获取上次检查时间
        last_check = last_check_time.get(job_id, 0)
        
        # 检查新执行
        new_runs = check_new_runs(job_id, last_check)
        
        for run in new_runs:
            analysis = analyze_run(run, timeout)
            
            if analysis['issues']:
                alert = generate_alert(job_name, analysis)
                alerts.append(alert)
                print(f"🚨 {job_name}: {', '.join(analysis['issues'])}")
            else:
                print(f"✅ {job_name}: {analysis['duration']/1000:.2f}秒 正常")
        
        # 更新检查时间
        last_check_time[job_id] = current_time
    
    # 保存检查时间
    save_last_check_time(last_check_time)
    
    # 保存告警
    if alerts:
        with open(ALERT_LOG, 'a', encoding='utf-8') as f:
            f.write(f"\n---\n## {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            for alert in alerts:
                f.write(alert + "\n\n")
        print(f"\n📝 告警已保存：{ALERT_LOG}")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
