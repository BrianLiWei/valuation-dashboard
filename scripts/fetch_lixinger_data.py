#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从理杏仁API获取A股估值数据
时间范围: 2010-01-01 至 2026-03-21 (用于计算五年滚动分位点)

API合规要求：
- headers: Content-Type: application/json
- headers: accept-encoding 必须包含 gzip
- 每分钟最大请求次数: 1000次，每秒: 36次
- 需要重试机制应对网络问题
- 遇到429限流时需等待后重试
"""

import requests
import json
import time
from datetime import datetime, timedelta

TOKEN = "87ed8c88-cda6-4000-939c-ac87d6da83b7"
INDEX_API_URL = "https://open.lixinger.com/api/a/index/fundamental"

# 请求头（理杏仁API要求）
HEADERS = {
    "Content-Type": "application/json",
    "Accept-Encoding": "gzip, deflate, br, *",
}

# 重试配置
MAX_RETRIES = 5
RETRY_BASE_DELAY = 2  # 基础重试延迟（秒）

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


def fetch_with_retry(url, payload, timeout=60):
    """
    带重试机制的API请求

    合规要求：
    - 理杏仁API要求 headers 包含 Content-Type 和 accept-encoding(含gzip)
    - 遇到429限流时，等待后自动重试
    - 遇到网络错误时，使用指数退避重试
    """
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                url,
                json=payload,
                headers=HEADERS,
                timeout=timeout
            )

            # 429 Too Many Requests - 限流，等待后重试
            if response.status_code == 429:
                wait_time = RETRY_BASE_DELAY * (2 ** attempt)
                print(f"  ⚠️ 触发限流 (429)，等待 {wait_time}s 后重试 (第{attempt+1}/{MAX_RETRIES}次)")
                time.sleep(wait_time)
                continue

            # 其他HTTP错误
            if response.status_code != 200:
                wait_time = RETRY_BASE_DELAY * (2 ** attempt)
                print(f"  ⚠️ API返回错误 {response.status_code}，等待 {wait_time}s 后重试 (第{attempt+1}/{MAX_RETRIES}次)")
                time.sleep(wait_time)
                continue

            return response.json()

        except requests.exceptions.Timeout:
            wait_time = RETRY_BASE_DELAY * (2 ** attempt)
            print(f"  ⚠️ 请求超时，等待 {wait_time}s 后重试 (第{attempt+1}/{MAX_RETRIES}次)")
            time.sleep(wait_time)
            continue

        except requests.exceptions.RequestException as e:
            wait_time = RETRY_BASE_DELAY * (2 ** attempt)
            print(f"  ⚠️ 网络错误: {e}，等待 {wait_time}s 后重试 (第{attempt+1}/{MAX_RETRIES}次)")
            time.sleep(wait_time)
            continue

    print(f"  ❌ 达到最大重试次数 ({MAX_RETRIES})，请求失败")
    return None


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

        result = fetch_with_retry(INDEX_API_URL, payload, timeout=60)

        if result is not None:
            if result.get('code') == 1:
                batch_data = result.get('data', [])
                all_data.extend(batch_data)
            else:
                error_msg = result.get('error', {})
                if '时间跨度不能超过10年' in str(error_msg):
                    current_end = current_start + timedelta(days=1825)
                    continue
                print(f"Error fetching {stock_code}: {error_msg}")
                break
        else:
            # 重试后仍失败，跳过此段
            break

        current_start = current_end + timedelta(days=1)
        # 请求间隔：满足每秒≤36次的要求，这里间隔0.5s，远低于限制
        time.sleep(0.5)

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

        # 指数之间增加请求间隔（满足每秒≤36次的要求）
        time.sleep(1.0)

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
