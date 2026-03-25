#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/admin/openclaw/workspace/tools')

from 高确定性推荐 - 定时任务 import HighProbRecommender, fetch_top_gainers

recommender = HighProbRecommender()
watchlist = recommender.fetch_realtime_watchlist()

print(f"\n观察池：{len(watchlist)} 只\n")

# 测试前 20 只
print("测试前 20 只股票分析结果:\n")
for code in watchlist[:20]:
    result = recommender.analyze_stock(code)
    if result:
        flag = '✅' if result['score'] >= 65 else '⚠️'
        print(f"{flag} {code} {result['name']:10s} {result['change_pct']:+6.2f}% | 得分：{result['score']:3d} | {', '.join(result['reasons'][:3])}")
    else:
        print(f"❌ {code} 分析失败")
