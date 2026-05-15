/* global React */
const { useState, useMemo, useEffect } = React;

// ============================================
// PANEL (corner-bracket card)
// ============================================
function Panel({ label, letter = 'A', meta, children, gold, className = '', headerRight }) {
  return (
    <div className={`cp ${gold ? 'gold' : ''} ${className}`}>
      {label && (
        <div className="cp-header">
          <div className="cp-label">
            <span className="letter-box">{letter}</span>
            <span>{label}</span>
          </div>
          {headerRight}
          {meta && !headerRight && <span className="cp-meta">{meta}</span>}
        </div>
      )}
      <div className="cp-body">{children}</div>
    </div>
  );
}

// ============================================
// STAT CARD (KPI)
// ============================================
function StatCard({ letter, eyebrow, value, unit, delta, deltaDir, color = 'amber', barPct, barColor }) {
  return (
    <div className="cp stat-card">
      <div className="stat-eyebrow">
        <span>{eyebrow}</span>
        {letter && <span className="stat-letter">{letter}</span>}
      </div>
      <div>
        <span className={`stat-num ${color}`}>{value}</span>
        {unit && <span className="stat-unit">{unit}</span>}
      </div>
      {delta && <div className={`stat-delta ${deltaDir || ''}`}>{delta}</div>}
      {barPct !== undefined && (
        <div className="stat-bar"><div className={`stat-bar-fill ${barColor || ''}`} style={{ width: `${Math.min(barPct, 100)}%` }} /></div>
      )}
    </div>
  );
}

// ============================================
// STACKED BAR CHART (HUD pixel style)
// rows: [{ x: label, series: [{ key, value, color }] }]
// ============================================
function StackedBar({ data, height = 240, yTickCount = 4, valueFormat = (v) => v.toLocaleString() }) {
  const totals = data.map(r => r.series.reduce((s, x) => s + x.value, 0));
  const max = Math.max(...totals, 1);
  // Round max up to nice number
  const niceMax = (() => {
    const exp = Math.pow(10, Math.floor(Math.log10(max)));
    const m = Math.ceil(max / exp);
    return m * exp;
  })();
  const yTicks = [];
  for (let i = yTickCount; i >= 0; i--) {
    yTicks.push((niceMax * i / yTickCount));
  }

  // Get unique series in order from first row that has them
  const seriesOrder = [];
  data.forEach(r => r.series.forEach(s => {
    if (!seriesOrder.find(x => x.key === s.key)) seriesOrder.push({ key: s.key, color: s.color });
  }));

  return (
    <div className="stack-bar">
      <div className="stack-bar-wrap" style={{ height }}>
        <div className="stack-bar-yaxis">
          {yTicks.map((t, i) => <span key={i}>{valueFormat(t)}</span>)}
        </div>
        <div className="stack-bar-chart" style={{ height }}>
          {data.map((row, ri) => {
            const total = totals[ri];
            const pct = (total / niceMax) * 100;
            return (
              <div key={ri} className="stack-bar-col" title={`${row.x} · ${valueFormat(total)}`}>
                {row.series.map((seg, si) => (
                  <div
                    key={seg.key}
                    className="stack-bar-seg"
                    style={{
                      height: `${(seg.value / niceMax) * 100}%`,
                      background: seg.color,
                    }}
                  />
                ))}
              </div>
            );
          })}
        </div>
      </div>
      <div className="stack-bar-axis" style={{ paddingLeft: 40 }}>
        {data.map((row, i) => (
          (i % Math.ceil(data.length / 7) === 0 || i === data.length - 1) && (
            <span key={i}>{row.x.slice(5)}</span>
          )
        ))}
      </div>
    </div>
  );
}

// ============================================
// DONUT CHART (SVG)
// data: [{ label, value, color }]
// ============================================
function Donut({ data, size = 200, thickness = 26, centerLabel, centerValue }) {
  const total = data.reduce((s, d) => s + d.value, 0) || 1;
  const r = size / 2 - thickness / 2 - 2;
  const c = 2 * Math.PI * r;
  let offset = 0;
  return (
    <svg className="donut-svg" viewBox={`0 0 ${size} ${size}`}>
      <g transform={`translate(${size/2}, ${size/2}) rotate(-90)`}>
        <circle r={r} fill="none" stroke="rgba(245,158,11,0.06)" strokeWidth={thickness} />
        {data.map((d, i) => {
          const len = (d.value / total) * c;
          const seg = (
            <circle
              key={i}
              r={r}
              fill="none"
              stroke={d.color}
              strokeWidth={thickness}
              strokeDasharray={`${len} ${c - len}`}
              strokeDashoffset={-offset}
            />
          );
          offset += len;
          return seg;
        })}
      </g>
      {centerValue && (
        <text x={size/2} y={size/2 - 2} className="donut-center" textAnchor="middle" fontSize="20" fill="#A8FF78">{centerValue}</text>
      )}
      {centerLabel && (
        <text x={size/2} y={size/2 + 18} className="donut-center" textAnchor="middle" fontSize="9" fill="#9A8870" letterSpacing="0.2em">{centerLabel}</text>
      )}
    </svg>
  );
}

function DonutWithLegend({ data, centerLabel, centerValue, valueFormat = (v) => v.toLocaleString() }) {
  const total = data.reduce((s, d) => s + d.value, 0) || 1;
  return (
    <div className="donut-wrap">
      <div style={{ display: 'flex', justifyContent: 'center' }}>
        <Donut data={data} centerLabel={centerLabel} centerValue={centerValue} />
      </div>
      <div className="donut-list">
        {data.map((d, i) => {
          const pct = (d.value / total) * 100;
          return (
            <div key={i} className="donut-row">
              <span className="legend-swatch" style={{ background: d.color }} />
              <span className="name">{d.label}</span>
              <span className="val">{valueFormat(d.value)}</span>
              <span className="pct">{pct.toFixed(1)}%</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ============================================
// LINE CHART (SVG, radar/scope thin lines)
// series: [{ key, color, points: [{ x, y }] }], xLabels
// ============================================
function LineChart({ series, xLabels, height = 240, valueFormat = (v) => v.toString() }) {
  const W = 700, H = height, padL = 36, padR = 12, padT = 10, padB = 22;
  const innerW = W - padL - padR;
  const innerH = H - padT - padB;
  const xCount = xLabels.length;
  const maxY = Math.max(...series.flatMap(s => s.points.map(p => p.y)), 1);
  const niceMax = (() => {
    const exp = Math.pow(10, Math.floor(Math.log10(maxY)));
    return Math.ceil(maxY / exp) * exp;
  })();
  const xPos = (i) => padL + (innerW * i) / (xCount - 1);
  const yPos = (v) => padT + innerH * (1 - v / niceMax);
  const yTicks = 4;
  return (
    <svg className="line-chart-svg" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
      {/* Grid */}
      {[...Array(yTicks + 1)].map((_, i) => {
        const v = (niceMax * i) / yTicks;
        const y = yPos(v);
        return (
          <g key={i}>
            <line x1={padL} y1={y} x2={W - padR} y2={y} className="line-chart-grid" />
            <text x={padL - 6} y={y + 3} textAnchor="end" className="line-chart-axis-text">{valueFormat(v)}</text>
          </g>
        );
      })}
      {/* X labels */}
      {xLabels.map((l, i) => {
        const step = Math.ceil(xCount / 7);
        if (i % step !== 0 && i !== xCount - 1) return null;
        return (
          <text key={i} x={xPos(i)} y={H - 6} textAnchor="middle" className="line-chart-axis-text">{l.slice(5)}</text>
        );
      })}
      {/* Lines */}
      {series.map((s, si) => (
        <g key={s.key}>
          <polyline
            fill="none"
            stroke={s.color}
            strokeWidth="1.5"
            points={s.points.map((p, i) => `${xPos(i)},${yPos(p.y)}`).join(' ')}
            opacity="0.95"
          />
          {s.points.map((p, i) => (
            <circle key={i} cx={xPos(i)} cy={yPos(p.y)} r="2" fill={s.color} />
          ))}
        </g>
      ))}
    </svg>
  );
}

// ============================================
// LEGEND
// ============================================
function Legend({ items, withValues, valueFormat = (v) => v.toLocaleString() }) {
  return (
    <div className="legend">
      {items.map((it, i) => (
        <div key={i} className="legend-item">
          <span className="legend-swatch" style={{ background: it.color }} />
          <span>{it.label}</span>
          {withValues && <span className="legend-val">{valueFormat(it.value)}</span>}
        </div>
      ))}
    </div>
  );
}

// ============================================
// RANK LIST (model leaderboard / openrouter-style)
// items: [{ name, value, pct, cost?, sessions?, color }]
// ============================================
function RankList({ items, t, valueFormat = (v) => v.toLocaleString(), costFormat = (v) => `$${v.toFixed(2)}` }) {
  const max = Math.max(...items.map(x => x.value), 1);
  return (
    <div className="rank-list">
      {items.map((it, i) => (
        <div key={i} className="rank-row" style={{ borderLeftColor: it.color }}>
          <span className="rank-num">#{String(i + 1).padStart(2, '0')}</span>
          <span className="rank-name">{it.name}</span>
          <span className="rank-num-val">{valueFormat(it.value)}</span>
          <span className="rank-pct">{it.pct.toFixed(1)}%</span>
          <span className="rank-cost">{it.cost !== undefined ? costFormat(it.cost) : '—'}</span>
          <div className="rank-bar-cell"><div className="rank-bar-fill" style={{ width: `${(it.value / max) * 100}%`, background: it.color }} /></div>
        </div>
      ))}
    </div>
  );
}

Object.assign(window, { Panel, StatCard, StackedBar, Donut, DonutWithLegend, LineChart, Legend, RankList });
