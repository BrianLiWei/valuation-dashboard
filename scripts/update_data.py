#!/usr/bin/env python3
"""
自动更新数据脚本
每天运行，从理杏仁API获取最新数据，更新本地JSON文件
"""

import os
import json
import requests
from datetime import datetime, timedelta

# 配置
LIXINGER_TOKEN = "87ed8c88-cda6-4000-939c-ac87d6da83b7"
INDEX_CODES = ["000985", "000922", "399006", "000852", "000016", "000905", "000906", "399673", "399702"]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
JSON_FILE = os.path.join(PROJECT_DIR, "src/data/lixinger_indices.json")

# 日期格式
def normalize_date(date_str):
    """标准化日期格式"""
    if "T" in date_str:
        return date_str.split("T")[0]
    return date_str

# 获取指数数据
def get_index_data(stock_code, start_date, end_date):
    """获取指数数据"""
    url = "https://open.lixinger.com/api/a/index/fundamental"
    params = {
        "stockCodes": [stock_code],
        "metricsList": ["pe_ttm.mcw", "pb.mcw"],
        "startDate": start_date,
        "endDate": end_date,
        "token": LIXINGER_TOKEN
    }

    try:
        resp = requests.post(url, json=params, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            raw_data = data.get("data", [])
            # 规范化日期格式
            for item in raw_data:
                if item.get("date") and "T" in item["date"]:
                    item["date"] = normalize_date(item["date"])
            return raw_data
        return []
    except Exception as e:
        print(f"获取 {stock_code} 数据失败: {e}")
        return []

def load_existing_data():
    """加载现有数据"""
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    """保存数据到JSON文件"""
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"数据已保存到 {JSON_FILE}")

def fetch_and_update_data():
    """获取并更新所有指数数据"""
    print("=" * 50)
    print("开始获取最新数据...")
    print("=" * 50)

    # 计算日期范围：获取过去6年的数据（确保有足够历史计算5年分位）
    end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=2200)).strftime("%Y-%m-%d")

    print(f"日期范围: {start_date} ~ {end_date}")

    # 加载现有数据
    existing_data = load_existing_data()
    print(f"现有数据: {list(existing_data.keys())}")

    # 获取所有指数数据
    all_data = {}
    for code in INDEX_CODES:
        print(f"获取 {code} 数据...")
        data = get_index_data(code, start_date, end_date)
        if data:
            # 获取指数名称
            name = existing_data.get(code, {}).get("name", code)
            all_data[code] = {
                "name": name,
                "data": data
            }
            print(f"  获取到 {len(data)} 条数据")
        else:
            print(f"  无数据")

    if not all_data:
        print("未获取到任何数据")
        return False

    # 保存数据
    save_data(all_data)
    print("数据更新完成!")
    return True

if __name__ == "__main__":
    fetch_and_update_data()
