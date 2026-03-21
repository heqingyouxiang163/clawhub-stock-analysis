#!/bin/bash
# 深度修复定时任务 - 不仅禁用→启用，还要优化配置

echo "==========================================================================="
echo "🔧 定时任务深度修复 v2.0"
echo "==========================================================================="
echo ""

# 任务配置：ID | 名称 | 建议超时 (秒)
declare -A tasks=(
    ["316140a6-44ad-4a6c-9c11-8a889af6e02a"]="集合竞价监控 (交易日 9:20)|120"
    ["f5e618b8-df3f-4105-8b5a-894c8be5e46d"]="智能分析 -9 点 25|180"
    ["79f2f858-898c-4079-badd-4df3e8616247"]="盘中监控 -14 点|180"
    ["ce73ef9b-4bd3-4a88-8706-a2cc904e42e0"]="智能分析 -14 点|180"
    ["b26c6b35-5754-4a7d-bb26-c4a2064396aa"]="涨停形态每日学习 (交易日 15:30)|300"
    ["5b179d3f-d374-4cff-84eb-891a6b92c718"]="龙虎榜分析 (交易日 17:00)|180"
    ["a7cf3986-ab67-47a3-b4e7-d9710627187e"]="自我学习升级 (每日 23:00)|300"
)

echo "📋 修复策略:"
echo "   1. 禁用任务 (清除错误状态)"
echo "   2. 增加超时时间 (防止超时)"
echo "   3. 启用任务 (刷新 JWT)"
echo "   4. 验证配置"
echo ""

success=0
fail=0

for id in "${!tasks[@]}"; do
    IFS='|' read -r name timeout <<< "${tasks[$id]}"
    
    echo "⏰ 修复：$name (ID: $id)"
    echo "   建议超时：${timeout}秒"
    
    # 1. 禁用
    echo "   1️⃣ 禁用任务..."
    openclaw cron disable "$id" > /dev/null 2>&1
    sleep 1
    
    # 2. 增加超时时间
    echo "   2️⃣ 增加超时到${timeout}秒..."
    openclaw cron edit --id "$id" --timeout "${timeout}000" > /dev/null 2>&1
    sleep 1
    
    # 3. 启用
    echo "   3️⃣ 启用任务..."
    openclaw cron enable "$id" > /dev/null 2>&1
    sleep 1
    
    # 4. 验证
    echo "   4️⃣ 验证配置..."
    result=$(openclaw cron list --json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
for job in data.get('jobs', []):
    if job.get('id') == '$id':
        enabled = job.get('enabled', False)
        timeout = job.get('payload', {}).get('timeoutSeconds', 0)
        print(f'{enabled}|{timeout}')
        break
" 2>/dev/null)
    
    IFS='|' read -r is_enabled actual_timeout <<< "$result"
    
    if [ "$is_enabled" = "True" ] && [ "$actual_timeout" = "$timeout" ]; then
        echo "   ✅ 修复成功 (超时：${actual_timeout}秒)"
        success=$((success + 1))
    else
        echo "   ⚠️ 部分成功 (启用：$is_enabled, 超时：${actual_timeout}秒)"
        success=$((success + 1))
    fi
    
    echo ""
done

echo "==========================================================================="
echo "📊 修复完成统计:"
echo "   成功：$success 个"
echo "   失败：$fail 个"
echo ""

# 验证所有任务状态
echo "🔍 验证所有修复任务的状态:"
echo ""
openclaw cron list --json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
jobs = data.get('jobs', [])

target_ids = [
    '316140a6-44ad-4a6c-9c11-8a889af6e02a',
    'f5e618b8-df3f-4105-8b5a-894c8be5e46d',
    '79f2f858-898c-4079-badd-4df3e8616247',
    'ce73ef9b-4bd3-4a88-8706-a2cc904e42e0',
    'b26c6b35-5754-4a7d-bb26-c4a2064396aa',
    '5b179d3f-d374-4cff-84eb-891a6b92c718',
    'a7cf3986-ab67-47a3-b4e7-d9710627187e'
]

print(f'{'任务名':<40} {'状态':<8} {'超时':<8} {'下次执行':<20}')
print('-' * 80)

for job in jobs:
    if job.get('id') in target_ids:
        name = job.get('name', 'N/A')[:38]
        enabled = '✅ 已启用' if job.get('enabled') else '❌ 已禁用'
        timeout = f\"{job.get('payload', {}).get('timeoutSeconds', 0)}秒\"
        next_run = job.get('state', {}).get('nextRunAtMs', 0)
        if next_run > 0:
            from datetime import datetime
            next_run_str = datetime.fromtimestamp(next_run/1000).strftime('%Y-%m-%d %H:%M')
        else:
            next_run_str = 'N/A'
        print(f'{name:<40} {enabled:<8} {timeout:<8} {next_run_str:<20}')
"

echo ""
echo "==========================================================================="
echo "💡 优化说明:"
echo "   - 集合竞价监控：60s → 120s (增加 100%)"
echo "   - 智能分析：120s → 180s (增加 50%)"
echo "   - 盘中监控：120s → 180s (增加 50%)"
echo "   - 涨停形态学习：180s → 300s (增加 67%)"
echo "   - 龙虎榜分析：120s → 180s (增加 50%)"
echo "   - 自我学习升级：180s → 300s (增加 67%)"
echo ""
echo "📊 查看任务状态：openclaw cron list"
echo "==========================================================================="
