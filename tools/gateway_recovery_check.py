#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gateway 重启自动检查脚本
用途：Gateway 重启后自动检查系统状态并恢复
"""

import json
import subprocess
from datetime import datetime

def run_command(cmd):
    """执行 shell 命令"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def check_cron_status():
    """检查 cron 任务状态"""
    print("🔍 检查 cron 任务状态...")
    output = run_command("cron status")
    
    if "enabled: true" in output:
        print("✅ cron 调度器：正常")
        return True
    else:
        print("❌ cron 调度器：异常")
        return False

def check_cron_jobs():
    """检查 cron 任务数量"""
    print("🔍 检查 cron 任务数量...")
    output = run_command("cron list --include-disabled")
    
    if "jobs:" in output:
        # 解析任务数量
        for line in output.split('\n'):
            if 'jobs:' in line:
                jobs_count = int(line.split(':')[1].strip())
                if jobs_count >= 22:
                    print(f"✅ cron 任务：正常 ({jobs_count}个)")
                    return True
                else:
                    print(f"⚠️ cron 任务：偏少 ({jobs_count}个，预期≥22)")
                    return False
    
    print("❌ cron 任务：无法解析")
    return False

def check_key_files():
    """检查关键文件"""
    print("🔍 检查关键文件...")
    
    files = [
        "/home/admin/openclaw/workspace/SOUL.md",
        "/home/admin/openclaw/workspace/MEMORY.md",
        "/home/admin/openclaw/workspace/AGENTS.md",
        "/home/admin/openclaw/workspace/memory/自我进化/",
    ]
    
    import os
    all_exist = True
    for file in files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} (缺失)")
            all_exist = False
    
    return all_exist

def check_heartbeat_task():
    """检查心跳任务"""
    print("🔍 检查心跳任务...")
    output = run_command("cron list --include-disabled | grep '心跳'")
    
    if "心跳" in output and "enabled: true" in output:
        print("✅ 心跳任务：正常")
        return True
    else:
        print("⚠️ 心跳任务：未找到或禁用")
        return False

def check_memory_role():
    """检查 MEMORY.md 角色设定"""
    print("🔍 检查 MEMORY.md 角色设定...")
    
    try:
        with open("/home/admin/openclaw/workspace/MEMORY.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        if "炒股龙虾 v17.0" in content:
            print("✅ 角色设定：正常")
            return True
        else:
            print("❌ 角色设定：缺失")
            return False
    except Exception as e:
        print(f"❌ 读取 MEMORY.md 失败：{e}")
        return False

def write_recovery_log(status, details):
    """写入恢复日志"""
    print("📝 写入恢复日志...")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    log_content = f"""# Gateway 恢复日志

## {timestamp} 重启检查

**触发**: GatewayRestart 通知

**检查结果**:
"""
    
    for key, value in details.items():
        status_icon = "✅" if value else "❌"
        log_content += f"- {status_icon} {key}\n"
    
    log_content += f"\n**总体状态**: {'✅ 全部正常' if all(details.values()) else '⚠️ 部分异常'}\n"
    log_content += f"\n**检查时间**: {timestamp}\n"
    
    log_path = "/home/admin/openclaw/workspace/memory/自我进化/Gateway 恢复日志.md"
    
    # 追加到日志文件
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(log_content + "\n---\n\n")
    
    print(f"✅ 恢复日志已写入：{log_path}")

def main():
    """主函数"""
    print("=" * 50)
    print("🦞 Gateway 重启自动检查")
    print("=" * 50)
    print()
    
    # 执行检查
    results = {}
    results["cron 调度器"] = check_cron_status()
    results["cron 任务"] = check_cron_jobs()
    results["关键文件"] = check_key_files()
    results["心跳任务"] = check_heartbeat_task()
    results["角色设定"] = check_memory_role()
    
    print()
    print("=" * 50)
    print("📊 检查结果汇总")
    print("=" * 50)
    
    all_ok = all(results.values())
    
    for key, value in results.items():
        status_icon = "✅" if value else "❌"
        print(f"{status_icon} {key}: {'正常' if value else '异常'}")
    
    print()
    if all_ok:
        print("✅ 全部检查通过！系统正常。")
    else:
        print("⚠️ 部分检查未通过，请手动检查。")
    
    # 写入恢复日志
    write_recovery_log(all_ok, results)
    
    print()
    print("=" * 50)
    print("🦞 检查完成！")
    print("=" * 50)

    # 显示总耗时
    total_elapsed = time.time() - total_start
    if total_elapsed < 1:
        print(f"✅ **总耗时**: {total_elapsed*1000:.0f}ms")
    elif total_elapsed < 60:
        print(f"✅ **总耗时**: {total_elapsed:.1f}秒")
    else:
        print(f"✅ **总耗时**: {total_elapsed/60:.1f}分钟")

if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    main()
