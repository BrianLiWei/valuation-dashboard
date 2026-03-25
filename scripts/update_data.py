#!/usr/bin/env python3
"""
自动更新数据脚本
每天运行，从理杏仁API获取最新数据，更新本地JSON文件
并在Python中预计算5年滚动百分位（与JavaScript原始方法完全一致）
"""

import os
import json
import requests
from datetime import datetime, timedelta

# 配置
LIXINGER_TOKEN = "87ed8c88-cda6-4000-939c-ac87d6da83b7"
INDEX_CODES = ["000985", "000922", "399006", "000852", "000905"]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
JSON_FILE = os.path.join(PROJECT_DIR, "src/data/lixinger_indices.json")

def normalize_date(date_str):
    """标准化日期格式"""
    if "T" in date_str:
        return date_str.split("T")[0]
    return date_str

def calculate_percentile(value, sorted_history):
    """计算百分位数 - 与JavaScript原始方法一致"""
    if len(sorted_history) < 250:
        return None
    count_below = sum(1 for v in sorted_history if v <= value)
    return (count_below / len(sorted_history)) * 100

def add_percentile_to_data(data_list):
    """
    为数据列表添加预计算的百分位
    data_list: 按日期排序的数据列表（从早到晚）
    关键：与JavaScript原始方法完全一致的计算逻辑
    """
    if not data_list:
        return data_list

    # 提取PE和PB值用于计算历史
    pe_values = []
    pb_values = []
    erp_values = []

    for item in data_list:
        pe_ttm = item.get('pe_ttm.mcw')
        pb = item.get('pb.mcw')
        if pe_ttm and pe_ttm > 0:
            pe_values.append((item['date'], pe_ttm))
            erp_values.append(1 / pe_ttm * 100 - 2.5)
        if pb and pb > 0:
            pb_values.append((item['date'], pb))

    # 按日期排序PE值（用于后续查找）
    pe_values.sort(key=lambda x: x[0])  # 按日期排序
    pb_values.sort(key=lambda x: x[0])

    # 预先提取所有PE和PB值用于历史窗口计算
    all_pe = [p[1] for p in pe_values]
    all_pb = [p[1] for p in pb_values]
    all_erp = erp_values[:]

    # 对每个数据点计算百分位
    for i, item in enumerate(data_list):
        date = item['date']

        # PE百分位：使用index 0到i-1的历史数据（即从开始到当前的前250个数据点）
        if i >= 250:
            hist_pe = all_pe[max(0, i-1250):i]  # 最多1250个历史数据点
            current_pe = item.get('pe_ttm.mcw')
            if current_pe and current_pe > 0 and len(hist_pe) >= 250:
                sorted_pe = sorted(hist_pe)
                item['pe_percentile_5y'] = round(calculate_percentile(current_pe, sorted_pe), 1)

                # ERP和ERP百分位
                erp = 1 / current_pe * 100 - 2.5
                item['erp'] = round(erp, 2)
                hist_erp = all_erp[max(0, i-1250):i]
                if len(hist_erp) >= 250:
                    sorted_erp = sorted(hist_erp)
                    erp_pct = calculate_percentile(erp, sorted_erp)
                    item['erp_percentile_5y'] = round(erp_pct, 1)
                    item['erp_reverse_percentile_5y'] = round(100 - erp_pct, 1)

        # PB百分位
        if i >= 250:
            hist_pb = all_pb[max(0, i-1250):i]
            current_pb = item.get('pb.mcw')
            if current_pb and current_pb > 0 and len(hist_pb) >= 250:
                sorted_pb = sorted(hist_pb)
                item['pb_percentile_5y'] = round(calculate_percentile(current_pb, sorted_pb), 1)

    return data_list

# 获取指数数据（处理API的10年限制）
def get_index_data(stock_code, start_date, end_date):
    """获取指数数据，自动处理10年限制"""
    url = "https://open.lixinger.com/api/a/index/fundamental"
    all_data = []

    current_start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    while current_start < end:
        segment_end = current_start + timedelta(days=3650)
        if segment_end > end:
            segment_end = end

        segment_start_str = current_start.strftime("%Y-%m-%d")
        segment_end_str = segment_end.strftime("%Y-%m-%d")

        params = {
            "stockCodes": [stock_code],
            "metricsList": ["pe_ttm.mcw", "pb.mcw"],
            "startDate": segment_start_str,
            "endDate": segment_end_str,
            "token": LIXINGER_TOKEN
        }

        try:
            resp = requests.post(url, json=params, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                raw_data = data.get("data", [])
                for item in raw_data:
                    if item.get("date") and "T" in item["date"]:
                        item["date"] = normalize_date(item["date"])
                all_data.extend(raw_data)
        except Exception as e:
            print(f"获取 {stock_code} 数据失败 ({segment_start_str}~{segment_end_str}): {e}")

        current_start = segment_end + timedelta(days=1)

    return all_data

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

    end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    start_date = "2010-01-01"

    print(f"日期范围: {start_date} ~ {end_date}")

    existing_data = load_existing_data()
    print(f"现有数据: {list(existing_data.keys())}")

    all_data = {}
    for code in INDEX_CODES:
        print(f"获取 {code} 数据...")
        data = get_index_data(code, start_date, end_date)
        if data:
            name = existing_data.get(code, {}).get("name", code)

            # 按日期排序（从早到晚）用于计算百分位
            data.sort(key=lambda x: x.get("date", ""))

            # 预计算百分位
            print(f"  计算百分位中...")
            data = add_percentile_to_data(data)

            # 排序回去（从新到旧）
            data.sort(key=lambda x: x.get("date", ""), reverse=True)

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

    save_data(all_data)
    print("数据更新完成!")
    return True

if __name__ == "__main__":
    fetch_and_update_data()
