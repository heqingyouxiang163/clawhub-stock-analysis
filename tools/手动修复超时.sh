#!/bin/bash
# 手动修复超时时间 - 逐个任务处理

echo "==========================================================================="
echo "🔧 手动修复超时时间"
echo "==========================================================================="
echo ""

# 任务列表：ID|名称|超时 (毫秒)
tasks=(
    "316140a6-44ad-4a6c-9c11-8a889af6e02a|集合竞价监控|120000"
    "f5e618b8-df3f-4105-8b5a-894c8be5e46d|智能分析 -9:25|180000"
    "79f2f858-898c-4079-badd-4df3e8616247|盘中监控 -14 点|180000"
    "ce73ef9b-4bd3-4a88-8706-a2cc904e42e0|智能分析 -14 点|180000"
    "b26c6b35-5754-4a7d-bb26-c4a2064396aa|涨停形态学习|300000"
    "5b179d3f-d374-4cff-84eb-891a6b92c718|龙虎榜分析|180000"
    "a7cf3986-ab67-47a3-b4e7-d9710627187e|自我学习升级|300000"
)

for task in "${tasks[@]}"; do
    IFS='|' read -r id name timeout <<< "$task"
    
    echo "⏰ 修复：$name"
    echo "   ID: $id"
    echo "   超时：${timeout}ms"
    echo ""
    
    # 1. 禁用
    echo "   1️⃣ 禁用..."
    openclaw cron disable "$id" 2>&1 | tail -1
    sleep 1
    
    # 2. 编辑超时 (通过 patch)
    echo "   2️⃣ 更新超时..."
    # 获取当前配置并修改超时
    cat > /tmp/patch_$id.json <<EOF
{
  "payload": {
    "timeoutSeconds": $((timeout / 1000))
  }
}
EOF
    
    # 使用 openclaw cron edit 的 patch 功能
    openclaw cron edit "$name" --timeout "$timeout" 2>&1 | grep -E "timeout|timeoutSeconds" | head -2
    sleep 1
    
    # 3. 启用
    echo "   3️⃣ 启用..."
    openclaw cron enable "$id" 2>&1 | tail -1
    sleep 1
    
    echo ""
    echo "   ✅ 完成"
    echo ""
    echo "---------------------------------------------------------------------------"
    echo ""
done

echo "==========================================================================="
echo "✅ 所有任务修复完成"
echo "==========================================================================="
