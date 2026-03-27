# A股估值信号看板功能增强实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增两个模块：DualEndsModule（双端对比）和 TrendSignalModule（趋势信号），提升看板对市场结构性分化和趋势方向的判断能力。

**Architecture:**
- DualEndsModule：纯展示组件，直接复用 `latestData.offenseScore` 和 `latestData.defenseScore`，无新增计算
- TrendSignalModule：需要进攻端分位的历史序列（最近20个交易日），在 `App.jsx` 的 `useMemo` 中计算 `offenseScore` 时间序列，再分别计算 SMA(5) 和 SMA(20)，结果作为 prop 传入组件
- 两模块均独立，不修改任何现有组件逻辑

**Tech Stack:** React + Recharts，原有技术栈不变

---

## 文件变更总览

| 操作 | 文件 |
|------|------|
| 新建 | `src/components/DualEndsModule.jsx` |
| 新建 | `src/components/TrendSignalModule.jsx` |
| 修改 | `src/App.jsx`（新增两个 useMemo + 两处组件插入） |
| 新建 | `src/components/DualEndsModule.css` |
| 新建 | `src/components/TrendSignalModule.css` |

---

## 实施任务

---

### 任务 1：实现 DualEndsModule 组件

**Files:**
- 创建: `src/components/DualEndsModule.jsx`
- 创建: `src/components/DualEndsModule.css`

- [ ] **Step 1: 创建 DualEndsModule.jsx**

```jsx
import { useMemo } from 'react';
import './DualEndsModule.css';

const STATUS_CONFIG = {
  'structural-attack': { label: '🔴 结构性分化（进攻强）', color: '#ef4444', bg: '#fef2f2' },
  'structural-defense': { label: '🔵 结构性分化（防守强）', color: '#3b82f6', bg: '#eff6ff' },
  'same-direction': { label: '🟡 整体同向', color: '#f59e0b', bg: '#fffbeb' },
  'neutral': { label: '⚪ 无明显分化', color: '#6b7280', bg: '#f9fafb' },
};

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

export default function DualEndsModule({ offenseScore, defenseScore }) {
  const status = useMemo(() => getStatus(offenseScore || 0, defenseScore || 0), [offenseScore, defenseScore]);
  const diff = Math.abs((offenseScore || 0) - (defenseScore || 0));
  const config = STATUS_CONFIG[status];

  if (offenseScore === null || defenseScore === null) {
    return null;
  }

  return (
    <div className="dual-ends-module" style={{ background: config.bg, borderColor: config.color }}>
      <div className="dual-ends-header">
        <span className="dual-ends-title">双端对比</span>
        <span className="dual-ends-badge" style={{ backgroundColor: config.color }}>{config.label}</span>
      </div>
      <div className="dual-ends-bars">
        <div className="dual-ends-row">
          <span className="dual-ends-label">进攻端</span>
          <div className="dual-ends-bar-track">
            <div
              className="dual-ends-bar-fill attack"
              style={{ width: `${offenseScore}%` }}
            />
          </div>
          <span className="dual-ends-value">{offenseScore.toFixed(1)}%</span>
        </div>
        <div className="dual-ends-row">
          <span className="dual-ends-label">防守端</span>
          <div className="dual-ends-bar-track">
            <div
              className="dual-ends-bar-fill defense"
              style={{ width: `${defenseScore}%` }}
            />
          </div>
          <span className="dual-ends-value">{defenseScore.toFixed(1)}%</span>
        </div>
      </div>
      <div className="dual-ends-diff">
        差值: {diff.toFixed(1)}%
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 创建 DualEndsModule.css**

```css
.dual-ends-module {
  border-radius: 12px;
  border: 1px solid;
  padding: 16px 20px;
  margin-bottom: 20px;
}

.dual-ends-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.dual-ends-title {
  font-size: 15px;
  font-weight: 600;
  color: #111827;
}

.dual-ends-badge {
  font-size: 12px;
  color: white;
  padding: 3px 10px;
  border-radius: 12px;
  font-weight: 600;
}

.dual-ends-bars {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.dual-ends-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.dual-ends-label {
  width: 48px;
  font-size: 13px;
  color: #6b7280;
  font-weight: 500;
}

.dual-ends-bar-track {
  flex: 1;
  height: 20px;
  background: #f3f4f6;
  border-radius: 4px;
  overflow: hidden;
}

.dual-ends-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.dual-ends-bar-fill.attack {
  background: linear-gradient(90deg, #fb923c, #ef4444);
}

.dual-ends-bar-fill.defense {
  background: linear-gradient(90deg, #3b82f6, #60a5fa);
}

.dual-ends-value {
  width: 56px;
  text-align: right;
  font-size: 13px;
  font-weight: 700;
  color: #374151;
}

.dual-ends-diff {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid rgba(0,0,0,0.08);
  font-size: 12px;
  color: #6b7280;
  text-align: center;
}
```

- [ ] **Step 3: 提交**

```bash
git add src/components/DualEndsModule.jsx src/components/DualEndsModule.css
git commit -m "feat: add DualEndsModule - 双端PE分位对比组件

显示进攻端(创业板指+中证1000均值)和防守端(中证红利)PE分位并排条形图，标注结构性分化状态"

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

---

### 任务 2：实现 TrendSignalModule 组件

**Files:**
- 创建: `src/components/TrendSignalModule.jsx`
- 创建: `src/components/TrendSignalModule.css`

**数据来源说明：**
- `offenseScoreHistory`: 最近20个交易日的进攻端分位数组（用于计算SMA）
- `currentZone`: 当前市场所处区间（来自 `latestLevel.label`）
- `offense`: 当前进攻端分位
- `defense`: 当前防守端分位

这些数据从 App.jsx 的 useMemo 计算后以 props 传入。

- [ ] **Step 1: 创建 TrendSignalModule.jsx**

```jsx
import './TrendSignalModule.css';

const TREND_STATUS = {
  'strong-heating': {
    label: '强升温',
    color: '#ef4444',
    bg: '#fef2f2',
    icon: '▲',
  },
  'heating-up': {
    label: '升温加速',
    color: '#f97316',
    bg: '#fff7ed',
    icon: '↗',
  },
  'mild-cooling': {
    label: '温和降温',
    color: '#f59e0b',
    bg: '#fffbeb',
    icon: '↘',
  },
  'cooling-down': {
    label: '降温加速',
    color: '#3b82f6',
    bg: '#eff6ff',
    icon: '↙',
  },
  'strong-cooling': {
    label: '强降温',
    color: '#16a34a',
    bg: '#f0fdf4',
    icon: '▼',
  },
  'mild-heating': {
    label: '温和升温',
    color: '#f59e0b',
    bg: '#fffbeb',
    icon: '↗',
  },
  'watch': {
    label: '观望',
    color: '#6b7280',
    bg: '#f9fafb',
    icon: '◆',
  },
};

function getTrendStatus(zone, maDirection, offense, defense) {
  const diff = offense - defense;
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
  if (Math.abs(diff) < 15) return 'watch';
  if (isAttacking) return 'mild-heating';
  return 'mild-cooling';
}

export default function TrendSignalModule({
  zone,
  maDirection,
  offense,
  defense,
  offenseMA5,
  offenseMA20,
}) {
  const status = getTrendStatus(zone, maDirection, offense, defense);
  const config = TREND_STATUS[status];

  const diff = Math.abs(offense - defense);

  return (
    <div className="trend-signal-module" style={{ background: config.bg }}>
      <div className="trend-signal-main">
        <span className="trend-signal-icon" style={{ color: config.color }}>
          {config.icon}
        </span>
        <span className="trend-signal-label" style={{ color: config.color }}>
          {config.label}
        </span>
        <span className="trend-signal-zone">{zone}</span>
      </div>
      <div className="trend-signal-details">
        <span>
          进攻端 {offense.toFixed(1)}% {maDirection === 'up' ? '↗' : '↘'}
        </span>
        <span className="trend-signal-sep">|</span>
        <span>均线5日>{maDirection === 'up' ? '20日(上升)' : '20日(下降)'}</span>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 创建 TrendSignalModule.css**

```css
.trend-signal-module {
  border-radius: 10px;
  padding: 12px 16px;
  margin-bottom: 20px;
  border: 1px solid rgba(0,0,0,0.06);
}

.trend-signal-main {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.trend-signal-icon {
  font-size: 16px;
  font-weight: 700;
}

.trend-signal-label {
  font-size: 15px;
  font-weight: 700;
}

.trend-signal-zone {
  font-size: 12px;
  color: #6b7280;
  background: rgba(0,0,0,0.05);
  padding: 2px 8px;
  border-radius: 8px;
  margin-left: 4px;
}

.trend-signal-details {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #6b7280;
}

.trend-signal-sep {
  color: #d1d5db;
}
```

- [ ] **Step 3: 提交**

```bash
git add src/components/TrendSignalModule.jsx src/components/TrendSignalModule.css
git commit -m "feat: add TrendSignalModule - 趋势信号组件

综合当前估值区间+进攻端均线方向+两端分化方向输出趋势状态标签
（强升温/降温加速/观望等）"

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

---

### 任务 3：App.jsx 新增进攻端分位历史序列计算

**Files:**
- 修改: `src/App.jsx`

- [ ] **Step 1: 在 App.jsx 中新增 useMemo 计算进攻端分位历史序列及均线**

在现有 `zg1000PEData` useMemo 之后添加：

```javascript
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
```

- [ ] **Step 2: 在 App.jsx 中引入两个新组件**

在文件顶部的 import 中添加：
```javascript
import DualEndsModule from './components/DualEndsModule';
import TrendSignalModule from './components/TrendSignalModule';
```

- [ ] **Step 3: 在 JSX 中插入 DualEndsModule**

在 `latest-valuation` section 结束后、`ValuationLegend` 之前插入：
```jsx
<DualEndsModule
  offenseScore={latestData?.offenseScore}
  defenseScore={latestData?.defenseScore}
/>
```

- [ ] **Step 4: 在 JSX 中插入 TrendSignalModule**

在三个 valuation-card 区域的正下方插入（在 `</section>` 闭合标签之前）：
```jsx
<TrendSignalModule
  zone={latestLevel.label}
  maDirection={offenseMA.direction}
  offense={latestData?.offenseScore}
  defense={latestData?.defenseScore}
  offenseMA5={offenseMA.ma5}
  offenseMA20={offenseMA.ma20}
/>
```

- [ ] **Step 5: 验证构建**

```bash
cd "/Users/weili/Library/Mobile Documents/com~apple~CloudDocs/Project JoinQuant/WebView Monitor/valuation-dashboard"
npm run build
```

预期：构建成功，无错误

- [ ] **Step 6: 提交**

```bash
git add src/App.jsx
git commit -m "feat: 集成DualEndsModule和TrendSignalModule到主页面

新增进攻端分位SMA(5/20)计算useMemo，在页面顶部展示双端对比和趋势信号"

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

---

## 验证检查清单

- [ ] DualEndsModule 在防守端和进攻端分位接近时显示"无明显分化"
- [ ] DualEndsModule 在分差 > 30% 时显示"结构性分化"
- [ ] TrendSignalModule 在极度高估+进攻端上升+进攻>防守时显示"强升温"
- [ ] TrendSignalModule 在极度低估+防守端主导时显示"强降温"
- [ ] 均线方向判断：SMA(5) > SMA(20) + 2 → 上升，反之下降
- [ ] npm run build 成功无报错
- [ ] 页面在 dev 模式下正常加载，两个新模块可见

---

## 实施顺序

1. 任务1：DualEndsModule 组件（独立，不依赖任何新数据）
2. 任务2：TrendSignalModule 组件（独立，props 由 App.jsx 计算后传入）
3. 任务3：App.jsx 集成（将两个模块接入页面，并新增均线计算）
