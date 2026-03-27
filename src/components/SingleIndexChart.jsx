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
  ReferenceArea,
  Brush,
} from 'recharts';
import { ZONE_COLORS } from '../utils/valuation';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const data = payload[0]?.payload;
    if (!data) return null;
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
        <p>PE: <span style={{ fontWeight: 'bold' }}>{data.pe?.toFixed(2)}</span></p>
        <p>PE分位（5年）: <span style={{ fontWeight: 'bold' }}>{data.pe_percentile?.toFixed(1)}%</span></p>
      </div>
    );
  }
  return null;
};

export default function SingleIndexChart({ data, title, dataKey = 'pe_percentile', lineName = 'PE分位（5年）', lineColor = '#374151' }) {
  // 过滤有效数据
  const validData = useMemo(() => {
    if (!data || data.length === 0) return [];
    return data.filter(d => d[dataKey] !== null && d[dataKey] !== undefined);
  }, [data, dataKey]);

  if (validData.length === 0) {
    return (
      <div style={{ width: '100%', height: 500, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p>暂无数据</p>
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
            ticks={[0, 10, 30, 70, 90, 100]}
            label={{ value: '分位 (%)', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fontSize: 12 } }}
          />

          <Tooltip content={<CustomTooltip />} />

          {/* 估值区间背景 */}
          <ReferenceArea y1={0} y2={10} fill={ZONE_COLORS.EXTREME_UNDERVALUED} fillOpacity={0.1} />
          <ReferenceArea y1={10} y2={30} fill={ZONE_COLORS.UNDERVALUED} fillOpacity={0.1} />
          <ReferenceArea y1={30} y2={70} fill={ZONE_COLORS.FAIR} fillOpacity={0.1} />
          <ReferenceArea y1={70} y2={90} fill={ZONE_COLORS.OVERVALUED} fillOpacity={0.1} />
          <ReferenceArea y1={90} y2={100} fill={ZONE_COLORS.EXTREME_OVERVALUED} fillOpacity={0.1} />

          <Line
            type="monotone"
            dataKey={dataKey}
            name={lineName}
            stroke={lineColor}
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
