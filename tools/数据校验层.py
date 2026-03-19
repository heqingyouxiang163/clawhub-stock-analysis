#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据校验层 v2.0
功能：对股票数据进行严格校验，防止错误数据
"""

import json
from datetime import datetime

class StockDataValidator:
    """股票数据校验器"""
    
    def __init__(self):
        # A 股硬约束
        self.RULES = {
            'change_pct': {'min': -10, 'max': 10, 'name': '涨跌幅'},
            'turnover_rate': {'min': 0, 'max': 50, 'name': '换手率'},
            'volume': {'min': 0, 'name': '成交量'},
            'amount': {'min': 0, 'name': '成交额'},
            'current': {'min': 0, 'name': '现价'},
            'market_cap': {'min': 0, 'name': '市值'},
        }
    
    def validate(self, data, symbol=''):
        """
        校验单只股票数据
        
        Returns:
            (is_valid, errors)
        """
        errors = []
        
        if not data:
            return False, ['数据为空']
        
        # 涨跌幅校验
        if 'percent' in data or 'change_pct' in data:
            change_pct = data.get('percent', data.get('change_pct', 0))
            if change_pct > 10:
                errors.append(f"涨跌幅 {change_pct:.2f}% 超过 +10% 限制")
            elif change_pct < -10:
                errors.append(f"涨跌幅 {change_pct:.2f}% 低于 -10% 限制")
        
        # 换手率校验
        if 'turnover_rate' in data:
            turnover = data['turnover_rate']
            if turnover > 50:
                errors.append(f"换手率 {turnover:.2f}% 超过 50% 限制")
            elif turnover < 0:
                errors.append(f"换手率 {turnover:.2f}% 不能为负")
        
        # 价格关系校验
        if all(k in data for k in ['current', 'high', 'low']):
            current = data['current']
            high = data['high']
            low = data['low']
            
            if high < current:
                errors.append(f"最高价 {high} < 现价 {current}")
            if low > current:
                errors.append(f"最低价 {low} > 现价 {current}")
        
        # 量价校验
        if 'volume' in data and data['volume'] <= 0:
            errors.append(f"成交量 {data['volume']} 不能<=0")
        
        if 'amount' in data and data['amount'] <= 0:
            errors.append(f"成交额 {data['amount']} 不能<=0")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def batch_validate(self, data_dict):
        """批量校验"""
        results = {}
        for symbol, data in data_dict.items():
            is_valid, errors = self.validate(data, symbol)
            results[symbol] = {
                'valid': is_valid,
                'errors': errors
            }
        return results


def test_validator():
    """测试校验器"""
    print("=" * 60)
    print("数据校验层 v2.0 - 测试")
    print("=" * 60)
    
    validator = StockDataValidator()
    
    # 测试数据
    test_cases = [
        {
            'symbol': 'SZ002828',
            'name': '贝肯能源',
            'current': 14.06,
            'percent': 1.30,
            'turnover_rate': 22.25,
            'high': 14.91,
            'low': 14.00,
            'volume': 447200,
            'amount': 645000000,
            'expected': 'valid'
        },
        {
            'symbol': 'SZ002342',
            'name': '巨力索具',
            'current': 13.78,
            'percent': 4.16,
            'turnover_rate': 24.98,
            'high': 14.55,
            'low': 13.39,
            'volume': 2398300,
            'amount': 3375000000,
            'expected': 'valid'
        },
        {
            'symbol': 'ERROR1',
            'name': '错误测试 1',
            'current': 10.00,
            'percent': 22.25,  # 错误：涨跌幅>10%
            'turnover_rate': 20.00,
            'high': 10.50,
            'low': 9.50,
            'expected': 'invalid'
        },
        {
            'symbol': 'ERROR2',
            'name': '错误测试 2',
            'current': 10.00,
            'percent': 5.00,
            'turnover_rate': 60.00,  # 错误：换手率>50%
            'high': 10.50,
            'low': 9.50,
            'expected': 'invalid'
        },
        {
            'symbol': 'ERROR3',
            'name': '错误测试 3',
            'current': 10.00,
            'percent': 5.00,
            'turnover_rate': 20.00,
            'high': 9.50,  # 错误：最高价<现价
            'low': 9.00,
            'expected': 'invalid'
        },
    ]
    
    print(f"\n测试 {len(test_cases)} 组数据...")
    print("=" * 60)
    
    correct = 0
    for case in test_cases:
        symbol = case['symbol']
        expected = case['expected']
        
        is_valid, errors = validator.validate(case, symbol)
        actual = 'valid' if is_valid else 'invalid'
        
        if expected == actual:
            correct += 1
            status = '✓'
        else:
            status = '✗'
        
        print(f"{status} {symbol} {case['name']}: 预期={expected}, 实际={actual}")
        if errors:
            for err in errors:
                print(f"    - {err}")
    
    print("=" * 60)
    print(f"测试结果：{correct}/{len(test_cases)} 正确，准确率 {correct/len(test_cases)*100:.1f}%")
    
    return correct == len(test_cases)


if __name__ == '__main__':
    success = test_validator()
    
    if success:
        print("\n✓ 所有测试通过！数据校验层 v2.0 就绪")
    else:
        print("\n✗ 部分测试失败，需要修复")
