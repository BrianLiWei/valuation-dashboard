import { useMemo } from 'react';
import './DualEndsModule.css';

function getStatus(offense, defense) {
  const diff = offense - defense;
  if (diff > 30) return 'structural-attack';
  if (diff < -30) return 'structural-defense';
  // 进攻端和防守端同时在高估或同时在低估区间
  const bothHigh = offense >= 70 && defense >= 70;
  const bothLow = offense <= 30 && defense <= 30;
  if (bothHigh || bothLow) return 'same-direction';
  return 'neutral';
}

const STATUS_CONFIG = {
  'structural-attack': { label: '🔴 结构性分化（进攻强）', color: '#ef4444', bg: '#fef2f2' },
  'structural-defense': { label: '🔵 结构性分化（防守强）', color: '#3b82f6', bg: '#eff6ff' },
  'same-direction': { label: '🟡 整体同向', color: '#f59e0b', bg: '#fffbeb' },
  'neutral': { label: '⚪ 无明显分化', color: '#6b7280', bg: '#f9fafb' },
};

export default function DualEndsModule({ offenseScore, defenseScore }) {
  // 如果两者都为 null，不渲染
  if (offenseScore === null && defenseScore === null) {
    return null;
  }

  // 处理 null 值，假设为 0 用于显示
  const offense = offenseScore ?? 0;
  const defense = defenseScore ?? 0;

  const status = useMemo(() => getStatus(offense, defense), [offense, defense]);
  const config = STATUS_CONFIG[status];
  const diff = offense - defense;

  return (
    <div className="dual-ends-module" style={{ backgroundColor: config.bg }}>
      <div className="dual-ends-header">
        <span className="dual-ends-status" style={{ color: config.color }}>
          {config.label}
        </span>
      </div>

      <div className="dual-ends-bars">
        <div className="bar-row">
          <span className="bar-label">进攻端</span>
          <div className="bar-track">
            <div
              className="bar-fill offense-bar"
              style={{ width: `${offense}%` }}
            />
          </div>
          <span className="bar-value">{offense.toFixed(1)}%</span>
        </div>

        <div className="bar-row">
          <span className="bar-label">防守端</span>
          <div className="bar-track">
            <div
              className="bar-fill defense-bar"
              style={{ width: `${defense}%` }}
            />
          </div>
          <span className="bar-value">{defense.toFixed(1)}%</span>
        </div>
      </div>

      <div className="dual-ends-footer">
        <span className="diff-value">
          差值: <strong style={{ color: diff > 0 ? '#ef4444' : diff < 0 ? '#3b82f6' : '#6b7280' }}>
            {diff > 0 ? '+' : ''}{diff.toFixed(1)}%
          </strong>
        </span>
      </div>
    </div>
  );
}