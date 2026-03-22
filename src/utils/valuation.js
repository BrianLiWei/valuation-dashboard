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

// 指数信息
export const INDEX_INFO = {
  "000985": { name: "中证全指", description: "全部A股" },
  "000852": { name: "中证1000", description: "小盘股" },
  "000016": { name: "上证50", description: "大盘蓝筹" },
  "000905": { name: "中证500", description: "中盘股" },
  "000906": { name: "中证800", description: "大中盘" },
  "399006": { name: "创业板指", description: "创业板" },
  "000922": { name: "中证红利", description: "中证红利" },
  "399673": { name: "创业板50", description: "创业板50" },
};

// 计算百分位数
function calculatePercentile(value, sortedHistory) {
  if (!sortedHistory || sortedHistory.length < 250) return null;
  const validHistory = sortedHistory.filter(v => v !== null && v !== undefined && !isNaN(v) && v > 0);
  if (validHistory.length < 250) return null;
  const countBelow = validHistory.filter(v => v <= value).length;
  return (countBelow / validHistory.length) * 100;
}

// 处理原始数据，计算五年滚动分位点
export function processLixingerData(rawData) {
  console.time('processLixingerData');

  // 预处理数据
  const indexDataMap = {};
  for (const [code, info] of Object.entries(rawData)) {
    indexDataMap[code] = {};
    for (const item of info.data || []) {
      indexDataMap[code][item.date] = {
        pe_ttm: item.pe_ttm,
        pb: item.pb,
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

  // 五年约1250个交易日
  const fiveYearDays = 1250;

  const result = [];

  // 对每个日期计算分位点
  for (let i = 0; i < sortedDates.length; i++) {
    const date = sortedDates[i];

    // 获取中证全指数据
    const zzqzData = indexDataMap["000985"]?.[date];
    if (!zzqzData || !zzqzData.pe_ttm || zzqzData.pe_ttm <= 0) continue;

    // 获取过去五年的PE/PB历史数据
    const startIdx = Math.max(0, i - fiveYearDays);
    const peVals = [];
    const pbVals = [];

    for (let j = startIdx; j < i; j++) {
      const histDate = sortedDates[j];
      const histData = indexDataMap["000985"]?.[histDate];
      if (histData?.pe_ttm && histData.pe_ttm > 0) peVals.push(histData.pe_ttm);
      if (histData?.pb && histData.pb > 0) pbVals.push(histData.pb);
    }

    if (peVals.length < 250) continue;

    // 排序用于分位点计算
    const sortedPE = [...peVals].sort((a, b) => a - b);
    const sortedPB = pbVals.length >= 250 ? [...pbVals].sort((a, b) => a - b) : null;

    const pe_ttm = zzqzData.pe_ttm;
    const pb = zzqzData.pb;

    // 计算PE/PB分位点
    const pePercentile = calculatePercentile(pe_ttm, sortedPE);
    const pbPercentile = sortedPB ? calculatePercentile(pb, sortedPB) : null;

    // 获取防守端指标 - 中证红利PE分位
    let defenseScore = null;
    const hbData = indexDataMap["000922"]?.[date];
    if (hbData?.pe_ttm && hbData.pe_ttm > 0) {
      const hbVals = [];
      for (let j = startIdx; j < i; j++) {
        const histDate = sortedDates[j];
        const histData = indexDataMap["000922"]?.[histDate];
        if (histData?.pe_ttm && histData.pe_ttm > 0) hbVals.push(histData.pe_ttm);
      }
      if (hbVals.length >= 250) {
        defenseScore = calculatePercentile(hbData.pe_ttm, [...hbVals].sort((a, b) => a - b));
      }
    }

    // 获取进攻端指标 - 创业板指+中证1000 PE分位均值
    let offenseScore = null;
    const cybData = indexDataMap["399006"]?.[date];
    const zg1000Data = indexDataMap["000852"]?.[date];

    if (cybData?.pe_ttm && cybData.pe_ttm > 0 && zg1000Data?.pe_ttm && zg1000Data.pe_ttm > 0) {
      const cybVals = [], zg1000Vals = [];
      for (let j = startIdx; j < i; j++) {
        const histDate = sortedDates[j];
        const cybHist = indexDataMap["399006"]?.[histDate];
        const zg1000Hist = indexDataMap["000852"]?.[histDate];
        if (cybHist?.pe_ttm && cybHist.pe_ttm > 0) cybVals.push(cybHist.pe_ttm);
        if (zg1000Hist?.pe_ttm && zg1000Hist.pe_ttm > 0) zg1000Vals.push(zg1000Hist.pe_ttm);
      }
      if (cybVals.length >= 250 && zg1000Vals.length >= 250) {
        const cybPct = calculatePercentile(cybData.pe_ttm, [...cybVals].sort((a, b) => a - b));
        const zg1000Pct = calculatePercentile(zg1000Data.pe_ttm, [...zg1000Vals].sort((a, b) => a - b));
        if (cybPct !== null && zg1000Pct !== null) {
          offenseScore = (cybPct + zg1000Pct) / 2;
        }
      }
    }

    // 计算ERP
    let erp = null;
    if (pe_ttm && pe_ttm > 0) {
      erp = (1 / pe_ttm * 100 - 2.5);
    }

    // ERP反向分位
    let erpReversePercentile = null;
    if (erp !== null) {
      const erpVals = [];
      for (let j = startIdx; j < i; j++) {
        const histDate = sortedDates[j];
        const histData = indexDataMap["000985"]?.[histDate];
        if (histData?.pe_ttm && histData.pe_ttm > 0) {
          erpVals.push(1 / histData.pe_ttm * 100 - 2.5);
        }
      }
      if (erpVals.length >= 250) {
        const erpPct = calculatePercentile(erp, [...erpVals].sort((a, b) => a - b));
        if (erpPct !== null) {
          erpReversePercentile = 100 - erpPct;
        }
      }
    }

    // 复合全局估值分数
    let compositeScore = null;
    if (pePercentile !== null && pbPercentile !== null && erpReversePercentile !== null) {
      compositeScore = pePercentile * 0.35 + pbPercentile * 0.25 + erpReversePercentile * 0.40;
    }

    // 进攻端分项
    let cybPctVal = null, zg1000PctVal = null;
    const cybD = indexDataMap["399006"]?.[date];
    const zg1000D = indexDataMap["000852"]?.[date];
    if (cybD?.pe_ttm && zg1000D?.pe_ttm) {
      const cybVals2 = [], zg1000Vals2 = [];
      for (let j = startIdx; j < i; j++) {
        const histDate = sortedDates[j];
        const cybH = indexDataMap["399006"]?.[histDate];
        const zg1000H = indexDataMap["000852"]?.[histDate];
        if (cybH?.pe_ttm && cybH.pe_ttm > 0) cybVals2.push(cybH.pe_ttm);
        if (zg1000H?.pe_ttm && zg1000H.pe_ttm > 0) zg1000Vals2.push(zg1000H.pe_ttm);
      }
      if (cybVals2.length >= 250) cybPctVal = calculatePercentile(cybD.pe_ttm, [...cybVals2].sort((a, b) => a - b));
      if (zg1000Vals2.length >= 250) zg1000PctVal = calculatePercentile(zg1000D.pe_ttm, [...zg1000Vals2].sort((a, b) => a - b));
    }

    result.push({
      date,
      pe_ttm,
      pb,
      pe_percentile: pePercentile !== null ? Math.round(pePercentile * 10) / 10 : null,
      pb_percentile: pbPercentile !== null ? Math.round(pbPercentile * 10) / 10 : null,
      erp: erp !== null ? Math.round(erp * 100) / 100 : null,
      erp_reverse_percentile: erpReversePercentile !== null ? Math.round(erpReversePercentile * 10) / 10 : null,
      compositeScore: compositeScore !== null ? Math.round(compositeScore * 10) / 10 : null,
      defenseScore: defenseScore !== null ? Math.round(defenseScore * 10) / 10 : null,
      defense_pe: hbData?.pe_ttm || null,
      offenseScore: offenseScore !== null ? Math.round(offenseScore * 10) / 10 : null,
      cyb_pe: cybD?.pe_ttm || null,
      cyb_pe_percentile: cybPctVal !== null ? Math.round(cybPctVal * 10) / 10 : null,
      zg1000_pe: zg1000D?.pe_ttm || null,
      zg1000_pe_percentile: zg1000PctVal !== null ? Math.round(zg1000PctVal * 10) / 10 : null,
    });
  }

  console.timeEnd('processLixingerData');
  console.log('Result:', result.length, 'items');

  return result;
}

// 获取所有指数数据
export function getAllIndexData(rawData) {
  const result = {};

  for (const [code, info] of Object.entries(rawData)) {
    const dataList = [];

    for (const item of info.data || []) {
      dataList.push({
        date: item.date,
        pe_ttm: item.pe_ttm,
        pb: item.pb,
      });
    }

    dataList.sort((a, b) => new Date(a.date) - new Date(b.date));

    result[code] = {
      name: info.name,
      data: dataList,
    };
  }

  return result;
}

// 计算单个指数的PE分位历史
export function getIndexPEPercentile(rawData, indexCode) {
  const indexData = rawData[indexCode];
  if (!indexData || !indexData.data) return [];

  // 获取所有日期
  const sortedDates = indexData.data.map(d => d.date).sort();

  const fiveYearDays = 1250;
  const result = [];

  for (let i = 0; i < sortedDates.length; i++) {
    const date = sortedDates[i];
    const currentData = indexData.data.find(d => d.date === date);

    if (!currentData?.pe_ttm || currentData.pe_ttm <= 0) continue;

    const startIdx = Math.max(0, i - fiveYearDays);
    const peVals = [];

    for (let j = startIdx; j < i; j++) {
      const histDate = sortedDates[j];
      const histData = indexData.data.find(d => d.date === histDate);
      if (histData?.pe_ttm && histData.pe_ttm > 0) {
        peVals.push(histData.pe_ttm);
      }
    }

    if (peVals.length < 250) continue;

    const sortedPE = [...peVals].sort((a, b) => a - b);
    const pePercentile = calculatePercentile(currentData.pe_ttm, sortedPE);

    result.push({
      date,
      pe: currentData.pe_ttm,
      pe_percentile: pePercentile !== null ? Math.round(pePercentile * 10) / 10 : null,
    });
  }

  return result;
}
