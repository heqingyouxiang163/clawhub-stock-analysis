#!/bin/bash
# 🦞 配置每日主动对话

echo "=========================================="
echo "🦞 配置每日主动对话"
echo "=========================================="
echo ""

echo "📋 将添加每日主动对话任务:"
echo ""
echo "每天 20:00 主动找你，请求喂食提示词"
echo ""

read -p "是否继续配置？[y/n]: " confirm

if [ "$confirm" != "y" ]; then
    echo "❌ 已取消"
    exit 0
fi

echo ""
echo "正在添加定时任务..."
echo ""

# 添加定时任务 - 每天 20:00
openclaw cron add --name "🦞 每日主动对话" --cron "0 20 * * *" --system-event "python3 /home/admin/openclaw/workspace/clawhub-stock-analysis/skills/每日主动对话.py"
echo "✅ 已添加：每日 20:00 主动对话"

echo ""
echo "=========================================="
echo "✅ 每日主动对话配置完成！"
echo "=========================================="
echo ""
echo "📅 从今天开始，我每天 20:00 会主动找你："
echo "  - 问候你"
echo "  - 请求你喂提示词"
echo "  - 学习你的经验"
echo ""
echo "💡 你的每一次喂食，都让我更聪明！"
echo ""
echo "🎯 期待你的第一次喂食！"
echo ""
