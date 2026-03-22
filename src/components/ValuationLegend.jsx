import { VALUATION_LEVELS } from '../utils/valuation';

export default function ValuationLegend() {
  const levels = [
    VALUATION_LEVELS.EXTREME_UNDERVALUED,
    VALUATION_LEVELS.UNDERVALUED,
    VALUATION_LEVELS.FAIR,
    VALUATION_LEVELS.OVERVALUED,
    VALUATION_LEVELS.EXTREME_OVERVALUED,
  ];

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      gap: '16px',
      flexWrap: 'wrap',
      marginBottom: '20px',
      padding: '12px',
      backgroundColor: '#f9fafb',
      borderRadius: '8px',
    }}>
      {levels.map((level) => (
        <div key={level.label} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div style={{
            width: '16px',
            height: '16px',
            backgroundColor: level.color,
            borderRadius: '4px',
          }} />
          <span style={{ fontSize: '12px', fontWeight: 'bold' }}>{level.label}</span>
          <span style={{ fontSize: '11px', color: '#6b7280' }}>({level.min}-{level.max})</span>
        </div>
      ))}
    </div>
  );
}
