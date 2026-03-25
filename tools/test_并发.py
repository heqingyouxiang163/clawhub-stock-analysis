#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/admin/openclaw/workspace/tools')

import importlib.util
spec = importlib.util.spec_from_file_location('recommend', '高确定性推荐 - 定时任务.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

recommender = module.HighProbRecommender()
watchlist = recommender.fetch_realtime_watchlist()

print(f"\n观察池：{len(watchlist)} 只\n")

# 并发测试
import concurrent.futures

results = []
errors = []

def analyze_with_error(code):
    try:
        result = recommender.analyze_stock(code)
        return (code, result)
    except Exception as e:
        return (code, f"ERROR: {e}")

print("开始并发分析...\n")

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    future_to_code = {executor.submit(analyze_with_error, code): code for code in watchlist}
    for future in concurrent.futures.as_completed(future_to_code, timeout=60):
        try:
            code, result = future.result()
            if isinstance(result, str) and result.startswith("ERROR"):
                errors.append((code, result))
            elif result:
                results.append(result)
        except Exception as e:
            errors.append((code, f"EXCEPTION: {e}"))

print(f"\n分析完成：{len(results)} 只成功，{len(errors)} 只失败\n")

# 显示 7-9% 的股票
print("7-9% 主升浪股票:")
print("=" * 80)
for r in results:
    if 7 <= r.get('change_pct', 0) < 9:
        flag = '✅' if r['score'] >= 65 else '⚠️'
        print(f"{flag} {r['code']} {r['name']:10s} {r['change_pct']:+6.2f}% | 得分：{r['score']:3d} | {', '.join(r['reasons'][:3])}")

if errors:
    print(f"\n失败 {len(errors)} 只:")
    for code, err in errors[:5]:
        print(f"  {code}: {err}")
