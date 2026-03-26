// 估值区间定义
export const VALUATION_LEVELS = {
  EXTREME_UNDERVALUED: { min: 0, max: 10, label: '极度低估', color: '#16a34a' },
  UNDERVALUED: { min: 10, max: 30, label: '低估', color: '#4ade80' },
  FAIR: { min: 30, max: 70, label: '合理', color: '#facc15' },
  OVERVALUED: { min: 70, max: 90, label: '高估', color: '#fb923c' },
  EXTREME_OVERVALUED: { min: 90, max: 100, label: '极度高估', color: '#ef4444' },
  INSUFFICIENT: { min: -1, max: -1, label: '数据不足', color: '#9ca3af' },
};

// 根据分数获取估值区间
export function getValuationLevel(score) {
  if (score === null || score === undefined) return VALUATION_LEVELS.INSUFFICIENT;
  if (score >= 90) return VALUATION_LEVELS.EXTREME_OVERVALUED;
  if (score >= 70) return VALUATION_LEVELS.OVERVALUED;
  if (score >= 30) return VALUATION_LEVELS.FAIR;
  if (score >= 10) return VALUATION_LEVELS.UNDERVALUED;
  return VALUATION_LEVELS.EXTREME_UNDERVALUED;
}

// 处理原始数据，使用预计算的百分位
export function processLixingerData(rawData) {
  console.time('processLixingerData');

  // 预处理数据 - 使用预计算的百分位
  const indexDataMap = {};
  for (const [code, info] of Object.entries(rawData)) {
    indexDataMap[code] = {};
    for (const item of info.data || []) {
      indexDataMap[code][item.date] = {
        pe_ttm: item['pe_ttm.mcw'],
        pb: item['pb.mcw'],
        pe_percentile: item['pe_percentile_5y'] || null,
        pb_percentile: item['pb_percentile_5y'] || null,
        erp: item['erp'] || null,
        erp_reverse_percentile: item['erp_reverse_percentile_5y'] || null,
      };
    }
  }

  // 获取所有日期并排序
  const allDates = new Set();
  for (const code in indexDataMap) {
    for (const date in indexDataMap[code]) {
      allDates.add(date);
    }
  }
  const sortedDates = Array.from(allDates).sort();
  console.log('Total dates:', sortedDates.length);

  const result = [];

  // 对每个日期组合数据（使用预计算值）
  for (let i = 0; i < sortedDates.length; i++) {
    const date = sortedDates[i];

    // 获取中证全指数据
    const zzqzData = indexDataMap["000985"]?.[date];
    if (!zzqzData || !zzqzData.pe_ttm || zzqzData.pe_ttm <= 0) continue;

    const pe_ttm = zzqzData.pe_ttm;
    const pb = zzqzData.pb;
    const pePercentile = zzqzData.pe_percentile;
    const pbPercentile = zzqzData.pb_percentile;
    const erp = zzqzData.erp;
    const erpReversePercentile = zzqzData.erp_reverse_percentile;

    // 跳过没有预计算分位的数据
    if (pePercentile === null) continue;

    // 防守端指标 - 中证红利PE分位
    const hbData = indexDataMap["000922"]?.[date];
    const defenseScore = hbData?.pe_percentile || null;

    // 进攻端指标 - 创业板指+中证1000/中证500 PE分位均值
    const cybData = indexDataMap["399006"]?.[date];
    const zg1000Data = indexDataMap["000852"]?.[date] || indexDataMap["000905"]?.[date];

    let offenseScore = null;
    let cybPctVal = null;
    let zg1000PctVal = null;

    if (cybData?.pe_percentile && zg1000Data?.pe_percentile) {
      cybPctVal = cybData.pe_percentile;
      zg1000PctVal = zg1000Data.pe_percentile;
      offenseScore = (cybPctVal + zg1000PctVal) / 2;
    }

    // 复合全局估值分数
    let compositeScore = null;
    if (pePercentile !== null && pbPercentile !== null && erpReversePercentile !== null) {
      compositeScore = pePercentile * 0.35 + pbPercentile * 0.25 + erpReversePercentile * 0.40;
    }

    result.push({
      date,
      pe_ttm,
      pb,
      pe_percentile: pePercentile,
      pb_percentile: pbPercentile,
      erp: erp,
      erp_reverse_percentile: erpReversePercentile,
      compositeScore: compositeScore !== null ? Math.round(compositeScore * 10) / 10 : null,
      defenseScore: defenseScore !== null ? Math.round(defenseScore * 10) / 10 : null,
      defense_pe: hbData?.pe_ttm || null,
      offenseScore: offenseScore !== null ? Math.round(offenseScore * 10) / 10 : null,
      cyb_pe: cybData?.pe_ttm || null,
      cyb_pe_percentile: cybPctVal,
      zg1000_pe: zg1000Data?.pe_ttm || null,
      zg1000_pe_percentile: zg1000PctVal,
    });
  }

  console.timeEnd('processLixingerData');
  console.log('Result:', result.length, 'items');

  return result;
}

// 获取单个指数的PE分位历史（使用Python预计算值）
export function getIndexPEPercentile(rawData, indexCode) {
  const indexData = rawData[indexCode];
  if (!indexData || !indexData.data) return [];

  const result = [];

  for (const item of indexData.data) {
    const pe_ttm = item['pe_ttm.mcw'];
    const pe_percentile = item['pe_percentile_5y'];

    // 只返回有有效PE分位的数据
    if (pe_ttm && pe_ttm > 0 && pe_percentile !== null && pe_percentile !== undefined) {
      result.push({
        date: item.date,
        pe: pe_ttm,
        pe_percentile: pe_percentile,
      });
    }
  }

  return result;
}

// 图表用估值区间颜色（英文key，供Recharts组件使用）
export const ZONE_COLORS = {
  EXTREME_UNDERVALUED: '#16a34a',
  UNDERVALUED: '#4ade80',
  FAIR: '#fde047',
  OVERVALUED: '#f97316',
  EXTREME_OVERVALUED: '#ef4444',
};

// 图表用估值区间颜色（中文key，供堆叠柱状图使用）
export const ZONE_COLORS_CN = {
  '极度低估': '#16a34a',
  '低估': '#4ade80',
  '合理': '#facc15',
  '高估': '#fb923c',
  '极度高估': '#ef4444',
};
