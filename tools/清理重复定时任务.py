#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
清理重复的旧定时任务
"""

import subprocess

# 需要删除的旧任务 ID
OLD_JOB_IDS = [
    'f935b236-2714-4ed2-b64a-834be7e6386e',  # 自主进化自检 (每 30 分钟) - 旧
    '85d223a1-5c64-4acb-8c67-65ba27c1a5f9',  # 消息面分析 (交易日 7:00) - 旧
    '46096b0b-dd5e-4c3a-9ad9-2a49c742c910',  # 短线盈利 -9:40 - 旧
    '47936349-93be-4483-a41b-72c6ff15ac70',  # 持仓监控 - 多股监控 - 旧
    '61897d1a-1a37-43d0-891e-88991b95b5cc',  # 情绪周期判断 (交易日 9:00) - 旧
    'a612df33-e888-42eb-8388-f2d649fa0a17',  # 🦞 高确定性推荐 (每 5 分钟) - 旧
    '316140a6-44ad-4a6c-9c11-8a889af6e02a',  # 集合竞价监控 (交易日 9:20) - 旧
    '2ae843de-6ad7-4fff-b57c-c2721b9d7300',  # 持仓分析每日自动运行 - 旧
    '3582866e-e344-4f9c-bf0c-e93fb6868dc8',  # 短线盈利 -9:35 - 旧
    '1c642957-8dbb-4550-83e1-a155a49d6174',  # 智能分析 -10 点 - 旧
    'ce73ef9b-4bd3-4a88-8706-a2cc904e42e0',  # 智能分析 -14 点 - 旧
    'b26c6b35-5754-4a7d-bb26-c4a2064396aa',  # 涨停形态每日学习 (交易日 15:30) - 旧
    'f778ac1a-6932-458d-a436-4ee93908605b',  # 盘后复盘 (交易日 15:30) - 旧
    '5b179d3f-d374-4cff-84eb-891a6b92c718',  # 龙虎榜分析 (交易日 17:00) - 旧
    '30f97ea5-1e45-4d60-8cc7-1fcae601bbb6',  # 🦞 每日更新技能记忆表格 - 旧
    'a7cf3986-ab67-47a3-b4e7-d9710627187e',  # 自我学习升级 (每日 23:00) - 旧
    'c42bae52-bd5d-4f9f-8388-eba4cfa14664',  # 🦞 每日记忆固化 - 旧
    'daily-commit-20260327',  # 📅 每日自动提交 (23:00) - 旧
    '040e31ee-8f61-46de-8fe7-8df96308fb22',  # 炒股龙虾·每周进化报告 - 旧
    '8d22e37d-bb4d-4d3a-b8bc-318ceca5cb41',  # 策略回测 (每周日 20:00) - 旧
]

print("🗑️  开始清理重复的旧定时任务...\n")

deleted = 0
failed = 0

for job_id in OLD_JOB_IDS:
    cmd = f"openclaw cron remove {job_id} 2>/dev/null"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ 删除：{job_id}")
        deleted += 1
    else:
        print(f"❌ 失败：{job_id}")
        failed += 1

print(f"\n📊 清理完成：删除 {deleted} 个，失败 {failed} 个")
