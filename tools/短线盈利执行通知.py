#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
短线盈利任务执行通知
功能：检查短线盈利任务执行情况，发送执行时间通知
"""

import json
import os
from datetime import datetime


# 配置
OUTPUT_DIR = "/home/admin/openclaw/workspace/temp/短线盈利助手"
STATS_FILE = os.path.join(OUTPUT_DIR, "推送统计.json")
NOTIFICATION_LOG = os.path.join(OUTPUT_DIR, "执行通知日志.md")


def check_and_notify():
    """检查执行记录并发送通知"""
    now = datetime.now()
    
    # 加载推送统计
    if not os.path.exists(STATS_FILE):
        print("⚠️ 推送统计文件不存在")
        return
    
    with open(STATS_FILE, 'r', encoding='utf-8') as f:
        stats = json.load(f)
    
    pushes = stats.get('pushes', [])
    
    if not pushes:
        print("✅ 无推送记录")
        return
    
    # 获取最近一次推送
    last_push = pushes[-1]
    push_time = last_push.get('time', '')
    stock_count = last_push.get('count', 0)
    stocks = last_push.get('stocks', [])
    
    # 生成通知
    notification = f"""
🦞 **短线盈利助手执行通知**

**执行时间**: {push_time}
**推荐股票**: {stock_count}只
"""
    
    if stocks:
        notification += "\n**推荐列表**:\n"
        for stock in stocks:
            code = stock.get('code', '')
            name = stock.get('name', '')
            score = stock.get('score', 0)
            notification += f"- {code} {name} ({score}分)\n"
    else:
        notification += "\n**说明**: 本次无符合条件的高确定性股票\n"
    
    notification += "\n⏱️ 下次执行：5 分钟后"
    notification += "\n📊 查看日志：`temp/短线盈利助手/`"
    
    # 保存通知日志
    with open(NOTIFICATION_LOG, 'a', encoding='utf-8') as f:
        f.write(f"\n---\n## {push_time}\n{notification}\n")
    
    # 打印通知
    print(notification)
    
    # TODO: 集成消息发送
    # send_message(notification)
    
    print(f"\n✅ 通知已记录：{NOTIFICATION_LOG}")


if __name__ == "__main__":
    check_and_notify()
