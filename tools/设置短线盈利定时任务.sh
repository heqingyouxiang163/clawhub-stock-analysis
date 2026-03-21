#!/bin/bash
# 短线盈利助手 - 定时任务设置脚本
# 功能：设置 9:35-10:35 的推送任务，每 5 分钟一次

echo "==========================================================================="
echo "🦞 短线盈利助手 - 定时任务设置"
echo "==========================================================================="
echo ""

# 检查是否已存在任务
echo "🔍 检查现有任务..."
existing_tasks=$(openclaw cron list 2>/dev/null | grep "短线盈利" | wc -l)

if [ "$existing_tasks" -gt 0 ]; then
    echo "⚠️ 发现$existing_tasks个已有的短线盈利任务"
    echo "   是否删除旧任务？(y/n)"
    read -r answer
    if [ "$answer" = "y" ]; then
        echo "🗑️ 删除旧任务..."
        openclaw cron list 2>/dev/null | grep "短线盈利" | awk '{print $1}' | while read -r task_id; do
            openclaw cron remove "$task_id" 2>/dev/null
            echo "   ✅ 删除任务 $task_id"
        done
    fi
fi

echo ""
echo "📅 设置新任务 (9:35-10:35，每 5 分钟一次)..."
echo ""

# 设置 12 个定时任务
tasks=(
    "35 9:短线盈利 -9:35"
    "40 9:短线盈利 -9:40"
    "45 9:短线盈利 -9:45"
    "50 9:短线盈利 -9:50"
    "55 9:短线盈利 -9:55"
    "60 9:短线盈利 -10:00"
    "5 10:短线盈利 -10:05"
    "10 10:短线盈利 -10:10"
    "15 10:短线盈利 -10:15"
    "20 10:短线盈利 -10:20"
    "25 10:短线盈利 -10:25"
    "30 10:短线盈利 -10:30"
    "35 10:短线盈利 -10:35"
)

success_count=0
fail_count=0

for task in "${tasks[@]}"; do
    IFS=':' read -r time name <<< "$task"
    IFS=' ' read -r minute hour <<< "$time"
    
    # 处理 60 分钟的情况
    if [ "$minute" -ge 60 ]; then
        hour=$((hour + 1))
        minute=$((minute - 60))
    fi
    
    echo "⏰ 设置任务：$name (cron:$minute $hour * * 1-5)"
    
    openclaw cron add \
        --name="$name" \
        --cron="$minute $hour * * 1-5" \
        --message="python3 /home/admin/openclaw/workspace/tools/短线盈利助手.py" \
        --timeout=120000 \
        --session="isolated" \
        --announce
    
    if [ $? -eq 0 ]; then
        echo "   ✅ 设置成功"
        success_count=$((success_count + 1))
    else
        echo "   ❌ 设置失败"
        fail_count=$((fail_count + 1))
    fi
    echo ""
done

echo "==========================================================================="
echo "📊 设置完成统计:"
echo "   成功：$success_count 个"
echo "   失败：$fail_count 个"
echo ""
echo "📁 相关文件:"
echo "   推送输出：/home/admin/openclaw/workspace/temp/短线盈利助手/"
echo "   错误日志：/home/admin/openclaw/workspace/temp/短线盈利助手/logs/"
echo "   运行统计：/home/admin/openclaw/workspace/temp/短线盈利助手/logs/运行统计_*.json"
echo "   每日报告：/home/admin/openclaw/workspace/temp/短线盈利助手/logs/每日报告_*.md"
echo ""
echo "🔍 查看任务列表:"
echo "   openclaw cron list"
echo ""
echo "🚀 测试推送:"
echo "   cd /home/admin/openclaw/workspace/tools"
echo "   python3 短线盈利助手.py force"
echo ""
echo "📊 查看错误日志:"
echo "   cat /home/admin/openclaw/workspace/temp/短线盈利助手/logs/错误日志_*.md"
echo ""
echo "==========================================================================="
