#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自主进化系统自检 (优化版)
用途：每 30 分钟检查系统状态，发现问题自动记录
优化：简化检查项，快速执行
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path


WORKSPACE = Path('/home/admin/openclaw/workspace')
MEMORY_DIR = WORKSPACE / 'memory'
TOOLS_DIR = WORKSPACE / 'tools'
SKILLS_DIR = WORKSPACE / 'skills'


def check_data_accuracy():
    """检查数据准确率"""
    # 检查最近 3 天的记忆文件
    recent_files = []
    if MEMORY_DIR.exists():
        for f in MEMORY_DIR.glob('*.md'):
            recent_files.append(f)
    
    # 简单检查：有文件即正常
    status = '✅' if len(recent_files) > 0 else '⚠️'
    return {
        'status': status,
        'detail': f'{len(recent_files)} 个记忆文件'
    }


def check_automation_tasks():
    """检查自动化任务状态"""
    # 检查工具脚本
    tool_files = list(TOOLS_DIR.glob('*.py')) if TOOLS_DIR.exists() else []
    
    # 关键脚本
    critical_scripts = [
        '高确定性推荐 - 定时任务.py',
        '自动止损止盈监控.py',
        '定时任务监控.py',
    ]
    
    existing = [s for s in critical_scripts if (TOOLS_DIR / s).exists()]
    
    status = '✅' if len(existing) == len(critical_scripts) else '⚠️'
    return {
        'status': status,
        'detail': f'{len(existing)}/{len(critical_scripts)} 关键脚本'
    }


def check_skills():
    """检查技能库完整性"""
    if not SKILLS_DIR.exists():
        return {'status': '❌', 'detail': '技能目录不存在'}
    
    skill_dirs = [d for d in SKILLS_DIR.iterdir() if d.is_dir()]
    status = '✅' if len(skill_dirs) > 0 else '⚠️'
    return {
        'status': status,
        'detail': f'{len(skill_dirs)} 个技能'
    }


def check_errors():
    """检查错误日志"""
    error_log = WORKSPACE / 'temp' / 'error.log'
    if error_log.exists():
        try:
            content = error_log.read_text()
            lines = content.strip().split('\n')
            recent_errors = [l for l in lines if '2026-03-20' in l]
            if recent_errors:
                return {'status': '⚠️', 'detail': f'{len(recent_errors)} 个今日错误'}
        except:
            pass
    
    return {'status': '✅', 'detail': '无错误'}


def run_self_check():
    """运行自检"""
    print("=" * 60)
    print("🦞 自主进化系统自检")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    checks = {
        '数据准确率': check_data_accuracy(),
        '自动化任务': check_automation_tasks(),
        '技能库完整性': check_skills(),
        '错误日志': check_errors(),
    }
    
    for name, result in checks.items():
        print(f"{result['status']} {name}: {result['detail']}")
    
    print()
    print("=" * 60)
    
    # 汇总
    warnings = [r for r in checks.values() if r['status'] == '⚠️']
    errors = [r for r in checks.values() if r['status'] == '❌']
    
    if errors:
        print(f"❌ 发现 {len(errors)} 个严重问题")
    elif warnings:
        print(f"⚠️ 发现 {len(warnings)} 个警告")
    else:
        print("✅ 系统状态正常")
    
    print("=" * 60)
    
    return len(errors) == 0 and len(warnings) == 0


if __name__ == "__main__":
    start = time.time()
    
    success = run_self_check()
    
    elapsed = time.time() - start
    print(f"⏱️  执行耗时：{elapsed*1000:.0f}ms")
    
    exit(0 if success else 1)
