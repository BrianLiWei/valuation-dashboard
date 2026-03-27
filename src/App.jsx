import { useState, useEffect, useMemo } from 'react';
import ValuationChart from './components/ValuationChart';
import MetricsChart from './components/MetricsChart';
import ValuationLegend from './components/ValuationLegend';
import { getValuationLevel, processLixingerData, getIndexPEPercentile } from './utils/valuation';
import { calculateYearlyDistribution } from './utils/yearlyDistribution';
import SingleIndexChart from './components/SingleIndexChart';
import YearlyDistributionChart from './components/YearlyDistributionChart';
import DualEndsModule from './components/DualEndsModule';
import TrendSignalModule from './components/TrendSignalModule';
import './App.css';

function App() {
  const [rawData, setRawData] = useState(null);
  const [dataLoading, setDataLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);

  // 动态加载数据（每次刷新页面时获取最新数据）
  useEffect(() => {
    fetch('./data/lixinger_indices.json')
      .then(res => res.json())
      .then(data => {
        console.log('Raw data keys:', Object.keys(data));
        console.log('Raw data sample:', data['000985']?.data?.slice(0, 2));
        setRawData(data);
        setDataLoading(false);
      })
      .catch(err => {
        console.error('Failed to load data:', err);
        setLoadError(true);
        setDataLoading(false);
      });
  }, []);

  // 处理理杏仁数据 - 所有hook必须在前面
  const processedData = useMemo(() => {
    if (!rawData) return [];
    console.log('Processing data...');
    const result = processLixingerData(rawData);
    console.log('Processed result:', result?.length, 'items');
    if (result?.length > 0) {
      console.log('First item:', result[0]);
      console.log('Last item:', result[result.length - 1]);
    }
    return result;
  }, [rawData]);

  // 中证红利PE分位历史
  const hongliPEData = useMemo(() => {
    if (!rawData) return [];
    const data = getIndexPEPercentile(rawData, '000922');
    return data.filter(d => d.date >= '2015-01-01');
  }, [rawData]);

  // 创业板指PE分位历史
  const cybPEData = useMemo(() => {
    if (!rawData) return [];
    const data = getIndexPEPercentile(rawData, '399006');
    return data.filter(d => d.date >= '2015-01-01');
  }, [rawData]);

  // 中证1000 PE分位历史（优先使用中证1000，无数据时用中证500替代）
  const zg1000PEData = useMemo(() => {
    if (!rawData) return [];
    const data852 = getIndexPEPercentile(rawData, '000852');
    const data905 = getIndexPEPercentile(rawData, '000905');
    // 合并数据，000852优先，000905作为补充
    const merged = [...data852];
    const dateSet = new Set(data852.map(d => d.date));
    for (const item of data905) {
      if (!dateSet.has(item.date)) {
        merged.push(item);
      }
    }
    merged.sort((a, b) => a.date.localeCompare(b.date));
    return merged.filter(d => d.date >= '2015-01-01');
  }, [rawData]);

  // 进攻端分位历史（用于TrendSignalModule均线计算）
  const offenseScoreHistory = useMemo(() => {
    if (!processedData || processedData.length === 0) return [];
    return processedData
      .filter(d => d.offenseScore !== null && d.offenseScore !== undefined)
      .slice(-30) // 取最近30个交易日，保证有足够数据计算SMA
      .map(d => ({
        date: d.date,
        offenseScore: d.offenseScore,
      }));
  }, [processedData]);

  // 进攻端5日均线和20日均线
  const offenseMA = useMemo(() => {
    if (offenseScoreHistory.length < 5) return { ma5: null, ma20: null, direction: 'neutral' };
    const scores5 = offenseScoreHistory.slice(-5).map(d => d.offenseScore);
    const scores20 = offenseScoreHistory.slice(-20).map(d => d.offenseScore);
    const ma5 = scores5.reduce((a, b) => a + b, 0) / scores5.length;
    const ma20 = scores20.length >= 20
      ? scores20.reduce((a, b) => a + b, 0) / scores20.length
      : ma5;
    const diff = ma5 - ma20;
    let direction = 'neutral';
    if (diff > 2) direction = 'up';
    else if (diff < -2) direction = 'down';
    return { ma5, ma20, direction };
  }, [offenseScoreHistory]);

  // 过滤2015年及之后的数据
  const filteredData = useMemo(() => {
    const result = processedData.filter(d => d.date >= '2015-01-01');
    console.log('Filtered data (2015+):', result.length, 'items');
    return result;
  }, [processedData]);

  const latestData = useMemo(() => {
    return filteredData[filteredData.length - 1];
  }, [filteredData]);

  const latestLevel = getValuationLevel(latestData?.compositeScore || 50);
  const defenseLevel = getValuationLevel(latestData?.defenseScore || 50);
  const offenseLevel = getValuationLevel(latestData?.offenseScore || 50);

  // 年度估值分布数据
  const yearlyDistributionData = useMemo(() => {
    return calculateYearlyDistribution(processedData);
  }, [processedData]);

  // 数据加载中或加载失败
  if (dataLoading) {
    return (
      <div className="app-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <p>加载数据中...</p>
      </div>
    );
  }

  if (loadError || !rawData) {
    return (
      <div className="app-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <p>数据加载失败，请刷新页面</p>
      </div>
    );
  }

  return (
    <div className="app-container">
      <header className="header">
        <h1>A股估值信号看板</h1>
        <p className="subtitle">基于全局估值体系的交易信号监控系统</p>
        <p className="data-source">数据来源: 理杏仁 | 计算: 五年滚动分位点</p>
      </header>

      {/* 最新估值卡片 */}
      <section className="latest-valuation">
        {/* 复合全局估值分数卡片 */}
        <div className="valuation-card main">
          <div className="card-label">复合全局估值分数</div>
          <div className="card-value" style={{ color: latestLevel.color }}>
            {latestData?.compositeScore?.toFixed(1) || '--'}
          </div>
          <div className="card-level" style={{ backgroundColor: latestLevel.color }}>
            {latestLevel.label}
          </div>
          <div className="card-date">更新日期：{latestData?.date || '--'}</div>
          {/* 分项指标详情 */}
          <div className="card-details">
            <div className="detail-item">
              <span>PE/PE分位（5年）:</span>
              <span>{latestData?.pe_ttm?.toFixed(2) || '--'} ({latestData?.pe_percentile?.toFixed(1) || '--'}%)</span>
            </div>
            <div className="detail-item">
              <span>PB/PB分位（5年）:</span>
              <span>{latestData?.pb?.toFixed(2) || '--'} ({latestData?.pb_percentile?.toFixed(1) || '--'}%)</span>
            </div>
            <div className="detail-item">
              <span>ERP/ERP分位（5年）:</span>
              <span>{latestData?.erp?.toFixed(2) || '--'}% (反向{latestData?.erp_reverse_percentile?.toFixed(1) || '--'}%)</span>
            </div>
          </div>
          <div className="detail-source">*基于中证全指计算</div>
        </div>

        {/* 防守端指标卡片 */}
        <div className="valuation-card defense">
          <div className="card-label">防守端指标</div>
          <div className="card-value" style={{ color: defenseLevel.color }}>
            {latestData?.defenseScore?.toFixed(1) || '--'}
          </div>
          <div className="card-level" style={{ backgroundColor: defenseLevel.color }}>
            {defenseLevel.label}
          </div>
          <div className="card-date">更新日期：{latestData?.date || '--'}</div>
          {/* 分项指标详情 */}
          <div className="card-details">
            <div className="detail-item">
              <span>中证红利PE/PE分位（5年）:</span>
              <span>{latestData?.defense_pe?.toFixed(2) || '--'} ({latestData?.defenseScore?.toFixed(1) || '--'}%)</span>
            </div>
          </div>
          <div className="detail-source">*基于中证红利计算</div>
        </div>

        {/* 进攻端指标卡片 */}
        <div className="valuation-card offense">
          <div className="card-label">进攻端指标</div>
          <div className="card-value" style={{ color: offenseLevel.color }}>
            {latestData?.offenseScore?.toFixed(1) || '--'}
          </div>
          <div className="card-level" style={{ backgroundColor: offenseLevel.color }}>
            {offenseLevel.label}
          </div>
          <div className="card-date">更新日期：{latestData?.date || '--'}</div>
          {/* 分项指标详情 */}
          <div className="card-details">
            <div className="detail-item">
              <span>创业板指PE/PE分位（5年）:</span>
              <span>{latestData?.cyb_pe?.toFixed(2) || '--'} ({latestData?.cyb_pe_percentile?.toFixed(1) || '--'}%)</span>
            </div>
            <div className="detail-item">
              <span>中证1000 PE/PE分位（5年）:</span>
              <span>{latestData?.zg1000_pe?.toFixed(2) || '--'} ({latestData?.zg1000_pe_percentile?.toFixed(1) || '--'}%)</span>
            </div>
          </div>
          <div className="detail-source">*基于创业板指和中证1000计算</div>
        </div>
      </section>

      <TrendSignalModule
        zone={latestLevel.label}
        maDirection={offenseMA.direction}
        offense={latestData?.offenseScore}
        defense={latestData?.defenseScore}
        offenseMA5={offenseMA.ma5}
        offenseMA20={offenseMA.ma20}
      />

      <DualEndsModule
        offenseScore={latestData?.offenseScore}
        defenseScore={latestData?.defenseScore}
      />

      {/* 估值区间图例 */}
      <ValuationLegend />

      {/* 主要估值信号图表 */}
      <section className="chart-section">
        <h2>全局估值信号历史走势</h2>
        <p className="chart-description">
          复合全局估值分数 = PE分位×35% + PB分位×25% + ERP反向分位×40%
        </p>
        <ValuationChart data={filteredData} />
      </section>

      {/* 原始指标图表 */}
      <section className="chart-section">
        <h2>中证全指估值指标历史</h2>
        <p className="chart-description">
          PE_TTM、PB及股权风险溢价(ERP)的历史走势
        </p>
        <MetricsChart data={filteredData} />
      </section>

      {/* 中证红利PE分位历史 */}
      <section className="chart-section">
        <h2>中证红利历史PE分位</h2>
        <p className="chart-description">
          中证红利(000922) PE及5年分位历史走势
        </p>
        <SingleIndexChart
          data={hongliPEData}
          title="中证红利PE分位"
          dataKey="pe_percentile"
          lineName="PE分位（5年）"
          lineColor="#0891b2"
        />
      </section>

      {/* 创业板指PE分位历史 */}
      <section className="chart-section">
        <h2>创业板指历史PE分位</h2>
        <p className="chart-description">
          创业板指(399006) PE及5年分位历史走势
        </p>
        <SingleIndexChart
          data={cybPEData}
          title="创业板指PE分位"
          dataKey="pe_percentile"
          lineName="PE分位（5年）"
          lineColor="#2563eb"
        />
      </section>

      {/* 中证1000 PE分位历史 */}
      <section className="chart-section">
        <h2>中证1000历史PE分位</h2>
        <p className="chart-description">
          中证1000(000852) PE及5年分位历史走势
        </p>
        <SingleIndexChart
          data={zg1000PEData}
          title="中证1000 PE分位"
          dataKey="pe_percentile"
          lineName="PE分位（5年）"
          lineColor="#059669"
        />
      </section>

      {/* 年度估值分布图 */}
      <section className="chart-section">
        <h2>年度估值分布（100%堆叠柱状图）</h2>
        <p className="chart-description">
          每年中证全指估值处于各区间的交易日占比
        </p>
        <YearlyDistributionChart data={yearlyDistributionData} />
      </section>

      {/* 数据说明 */}
      <section className="info-section">
        <h3>数据说明</h3>
        <div className="info-grid">
          <div className="info-item">
            <strong>复合全局估值分数</strong> = PE分位×35% + PB分位×25% + ERP反向分位×40%
          </div>
          <div className="info-item">
            <strong>防守端指标</strong> = 中证红利(000922.sh) PE分位
          </div>
          <div className="info-item">
            <strong>进攻端指标</strong> = 创业板指(399006) PE分位 + 中证1000(000852) PE分位 的均值
          </div>
          <div className="info-item">
            <strong>ERP (股权风险溢价)</strong> = 1/PE - 10年期国债收益率(2.5%)
          </div>
        </div>
      </section>

      <footer className="footer">
        <p>数据来源: 理杏仁 | 五年滚动分位点计算 | 仅供演示参考，不构成投资建议</p>
      </footer>
    </div>
  );
}

export default App;
