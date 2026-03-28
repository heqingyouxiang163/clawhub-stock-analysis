#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
23:00 任务完成通知工具

用途：在 23:00 任务执行完成后立即发送通知
使用：在每个 23:00 任务的 payload 末尾调用此脚本
"""

import subprocess
import sys
from datetime import datetime

def send_notification(task_name, message):
    """发送通知"""
    time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 替换时间占位符
    message = message.replace('{time}', time_str)
    
    # 发送通知
    try:
        cmd = [
            'openclaw', 'message', 'send',
            '--target', '779558319',
            '--message', message
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ 通知已发送：{task_name}")
        return True
    except Exception as e:
        print(f"❌ 通知发送失败：{e}")
        return False

if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    if len(sys.argv) < 3:
        print("用法：python3 23 点任务完成通知.py <任务名> <消息模板>")
        sys.exit(1)
    
    task_name = sys.argv[1]
    message = sys.argv[2]
    send_notification(task_name, message)
