#!/usr/bin/env python3
import requests
import sys
sys.path.insert(0, '/home/admin/openclaw/workspace/tools')

url = 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeDataSimple'
params = {'page': '1', 'num': '100', 'sort': 'changepercent', 'asc': '0', 'node': 'hs_a'}
headers = {'Referer': 'http://vip.stock.finance.sina.com.cn/'}

try:
    resp = requests.get(url, params=params, headers=headers, timeout=10)
    print('状态码:', resp.status_code)
    
    if resp.status_code == 200:
        try:
            data = resp.json()
            print(f'获取到 {len(data)} 只股票\n')
            
            # 过滤主板
            main_board = [s for s in data if s.get('code', '').startswith('60') or s.get('code', '').startswith('00')]
            print(f'主板股票：{len(main_board)} 只\n')
            
            # 找 7-9% 的
            target = [s for s in main_board if 7 <= float(s.get('changepercent', 0) or 0) < 9]
            print(f'7-9% 主升浪：{len(target)} 只\n')
            
            if target:
                print('前 20 只 7-9% 主升浪:')
                print('=' * 80)
                for i, s in enumerate(target[:20], 1):
                    code = s.get('code', '?')
                    name = s.get('name', '?')
                    change = float(s.get('changepercent', 0) or 0)
                    amount = float(s.get('turnover', 0) or 0) / 10000
                    print(f'{i:2d}. {code} {name:10s} {change:+6.2f}% | 成交：{amount:6.2f}亿')
            else:
                print('没有找到 7-9% 的股票')
                print('\n前 20 只涨幅榜:')
                print('=' * 80)
                for i, s in enumerate(main_board[:20], 1):
                    code = s.get('code', '?')
                    name = s.get('name', '?')
                    change = float(s.get('changepercent', 0) or 0)
                    amount = float(s.get('turnover', 0) or 0) / 10000
                    print(f'{i:2d}. {code} {name:10s} {change:+6.2f}% | 成交：{amount:6.2f}亿')
        except Exception as e:
            print('JSON 解析错误:', e)
            print('响应内容:', resp.text[:200])
except Exception as e:
    print('请求错误:', e)
