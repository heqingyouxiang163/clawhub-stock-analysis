#!/bin/bash

# 🦞 小艺系统自动备份脚本
# 用法：./自动备份.sh [commit_message]

set -e

cd /home/admin/openclaw/workspace

echo "🦞 开始自动备份..."
echo "📅 时间：$(date +'%Y-%m-%d %H:%M:%S')"
echo ""

# 添加所有文件
git add -A

# 检查是否有变化
if git diff --staged --quiet; then
    echo "✅ 无变化，跳过备份"
    exit 0
fi

# 显示变化的文件
echo "📝 变化的文件:"
git diff --staged --name-only | head -10
echo ""

# 提交变化
MESSAGE="${1:-🦞 自动备份 $(date +'%Y-%m-%d %H:%M')}"
echo "💾 提交：$MESSAGE"
git commit -m "$MESSAGE"

# 推送到所有远程仓库
echo ""
echo "📤 开始推送..."

if git remote get-url origin &>/dev/null; then
    echo "📤 推送到 GitHub..."
    git push origin main 2>&1 | grep -E "Updating|error|!" || echo "  ✅ 推送成功"
fi

if git remote get-url gitlab &>/dev/null; then
    echo "📤 推送到 GitLab..."
    git push gitlab main 2>&1 | grep -E "Updating|error|!" || echo "  ✅ 推送成功"
fi

if git remote get-url gitee &>/dev/null; then
    echo "📤 推送到 Gitee..."
    git push gitee main 2>&1 | grep -E "Updating|error|!" || echo "  ✅ 推送成功"
fi

echo ""
echo "✅ 备份完成！"
echo "📊 仓库大小：$(du -sh .git | cut -f1)"
echo "📝 提交数量：$(git rev-list --count HEAD)"
