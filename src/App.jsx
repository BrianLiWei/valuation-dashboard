import { useMemo } from 'react';
import ValuationChart from './components/ValuationChart';
import MetricsChart from './components/MetricsChart';
import ValuationLegend from './components/ValuationLegend';
import { getValuationLevel, processLixingerData, getAllIndexData, getIndexPEPercentile } from './utils/valuation';
import SingleIndexChart from './components/SingleIndexChart';
import rawData from './data/lixinger_indices.json';
import './App.css';

function App() {
  console.log('Raw data keys:', Object.keys(rawData));
  console.log('Raw data sample:', rawData['000985']?.data?.slice(0, 2));

  // 处理理杏仁数据
  const processedData = useMemo(() => {
    console.log('Processing data...');
    const result = processLixingerData(rawData);
    console.log('Processed result:', result?.length, 'items');
    if (result?.length > 0) {
      console.log('First item:', result[0]);
      console.log('Last item:', result[result.length - 1]);
    }
    return result;
  }, []);

  const allIndexData = useMemo(() => getAllIndexData(rawData), []);

  // 中证红利PE分位历史
  const hongliPEData = useMemo(() => {
    const data = getIndexPEPercentile(rawData, '000922');
    return data.filter(d => d.date >= '2015-01-01');
  }, []);

  // 创业板指PE分位历史
  const cybPEData = useMemo(() => {
    const data = getIndexPEPercentile(rawData, '399006');
    return data.filter(d => d.date >= '2015-01-01');
  }, []);

  // 中证1000 PE分位历史
  const zg1000PEData = useMemo(() => {
    const data = getIndexPEPercentile(rawData, '000852');
    return data.filter(d => d.date >= '2015-01-01');
  }, []);

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

  // 数据来源信息
  const dataSourceInfo = useMemo(() => {
    const codes = Object.keys(allIndexData);
    return codes.map(code => ({
      code,
      name: allIndexData[code].name,
      count: allIndexData[code].data.length,
    }));
  }, [allIndexData]);

  return (
    <div className="app-container">
      <header className="header">
        <h1>A股估值信号看板</h1>
        <p className="subtitle">基于全局估值体系的交易信号监控系统</p>
        <p className="data-source">数据来源: 理杏仁 | 计算: 五年滚动分位点</p>
      </header>

      {/* 数据来源信息 */}
      <section className="data-source-section">
        <h4>可用指数数据</h4>
        <div className="index-tags">
          {dataSourceInfo.map(item => (
            <span key={item.code} className="index-tag">
              {item.name} ({item.count}条)
            </span>
          ))}
        </div>
      </section>

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
          lineColor="#374151"
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
          lineColor="#374151"
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
          lineColor="#374151"
        />
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
