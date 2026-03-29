#!/usr/bin/env python3
"""
自动更新数据脚本
每天运行，从理杏仁API获取最新数据，更新本地JSON文件
并在Python中预计算5年滚动百分位（与JavaScript原始方法完全一致）

API合规要求：
- headers: Content-Type: application/json
- headers: accept-encoding 必须包含 gzip
- 每分钟最大请求次数: 1000次，每秒: 36次
- 需要重试机制应对网络问题
- 遇到429限流时需等待后重试
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta

# 配置
LIXINGER_TOKEN = "87ed8c88-cda6-4000-939c-ac87d6da83b7"
INDEX_CODES = ["000985", "000922", "399006", "000852", "000905"]
API_URL = "https://open.lixinger.com/api/a/index/fundamental"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
JSON_FILE = os.path.join(PROJECT_DIR, "src/data/lixinger_indices.json")

# 请求头（理杏仁API要求）
HEADERS = {
    "Content-Type": "application/json",
    "Accept-Encoding": "gzip, deflate, br, *",
}

# 重试配置
MAX_RETRIES = 5
RETRY_BASE_DELAY = 2  # 基础重试延迟（秒）

def normalize_date(date_str):
    """标准化日期格式"""
    if "T" in date_str:
        return date_str.split("T")[0]
    return date_str


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
    all_data = []

    current_start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    while current_start < end:
        segment_end = current_start + timedelta(days=3650)
        if segment_end > end:
            segment_end = end

        segment_start_str = current_start.strftime("%Y-%m-%d")
        segment_end_str = segment_end.strftime("%Y-%m-%d")

        payload = {
            "stockCodes": [stock_code],
            "metricsList": ["pe_ttm.mcw", "pb.mcw"],
            "startDate": segment_start_str,
            "endDate": segment_end_str,
            "token": LIXINGER_TOKEN
        }

        result = fetch_with_retry(API_URL, payload, timeout=60)

        if result is not None:
            raw_data = result.get("data", [])
            for item in raw_data:
                if item.get("date") and "T" in item["date"]:
                    item["date"] = normalize_date(item["date"])
            all_data.extend(raw_data)
        else:
            print(f"获取 {stock_code} 数据失败 ({segment_start_str}~{segment_end_str})")

        current_start = segment_end + timedelta(days=1)
        # 请求间隔：满足每秒≤36次的要求，这里间隔0.5s，远低于限制
        time.sleep(0.5)

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
    print(f"文件路径: {JSON_FILE}")

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
    has_new_data = False

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

            # 对比新旧数据的最后日期
            existing_items = existing_data.get(code, {}).get("data", [])
            existing_dates = [d.get("date") for d in existing_items if d.get("date")]
            existing_dates.sort(reverse=True)
            old_latest = existing_dates[0] if existing_dates else None

            new_dates = [d.get("date") for d in data if d.get("date")]
            new_dates.sort(reverse=True)
            new_latest = new_dates[0] if new_dates else None

            if old_latest and new_latest:
                if new_latest > old_latest:
                    print(f"  ✅ 新增数据，最新日期: {new_latest}（原: {old_latest}）")
                    has_new_data = True
                else:
                    print(f"  ⏳ 数据无变化，最后日期: {old_latest}")
            elif new_latest:
                print(f"  ✅ 新数据，最早日期: {new_dates[-1]}，最新: {new_latest}")
                has_new_data = True

            all_data[code] = {
                "name": name,
                "data": data
            }
            print(f"  共 {len(data)} 条数据")
        else:
            print(f"  ⚠️ 无数据（保留现有数据）")
            if code in existing_data:
                all_data[code] = existing_data[code]

        # 指数之间增加请求间隔（满足每秒≤36次的要求）
        time.sleep(1.0)

    if not all_data:
        print("未获取到任何数据")
        return False

    print("-" * 50)
    if has_new_data:
        print("📈 有新增数据，更新文件...")
        save_data(all_data)
        print("✅ 数据更新完成！")
    else:
        print("⏳ 数据无变化，跳过保存。")
    return True

if __name__ == "__main__":
    fetch_and_update_data()
