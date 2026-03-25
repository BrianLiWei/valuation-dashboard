import { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

const ZONE_COLORS = {
  '极度低估': '#16a34a',
  '低估': '#4ade80',
  '合理': '#facc15',
  '高估': '#fb923c',
  '极度高估': '#ef4444',
};

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const total = payload[0]?.payload?.total || 0;
    return (
      <div style={{
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        border: '1px solid #ccc',
        borderRadius: '8px',
        padding: '12px',
        fontSize: '12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
      }}>
        <p style={{ fontWeight: 'bold', marginBottom: '8px' }}>{label}年</p>
        {payload.map((p, idx) => (
          <p key={idx} style={{ color: p.fill }}>
            {p.name}: {p.value}%
          </p>
        ))}
        <p style={{ marginTop: '8px', borderTop: '1px solid #eee', paddingTop: '8px' }}>
          共 {total} 个交易日
        </p>
      </div>
    );
  }
  return null;
};

// 自定义图例 - 确保顺序正确
function CustomLegend() {
  const zones = ['极度低估', '低估', '合理', '高估', '极度高估'];
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      gap: '20px',
      paddingTop: '16px',
      paddingBottom: '8px',
      flexWrap: 'wrap',
    }}>
      {zones.map(zone => (
        <div key={zone} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div style={{
            width: '14px',
            height: '14px',
            backgroundColor: ZONE_COLORS[zone],
            borderRadius: '3px',
          }} />
          <span style={{ fontSize: '13px', color: '#374151' }}>{zone}</span>
        </div>
      ))}
    </div>
  );
}

export default function YearlyDistributionChart({ data }) {
  const chartData = useMemo(() => {
    if (!data || data.length === 0) return [];
    return data.filter(d => d.year >= '2015' && d.year <= '2025');
  }, [data]);

  if (chartData.length === 0) {
    return (
      <div style={{ width: '100%', height: 500, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p>暂无数据</p>
      </div>
    );
  }

  const zones = ['极度低估', '低估', '合理', '高估', '极度高估'];

  return (
    <div style={{ width: '100%', height: 500 }}>
      <ResponsiveContainer>
        <BarChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="year"
            tick={{ fontSize: 11 }}
            tickMargin={5}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fontSize: 11 }}
            ticks={[0, 25, 50, 75, 100]}
            label={{ value: '占比 (%)', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fontSize: 12 } }}
          />
          <Tooltip content={<CustomTooltip />} />
          {zones.map(zone => (
            <Bar
              key={zone}
              dataKey={zone}
              stackId="a"
              fill={ZONE_COLORS[zone]}
              name={zone}
              legendType="plainline"
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
      <CustomLegend />
    </div>
  );
}
