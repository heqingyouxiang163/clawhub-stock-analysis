#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Token 消耗分析工具

功能:
1. 检查所有定时任务的 Token 消耗
2. 识别不合理的配置
3. 给出优化建议
"""

import json
import os
from datetime import datetime

# Cron 任务文件
CRON_JOBS_FILE = "/home/admin/.openclaw/cron/jobs.json"

# 配置
HIGH_FREQUENCY_THRESHOLD = 60  # 执行间隔<60 秒视为高频
LONG_TIMEOUT_THRESHOLD = 120  # 超时>120 秒视为过长
EXPENSIVE_MODELS = ['qwen3.5-plus', 'qwen-max']  # 昂贵模型

def load_jobs():
    """加载任务列表"""
    try:
        with open(CRON_JOBS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('jobs', [])
    except Exception as e:
        print(f"❌ 加载失败：{e}")
        return []

def analyze_frequency(job):
    """分析执行频率"""
    schedule = job.get('schedule', {})
    kind = schedule.get('kind', '')
    
    if kind == 'every':
        every_ms = schedule.get('everyMs', 0)
        every_sec = every_ms / 1000
        
        if every_sec < HIGH_FREQUENCY_THRESHOLD:
            return f"⚠️ 高频：每{every_sec}秒执行一次"
        elif every_sec < 300:
            return f"✅ 合理：每{every_sec/60:.0f}分钟执行一次"
        else:
            return f"✅ 低频：每{every_sec/3600:.1f}小时执行一次"
    
    elif kind == 'cron':
        expr = schedule.get('expr', '')
        # 简单分析 cron 表达式
        if expr.startswith('*/1'):
            return "⚠️ 高频：每分钟执行"
        elif expr.startswith('*/5'):
            return "✅ 合理：每 5 分钟执行"
        elif expr.startswith('*/10'):
            return "✅ 合理：每 10 分钟执行"
        else:
            return f"✅ 定时：{expr}"
    
    return "✅ 未知频率"

def analyze_timeout(job):
    """分析超时设置"""
    payload = job.get('payload', {})
    timeout = payload.get('timeoutSeconds', 0)
    
    if timeout > LONG_TIMEOUT_THRESHOLD:
        return f"⚠️ 过长：{timeout}秒 (建议≤120 秒)"
    elif timeout > 300:
        return f"❌ 太长：{timeout}秒 (建议≤300 秒)"
    elif timeout == 0:
        return "⚠️ 无超时限制 (建议设置)"
    else:
        return f"✅ 合理：{timeout}秒"

def analyze_model(job):
    """分析模型使用"""
    payload = job.get('payload', {})
    model = payload.get('model', 'default')
    
    if model in EXPENSIVE_MODELS:
        return f"⚠️ 昂贵：{model} (考虑使用默认模型)"
    elif model == 'default' or not model:
        return "✅ 默认模型"
    else:
        return f"✅ {model}"

def analyze_task(job):
    """分析单个任务"""
    job_name = job.get('name', 'Unknown')
    
    print(f"\n📋 {job_name}")
    print(f"  频率：{analyze_frequency(job)}")
    print(f"  超时：{analyze_timeout(job)}")
    print(f"  模型：{analyze_model(job)}")

def main():
    """主函数"""
    print("=" * 70)
    print("💰 Token 消耗分析")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()
    
    jobs = load_jobs()
    if not jobs:
        print("❌ 无任务数据")
        return
    
    print(f"📊 任务总数：{len(jobs)}个")
    print()
    
    # 分类统计
    high_frequency = []
    long_timeout = []
    expensive_model = []
    
    for job in jobs:
        job_name = job.get('name', 'Unknown')
        schedule = job.get('schedule', {})
        payload = job.get('payload', {})
        
        # 检查频率
        if schedule.get('kind') == 'every':
            every_sec = schedule.get('everyMs', 0) / 1000
            if every_sec < HIGH_FREQUENCY_THRESHOLD:
                high_frequency.append(job_name)
        
        # 检查超时
        timeout = payload.get('timeoutSeconds', 0)
        if timeout > LONG_TIMEOUT_THRESHOLD:
            long_timeout.append((job_name, timeout))
        
        # 检查模型
        model = payload.get('model', '')
        if model in EXPENSIVE_MODELS:
            expensive_model.append((job_name, model))
    
    # 输出问题
    print("=" * 70)
    print("⚠️ 发现问题")
    print("=" * 70)
    
    if high_frequency:
        print(f"\n📍 高频任务 ({len(high_frequency)}个):")
        for name in high_frequency:
            print(f"  - {name}")
    
    if long_timeout:
        print(f"\n⏱️ 超时过长 ({len(long_timeout)}个):")
        for name, timeout in long_timeout:
            print(f"  - {name}: {timeout}秒")
    
    if expensive_model:
        print(f"\n💎 昂贵模型 ({len(expensive_model)}个):")
        for name, model in expensive_model:
            print(f"  - {name}: {model}")
    
    if not high_frequency and not long_timeout and not expensive_model:
        print("\n✅ 未发现明显问题！")
    
    # 优化建议
    print()
    print("=" * 70)
    print("💡 优化建议")
    print("=" * 70)
    
    if high_frequency:
        print("\n1. 降低高频任务频率:")
        for name in high_frequency:
            print(f"   - {name}: 建议改为每 5-10 分钟")
    
    if long_timeout:
        print("\n2. 缩短超时时间:")
        for name, timeout in long_timeout:
            print(f"   - {name}: {timeout}秒 → 建议 60-120 秒")
    
    if expensive_model:
        print("\n3. 使用默认模型:")
        for name, model in expensive_model:
            print(f"   - {name}: {model} → 建议 default")
    
    print("\n4. 添加缓存机制:")
    print("   - 数据获取任务添加 2-5 分钟缓存")
    print("   - 避免重复 API 调用")
    
    print("\n5. 盘中任务时段限制:")
    print("   - 确保所有盘中任务仅在 9-11,13-15 执行")
    print("   - 避免非交易时段无效执行")
    
    print()
    print("=" * 70)

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
    main()
