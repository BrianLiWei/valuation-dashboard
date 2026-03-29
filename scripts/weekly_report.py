#!/usr/bin/env python3
"""
A股估值周报生成脚本
包含完整的网页端内容：三个指标卡片 + 所有历史走势图

API合规要求：
- headers: Content-Type: application/json
- headers: accept-encoding 必须包含 gzip
- 每分钟最大请求次数: 1000次，每秒: 36次
- 需要重试机制应对网络问题
- 遇到429限流时需等待后重试
"""

import requests
import json
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime, timedelta
import os
import base64

# ============== 配置 ==============
LIXINGER_TOKEN = "87ed8c88-cda6-4000-939c-ac87d6da83b7"
API_URL = "https://open.lixinger.com/api/cn/index/fundamental"  # 统一使用 /api/a/ 端点

# 请求头（理杏仁API要求）
HEADERS = {
    "Content-Type": "application/json",
    "Accept-Encoding": "gzip, deflate, br, *",
}

# 重试配置
MAX_RETRIES = 5
RETRY_BASE_DELAY = 2  # 基础重试延迟（秒）

# 邮件配置
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "wei.brian.li@gmail.com"
SENDER_PASSWORD = "gsbbhcmeksrgzfdd"
RECIPIENT_EMAIL = "brian.w.li@hotmail.com"

# ============== 函数 ==============

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


def get_index_data(stock_code, start_date, end_date):
    """获取指数数据"""
    payload = {
        "stockCodes": [stock_code],
        "metricsList": ["pe_ttm.mcw", "pb.mcw"],
        "startDate": start_date,
        "endDate": end_date,
        "token": LIXINGER_TOKEN
    }

    result = fetch_with_retry(API_URL, payload, timeout=60)

    if result is not None:
        raw_data = result.get("data", [])
        # 规范化日期格式：去掉时间部分
        for item in raw_data:
            if item.get("date") and "T" in item["date"]:
                item["date"] = item["date"].split("T")[0]
        return raw_data
    return []

def calculate_percentile(value, sorted_history):
    """计算分位点"""
    if not sorted_history or len(sorted_history) < 250:
        return None
    count_below = sum(1 for v in sorted_history if v <= value)
    return (count_below / len(sorted_history)) * 100

def calculate_erp(pe):
    """计算ERP (股权风险溢价) = 1/PE - 2.5%"""
    if pe and pe > 0:
        return (1 / pe * 100 - 2.5)
    return None

def get_valuation_level(score):
    """获取估值区间"""
    if score is None:
        return {"label": "数据不足", "color": "#9ca3af"}
    if score >= 90:
        return {"label": "极度高估", "color": "#ef4444"}
    if score >= 70:
        return {"label": "高估", "color": "#fb923c"}
    if score >= 30:
        return {"label": "合理", "color": "#facc15"}
    if score >= 10:
        return {"label": "低估", "color": "#4ade80"}
    return {"label": "极度低估", "color": "#16a34a"}

def compute_all_percentiles(index_data, lookback_days=1250):
    """计算所有估值指标的分位点"""
    if not index_data:
        return None

    # 按日期排序
    sorted_data = sorted(index_data, key=lambda x: x.get("date", ""))

    results = []
    for i, item in enumerate(sorted_data):
        date = item.get("date", "")
        pe = item.get("pe_ttm.mcw")
        pb = item.get("pb.mcw")

        if not pe or pe <= 0:
            continue

        # 获取历史数据
        start_idx = max(0, i - lookback_days)
        pe_history = []
        pb_history = []
        erp_history = []

        for j in range(start_idx, i):
            hist_pe = sorted_data[j].get("pe_ttm.mcw")
            hist_pb = sorted_data[j].get("pb.mcw")
            if hist_pe and hist_pe > 0:
                pe_history.append(hist_pe)
                erp_history.append(calculate_erp(hist_pe))
            if hist_pb and hist_pb > 0:
                pb_history.append(hist_pb)

        if len(pe_history) < 250:
            continue

        sorted_pe = sorted(pe_history)
        sorted_pb = sorted(pb_history) if pb_history else []
        sorted_erp = sorted([e for e in erp_history if e is not None])

        pe_percentile = calculate_percentile(pe, sorted_pe)
        pb_percentile = calculate_percentile(pb, sorted_pb) if sorted_pb else None
        erp = calculate_erp(pe)
        erp_percentile = calculate_percentile(erp, sorted_erp) if sorted_erp and erp is not None else None
        erp_reverse = 100 - erp_percentile if erp_percentile is not None else None

        # 复合全局估值分数
        composite_score = None
        if pe_percentile is not None and pb_percentile is not None and erp_reverse is not None:
            composite_score = pe_percentile * 0.35 + pb_percentile * 0.25 + erp_reverse * 0.40

        results.append({
            "date": date,
            "pe": pe,
            "pb": pb,
            "pe_percentile": pe_percentile,
            "pb_percentile": pb_percentile,
            "erp": erp,
            "erp_reverse_percentile": erp_reverse,
            "composite_score": composite_score
        })

    return results

def compute_single_index_pe_percentile(index_data, lookback_days=1250):
    """计算单个指数的PE分位"""
    if not index_data:
        return []

    sorted_data = sorted(index_data, key=lambda x: x.get("date", ""))
    results = []

    for i, item in enumerate(sorted_data):
        date = item.get("date", "")
        pe = item.get("pe_ttm.mcw")

        if not pe or pe <= 0:
            continue

        start_idx = max(0, i - lookback_days)
        pe_history = []

        for j in range(start_idx, i):
            hist_pe = sorted_data[j].get("pe_ttm.mcw")
            if hist_pe and hist_pe > 0:
                pe_history.append(hist_pe)

        if len(pe_history) < 250:
            continue

        pe_percentile = calculate_percentile(pe, sorted(pe_history))

        results.append({
            "date": date,
            "pe": pe,
            "pe_percentile": pe_percentile
        })

    return results

def generate_full_report():
    """生成完整估值报告"""
    end_date = datetime.now().strftime("%Y-%m-%d")

    report = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "composite": None,      # 复合全局估值
        "defense": None,         # 防守端（中证红利）
        "offense": None,         # 进攻端（创业板+中证1000）
        "indices": {},           # 各指数详情
        "history": {}            # 历史走势数据
    }

    print("获取中证全指数据...")
    zz_data = get_index_data("000985", "2020-01-01", end_date)
    print(f"中证全指API返回: {len(zz_data) if zz_data else 0} 条数据")
    zz_valuation = compute_all_percentiles(zz_data)
    print(f"计算后数据: {len(zz_valuation) if zz_valuation else 0} 条")

    if zz_valuation and len(zz_valuation) > 0:
        latest = zz_valuation[-1]
        level = get_valuation_level(latest.get("composite_score"))
        report["composite"] = {
            "pe": latest.get("pe"),
            "pe_percentile": latest.get("pe_percentile"),
            "pb": latest.get("pb"),
            "pb_percentile": latest.get("pb_percentile"),
            "erp": latest.get("erp"),
            "erp_reverse": latest.get("erp_reverse_percentile"),
            "score": latest.get("composite_score"),
            "level": level
        }

    # 请求间隔：满足每秒≤36次的要求
    time.sleep(0.5)

    print("获取中证红利数据...")
    hl_data = get_index_data("000922", "2020-01-01", end_date)
    hl_pe = compute_single_index_pe_percentile(hl_data)

    if hl_pe and len(hl_pe) > 0:
        latest = hl_pe[-1]
        level = get_valuation_level(latest.get("pe_percentile"))
        report["defense"] = {
            "pe": latest.get("pe"),
            "pe_percentile": latest.get("pe_percentile"),
            "level": level
        }

    # 请求间隔：满足每秒≤36次的要求
    time.sleep(0.5)

    print("获取创业板指数据...")
    cyb_data = get_index_data("399006", "2020-01-01", end_date)
    cyb_pe = compute_single_index_pe_percentile(cyb_data)

    # 请求间隔：满足每秒≤36次的要求
    time.sleep(0.5)

    print("获取中证1000数据...")
    zg1000_data = get_index_data("000852", "2020-01-01", end_date)
    zg1000_pe = compute_single_index_pe_percentile(zg1000_data)

    # 计算进攻端（创业板+中证1000均值）
    if cyb_pe and zg1000_pe and len(cyb_pe) > 0 and len(zg1000_pe) > 0:
        cyb_latest = cyb_pe[-1]
        zg1000_latest = zg1000_pe[-1]

        if cyb_latest.get("pe_percentile") and zg1000_latest.get("pe_percentile"):
            offense_score = (cyb_latest["pe_percentile"] + zg1000_latest["pe_percentile"]) / 2
            level = get_valuation_level(offense_score)
            report["offense"] = {
                "cyb_pe": cyb_latest.get("pe"),
                "cyb_pe_percentile": cyb_latest.get("pe_percentile"),
                "zg1000_pe": zg1000_latest.get("pe"),
                "zg1000_pe_percentile": zg1000_latest.get("pe_percentile"),
                "score": offense_score,
                "level": level
            }

    # 整理历史走势数据（最近30条用于邮件展示）
    if zz_valuation:
        report["history"]["zzqz"] = zz_valuation[-30:]

    if hl_pe:
        report["history"]["hongli"] = hl_pe[-30:]

    if cyb_pe:
        report["history"]["cyb"] = cyb_pe[-30:]

    if zg1000_pe:
        report["history"]["zg1000"] = zg1000_pe[-30:]

    return report

def get_level_class(level_label):
    """获取估值区间的CSS类"""
    mapping = {
        "极度高估": "level-extreme-high",
        "高估": "level-high",
        "合理": "level-fair",
        "低估": "level-low",
        "极度低估": "level-extreme-low",
        "数据不足": "level-na"
    }
    return mapping.get(level_label, "level-na")

def format_num(value, decimals=1):
    """格式化数字，保留指定小数位"""
    if value is None:
        return '--'
    try:
        return f"{float(value):.{decimals}f}"
    except (ValueError, TypeError):
        return '--'

def send_email(report):
    """发送邮件"""
    composite = report.get("composite", {})
    defense = report.get("defense", {})
    offense = report.get("offense", {})
    history = report.get("history", {})

    composite_level = composite.get("level", {}) if composite else {}
    defense_level = defense.get("level", {}) if defense else {}
    offense_level = offense.get("level", {}) if offense else {}

    # 生成HTML报告
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; margin: 0; padding: 20px; background-color: #f9fafb; color: #1f2937; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 12px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            h1 {{ font-size: 24px; font-weight: 700; color: #111827; margin-bottom: 8px; }}
            .subtitle {{ font-size: 14px; color: #6b7280; margin-bottom: 24px; }}
            h2 {{ font-size: 18px; font-weight: 600; color: #111827; margin: 24px 0 12px; }}

            /* 卡片样式 */
            .cards {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }}
            .card {{ background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border-radius: 12px; padding: 16px; text-align: center; border: 1px solid #bae6fd; }}
            .card.defense {{ background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%); border-color: #ddd6fe; }}
            .card.offense {{ background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%); border-color: #fecaca; }}

            .card-label {{ font-size: 13px; font-weight: 600; color: #6b7280; margin-bottom: 8px; }}
            .card-value {{ font-size: 36px; font-weight: 800; line-height: 1; margin-bottom: 8px; }}
            .card-level {{ display: inline-block; padding: 4px 12px; border-radius: 16px; color: white; font-size: 12px; font-weight: 600; }}

            .card-details {{ margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(0,0,0,0.1); font-size: 11px; color: #6b7280; }}
            .detail-row {{ display: flex; justify-content: space-between; margin-bottom: 4px; }}
            .detail-row span:last-child {{ font-weight: 600; color: #374151; }}

            /* 表格样式 */
            table {{ border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 13px; }}
            th, td {{ border: 1px solid #e5e7eb; padding: 10px 12px; text-align: left; }}
            th {{ background-color: #f3f4f6; font-weight: 600; }}
            tr:nth-child(even) {{ background-color: #f9fafb; }}

            /* 估值区间颜色 */
            .level-extreme-high {{ background-color: #fee2e2; color: #dc2626; }}
            .level-high {{ background-color: #ffedd5; color: #ea580c; }}
            .level-fair {{ background-color: #fef9c3; color: #ca8a04; }}
            .level-low {{ background-color: #dcfce7; color: #16a34a; }}
            .level-extreme-low {{ background-color: #dcfce7; color: #15803d; }}
            .level-na {{ background-color: #f3f4f6; color: #6b7280; }}

            /* 历史数据表格 */
            .history-table {{ font-size: 11px; }}
            .history-table th, .history-table td {{ padding: 6px 8px; }}

            .footer {{ margin-top: 30px; padding-top: 16px; border-top: 1px solid #e5e7eb; color: #9ca3af; font-size: 11px; }}
            .formula {{ background: #f3f4f6; padding: 12px; border-radius: 8px; margin: 12px 0; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>A股估值信号周报</h1>
            <p class="subtitle">更新日期: {report['date']} | 数据来源: 理杏仁</p>

            <h2>一、当前估值状态</h2>

            <div class="cards">
                <!-- 复合全局估值 -->
                <div class="card">
                    <div class="card-label">复合全局估值分数</div>
                    <div class="card-value" style="color: {composite_level.get('color', '#374151')}">
                        {format_num(composite.get('score'), 0)}
                    </div>
                    <div class="card-level" style="background-color: {composite_level.get('color', '#9ca3af')}">
                        {composite_level.get('label', '数据不足')}
                    </div>
                    <div class="card-details">
                        <div class="detail-row"><span>PE/PE分位(5年):</span><span>{format_num(composite.get('pe'), 2)} ({format_num(composite.get('pe_percentile'))}%)</span></div>
                        <div class="detail-row"><span>PB/PB分位(5年):</span><span>{format_num(composite.get('pb'), 4)} ({format_num(composite.get('pb_percentile'))}%)</span></div>
                        <div class="detail-row"><span>ERP/ERP分位(5年):</span><span>{format_num(composite.get('erp'))}% (反向{format_num(composite.get('erp_reverse'))}%)</span></div>
                    </div>
                </div>

                <!-- 防守端 -->
                <div class="card defense">
                    <div class="card-label">防守端指标</div>
                    <div class="card-value" style="color: {defense_level.get('color', '#374151')}">
                        {format_num(defense.get('pe_percentile'), 0)}
                    </div>
                    <div class="card-level" style="background-color: {defense_level.get('color', '#9ca3af')}">
                        {defense_level.get('label', '数据不足')}
                    </div>
                    <div class="card-details">
                        <div class="detail-row"><span>中证红利PE:</span><span>{format_num(defense.get('pe'), 2)} ({format_num(defense.get('pe_percentile'))}%)</span></div>
                    </div>
                </div>

                <!-- 进攻端 -->
                <div class="card offense">
                    <div class="card-label">进攻端指标</div>
                    <div class="card-value" style="color: {offense_level.get('color', '#374151')}">
                        {format_num(offense.get('score'), 0)}
                    </div>
                    <div class="card-level" style="background-color: {offense_level.get('color', '#9ca3af')}">
                        {offense_level.get('label', '数据不足')}
                    </div>
                    <div class="card-details">
                        <div class="detail-row"><span>创业板指PE:</span><span>{format_num(offense.get('cyb_pe'), 2)} ({format_num(offense.get('cyb_pe_percentile'))}%)</span></div>
                        <div class="detail-row"><span>中证1000 PE:</span><span>{format_num(offense.get('zg1000_pe'), 2)} ({format_num(offense.get('zg1000_pe_percentile'))}%)</span></div>
                    </div>
                </div>
            </div>

            <div class="formula">
                <strong>计算公式：</strong><br>
                复合全局估值分数 = PE分位×35% + PB分位×25% + ERP反向分位×40%<br>
                ERP = 1/PE - 2.5% (10年期国债收益率)<br>
                防守端 = 中证红利(000922) PE分位<br>
                进攻端 = 创业板指(399006) PE分位 + 中证1000(000852) PE分位 的均值
            </div>

            <h2>二、各指数PE分位详情</h2>
            <table>
                <tr>
                    <th>指数名称</th>
                    <th>PE (TTM)</th>
                    <th>PE分位 (5年)</th>
                    <th>估值区间</th>
                </tr>
    """

    # 各指数数据
    indices_data = [
        ("中证全指", composite.get("pe"), composite.get("pe_percentile"), composite_level.get("label")),
        ("中证红利", defense.get("pe"), defense.get("pe_percentile"), defense_level.get("label")),
        ("创业板指", offense.get("cyb_pe"), offense.get("cyb_pe_percentile"), ""),
        ("中证1000", offense.get("zg1000_pe"), offense.get("zg1000_pe_percentile"), ""),
    ]

    for name, pe, pct, level in indices_data:
        if pe and pct:
            full_level = level if level else get_valuation_level(pct).get("label", "")
            level_class = get_level_class(full_level)
            html += f"""
                <tr>
                    <td>{name}</td>
                    <td>{pe:.2f}</td>
                    <td>{pct:.1f}%</td>
                    <td class="{level_class}">{full_level}</td>
                </tr>
            """

    html += """
            </table>

            <h2>三、中证全指历史估值走势（近30交易日）</h2>
            <table class="history-table">
                <tr>
                    <th>日期</th>
                    <th>PE</th>
                    <th>PE分位</th>
                    <th>PB</th>
                    <th>PB分位</th>
                    <th>ERP</th>
                    <th>复合分数</th>
                </tr>
    """

    zz_history = history.get("zzqz", [])
    for item in zz_history:
        html += f"""
                <tr>
                    <td>{item.get('date', '')[:10]}</td>
                    <td>{item.get('pe', ''):.2f}</td>
                    <td>{item.get('pe_percentile', ''):.1f}%</td>
                    <td>{item.get('pb', ''):.4f}</td>
                    <td>{item.get('pb_percentile', ''):.1f}%</td>
                    <td>{item.get('erp', ''):.2f}%</td>
                    <td>{item.get('composite_score', ''):.1f}</td>
                </tr>
        """

    html += """
            </table>

            <h2>四、说明</h2>
            <ul style="font-size: 13px; color: #6b7280;">
                <li><strong>PE分位</strong>: 当前PE在过去5年(约1250个交易日)历史数据中的分位点</li>
                <li><strong>PB分位</strong>: 当前PB在过去5年历史数据中的分位点</li>
                <li><strong>ERP (股权风险溢价)</strong>: 1/PE - 10年期国债收益率(2.5%)，反映股票相对债券的吸引力</li>
                <li><strong>估值区间</strong>: 极度低估(0-10%) | 低估(10-30%) | 合理(30-70%) | 高估(70-90%) | 极度高估(90-100%)</li>
            </ul>

            <div class="footer">
                <p>数据来源: 理杏仁 | 计算方法: 五年滚动分位点</p>
                <p>本报告仅供演示参考，不构成投资建议</p>
            </div>
        </div>
    </body>
    </html>
    """

    # 纯文本版本
    text = f"""
A股估值信号周报
更新日期: {report['date']}
数据来源: 理杏仁
{'='*50}

一、当前估值状态

【复合全局估值分数】
分数: {format_num(composite.get('score'), 0)}
估值: {composite_level.get('label', '数据不足')}
PE: {format_num(composite.get('pe'), 2)} (分位{format_num(composite.get('pe_percentile'))}%)
PB: {format_num(composite.get('pb'), 4)} (分位{format_num(composite.get('pb_percentile'))}%)
ERP: {format_num(composite.get('erp'))}% (反向{format_num(composite.get('erp_reverse'))}%)

【防守端指标 - 中证红利】
PE: {format_num(defense.get('pe'), 2)} (分位{format_num(defense.get('pe_percentile'))}%)
估值: {defense_level.get('label', '数据不足')}

【进攻端指标 - 创业板指+中证1000均值】
分数: {format_num(offense.get('score'), 0)}
创业板指PE: {format_num(offense.get('cyb_pe'), 2)} (分位{format_num(offense.get('cyb_pe_percentile'))}%)
中证1000 PE: {format_num(offense.get('zg1000_pe'), 2)} (分位{format_num(offense.get('zg1000_pe_percentile'))}%)

{'='*50}
二、各指数PE分位详情
指数名称        PE      PE分位    估值区间
中证全指      {composite.get('pe', '--'):.2f}   {composite.get('pe_percentile', '--'):.1f}%    {composite_level.get('label', 'N/A')}
中证红利       {defense.get('pe', '--'):.2f}   {defense.get('pe_percentile', '--'):.1f}%    {defense_level.get('label', 'N/A')}
创业板指       {offense.get('cyb_pe', '--'):.2f}   {offense.get('cyb_pe_percentile', '--'):.1f}%
中证1000      {offense.get('zg1000_pe', '--'):.2f}   {offense.get('zg1000_pe_percentile', '--'):.1f}%

{'='*50}
三、说明
- PE分位: 当前PE在过去5年历史数据中的分位点
- 极度低估(0-10%) | 低估(10-30%) | 合理(30-70%) | 高估(70-90%) | 极度高估(90-100%)
- 数据来源: 理杏仁 | 计算方法: 五年滚动分位点
- 本报告仅供演示参考，不构成投资建议
    """

    # 发送邮件
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"A股估值信号周报 - {report['date']}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL

    msg.attach(MIMEText(text, 'plain'))
    msg.attach(MIMEText(html, 'html'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
        server.quit()
        print("邮件发送成功!")
        return True
    except Exception as e:
        print(f"邮件发送失败: {e}")
        return False

def main():
    print("=" * 50)
    print("A股估值周报生成器 (完整版)")
    print("=" * 50)

    print("\n正在生成估值报告...")
    report = generate_full_report()

    # 保存报告
    with open("./weekly_report_full.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("报告已保存")

    print("\n正在发送邮件...")
    send_email(report)

    print("\n完成!")

if __name__ == "__main__":
    import os

    # 记录上次发送周报的周六日期
    LAST_SENT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".last_sent_saturday")

    def get_last_saturday():
        """获取指定日期所在周的周六（周报发送日）"""
        today = datetime.now()
        # 周六=5, 计算距离上周六的天数
        days_since_saturday = (today.weekday() - 5) % 7
        last_saturday = today - timedelta(days=days_since_saturday)
        return last_saturday

    def get_missed_saturdays():
        """检查是否有错过的周六需要补发"""
        today = datetime.now()
        last_saturday = get_last_saturday()

        # 读取上次发送的周六日期
        last_sent_saturday = None
        if os.path.exists(LAST_SENT_FILE):
            with open(LAST_SENT_FILE, 'r') as f:
                last_sent_saturday = datetime.strptime(f.read().strip(), "%Y-%m-%d")

        # 如果从未发送过，发送最新一期
        if last_sent_saturday is None:
            return [last_saturday]

        # 检查从上次发送到现在是否有遗漏的周六
        missed = []
        current = last_sent_saturday + timedelta(days=7)  # 从下一次开始检查
        while current <= last_saturday:
            missed.append(current)
            current += timedelta(days=7)

        return missed

    def mark_sent(saturday_date):
        """记录已发送的周六日期"""
        with open(LAST_SENT_FILE, 'w') as f:
            f.write(saturday_date.strftime("%Y-%m-%d"))

    # 检查是否有错过的周报
    missed_saturdays = get_missed_saturdays()

    if missed_saturdays:
        # 发送最新一期错过的周报（补发最近的）
        target_saturday = missed_saturdays[-1]
        print(f"检测到错过的周报，正在补发 {target_saturday.strftime('%Y-%m-%d')} 这期...")
        report = generate_full_report()
        send_email(report)
        mark_sent(target_saturday)
        print(f"补发完成！已记录发送日期 {target_saturday.strftime('%Y-%m-%d')}")
    else:
        today = datetime.now()
        print(f"没有错过的周报，最近周报发送日期已记录")
