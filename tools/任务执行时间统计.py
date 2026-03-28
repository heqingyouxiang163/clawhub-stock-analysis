#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务执行时间统计工具

功能:
1. 记录每次任务执行时间
2. 分析执行时间趋势
3. 发现性能劣化
4. 生成统计报告

使用方式:
    python3 任务执行时间统计.py [选项]
    
选项:
    --view      查看最新统计
    --trend     显示趋势图 (文本)
    --analyze   分析性能劣化任务
    --clear     清空历史数据
"""

import json
import os
import sys
from datetime import datetime, timedelta

# 配置
STATS_FILE = "/home/admin/openclaw/workspace/temp/任务执行时间统计.json"
HISTORY_DAYS = 7  # 保留 7 天数据


def load_stats():
    """加载统计数据"""
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"history": [], "tasks": {}}


def save_stats(stats):
    """保存统计数据"""
    os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)


def add_execution(task_name, duration_ms, status="ok"):
    """添加执行记录"""
    stats = load_stats()
    
    record = {
        "task": task_name,
        "duration_ms": duration_ms,
        "status": status,
        "timestamp": datetime.now().isoformat()
    }
    
    stats["history"].append(record)
    
    # 更新任务统计
    if task_name not in stats["tasks"]:
        stats["tasks"][task_name] = {
            "count": 0,
            "total_ms": 0,
            "min_ms": float('inf'),
            "max_ms": 0,
            "last_ms": 0
        }
    
    task_stats = stats["tasks"][task_name]
    task_stats["count"] += 1
    task_stats["total_ms"] += duration_ms
    task_stats["min_ms"] = min(task_stats["min_ms"], duration_ms)
    task_stats["max_ms"] = max(task_stats["max_ms"], duration_ms)
    task_stats["last_ms"] = duration_ms
    task_stats["avg_ms"] = task_stats["total_ms"] / task_stats["count"]
    
    # 清理旧数据 (保留 7 天)
    cutoff = (datetime.now() - timedelta(days=HISTORY_DAYS)).isoformat()
    stats["history"] = [r for r in stats["history"] if r["timestamp"] > cutoff]
    
    save_stats(stats)
    print(f"✅ 记录：{task_name} 执行 {duration_ms}ms")


def analyze_degradation():
    """分析性能劣化"""
    stats = load_stats()
    
    print("=" * 70)
    print("📊 任务执行时间趋势分析")
    print(f"统计范围：最近{HISTORY_DAYS}天")
    print("=" * 70)
    print()
    
    degraded_tasks = []
    
    for task_name, task_stats in stats["tasks"].items():
        count = task_stats["count"]
        if count < 5:  # 至少 5 次执行才分析
            continue
        
        avg_ms = task_stats.get("avg_ms", 0)
        last_ms = task_stats.get("last_ms", 0)
        min_ms = task_stats.get("min_ms", 0)
        max_ms = task_stats.get("max_ms", 0)
        
        # 检测劣化：最近执行时间 > 平均时间 50%
        if last_ms > avg_ms * 1.5:
            degradation = (last_ms - avg_ms) / avg_ms * 100
            degraded_tasks.append({
                "task": task_name,
                "avg_ms": avg_ms,
                "last_ms": last_ms,
                "degradation": degradation
            })
    
    if degraded_tasks:
        print("⚠️ 发现性能劣化任务:")
        print()
        print(f"{'任务名':<40} {'平均':>10} {'最新':>10} {'劣化':>10}")
        print("-" * 70)
        
        for task in sorted(degraded_tasks, key=lambda x: x["degradation"], reverse=True):
            print(f"{task['task']:<40} {task['avg_ms']:>8.0f}ms {task['last_ms']:>8.0f}ms +{task['degradation']:>6.0f}%")
        
        print()
        print(f"总计：{len(degraded_tasks)}个任务性能劣化")
    else:
        print("✅ 所有任务性能正常")
    
    print()
    print("=" * 70)
    
    return degraded_tasks


def show_statistics():
    """显示统计信息"""
    stats = load_stats()
    
    print("=" * 70)
    print("📊 任务执行时间统计")
    print(f"统计范围：最近{HISTORY_DAYS}天")
    print("=" * 70)
    print()
    
    if not stats["tasks"]:
        print("⚠️ 暂无统计数据")
        return
    
    # 按执行次数排序
    sorted_tasks = sorted(
        stats["tasks"].items(),
        key=lambda x: x[1]["count"],
        reverse=True
    )
    
    print(f"{'任务名':<35} {'次数':>6} {'平均':>10} {'最小':>10} {'最大':>10} {'最新':>10}")
    print("-" * 90)
    
    for task_name, task_stats in sorted_tasks:
        print(f"{task_name:<35} {task_stats['count']:>6} "
              f"{task_stats.get('avg_ms', 0):>8.0f}ms "
              f"{task_stats['min_ms']:>8.0f}ms "
              f"{task_stats['max_ms']:>8.0f}ms "
              f"{task_stats['last_ms']:>8.0f}ms")
    
    print()
    print(f"总计：{len(stats['tasks'])}个任务，{len(stats['history'])}条记录")
    print("=" * 70)


def clear_history():
    """清空历史数据"""
    if os.path.exists(STATS_FILE):
        os.remove(STATS_FILE)
        print("✅ 历史数据已清空")
    else:
        print("ℹ️ 无历史数据")


def show_trend():
    """显示趋势图 (文本版)"""
    stats = load_stats()
    
    print("=" * 70)
    print("📈 任务执行时间趋势 (最近 10 次)")
    print("=" * 70)
    print()
    
    # 按任务分组
    task_history = {}
    for record in stats["history"]:
        task = record["task"]
        if task not in task_history:
            task_history[task] = []
        task_history[task].append(record)
    
    for task_name, records in task_history.items():
        print(f"{task_name}:")
        
        # 显示最近 10 次
        recent = records[-10:]
        max_duration = max(r["duration_ms"] for r in recent)
        
        for record in recent:
            duration = record["duration_ms"]
            bar_len = int(duration / max_duration * 40) if max_duration > 0 else 0
            bar = "█" * bar_len
            status_icon = "✅" if record["status"] == "ok" else "❌"
            print(f"  {record['timestamp'][-8:]} {bar:<40} {duration:>6.0f}ms {status_icon}")
        
        print()


if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    if len(sys.argv) < 2:
        print("用法：python3 任务执行时间统计.py [选项]")
        print()
        print("选项:")
        print("  --view      查看最新统计")
        print("  --trend     显示趋势图 (文本)")
        print("  --analyze   分析性能劣化任务")
        print("  --clear     清空历史数据")
        print()
        print("示例:")
        print("  python3 任务执行时间统计.py --view")
        print("  python3 任务执行时间统计.py --analyze")
        sys.exit(1)
    
    option = sys.argv[1]
    
    if option == "--view":
        show_statistics()
    elif option == "--trend":
        show_trend()
    elif option == "--analyze":
        analyze_degradation()
    elif option == "--clear":
        clear_history()
    else:
        print(f"❌ 未知选项：{option}")
        sys.exit(1)
