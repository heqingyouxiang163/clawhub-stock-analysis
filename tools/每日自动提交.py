#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📅 每日自动提交脚本

功能：
- 每天 23:00 自动提交当天的所有更改
- 生成提交摘要
- 推送到 GitHub 远程仓库

使用方式：
作为 cron 定时任务运行
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_command(cmd, cwd=None):
    """运行 shell 命令"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def get_git_status(cwd):
    """获取 git 状态"""
    code, out, err = run_command("git status --short", cwd)
    return out.strip().split('\n') if out else []


def get_git_diff(cwd):
    """获取变更统计"""
    code, out, err = run_command("git diff --stat", cwd)
    return out.strip() if out else ""


def auto_commit_and_push():
    """自动提交并推送"""
    
    workspace = Path("/home/admin/openclaw/workspace")
    today = datetime.now().strftime('%Y-%m-%d')
    
    print("=" * 70)
    print(f"📅 每日自动提交 - {today}")
    print("=" * 70)
    
    # 1. 检查 git 状态
    print("\n1️⃣ 检查 git 状态...")
    status = get_git_status(workspace)
    
    if not status:
        print("✅ 没有需要提交的更改")
        return True
    
    print(f"📝 发现 {len(status)} 个文件变更:")
    for line in status[:10]:  # 只显示前 10 个
        print(f"   {line}")
    if len(status) > 10:
        print(f"   ... 还有 {len(status) - 10} 个文件")
    
    # 2. 添加所有更改
    print("\n2️⃣ 添加所有更改...")
    code, out, err = run_command("git add -A", workspace)
    if code != 0:
        print(f"❌ git add 失败：{err}")
        return False
    print("✅ 已添加所有文件")
    
    # 3. 获取变更统计
    print("\n3️⃣ 变更统计:")
    diff_stat = get_git_diff(workspace)
    if diff_stat:
        for line in diff_stat.split('\n')[:5]:
            print(f"   {line}")
    
    # 4. 提交
    print("\n4️⃣ 提交更改...")
    commit_msg = f"chore: {today} 每日自动提交\n\n- 自动提交当日所有更改\n- 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    code, out, err = run_command(f'git commit -m "{commit_msg}"', workspace)
    
    if code != 0:
        if "nothing to commit" in err:
            print("✅ 没有需要提交的更改")
            return True
        print(f"❌ 提交失败：{err}")
        return False
    
    # 提取 commit hash
    commit_hash = out.split('[')[1].split(']')[0] if '[' in out else "unknown"
    print(f"✅ 提交成功：{commit_hash}")
    
    # 5. 推送
    print("\n5️⃣ 推送到远程仓库...")
    code, out, err = run_command("git push origin main", workspace)
    
    if code != 0:
        if "already up-to-date" in out or "already up to date" in out:
            print("✅ 已经是最新")
            return True
        print(f"❌ 推送失败：{err}")
        return False
    
    print("✅ 推送成功")
    
    # 6. 总结
    print("\n" + "=" * 70)
    print("🎉 每日自动提交完成！")
    print("=" * 70)
    print(f"📅 日期：{today}")
    print(f"📝 文件变更：{len(status)} 个")
    print(f"🔖 Commit: {commit_hash}")
    print("=" * 70)
    
    return True


def main():
    """主函数"""
    
    print("\n🦞 炒股龙虾系统 - 每日自动提交\n")
    
    success = auto_commit_and_push()
    
    if success:
        print("\n✅ 自动提交成功")
        sys.exit(0)
    else:
        print("\n❌ 自动提交失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
