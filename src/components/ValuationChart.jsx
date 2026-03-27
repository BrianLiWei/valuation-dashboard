import { useMemo } from 'react';
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceArea,
  Brush,
  Bar,
} from 'recharts';
import { getValuationLevel, ZONE_COLORS } from '../utils/valuation';

// 估值区间颜色
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const data = payload[0]?.payload;
    if (!data) return null;
    const level = getValuationLevel(data.compositeScore);

    return (
      <div style={{
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        border: '1px solid #ccc',
        borderRadius: '8px',
        padding: '12px',
        fontSize: '12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
      }}>
        <p style={{ fontWeight: 'bold', marginBottom: '8px' }}>{label}</p>
        <p style={{ color: '#2563eb', fontWeight: 'bold', fontSize: '14px' }}>
          复合全局估值分数: {data.compositeScore?.toFixed(1)} ({level?.label})
        </p>
        <hr style={{ margin: '8px 0' }} />
        <p>PE分位: {data.pe_percentile?.toFixed(1)}%</p>
        <p>PB分位: {data.pb_percentile?.toFixed(1)}%</p>
        <p>ERP: {data.erp?.toFixed(2)}%</p>
      </div>
    );
  }
  return null;
};

export default function ValuationChart({ data }) {
  console.log('ValuationChart received data:', data?.length, 'items');

  // 过滤有效数据
  const validData = useMemo(() => {
    if (!data || data.length === 0) return [];
    return data.filter(d => d.compositeScore !== null && d.compositeScore !== undefined);
  }, [data]);

  console.log('Valid data:', validData.length, 'items');

  if (validData.length === 0) {
    return (
      <div style={{ width: '100%', height: 500, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p>暂无数据，请检查数据源</p>
      </div>
    );
  }

  return (
    <div style={{ width: '100%', height: 500 }}>
      <ResponsiveContainer>
        <ComposedChart data={validData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />

          <XAxis
            dataKey="date"
            tick={{ fontSize: 10 }}
            tickFormatter={(value) => value?.slice(0, 10)}
            tickCount={10}
            minTickGap={50}
          />

          <YAxis
            domain={[0, 100]}
            tick={{ fontSize: 11 }}
            tickMargin={8}
            ticks={[0, 10, 30, 70, 90, 100]}
            label={{ value: '估值分数', angle: 0, position: 'insideTop', style: { textAnchor: 'middle', fontSize: 12 } }}
          />

          <Tooltip content={<CustomTooltip />} />

          {/* 估值区间背景 */}
          <ReferenceArea y1={0} y2={10} fill={ZONE_COLORS.EXTREME_UNDERVALUED} fillOpacity={0.1} />
          <ReferenceArea y1={10} y2={30} fill={ZONE_COLORS.UNDERVALUED} fillOpacity={0.1} />
          <ReferenceArea y1={30} y2={70} fill={ZONE_COLORS.FAIR} fillOpacity={0.1} />
          <ReferenceArea y1={70} y2={90} fill={ZONE_COLORS.OVERVALUED} fillOpacity={0.1} />
          <ReferenceArea y1={90} y2={100} fill={ZONE_COLORS.EXTREME_OVERVALUED} fillOpacity={0.1} />

          {/* 复合全局估值分数线 */}
          <Line
            type="monotone"
            dataKey="compositeScore"
            name="复合全局估值分数"
            stroke="#60a5fa"
            strokeWidth={1.5}
            dot={false}
            activeDot={{ r: 4 }}
            connectNulls
          />

          <Brush
            dataKey="date"
            height={30}
            stroke="#475569"
            tickFormatter={(value) => value?.slice(0, 10)}
            travellerWidth={10}
            gap={1}
          />

          <Legend
            wrapperStyle={{ paddingTop: '10px', cursor: 'pointer' }}
            formatter={(value) => <span style={{ color: '#374151', fontSize: '12px' }}>{value}</span>}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
