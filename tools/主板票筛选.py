#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主板票筛选工具 - 只筛选沪深主板股票
用途：过滤创业板和科创板，只保留主板票
"""

def is_main_board(code):
    """
    判断是否为沪深主板股票
    
    Args:
        code: 股票代码 (6 位数字)
    
    Returns:
        bool: True=主板，False=创业板/科创板
    """
    # 确保是 6 位数字
    code = str(code).zfill(6)
    
    # 沪市主板：600, 601, 603, 605
    if code.startswith('600') or code.startswith('601') or \
       code.startswith('603') or code.startswith('605'):
        return True
    
    # 深市主板：000, 001, 002, 003
    if code.startswith('000') or code.startswith('001') or \
       code.startswith('002') or code.startswith('003'):
        return True
    
    # 创业板：300, 301 (排除)
    if code.startswith('300') or code.startswith('301'):
        return False
    
    # 科创板：688, 689 (排除)
    if code.startswith('688') or code.startswith('689'):
        return False
    
    # 其他未知情况，默认排除
    return False


def filter_main_board(stock_list):
    """
    筛选主板股票
    
    Args:
        stock_list: 股票列表，每项为 dict 或 tuple
    
    Returns:
        list: 只包含主板股票
    """
    result = []
    
    for stock in stock_list:
        # 支持 dict 格式
        if isinstance(stock, dict) and 'code' in stock:
            code = stock['code']
        # 支持 tuple 格式 (code, name, ...)
        elif isinstance(stock, (tuple, list)):
            code = stock[0]
        else:
            continue
        
        if is_main_board(code):
            result.append(stock)
    
    return result


def get_main_board_codes(limit_up_codes):
    """
    从涨停股代码列表中筛选主板票
    
    Args:
        limit_up_codes: 涨停股代码列表
    
    Returns:
        list: 主板涨停股代码
    """
    return [code for code in limit_up_codes if is_main_board(code)]


# 测试
if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    print("=" * 50)
    print("🦞 主板票筛选测试")
    print("=" * 50)
    
    test_codes = [
        # 沪市主板
        ("600519", "贵州茅台", True),
        ("601318", "中国平安", True),
        ("603259", "药明康德", True),
        ("605117", "德业股份", True),
        
        # 深市主板
        ("000001", "平安银行", True),
        ("000858", "五粮液", True),
        ("002594", "比亚迪", True),
        ("003000", "劲仔食品", True),
        
        # 创业板 (排除)
        ("300750", "宁德时代", False),
        ("300059", "东方财富", False),
        ("301000", "肇民科技", False),
        
        # 科创板 (排除)
        ("688981", "中芯国际", False),
        ("688001", "华兴源创", False),
    ]
    
    print("\n测试代码识别:")
    all_pass = True
    
    for code, name, expected in test_codes:
        result = is_main_board(code)
        status = "✅" if result == expected else "❌"
        
        if result != expected:
            all_pass = False
        
        board_type = "主板" if result else "非主板"
        print(f"{status} {code} {name:8s} -> {board_type}")
    
    print("\n" + "=" * 50)
    if all_pass:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败！")
    
    # 测试筛选功能
    print("\n测试筛选功能:")
    all_codes = [code for code, _, _ in test_codes]
    main_codes = get_main_board_codes(all_codes)
    
    print(f"总股票数：{len(all_codes)}")
    print(f"主板股票：{len(main_codes)}")
    print(f"主板代码：{', '.join(main_codes)}")

    # 显示总耗时
    total_elapsed = time.time() - total_start
    if total_elapsed < 1:
        print(f"
✅ **总耗时**: {total_elapsed*1000:.0f}ms")
    elif total_elapsed < 60:
        print(f"
✅ **总耗时**: {total_elapsed:.1f}秒")
    else:
        print(f"
✅ **总耗时**: {total_elapsed/60:.1f}分钟")
