#!/bin/bash
# 🦞 配置主动对话定时任务

echo "=========================================="
echo "🦞 配置主动对话 - 完全自动化"
echo "=========================================="
echo ""

echo "📋 将添加以下定时任务:"
echo ""
echo "1. 09:20 早盘关注 (每日开盘前)"
echo "2. 11:30 上午总结 (每日上午收盘)"
echo "3. 15:00 收盘总结 (每日下午收盘)"
echo "4. 20:00 策略升级 (每晚上)"
echo ""

read -p "是否继续配置？[y/n]: " confirm

if [ "$confirm" != "y" ]; then
    echo "❌ 已取消"
    exit 0
fi

echo ""
echo "正在添加定时任务..."
echo ""

# 添加定时任务
openclaw cron add --name "🦞 主动对话 - 早盘关注" --cron "20 9 * * 1-5" --system-event "python3 /home/admin/openclaw/workspace/clawhub-stock-analysis/skills/主动对话.py 早盘关注"
echo "✅ 已添加：09:20 早盘关注"

openclaw cron add --name "🦞 主动对话 - 上午总结" --cron "30 11 * * 1-5" --system-event "python3 /home/admin/openclaw/workspace/clawhub-stock-analysis/skills/主动对话.py 上午总结"
echo "✅ 已添加：11:30 上午总结"

openclaw cron add --name "🦞 主动对话 - 收盘总结" --cron "0 15 * * 1-5" --system-event "python3 /home/admin/openclaw/workspace/clawhub-stock-analysis/skills/主动对话.py 收盘总结"
echo "✅ 已添加：15:00 收盘总结"

openclaw cron add --name "🦞 主动对话 - 策略升级" --cron "0 20 * * *" --system-event "python3 /home/admin/openclaw/workspace/clawhub-stock-analysis/skills/主动对话.py 策略升级"
echo "✅ 已添加：20:00 策略升级"

echo ""
echo "=========================================="
echo "✅ 主动对话配置完成！"
echo "=========================================="
echo ""
echo "📅 从明天开始，我会主动找你："
echo "  09:20 早盘关注"
echo "  11:30 上午总结"
echo "  15:00 收盘总结"
echo "  20:00 策略升级"
echo ""
echo "🎯 完全自动化，不需要你给提示词！"
echo ""
