#!/usr/bin/env python3
# 更新智能分析系统的持仓配置

file_path = "/home/admin/openclaw/workspace/tools/智能分析系统.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 替换持仓配置
old_holdings = '''    {"code": "002455", "name": "百川股份", "cost": 16.318, "shares": 500},
    {"code": "603538", "name": "美诺华", "cost": 24.370, "shares": 500},'''

new_holdings = '''    {"code": "002828", "name": "贝肯能源", "cost": 14.850, "shares": 500},
    {"code": "002342", "name": "巨力索具", "cost": 14.253, "shares": 900},'''

content = content.replace(old_holdings, new_holdings)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 持仓配置已更新")
print("旧：百川股份、美诺华")
print("新：贝肯能源 (500 股)、巨力索具 (900 股)")
