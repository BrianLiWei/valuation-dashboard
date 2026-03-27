import './TrendSignalModule.css';

function getTrendStatus(zone, maDirection, offense, defense) {
  const isAttacking = offense > defense;

  if (zone === '极度高估') {
    if (maDirection === 'up' && isAttacking) return 'strong-heating';
    return 'mild-cooling';
  }
  if (zone === '高估') {
    if (maDirection === 'up' && isAttacking) return 'heating-up';
    if (maDirection === 'down' && !isAttacking) return 'cooling-down';
    return 'mild-cooling';
  }
  if (zone === '极度低估') {
    if (maDirection === 'down' && !isAttacking) return 'strong-cooling';
    return 'mild-heating';
  }
  if (zone === '低估') {
    if (maDirection === 'down' && !isAttacking) return 'cooling-down';
    if (maDirection === 'up' && isAttacking) return 'mild-heating';
    return 'watch';
  }
  // 合理区间
  if (Math.abs(offense - defense) < 15) return 'watch';
  if (isAttacking) return 'mild-heating';
  return 'mild-cooling';
}

const TREND_STATUS = {
  'strong-heating': { label: '强升温', color: '#ef4444', bg: '#fef2f2', icon: '▲' },
  'heating-up':     { label: '升温加速', color: '#f97316', bg: '#fff7ed', icon: '↗' },
  'mild-cooling':   { label: '温和降温', color: '#f59e0b', bg: '#fffbeb', icon: '↘' },
  'cooling-down':   { label: '降温加速', color: '#3b82f6', bg: '#eff6ff', icon: '↙' },
  'strong-cooling': { label: '强降温', color: '#16a34a', bg: '#f0fdf4', icon: '▼' },
  'mild-heating':   { label: '温和升温', color: '#f59e0b', bg: '#fffbeb', icon: '↗' },
  'watch':          { label: '观望', color: '#6b7280', bg: '#f9fafb', icon: '◆' },
};

function getMA方向Text(maDirection) {
  if (maDirection === 'up') return '均线向上';
  if (maDirection === 'down') return '均线向下';
  return '均线走平';
}

export default function TrendSignalModule({
  zone,
  maDirection,
  offense,
  defense,
  offenseMA5,
  offenseMA20,
}) {
  const effectiveZone = zone ?? '合理';
  const status = getTrendStatus(effectiveZone, maDirection, offense, defense);
  const config = TREND_STATUS[status];

  return (
    <div className="trend-signal-module" style={{ backgroundColor: config.bg }}>
      <div className="trend-signal-main">
        <span className="trend-signal-icon" style={{ color: config.color }}>
          {config.icon}
        </span>
        <span className="trend-signal-label" style={{ color: config.color }}>
          {config.label}
        </span>
        <span className="trend-signal-zone">{effectiveZone}</span>
      </div>
      <div className="trend-signal-footer">
        <span className="trend-signal-detail">
          进攻端 {offense?.toFixed(1) ?? '--'}% | {getMA方向Text(maDirection)}
        </span>
      </div>
    </div>
  );
}