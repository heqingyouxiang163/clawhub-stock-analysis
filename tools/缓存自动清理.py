#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存自动清理脚本
功能：
1. 清理超过 24 小时的缓存文件
2. 清理临时文件 (.tmp)
3. 保留今日文件
"""

import os
import time
from datetime import datetime

# 配置
TEMP_DIR = "/home/admin/openclaw/workspace/temp"
CACHE_TTL = 86400  # 24 小时 (秒)


def cleanup_old_files():
    """清理过期文件"""
    cleaned_count = 0
    freed_size = 0
    current_time = time.time()
    
    print(f"🧹 开始清理缓存...")
    print(f"📂 目录：{TEMP_DIR}")
    print(f"⏰ 保留：{CACHE_TTL/3600:.0f}小时内的文件")
    print()
    
    for root, dirs, files in os.walk(TEMP_DIR):
        for filename in files:
            filepath = os.path.join(root, filename)
            
            try:
                # 获取文件修改时间
                file_age = current_time - os.path.getmtime(filepath)
                file_size = os.path.getsize(filepath)
                
                # 清理条件
                should_delete = False
                reason = ""
                
                # 1. 清理.tmp 文件
                if filename.endswith('.tmp'):
                    should_delete = True
                    reason = "临时文件"
                
                # 2. 清理超过 TTL 的缓存
                elif file_age > CACHE_TTL:
                    should_delete = True
                    reason = f"过期 {file_age/3600:.1f}小时"
                
                # 3. 清理旧日志 (7 天前)
                elif filename.endswith('.log') and file_age > 7 * 86400:
                    should_delete = True
                    reason = "旧日志"
                
                # 执行清理
                if should_delete:
                    os.remove(filepath)
                    cleaned_count += 1
                    freed_size += file_size
                    print(f"  ✅ 删除：{filename} ({reason}, {file_size/1024:.1f}KB)")
            
            except Exception as e:
                print(f"  ⚠️ 跳过：{filename} ({e})")
    
    print()
    print(f"📊 清理完成:")
    print(f"  删除文件：{cleaned_count}个")
    print(f"  释放空间：{freed_size/1024:.1f}KB")
    
    return cleaned_count, freed_size


if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    print("=" * 60)
    print("🧹 缓存自动清理")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    cleanup_old_files()
    
    print()
    print("=" * 60)

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
