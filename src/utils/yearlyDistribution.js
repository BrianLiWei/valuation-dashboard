import { getValuationLevel } from './valuation';

// 计算年度估值分布数据
export function calculateYearlyDistribution(data) {
  if (!data || data.length === 0) return [];

  // 按年份分组
  const yearlyData = {};

  for (const item of data) {
    const year = item.date.substring(0, 4);
    if (year < '2015' || year > '2025') continue;

    const level = getValuationLevel(item.compositeScore);
    const zone = level.label; // '极度低估', '低估', '合理', '高估', '极度低估'

    if (!yearlyData[year]) {
      yearlyData[year] = {
        year,
        '极度低估': 0,
        '低估': 0,
        '合理': 0,
        '高估': 0,
        '极度高估': 0,
        total: 0,
      };
    }

    yearlyData[year][zone]++;
    yearlyData[year].total++;
  }

  // 转换为百分比
  const result = Object.values(yearlyData)
    .filter(y => y.total > 0)
    .map(y => ({
      year: y.year,
      '极度低估': Math.round((y['极度低估'] / y.total) * 1000) / 10,
      '低估': Math.round((y['低估'] / y.total) * 1000) / 10,
      '合理': Math.round((y['合理'] / y.total) * 1000) / 10,
      '高估': Math.round((y['高估'] / y.total) * 1000) / 10,
      '极度高估': Math.round((y['极度高估'] / y.total) * 1000) / 10,
      total: y.total,
    }))
    .sort((a, b) => a.year.localeCompare(b.year));

  return result;
}
