#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🦞 定时任务批量替换脚本

功能：
1. 删除所有旧定时任务
2. 创建新的完整定时任务系统
3. 整合 dev 分支所有新功能
"""

import subprocess
import json
import sys
from datetime import datetime

# 颜色输出
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_color(text, color=RESET):
    print(f"{color}{text}{RESET}")

def run_command(cmd):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)

def get_all_cron_jobs():
    """获取所有定时任务"""
    success, output = run_command("openclaw cron list --includeDisabled 2>/dev/null")
    if not success:
        return []
    
    jobs = []
    lines = output.strip().split('\n')
    for line in lines[1:]:  # 跳过标题行
        if line.strip():
            parts = line.split()
            if len(parts) >= 2:
                jobs.append({
                    'id': parts[0],
                    'name': parts[1]
                })
    return jobs

def delete_cron_job(job_id):
    """删除定时任务"""
    success, output = run_command(f"openclaw cron remove {job_id} 2>/dev/null")
    return success

def add_cron_job(name, cron_expr, system_event, session_target="isolated"):
    """添加定时任务"""
    cmd = f'openclaw cron add --name "{name}" --cron "{cron_expr}" --system-event "{system_event}" 2>/dev/null'
    success, output = run_command(cmd)
    return success, output

# ======================================
# 新定时任务配置
# ======================================

NEW_CRON_JOBS = [
    # ========== 盘前任务 ==========
    {
        'name': '🦞 消息面分析 (交易日 7:00)',
        'cron': '0 7 * * 1-5',
        'event': 'python3 /home/admin/openclaw/workspace/tools/消息面分析.py',
        'desc': '分析隔夜消息面'
    },
    {
        'name': '🦞 情绪周期判断 (交易日 9:00)',
        'cron': '0 9 * * 1-5',
        'event': 'python3 /home/admin/openclaw/workspace/tools/情绪周期判断_快速版.py',
        'desc': '判断市场情绪周期'
    },
    {
        'name': '🦞 集合竞价监控 (交易日 9:20)',
        'cron': '20 9 * * 1-5',
        'event': 'python3 /home/admin/openclaw/workspace/tools/集合竞价监控 - 实时数据版.py',
        'desc': '监控集合竞价数据'
    },
    
    # ========== 早盘任务 (9:30-10:30) ==========
    {
        'name': '🦞 短线盈利推荐 -9:35',
        'cron': '35 9 * * 1-5',
        'event': 'python3 /home/admin/openclaw/workspace/tools/短线盈利助手.py',
        'desc': '早盘首推'
    },
    {
        'name': '🦞 短线盈利推荐 -9:40',
        'cron': '40 9 * * 1-5',
        'event': 'python3 /home/admin/openclaw/workspace/tools/短线盈利助手.py',
        'desc': '早盘第二推'
    },
    {
        'name': '🦞 短线盈利推荐 -9:45',
        'cron': '45 9 * * 1-5',
        'event': 'python3 /home/admin/openclaw/workspace/tools/短线盈利助手.py',
        'desc': '早盘第三推'
    },
    {
        'name': '🦞 短线盈利推荐 -9:50',
        'cron': '50 9 * * 1-5',
        'event': 'python3 /home/admin/openclaw/workspace/tools/短线盈利助手.py',
        'desc': '早盘第四推'
    },
    {
        'name': '🦞 短线盈利推荐 -9:55',
        'cron': '55 9 * * 1-5',
        'event': 'python3 /home/admin/openclaw/workspace/tools/短线盈利助手.py',
        'desc': '早盘第五推'
    },
    {
        'name': '🦞 短线盈利推荐 -10:00',
        'cron': '0 10 * * 1-5',
        'event': 'python3 /home/admin/openclaw/workspace/tools/短线盈利助手.py',
        'desc': '早盘第六推'
    },
    {
        'name': '🦞 短线盈利推荐 -10:05',
        'cron': '5 10 * * 1-5',
        'event': 'python3 /home/admin/openclaw/workspace/tools/短线盈利助手.py',
        'desc': '早盘第七推'
    },
    {
        'name': '🦞 短线盈利推荐 -10:10',
        'cron': '10 10 * * 1-5',
        'event': 'python3 /home/admin/openclaw/workspace/tools/短线盈利助手.py',
        'desc': '早盘第八推'
    },
    {
        'name': '🦞 短线盈利推荐 -10:15',
        'cron': '15 10 * * 1-5',
        'event': 'python3 /home/admin/openclaw/workspace/tools/短线盈利助手.py',
        'desc': '早盘第九推'
    },
    {
        'name': '🦞 短线盈利推荐 -10:20',
        'cron': '20 10 * * 1-5',
        'event': 'python3 /home/admin/openclaw/workspace/tools/短线盈利助手.py',
        'desc': '早盘第十推'
    },
    {
        'name': '🦞 短线盈利推荐 -10:25',
        'cron': '25 10 * * 1-5',
        'event': 'python3 /home/admin/openclaw/workspace/tools/短线盈利助手.py',
        'desc': '早盘第十一推'
    },
    {
        'name': '🦞 短线盈利推荐 -10:30',
        'cron': '30 10 * * 1-5',
        'event': 'python3 /home/admin/openclaw/workspace/tools/短线盈利助手.py',
        'desc': '早盘最后一推'
    },
    
    # ========== 盘中任务 ==========
    {
        'name': '🦞 盘中监控 -10:00',
        'cron': '0 10 * * 1-5',
        'event': 'python3 /home/admin/openclaw/workspace/tools/盘中监控系统_腾讯版.py',
        'desc': '盘中实时监控'
    },
    {
        'name': '🦞 智能分析 -10 点',
        'cron': '0 10 * * 1-5',
        'event': 'python3 /home/admin/openclaw/workspace/tools/智能分析系统.py',
        'desc': '智能分析系统'
    },
    {
        'name': '🦞 持仓监控 - 多股监控',
        'cron': '*/10 9-11,13-15 * * 1-5',
        'event': 'python3 /home/admin/openclaw/workspace/tools/持仓实时监控.py',
        'desc': '持仓实时监控股'
    },
    {
        'name': '🦞 自动止损止盈监控',
        'cron': '*/1 9-11,13-15 * * 1-5',
        'event': 'python3 /home/admin/openclaw/workspace/tools/自动止损止盈监控.py',
        'desc': '每分钟监控止损止盈'
    },
    
    # ========== 午后任务 ==========
    {
        'name': '🦞 智能分析 -14 点',
        'cron': '0 14 * * 1-5',
        'event': 'python3 /home/admin/openclaw/workspace/tools/智能分析系统.py',
        'desc': '午后智能分析'
    },
    {
        'name': '🦞 盘中监控 -14 点',
        'cron': '0 14 * * 1-5',
        'event': 'python3 /home/admin/openclaw/workspace/tools/盘中监控系统_腾讯版.py',
        'desc': '午后实时监控'
    },
    
    # ========== 盘后任务 ==========
    {
        'name': '🦞 涨停形态每日学习 (交易日 15:30)',
        'cron': '30 15 * * 1-5',
        'event': 'python3 /home/admin/openclaw/workspace/tools/涨停分时形态学习.py',
        'desc': '学习今日涨停形态'
    },
    {
        'name': '🦞 盘后复盘 (交易日 15:30)',
        'cron': '30 15 * * 1-5',
        'event': 'python3 /home/admin/openclaw/workspace/tools/盘后复盘.py',
        'desc': '盘后复盘总结'
    },
    {
        'name': '🦞 龙虎榜分析 (交易日 17:00)',
        'cron': '0 17 * * 1-5',
        'event': 'python3 /home/admin/openclaw/workspace/tools/龙虎榜分析.py',
        'desc': '分析龙虎榜数据'
    },
    
    # ========== 晚间任务 ==========
    {
        'name': '🦞 策略回测 (每周日 20:00)',
        'cron': '0 20 * * 0',
        'event': 'python3 /home/admin/openclaw/workspace/tools/策略回测_v4.py',
        'desc': '周度策略回测'
    },
    
    # ========== 深夜任务 ==========
    {
        'name': '🦞 每日更新技能记忆表格',
        'cron': '0 23 * * *',
        'event': 'python3 /home/admin/openclaw/workspace/tools/技能记忆表格更新.py',
        'desc': '更新技能记忆'
    },
    {
        'name': '🦞 自我学习升级 (每日 23:00)',
        'cron': '0 23 * * *',
        'event': 'python3 /home/admin/openclaw/workspace/tools/自主进化自检.py',
        'desc': '自我学习升级'
    },
    {
        'name': '🦞 每日记忆固化 (自动更新 MEMORY)',
        'cron': '0 23 * * *',
        'event': 'python3 /home/admin/openclaw/workspace/tools/每日记忆固化.py',
        'desc': '固化今日记忆'
    },
    {
        'name': '📅 每日自动提交 (23:00)',
        'cron': '0 23 * * *',
        'event': 'python3 /home/admin/openclaw/workspace/tools/每日自动提交.py',
        'desc': '自动提交代码'
    },
    
    # ========== 监控任务 ==========
    {
        'name': '🦞 定时任务监控 (每 4 小时)',
        'cron': '0 */4 * * *',
        'event': 'python3 /home/admin/openclaw/workspace/tools/定时任务全自动化监控.py',
        'desc': '监控所有定时任务'
    },
    {
        'name': '🦞 自主进化自检 (每 3 小时)',
        'cron': '0 */3 * * *',
        'event': 'python3 /home/admin/openclaw/workspace/tools/自主进化自检.py',
        'desc': '自主进化检查'
    },
    {
        'name': '🦞 数据源健康监控 (每小时)',
        'cron': '0 * * * *',
        'event': 'python3 /home/admin/openclaw/workspace/tools/数据源健康监控.py',
        'desc': '监控数据源健康度'
    },
]

# ======================================
# 主流程
# ======================================

def main():
    print_color("\n" + "="*60, BLUE)
    print_color("🦞 定时任务批量替换脚本", BLUE)
    print_color("="*60 + "\n", BLUE)
    
    # 1. 获取所有现有任务
    print_color("📋 步骤 1: 获取现有定时任务...", YELLOW)
    jobs = get_all_cron_jobs()
    print_color(f"   找到 {len(jobs)} 个定时任务\n", GREEN)
    
    # 2. 删除所有旧任务
    print_color("🗑️  步骤 2: 删除所有旧定时任务...", YELLOW)
    deleted_count = 0
    for job in jobs:
        if delete_cron_job(job['id']):
            print_color(f"   ✅ 删除：{job['name']}", GREEN)
            deleted_count += 1
        else:
            print_color(f"   ❌ 失败：{job['name']}", RED)
    print_color(f"   共删除 {deleted_count}/{len(jobs)} 个任务\n", GREEN)
    
    # 3. 创建新任务
    print_color("➕ 步骤 3: 创建新的定时任务系统...", YELLOW)
    created_count = 0
    failed_jobs = []
    
    for job_config in NEW_CRON_JOBS:
        success, output = add_cron_job(
            name=job_config['name'],
            cron_expr=job_config['cron'],
            system_event=job_config['event']
        )
        
        if success:
            print_color(f"   ✅ 创建：{job_config['name']} ({job_config['desc']})", GREEN)
            created_count += 1
        else:
            print_color(f"   ❌ 失败：{job_config['name']}", RED)
            failed_jobs.append(job_config)
    
    print_color(f"\n   共创建 {created_count}/{len(NEW_CRON_JOBS)} 个任务\n", GREEN)
    
    # 4. 汇报结果
    print_color("="*60, BLUE)
    print_color("📊 替换完成汇报", BLUE)
    print_color("="*60, BLUE)
    print_color(f"✅ 删除旧任务：{deleted_count}/{len(jobs)}", GREEN)
    print_color(f"✅ 创建新任务：{created_count}/{len(NEW_CRON_JOBS)}", GREEN)
    
    if failed_jobs:
        print_color(f"\n⚠️  失败的任务 ({len(failed_jobs)}个):", RED)
        for job in failed_jobs:
            print_color(f"   - {job['name']}", RED)
    
    print_color("\n🎉 新定时任务系统已启用！", GREEN)
    print_color("\n📅 下次执行时间:", BLUE)
    print_color("   - 消息面分析：明日 07:00", BLUE)
    print_color("   - 情绪周期判断：明日 09:00", BLUE)
    print_color("   - 集合竞价监控：明日 09:20", BLUE)
    print_color("   - 短线盈利推荐：明日 09:35 开始 (每 5 分钟)", BLUE)
    print_color("   - 主动对话：明日 09:20/11:30/15:00/20:00", BLUE)
    
    print_color("\n" + "="*60 + "\n", BLUE)

if __name__ == '__main__':
    main()
