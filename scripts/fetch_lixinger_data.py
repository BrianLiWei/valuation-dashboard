#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从理杏仁API获取A股估值数据
时间范围: 2010-01-01 至 2026-03-21 (用于计算五年滚动分位点)
"""

import requests
import json
import time
from datetime import datetime, timedelta

TOKEN = "87ed8c88-cda6-4000-939c-ac87d6da83b7"
INDEX_API_URL = "https://open.lixinger.com/api/a/index/fundamental"

# 所有需要获取的指数
INDEX_CODES = {
    "000985": "中证全指",
    "000852": "中证1000",
    "000016": "上证50",
    "000905": "中证500",
    "000906": "中证800",
    "399006": "创业板指",
    "399702": "红利低波",
    "399673": "创业板50",
}

def fetch_index_data(stock_code, start_date, end_date, metrics):
    """获取单个指数的历史数据（支持10年以上分批获取）"""
    all_data = []
    current_start = datetime.strptime(start_date, "%Y-%m-%d")
    final_end = datetime.strptime(end_date, "%Y-%m-%d")

    while current_start < final_end:
        current_end = current_start + timedelta(days=3650)  # 10年
        if current_end > final_end:
            current_end = final_end

        payload = {
            "token": TOKEN,
            "startDate": current_start.strftime("%Y-%m-%d"),
            "endDate": current_end.strftime("%Y-%m-%d"),
            "stockCodes": [stock_code],
            "metricsList": metrics
        }

        try:
            resp = requests.post(INDEX_API_URL, json=payload, timeout=60)
            data = resp.json()

            if data.get('code') == 1:
                batch_data = data.get('data', [])
                all_data.extend(batch_data)
            else:
                error_msg = data.get('error', {})
                if '时间跨度不能超过10年' in str(error_msg):
                    current_end = current_start + timedelta(days=1825)
                    continue
                print(f"Error fetching {stock_code}: {error_msg}")
                break

        except Exception as e:
            print(f"Exception for {stock_code}: {e}")
            break

        current_start = current_end + timedelta(days=1)
        time.sleep(0.3)

    return all_data

def get_all_data():
    """获取所有指数的数据"""
    # 需要的指标：PE_TTM、PB (使用mcw格式)
    metrics = ["pe_ttm.mcw", "pb.mcw"]

    # 数据范围从2010年开始，确保能计算2015年起的五年分位点
    start_date = "2010-01-01"
    end_date = "2026-03-21"

    all_data = {}

    for code, name in INDEX_CODES.items():
        print(f"正在获取 {name}({code}) 的数据...")
        data = fetch_index_data(code, start_date, end_date, metrics)

        if data:
            # 格式化数据
            formatted = []
            for item in data:
                formatted.append({
                    "date": item.get("date", "")[:10],
                    "stockCode": item.get("stockCode", code),
                    "pe_ttm": item.get("pe_ttm.mcw"),
                    "pb": item.get("pb.mcw"),
                })

            # 按日期排序
            formatted.sort(key=lambda x: x["date"])

            all_data[code] = {
                "name": name,
                "data": formatted
            }
            print(f"  获取到 {len(formatted)} 条数据 ({formatted[0]['date']} 至 {formatted[-1]['date']})")
        else:
            print(f"  无法获取数据")

        time.sleep(0.5)  # 避免请求过快

    return all_data

def main():
    print("=" * 60)
    print("从理杏仁API获取A股估值数据")
    print("=" * 60)
    print(f"日期范围: 2010-01-01 至 2026-03-21")
    print(f"目的: 计算五年滚动PE/PB分位点")
    print("-" * 60)

    all_data = get_all_data()

    # 保存到JSON文件
    output_file = "../src/data/lixinger_indices.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print("-" * 60)
    print(f"数据已保存到: {output_file}")
    print("\n数据统计:")
    print("-" * 40)

    # 统计
    for code, info in all_data.items():
        if info['data']:
            print(f"{info['name']}({code}): {len(info['data'])} 条")
            print(f"  时间范围: {info['data'][0]['date']} 至 {info['data'][-1]['date']}")

if __name__ == "__main__":
    main()
