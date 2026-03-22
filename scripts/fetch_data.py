#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取A股估值数据
使用方法: python fetch_data.py
需要设置环境变量 JQ_USERNAME 和 JQ_PASSWORD
或直接在代码中填写账号密码
"""

import os
import json
import jqdatasdk as jq
from datetime import datetime, timedelta

# 尝试获取环境变量中的账号密码
JQ_USERNAME = os.environ.get('JQ_USERNAME', '')
JQ_PASSWORD = os.environ.get('JQ_PASSWORD', '')

# 如果环境变量为空，提示用户填写
if not JQ_USERNAME or not JQ_PASSWORD:
    print("请设置环境变量或在代码中填写JoinQuant账号密码")
    print("设置方法:")
    print("  export JQ_USERNAME='你的账号'")
    print("  export JQ_PASSWORD='你的密码'")
    print("")
    # 这里可以硬编码账号密码（仅用于测试）
    JQ_USERNAME = input("请输入JoinQuant账号: ").strip()
    JQ_PASSWORD = input("请输入JoinQuant密码: ").strip()

# 认证
print(f"正在登录JoinQuant账号: {JQ_USERNAME}")
jq.auth(JQ_USERNAME, JQ_PASSWORD)

# 万得全A指数代码
INDEX_CODE = '000985.CSI'  # 万得全A

# 获取日期范围
# 从2015年1月1日到今天
start_date = '2015-01-01'
end_date = datetime.now().strftime('%Y-%m-%d')

print(f"正在获取万得全A估值数据...")
print(f"日期范围: {start_date} 至 {end_date}")

# 获取指数估值数据
df = jq.get_index_valuation(
    INDEX_CODE,
    start_date=start_date,
    end_date=end_date,
    fields='code,day,pe_ratio,pb_ratio'
)

print(f"获取到 {len(df)} 条数据")

# 处理数据
data_list = []
for _, row in df.iterrows():
    data_list.append({
        'date': str(row['day'])[:10],  # 只保留日期部分
        'pe_ratio': float(row['pe_ratio']) if row['pe_ratio'] is not None else None,
        'pb_ratio': float(row['pb_ratio']) if row['pb_ratio'] is not None else None,
    })

# 按日期排序
data_list.sort(key=lambda x: x['date'])

print(f"数据日期范围: {data_list[0]['date']} 至 {data_list[-1]['date']}")

# 保存到JSON文件
output_file = '../src/data/valuation_data.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data_list, f, ensure_ascii=False, indent=2)

print(f"数据已保存到: {output_file}")

# 退出登录
jq.logout()
print("完成!")
