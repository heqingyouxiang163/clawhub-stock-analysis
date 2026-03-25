#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
东方财富实时涨幅榜 - 全市场数据
替代腾讯财经的硬编码列表
"""

import requests
import time

def get_top_gainers(limit=100):
    """
    获取新浪财经实时涨幅榜 (备用：东方财富)
    
    Returns:
        list: 股票列表，每只包含 code, name, change_pct, current, amount
    """
    # 先尝试新浪
    stocks = _fetch_sina(limit)
    if stocks:
        return stocks
    
    # 新浪失败，尝试东方财富
    return _fetch_eastmoney(limit)


def _fetch_sina(limit=100):
    """新浪财经涨幅榜"""
    try:
        # 新浪财经涨幅榜
        url = f'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeDataSimple?page=1&num={limit}&sort=changepercent&asc=0&node=hs_a&symbol=&_s_r_a=page'
        headers = {
            'Referer': 'http://vip.stock.finance.sina.com.cn/',
            'User-Agent': 'Mozilla/5.0'
        }
        
        start = time.time()
        response = requests.get(url, headers=headers, timeout=10)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            if data and isinstance(data, list):
                stocks = []
                for item in data:
                    code = item.get('code', '')
                    name = item.get('name', '')
                    change_pct = float(item.get('changepercent', 0) or 0)
                    current = float(item.get('trade', 0) or 0)
                    amount = float(item.get('turnover', 0) or 0)  # 已经是万
                    
                    if current == 0:
                        continue
                    
                    # 只取主板
                    if not (code.startswith('6') or code.startswith('0')):
                        continue
                    
                    stocks.append({
                        'code': code,
                        'name': name,
                        'current': current,
                        'change_pct': change_pct,
                        'amount': amount,
                        'elapsed': elapsed
                    })
                
                print(f"✅ 新浪财经涨幅榜：{len(stocks)}只 ({elapsed*1000:.0f}ms)")
                return stocks
    except Exception as e:
        pass
    
    return None
        params = {
            'pn': '1',
            'pz': str(limit),
            'po': '1',  # 降序
            'np': '1',
            'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
            'fltt': '2',
            'invt': '2',
            'fid': 'f3',  # 按涨幅排序
            'fs': 'm:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23',  # 沪深 A 股
            'fields': 'f12,f14,f3,f11,f17,f18,f19,f2,f8,f15,f16,f19',
            '_': str(int(time.time() * 1000))
        }
        
        headers = {
            'Referer': 'http://quote.eastmoney.com/',
            'User-Agent': 'Mozilla/5.0'
        }
        
        start = time.time()
        response = requests.get(url, params=params, headers=headers, timeout=10)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'diff' in data['data']:
                stocks = []
                for item in data['data']['diff']:
                    code = item['f12']  # 代码
                    name = item['f14']  # 名称
                    change_pct = item['f3']  # 涨幅%
                    current = item['f2']  # 现价
                    amount = item['f17'] * 10000  # 成交额 (万)
                    
                    # 排除停牌
                    if current == 0:
                        continue
                    
                    # 只取主板
                    if not (code.startswith('60') or code.startswith('00')):
                        continue
                    
                    stocks.append({
                        'code': code,
                        'name': name,
                        'current': current,
                        'change_pct': change_pct,
                        'amount': amount,  # 单位：万
                        'elapsed': elapsed
                    })
                
                print(f"✅ 东方财富涨幅榜：{len(stocks)}只 ({elapsed*1000:.0f}ms)")
                return stocks
        else:
            print(f"⚠️ 东方财富 HTTP {response.status_code}")
    
    except Exception as e:
        print(f"⚠️ 东方财富失败：{str(e)[:50]}")
    
    return []


if __name__ == "__main__":
    stocks = get_top_gainers(50)
    
    print(f"\n前 20 只涨幅榜:\n")
    print("=" * 80)
    
    for i, s in enumerate(stocks[:20], 1):
        flag = '🟢' if s['change_pct'] >= 7 else '🟡' if s['change_pct'] >= 5 else '⚪'
        print(f"{flag} {i:2d}. {s['code']} {s['name']:10s} {s['change_pct']:+6.2f}% | 成交：{s['amount']/10000:.2f}亿")
