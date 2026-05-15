/* global React, Panel, StatCard, StackedBar, DonutWithLegend, LineChart, Legend, RankList, HERMES_DATA, HERMES_I18N */
const { useState: useStateS, useMemo: useMemoS } = React;

// Helpers
const fmtNum = (v) => v.toLocaleString('en-US');
const fmtCompact = (v) => {
  if (v >= 1e9) return (v / 1e9).toFixed(1) + 'B';
  if (v >= 1e6) return (v / 1e6).toFixed(1) + 'M';
  if (v >= 1e3) return (v / 1e3).toFixed(1) + 'K';
  return Math.round(v).toString();
};
const fmtUsd = (v) => `$${v.toFixed(2)}`;
const fmtEur = (v) => `€${v.toFixed(2)}`;

// =================================================
// SECTION 01 — OVERVIEW
// =================================================
function SectionOverview({ t }) {
  const D = HERMES_DATA;
  const tokensByModelStacked = D.tokensPerDay.map(row => ({
    x: row.date,
    series: D.models.map(m => ({ key: m.id, value: row[m.id], color: m.color })),
  }));
  const sourceDonut = D.sources.map(s => ({ label: s.name.toUpperCase(), value: s.count, color: s.color }));
  const modelLegend = D.models.map(m => {
    const tot = D.tokensPerDay.reduce((s, r) => s + r[m.id], 0);
    return { label: m.short, color: m.color, value: tot };
  });

  return (
    <>
      <div className="stat-grid">
        <StatCard letter="A" eyebrow={t.kpi.sessions} value={fmtNum(D.totals.sessions)} unit="SES" delta={`${D.totals.daysActive} ${t.misc.today === 'HOY' ? 'DÍAS ACTIVOS' : 'ACTIVE DAYS'}`} color="amber" barPct={78} />
        <StatCard letter="B" eyebrow={t.kpi.tokens} value={fmtCompact(D.totals.tokens)} delta={`INPUT ${Math.round(D.totals.inputTokens/D.totals.tokens*100)}% · OUTPUT ${Math.round(D.totals.outputTokens/D.totals.tokens*100)}%`} color="gold" barPct={65} barColor="gold" />
        <StatCard letter="C" eyebrow={t.kpi.spent + ' · OR'} value={fmtUsd(D.openRouter.totalUsage)} unit="USD" delta={`${(D.openRouter.totalUsage/D.openRouter.totalCredits*100).toFixed(0)}% ${t.misc.used}  ·  ${fmtEur(D.openRouter.totalUsage*0.92)}`} color="green" barPct={D.openRouter.totalUsage/D.openRouter.totalCredits*100} />
        <StatCard letter="D" eyebrow={t.kpi.models} value={D.totals.models} delta={`${D.sources.length} ${t.misc.source.toUpperCase()}S · ${D.tools.length} TOOLS`} color="amber" barPct={(D.totals.models/10)*100} />
      </div>

      <div className="grid-2-1">
        <Panel label={t.labels.tokens_by_model} letter="A" meta={`14D · ${fmtCompact(D.totals.tokens)} TOT`} gold>
          <StackedBar data={tokensByModelStacked} valueFormat={fmtCompact} />
          <Legend items={modelLegend} withValues valueFormat={fmtCompact} />
        </Panel>

        <Panel label={t.labels.source_dist} letter="B" meta={`${D.totals.sessions} SES`}>
          <DonutWithLegend data={sourceDonut} centerValue={D.totals.sessions} centerLabel="SESSIONS" />
        </Panel>
      </div>

      <Panel label={t.labels.recent_sessions} letter="C" meta={`10 / ${D.totals.sessions}`} gold>
        <table className="dtable">
          <thead>
            <tr>
              <th>{t.table.id}</th>
              <th>{t.table.date}</th>
              <th>{t.table.model}</th>
              <th>{t.table.source}</th>
              <th className="r">{t.table.msgs}</th>
              <th className="r">{t.table.tools}</th>
              <th className="r">{t.table.tokens}</th>
              <th className="r">{t.table.cost}</th>
            </tr>
          </thead>
          <tbody>
            {D.recentSessions.map((s, i) => (
              <tr key={i}>
                <td className="amber">{s.id}</td>
                <td className="dim">{s.started}</td>
                <td>{s.model}</td>
                <td className="dim">{s.source}</td>
                <td className="r code">{s.msgs}</td>
                <td className="r code">{s.tools}</td>
                <td className="r code">{fmtNum(s.tokens)}</td>
                <td className="r amber">{fmtUsd(s.cost)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    </>
  );
}

// =================================================
// SECTION 02 — TOOLS ANALYTICS
// =================================================
function SectionTools({ t }) {
  const D = HERMES_DATA;
  const totalCalls = D.tools.reduce((s, x) => s + x.count, 0);
  const avgSuccess = D.tools.reduce((s, x) => s + x.success * x.count, 0) / totalCalls;

  // Simulated daily usage per tool (top 6) — derive from tool counts
  const topTools = [...D.tools].slice(0, 6);
  const toolDaily = D.days.map((date, di) => ({
    x: date,
    series: topTools.map((tool, ti) => {
      const seed = di * 17 + ti * 11;
      const noise = 0.4 + (Math.sin(seed) * 10000 - Math.floor(Math.sin(seed) * 10000)) * 1.2;
      return { key: tool.name, value: Math.round((tool.count / 14) * noise), color: D.toolColors[ti] };
    }),
  }));

  const toolDist = D.tools.map((tool, i) => ({
    label: tool.name, value: tool.count, color: D.toolColors[i % D.toolColors.length],
  }));

  return (
    <>
      <div className="stat-grid">
        <StatCard letter="A" eyebrow={t.kpi.tool_calls} value={fmtNum(totalCalls)} delta={`${D.totals.daysActive}D · AVG ${Math.round(totalCalls/D.totals.daysActive)}/DAY`} color="amber" barPct={75} />
        <StatCard letter="B" eyebrow={t.kpi.unique_tools} value={D.tools.length} delta={`MOST USED · ${D.tools[0].name}`} color="gold" barPct={80} barColor="gold" />
        <StatCard letter="C" eyebrow={t.kpi.success_rate} value={(avgSuccess*100).toFixed(1)} unit="%" delta={`${Math.round(totalCalls*(1-avgSuccess))} FAILURES`} color="green" barPct={avgSuccess*100} barColor="gold" />
        <StatCard letter="D" eyebrow={t.kpi.sessions_with_tools} value={D.totals.sessions} delta={`AVG ${Math.round(totalCalls/D.totals.sessions)} TOOLS / SES`} color="amber" barPct={100} />
      </div>

      <div className="grid-2-1">
        <Panel label={t.labels.tool_usage} letter="A" meta={`14D · TOP 6`} gold>
          <StackedBar data={toolDaily} valueFormat={fmtCompact} />
          <Legend items={topTools.map((tool, i) => ({ label: tool.name, color: D.toolColors[i], value: tool.count }))} withValues />
        </Panel>

        <Panel label={t.labels.tool_dist} letter="B" meta={`${D.tools.length} TOOLS`}>
          <DonutWithLegend data={toolDist.slice(0, 8)} centerValue={fmtCompact(totalCalls)} centerLabel="CALLS" />
        </Panel>
      </div>

      <Panel label={t.labels.top_tools} letter="C" meta="RANKED · CALL FREQ" gold>
        <table className="dtable">
          <thead>
            <tr>
              <th>#</th>
              <th>{t.table.tool}</th>
              <th className="r">{t.table.calls}</th>
              <th className="r">{t.table.pct}</th>
              <th className="r">{t.table.success}</th>
              <th className="r">{t.table.duration}</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {D.tools.map((tool, i) => (
              <tr key={i}>
                <td className="dim">{String(i+1).padStart(2,'0')}</td>
                <td className="amber">{tool.name}</td>
                <td className="r code">{fmtNum(tool.count)}</td>
                <td className="r dim">{(tool.count/totalCalls*100).toFixed(1)}%</td>
                <td className="r code">{(tool.success*100).toFixed(1)}</td>
                <td className="r code">{tool.durMs} ms</td>
                <td style={{ width: 120 }}>
                  <div style={{ height: 4, background: 'var(--text-faint)', position: 'relative' }}>
                    <div style={{ position: 'absolute', inset: '0 auto 0 0', width: `${(tool.count/D.tools[0].count)*100}%`, background: D.toolColors[i % D.toolColors.length] }} />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    </>
  );
}

// =================================================
// SECTION 03 — TOKEN ANALYTICS
// =================================================
function SectionTokens({ t }) {
  const D = HERMES_DATA;
  const totalAll = D.totals.tokens;
  const remaining = D.openRouter.totalCredits - D.openRouter.totalUsage;
  const costPerM = (D.openRouter.totalUsage / totalAll) * 1_000_000;

  const modelRanking = D.models.map((m) => {
    const tot = D.tokensPerDay.reduce((s, r) => s + r[m.id], 0);
    return { name: m.id, value: tot, pct: (tot / totalAll) * 100, color: m.color, cost: tot * 0.0000005 * (Math.random() * 3 + 2) };
  }).sort((a, b) => b.value - a.value);
  // assign cost more deterministically
  modelRanking.forEach((m, i) => m.cost = (D.openRouter.totalUsage * (m.pct / 100)));

  const tokensByModelStacked = D.tokensPerDay.map(row => ({
    x: row.date,
    series: D.models.map(m => ({ key: m.id, value: row[m.id], color: m.color })),
  }));

  const breakdown = [
    { label: 'INPUT',       value: D.totals.inputTokens,      color: '#F59E0B' }, // amber
    { label: 'OUTPUT',      value: D.totals.outputTokens,     color: '#00D4B4' }, // cyan
    { label: 'CACHE READ',  value: D.totals.cacheReadTokens,  color: '#39D966' }, // green
    { label: 'CACHE WRITE', value: D.totals.cacheWriteTokens, color: '#A855F7' }, // purple
    { label: 'REASONING',   value: D.totals.reasoningTokens,  color: '#E84848' }, // coral
  ];

  return (
    <>
      <div className="stat-grid">
        <StatCard letter="A" eyebrow={t.kpi.tokens} value={fmtCompact(totalAll)} delta={`IN ${Math.round(D.totals.inputTokens/totalAll*100)}% · OUT ${Math.round(D.totals.outputTokens/totalAll*100)}% · CACHE ${Math.round((D.totals.cacheReadTokens+D.totals.cacheWriteTokens)/totalAll*100)}%`} color="amber" barPct={80} />
        <StatCard letter="B" eyebrow={t.kpi.credit_used} value={fmtUsd(D.openRouter.totalUsage)} delta={`${(D.openRouter.totalUsage/D.openRouter.totalCredits*100).toFixed(1)}% / $${D.openRouter.totalCredits.toFixed(0)}`} color="red" barPct={D.openRouter.totalUsage/D.openRouter.totalCredits*100} />
        <StatCard letter="C" eyebrow={t.kpi.credit_remaining} value={fmtUsd(remaining)} delta={`${(remaining/D.openRouter.totalCredits*100).toFixed(0)}% LEFT`} color="green" barPct={(remaining/D.openRouter.totalCredits)*100} barColor="gold" />
        <StatCard letter="D" eyebrow={t.kpi.cost_per_million} value={fmtUsd(costPerM)} delta={`${D.totals.daysActive} ${t.misc.today === 'HOY' ? 'DÍAS' : 'DAYS'} · ${fmtCompact(totalAll/D.totals.daysActive)}/DAY`} color="gold" barPct={70} barColor="gold" />
      </div>

      <Panel label={t.labels.model_ranking} letter="A" meta={`${D.models.length} MODELS · BY TOKENS`} gold>
        <RankList items={modelRanking} t={t} valueFormat={fmtCompact} />
      </Panel>
      <div style={{ height: 14 }} />

      <Panel label={t.labels.daily_consumption} letter="B" meta="14D · STACKED">
        <StackedBar data={tokensByModelStacked} valueFormat={fmtCompact} />
        <Legend items={D.models.map(m => ({ label: m.short, color: m.color, value: D.tokensPerDay.reduce((s,r) => s + r[m.id], 0) }))} withValues valueFormat={fmtCompact} />
      </Panel>
      <div style={{ height: 14 }} />

      <div className="grid-2">
        <Panel label={t.labels.token_breakdown} letter="C" meta="BY TYPE">
          <DonutWithLegend data={breakdown} centerValue={fmtCompact(totalAll)} centerLabel="TOKENS" valueFormat={fmtCompact} />
        </Panel>
        <Panel label={t.labels.cost_by_model} letter="D" meta="USD" gold>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, padding: '4px 0' }}>
            {modelRanking.map((m, i) => (
              <div key={i} style={{ display: 'grid', gridTemplateColumns: '24px 1fr 60px', gap: 10, alignItems: 'center', fontSize: 11 }}>
                <span style={{ fontFamily: 'var(--font-m)', color: 'var(--text-muted)' }}>#{i+1}</span>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ color: 'var(--text)', letterSpacing: '0.05em' }}>{m.name.split('/')[1]}</span>
                  </div>
                  <div style={{ height: 8, background: 'var(--text-faint)', position: 'relative' }}>
                    <div style={{ position: 'absolute', inset: '0 auto 0 0', width: `${(m.cost / modelRanking[0].cost) * 100}%`, background: m.color }} />
                  </div>
                </div>
                <span style={{ fontFamily: 'var(--font-m)', color: 'var(--amber)', textAlign: 'right' }}>{fmtUsd(m.cost)}</span>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <div className="callout">
        <div className="callout-icon">!</div>
        <div className="callout-body">
          <div className="callout-title">{t.misc.mgmt_key}</div>
          <div className="callout-msg">
            {t.misc.mgmt_key_msg.split(/(`[^`]+`)/g).map((part, i) => part.startsWith('`')
              ? <code key={i}>{part.slice(1, -1)}</code>
              : <React.Fragment key={i}>{part}</React.Fragment>
            )}
            {' '}
            <a href="https://openrouter.ai/settings/keys" target="_blank">{t.misc.get_key} →</a>
          </div>
        </div>
      </div>
    </>
  );
}

// =================================================
// SECTION 04 — ERRORS & PERFORMANCE
// =================================================
function SectionErrors({ t }) {
  const D = HERMES_DATA;
  const [filterSource, setFilterSource] = useStateS('all');
  const [filterTool, setFilterTool] = useStateS('all');
  const [filterStatus, setFilterStatus] = useStateS('all');

  const allErrors = D.errors;
  const filtered = useMemoS(() => {
    return allErrors.filter(e => {
      if (filterStatus === 'resolved' && e.unresolved > 0) return false;
      if (filterStatus === 'unresolved' && e.unresolved === 0) return false;
      if (filterSource !== 'all' && !e.sources.includes(filterSource)) return false;
      return true;
    });
  }, [filterSource, filterStatus]);

  const totalErr = allErrors.reduce((s, e) => s + e.total, 0);
  const unresolved = allErrors.reduce((s, e) => s + e.unresolved, 0);
  const toolErrors = allErrors.filter(e => e.sources.includes('tool_call')).reduce((s, e) => s + e.total, 0);
  const sourcesCount = new Set(allErrors.flatMap(e => e.sources.split(','))).size;

  const trendSeries = [
    { key: 'api',       color: '#F59E0B', points: D.errorTrend.map(d => ({ x: d.date, y: d.api })) },        // amber
    { key: 'tool',      color: '#00D4B4', points: D.errorTrend.map(d => ({ x: d.date, y: d.tool })) },       // cyan
    { key: 'agent',     color: '#A855F7', points: D.errorTrend.map(d => ({ x: d.date, y: d.agent })) },      // purple
    { key: 'collector', color: '#E84848', points: D.errorTrend.map(d => ({ x: d.date, y: d.collector })) }, // coral
  ];

  const maxPrio = Math.max(...filtered.map(e => e.priority), 1);

  return (
    <>
      <Panel label={t.labels.filters} letter="A" meta={filtered.length < allErrors.length ? `${filtered.length} ${t.misc.filtered_of} ${allErrors.length}` : `${allErrors.length} TOT`}>
        <div className="filter-bar">
          <div className="filter-item">
            <label>{t.misc.source}</label>
            <select value={filterSource} onChange={e => setFilterSource(e.target.value)}>
              <option value="all">{t.misc.all}</option>
              <option value="api">API</option>
              <option value="tool_call">TOOL_CALL</option>
              <option value="agent">AGENT</option>
              <option value="collector">COLLECTOR</option>
            </select>
          </div>
          <div className="filter-item">
            <label>{t.misc.type}</label>
            <select disabled><option>{t.misc.all}</option></select>
          </div>
          <div className="filter-item">
            <label>{t.misc.tool}</label>
            <select disabled><option>{t.misc.all}</option></select>
          </div>
          <div className="filter-item">
            <label>{t.misc.resolved_all}</label>
            <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
              <option value="all">{t.misc.all}</option>
              <option value="unresolved">{t.misc.resolved_no}</option>
              <option value="resolved">{t.misc.resolved_yes}</option>
            </select>
          </div>
          <div className="filter-count">{filtered.reduce((s,e) => s + e.total, 0)} EVTS</div>
        </div>
      </Panel>
      <div style={{ height: 14 }} />

      <div className="stat-grid">
        <StatCard letter="A" eyebrow={t.kpi.errors_total} value={fmtNum(totalErr)} delta={`${allErrors.length} PATTERNS`} color="red" barPct={70} />
        <StatCard letter="B" eyebrow={t.kpi.sources_count} value={sourcesCount} delta="API · TOOL · AGENT · COL" color="amber" barPct={80} />
        <StatCard letter="C" eyebrow={t.kpi.unresolved} value={unresolved} delta={`${((unresolved/totalErr)*100).toFixed(1)}% OF TOTAL`} color="amber" barPct={(unresolved/totalErr)*100} />
        <StatCard letter="D" eyebrow={t.kpi.tool_errors} value={toolErrors} delta={`${((toolErrors/totalErr)*100).toFixed(0)}% FROM TOOLS`} color="gold" barPct={(toolErrors/totalErr)*100} barColor="gold" />
      </div>

      <Panel label={t.labels.clustering} letter="A" meta={`TOP ${filtered.length} · BY PRIORITY`} gold>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {filtered.sort((a, b) => b.priority - a.priority).map((e, i) => {
            const danger = e.priority >= 30;
            const warn = e.priority >= 15 && !danger;
            const cls = danger ? 'danger' : warn ? 'warn' : '';
            return (
              <div key={i} className={`cluster-row ${cls}`}>
                <span className={`cluster-prio ${danger ? 'danger' : ''}`}>{e.priority}</span>
                <div>
                  <div className="cluster-msg">{e.pattern}</div>
                  <div className="cluster-meta">{e.sources.toUpperCase()} · {e.firstSeen} → {e.lastSeen}</div>
                </div>
                <span className="cluster-num">{e.total}</span>
                <span className={`cluster-num ${e.unresolved > 0 ? 'red' : ''}`}>{e.unresolved}</span>
                <div className="cluster-bar-cell">
                  <div className={`cluster-bar-fill ${danger ? 'danger' : ''}`} style={{ width: `${(e.priority / maxPrio) * 100}%` }} />
                </div>
              </div>
            );
          })}
        </div>
      </Panel>
      <div style={{ height: 14 }} />

      <Panel label={t.labels.error_trend} letter="B" meta="14D · BY SOURCE">
        <div className="line-chart-wrap">
          <LineChart series={trendSeries} xLabels={D.errorTrend.map(d => d.date)} />
        </div>
        <Legend items={[
          { label: 'API',       color: '#F59E0B' },
          { label: 'TOOL',      color: '#00D4B4' },
          { label: 'AGENT',     color: '#A855F7' },
          { label: 'COLLECTOR', color: '#E84848' },
        ]} />
      </Panel>
    </>
  );
}

// =================================================
// SECTION 05 — SYSTEM PERFORMANCE
// =================================================
function SectionSystem({ t }) {
  const D = HERMES_DATA;

  const heatmapMax = Math.max(...D.heatmap.flat());
    const cellColor = (v) => {
    const intensity = v / heatmapMax;
    // Vivid 6-stop heat scale: navy → blue → teal → gold → orange → red
    if (intensity < 0.05) return '#0a1e3d';
    if (intensity < 0.15) return '#0d47a1';
    if (intensity < 0.3)  return '#00897b';
    if (intensity < 0.5)  return '#f9a825';
    if (intensity < 0.7)  return '#ef6c00';
    if (intensity < 0.85) return '#c62828';
    return '#b71c1c';
  };
    const cellText = (v) => {
    const intensity = v / heatmapMax;
    if (intensity < 0.15) return '#9e9e9e';
    if (intensity < 0.3)  return '#ffffff';
    return '#ffffff';
  };

  // Sessions per hour of day
  const hourly = [...Array(24)].map((_, h) => {
    const seed = h * 13;
    const noise = Math.sin(seed) * 10000 - Math.floor(Math.sin(seed) * 10000);
    const base = h >= 9 && h <= 23 ? 4 + Math.sin((h-12)/4) * 3 : 0.5;
    return { hour: h, count: Math.max(0, Math.round(base * (0.6 + noise * 0.8))) };
  });
  const maxHourly = Math.max(...hourly.map(h => h.count));

  // Daily error rate trend (line)
  const errorRateSeries = [{
    key: 'rate',
    color: '#00BCD4',
    points: D.errorTrend.map(d => ({ x: d.date, y: +(d.api + d.tool + d.agent + d.collector).toFixed(0) })),
  }];

  // Latency dist (fake)
  const latencyBuckets = [
    { label: '< 50ms',     pct: 22, color: '#39D966' }, // green - fastest
    { label: '50-200ms',   pct: 41, color: '#00D4B4' }, // cyan
    { label: '200-500ms',  pct: 24, color: '#F59E0B' }, // amber
    { label: '500ms-1s',   pct: 9,  color: '#EAB308' }, // gold
    { label: '1-3s',       pct: 3,  color: '#A855F7' }, // purple
    { label: '> 3s',       pct: 1,  color: '#E84848' }, // coral - slowest
  ];

  return (
    <>
      <div className="stat-grid">
        <StatCard letter="A" eyebrow={t.kpi.uptime} value="99.84" unit="%" delta="14D · 32 MIN DOWN" color="green" barPct={99.84} />
        <StatCard letter="B" eyebrow={t.kpi.avg_latency} value="187" unit="ms" delta="P95 = 612ms" color="amber" barPct={45} />
        <StatCard letter="C" eyebrow={t.kpi.error_rate} value="3.2" unit="%" delta="98 / 3,087 OPS" color="gold" barPct={32} barColor="gold" />
        <StatCard letter="D" eyebrow={t.kpi.cron_status} value="OK" delta={`LAST: ${D.collector.lastRun.split(' ')[1]}`} color="green" barPct={100} />
      </div>

      <Panel label={t.labels.heatmap} letter="A" meta={`${D.heatmapModels.length} × ${D.heatmapTools.length} · ERROR %`} gold>
        <div className="heatmap-grid" style={{ gridTemplateColumns: `100px repeat(${D.heatmapTools.length}, 1fr)` }}>
          <div />
          {D.heatmapTools.map((tl, i) => (
            <div key={i} className="heatmap-header">{tl}</div>
          ))}
          {D.heatmapModels.map((m, mi) => (
            <React.Fragment key={mi}>
              <div className="heatmap-rowlabel">{m}</div>
              {D.heatmap[mi].map((v, ti) => (
                <div
                  key={ti}
                  className="heatmap-cell"
                  style={{ background: cellColor(v), color: cellText(v) }}
                  title={`${m} · ${D.heatmapTools[ti]} · ${(v*100).toFixed(1)}%`}
                >
                  {(v*100).toFixed(1)}%
                </div>
              ))}
            </React.Fragment>
          ))}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 18, fontSize: 11, color: 'var(--text-muted)', letterSpacing: '0.15em' }}>
          <span style={{ fontWeight: 700, color: 'var(--gold)' }}>SCALE</span>
          <div style={{ display: 'flex', flex: 1, gap: 2, borderRadius: 4, overflow: 'hidden' }}>
            {[0.05, 0.15, 0.3, 0.5, 0.7, 0.85, 1].map((v, i) => (
              <div key={i} style={{ flex: 1, height: 14, background: cellColor(v * heatmapMax) }} />
            ))}
          </div>
          <span style={{ fontFamily: 'var(--font-m)', color: 'var(--text-dim)', fontSize: 10 }}>0%</span>
          <span style={{ fontFamily: 'var(--font-m)', color: 'var(--red)', fontSize: 10 }}>{(heatmapMax*100).toFixed(1)}%</span>
        </div>
      </Panel>
      <div style={{ height: 14 }} />

      <div className="grid-2">
        <Panel label={t.labels.daily_error_rate} letter="B" meta="14D">
          <div className="line-chart-wrap">
            <LineChart series={errorRateSeries} xLabels={D.errorTrend.map(d => d.date)} />
          </div>
        </Panel>

        <Panel label={t.labels.latency_dist} letter="C" meta="P50 187ms · P95 612ms" gold>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {latencyBuckets.map((b, i) => (
              <div key={i} style={{ display: 'grid', gridTemplateColumns: '80px 1fr 40px', gap: 10, alignItems: 'center', fontSize: 11 }}>
                <span style={{ fontFamily: 'var(--font-m)', color: 'var(--text-dim)' }}>{b.label}</span>
                <div style={{ height: 10, background: 'var(--text-faint)', position: 'relative' }}>
                  <div style={{ position: 'absolute', inset: '0 auto 0 0', width: `${b.pct}%`, background: b.color, boxShadow: `0 0 6px ${b.color}40` }} />
                </div>
                <span style={{ fontFamily: 'var(--font-m)', color: 'var(--code-green)', textAlign: 'right' }}>{b.pct}%</span>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <Panel label={t.labels.sessions_per_hour} letter="D" meta="24H · UTC+1">
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 4, height: 140, borderBottom: '1px solid var(--amber-border)', paddingBottom: 1 }}>
          {hourly.map((h, i) => (
            <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100%', justifyContent: 'flex-end' }}>
              <div style={{
                width: '100%',
                height: `${(h.count / maxHourly) * 100}%`,
                background: h.count >= maxHourly * 0.7 ? '#00BCD4' : h.count >= maxHourly * 0.5 ? '#00A3CC' : h.count >= maxHourly * 0.3 ? '#00897B' : '#006064',
                boxShadow: h.count >= maxHourly * 0.7 ? '0 0 8px rgba(0,188,212,0.4)' : 'none',
              }} />
            </div>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 4, paddingTop: 4 }}>
          {hourly.map((h, i) => (
            <div key={i} style={{ flex: 1, fontFamily: 'var(--font-m)', fontSize: 9, color: 'var(--text-muted)', textAlign: 'center' }}>
              {i % 3 === 0 ? String(i).padStart(2, '0') : ''}
            </div>
          ))}
        </div>
      </Panel>
    </>
  );
}

Object.assign(window, { SectionOverview, SectionTools, SectionTokens, SectionErrors, SectionSystem });
