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
const fmtDuration = (s) => {
  if (!s || s <= 0) return '0s';
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = Math.floor(s % 60);
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${sec}s`;
  return `${sec}s`;
};
const fmtEur = (v) => `€${v.toFixed(2)}`;
const pct = (value, total, digits = 0) => total > 0 ? Number(((value / total) * 100).toFixed(digits)) : 0;

// =================================================
// SECTION 01 — OVERVIEW
// =================================================
function SectionOverview({ t }) {
  const D = HERMES_DATA;
  const openRouterUsagePct = pct(D.openRouter.totalUsage, D.openRouter.totalCredits, 0);
  const tokensByModelStacked = D.tokensPerDay.map(row => ({
    x: row.date,
    series: D.models.map(m => ({ key: m.id, value: row[m.id], color: m.color })),
  }));
  const sourceDonut = D.sources.map(s => ({ label: s.name.toUpperCase(), value: s.count, color: s.color }));
  const modelLegend = D.models.map(m => {
    const tot = D.tokensPerDay.reduce((s, r) => s + (r[m.id] || 0), 0);
    return { label: m.short, color: m.color, value: tot };
  });

  return (
    <>
      <div className="stat-grid">
        <StatCard letter="A" eyebrow={t.kpi.sessions} value={fmtNum(D.totals.sessions)} unit="SES" delta={`${D.totals.daysActive} ${t.misc.today === 'HOY' ? 'DÍAS ACTIVOS' : 'ACTIVE DAYS'}`} color="amber" barPct={78} />
        <StatCard letter="B" eyebrow={t.kpi.tokens} value={fmtCompact(D.totals.tokens)} delta={`INPUT ${pct(D.totals.inputTokens, D.totals.tokens)}% · OUTPUT ${pct(D.totals.outputTokens, D.totals.tokens)}%`} color="gold" barPct={65} barColor="gold" />
        <StatCard letter="C" eyebrow={t.kpi.openrouter_billing} value={fmtUsd(D.openRouter.totalUsage)} unit="USD" delta={`${fmtUsd(D.openRouter.today)} ${t.misc.today} · ${fmtUsd(D.openRouter.month)} ${t.misc.month}`} color="green" barPct={openRouterUsagePct} />
        <StatCard letter="D" eyebrow={t.kpi.models} value={D.totals.models} delta={`${D.sources.length} ${t.misc.source.toUpperCase()}S · ${D.tools.length} TOOLS`} color="amber" barPct={(D.totals.models/10)*100} />
      </div>

      <div className="grid-2">
        <Panel label={t.labels.global_telemetry} letter="E" meta={t.misc.all_providers}>
          <div className="mini-kpi-row">
            <div className="mini-kpi"><div className="label">{t.kpi.sessions}</div><div className="val">{fmtNum(D.totals.sessions)}</div></div>
            <div className="mini-kpi"><div className="label">{t.kpi.tokens}</div><div className="val">{fmtCompact(D.totals.tokens)}</div></div>
            <div className="mini-kpi"><div className="label">{t.kpi.tool_calls}</div><div className="val">{fmtNum(D.totals.toolCalls || 0)}</div></div>
            <div className="mini-kpi"><div className="label">{t.kpi.models}</div><div className="val">{fmtNum(D.totals.models)}</div></div>
          </div>
        </Panel>
        <Panel label={t.labels.openrouter_billing_scope} letter="F" meta={t.misc.openrouter_only} gold>
          <div className="mini-kpi-row">
            <div className="mini-kpi"><div className="label">{t.misc.total}</div><div className="val">{fmtUsd(D.openRouter.totalUsage)}</div></div>
            <div className="mini-kpi"><div className="label">{t.misc.today}</div><div className="val">{fmtUsd(D.openRouter.today)}</div></div>
            <div className="mini-kpi"><div className="label">{t.misc.week}</div><div className="val">{fmtUsd(D.openRouter.week)}</div></div>
            <div className="mini-kpi"><div className="label">{t.misc.month}</div><div className="val">{fmtUsd(D.openRouter.month)}</div></div>
          </div>
        </Panel>
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
                <td className="code">{s.id}</td>
                <td>{s.date}</td>
                <td className="amber">{s.modelShort}</td>
                <td>{s.source}</td>
                <td className="r code">{s.messages}</td>
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
  const toolDaily = D.days.map((date) => ({
    x: date,
    series: topTools.map((tool, ti) => {
      const dayCount = D.toolDaily && D.toolDaily[date] ? D.toolDaily[date][tool.name] || 0 : 0;
      return { key: tool.name, value: dayCount, color: D.toolColors[ti] };
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
              <tr key={i} style={{animation: 'statFadeIn 300ms ease both', animationDelay: (i*20)+'ms'}}>
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
  const totalAll = D.totals.tokens || 0;
  const remaining = Math.max((D.openRouter.totalCredits || 0) - (D.openRouter.totalUsage || 0), 0);
  const billedTokenTotal = D.modelCosts.reduce((sum, m) => sum + (m.input_tokens || 0) + (m.output_tokens || 0) + (m.cache_read_tokens || 0) + (m.reasoning_tokens || 0), 0);
  const outsideBilling = Math.max(totalAll - billedTokenTotal, 0);
  const coveragePct = pct(billedTokenTotal, totalAll, 0);
  const costPerM = billedTokenTotal > 0 ? (D.openRouter.totalUsage / billedTokenTotal) * 1_000_000 : 0;

  const modelRanking = D.models.map((m) => {
    const globalTokens = D.tokensPerDay.reduce((s, r) => s + (r[m.id] || 0), 0);
    const mc = D.modelCosts.find(c => c.model === m.id);
    const cost = mc ? mc.real_cost : 0;
    return { name: m.id, value: globalTokens, pct: pct(globalTokens, totalAll, 1), color: m.color, cost: cost };
  }).sort((a, b) => b.value - a.value);

  const tokensByModelStacked = D.tokensPerDay.map(row => ({
    x: row.date,
    series: D.models.map(m => ({ key: m.id, value: row[m.id], color: m.color })),
  }));

  const breakdown = [
    { label: 'INPUT',       value: D.totals.inputTokens,      color: '#00D4B4' },
    { label: 'OUTPUT',      value: D.totals.outputTokens,     color: '#E84848' },
    { label: 'CACHE READ',  value: D.totals.cacheReadTokens,  color: '#A855F7' },
    { label: 'CACHE WRITE', value: D.totals.cacheWriteTokens, color: '#F59E0B' },
    { label: 'REASONING',   value: D.totals.reasoningTokens,  color: '#06B6D4' },
  ].filter(d => d.value > 0);

  return (
    <>
      <div className="stat-grid">
        <StatCard letter="A" eyebrow={t.kpi.tokens} value={fmtCompact(totalAll)} delta={`IN ${pct(D.totals.inputTokens, totalAll)}% · OUT ${pct(D.totals.outputTokens, totalAll)}% · CACHE ${pct(D.totals.cacheReadTokens + D.totals.cacheWriteTokens, totalAll)}%`} color="amber" barPct={80} />
        <StatCard letter="B" eyebrow={t.kpi.billed_tokens} value={fmtCompact(billedTokenTotal)} delta={`${coveragePct}% ${t.misc.tracked_share} · ${fmtCompact(outsideBilling)} ${t.misc.outside_openrouter}`} color="gold" barPct={coveragePct} barColor="gold" />
        <StatCard letter="C" eyebrow={t.kpi.credit_used} value={fmtUsd(D.openRouter.totalUsage)} delta={`${fmtUsd(D.openRouter.month)} ${t.misc.month} · ${fmtUsd(D.openRouter.week)} ${t.misc.week}`} color="red" barPct={pct(D.openRouter.totalUsage, D.openRouter.totalCredits, 1)} />
        <StatCard letter="D" eyebrow={t.kpi.cost_per_million} value={fmtUsd(costPerM)} delta={`${fmtCompact(Math.round(totalAll / Math.max(D.totals.daysActive || 1, 1)))} ${t.misc.avg_per_day} · ${t.misc.openrouter_only}`} color="gold" barPct={70} barColor="gold" />
      </div>

      <div className="grid-2">
        <Panel label={t.labels.global_telemetry} letter="A" meta={t.misc.all_providers}>
          <div className="mini-kpi-row">
            <div className="mini-kpi"><div className="label">{t.kpi.tokens}</div><div className="val">{fmtCompact(totalAll)}</div></div>
            <div className="mini-kpi"><div className="label">INPUT</div><div className="val">{fmtCompact(D.totals.inputTokens)}</div></div>
            <div className="mini-kpi"><div className="label">OUTPUT</div><div className="val">{fmtCompact(D.totals.outputTokens)}</div></div>
            <div className="mini-kpi"><div className="label">{t.kpi.models}</div><div className="val">{fmtNum(D.totals.models)}</div></div>
          </div>
        </Panel>
        <Panel label={t.labels.openrouter_billing_scope} letter="B" meta={t.misc.openrouter_only} gold>
          <div className="mini-kpi-row">
            <div className="mini-kpi"><div className="label">{t.kpi.billed_tokens}</div><div className="val">{fmtCompact(billedTokenTotal)}</div></div>
            <div className="mini-kpi"><div className="label">{t.kpi.credit_used}</div><div className="val">{fmtUsd(D.openRouter.totalUsage)}</div></div>
            <div className="mini-kpi"><div className="label">{t.kpi.credit_remaining}</div><div className="val">{fmtUsd(remaining)}</div></div>
            <div className="mini-kpi"><div className="label">{t.misc.tracked_share}</div><div className="val">{coveragePct}%</div></div>
          </div>
        </Panel>
      </div>

      <Panel label={t.labels.model_ranking} letter="C" meta={`${D.models.length} MODELS · GLOBAL TOKENS`} gold>
        <RankList items={modelRanking} t={t} valueFormat={fmtCompact} />
      </Panel>
      <div style={{ height: 14 }} />

      <Panel label={t.labels.daily_consumption} letter="D" meta="14D · STACKED">
        <StackedBar data={tokensByModelStacked} valueFormat={fmtCompact} />
        <Legend items={D.models.map(m => ({ label: m.short, color: m.color, value: D.tokensPerDay.reduce((s,r) => s + (r[m.id] || 0), 0) }))} withValues valueFormat={fmtCompact} />
      </Panel>
      <div style={{ height: 14 }} />

      <div className="grid-2">
        <Panel label={t.labels.token_breakdown} letter="E" meta="GLOBAL BY TYPE">
          <DonutWithLegend data={breakdown} centerValue={fmtCompact(totalAll)} centerLabel="TOKENS" valueFormat={fmtCompact} />
        </Panel>
        <Panel label={t.labels.cost_by_model} letter="F" meta="USD · OPENROUTER ONLY" gold>
          <DonutWithLegend data={modelRanking.filter(m => m.cost > 0).map((m) => ({
            label: m.name.split('/').pop(),
            value: m.cost,
            color: m.color,
          }))} centerValue={fmtUsd(modelRanking.reduce((s, m) => s + m.cost, 0))} centerLabel="TOTAL" valueFormat={(v) => fmtUsd(v)} />
        </Panel>
      </div>

      <div className="callout">
        <div className="callout-icon">!</div>
        <div className="callout-body">
          <div className="callout-title">{t.misc.mgmt_key}</div>
          <div className="callout-msg">
            {t.misc.mgmt_key_msg.split(/(`[^`]+`)/g).map((part, i) => part.startsWith('`') && part.endsWith('`')
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


  const allErrors = D.errors;
  const filtered = useMemoS(() => {
    return allErrors.filter(e => {
      if (filterSource !== 'all' && !e.sources.includes(filterSource)) return false;
      if (filterTool !== 'all' && !(e.tools || '').includes(filterTool)) return false;
      return true;
    });
  }, [filterSource, filterTool]);

  const totalErr = allErrors.reduce((s, e) => s + e.total, 0);
  const sourcesCount = new Set(allErrors.flatMap(e => e.sources.split(','))).size;

  const trendSeries = [
    { key: 'tool_failure',   color: '#E84848', points: D.errorTrend.map(d => ({ x: d.date, y: d.tool_failure })) },   // coral
    { key: 'model_behavior', color: '#A855F7', points: D.errorTrend.map(d => ({ x: d.date, y: d.model_behavior })) }, // purple
    { key: 'provider',       color: '#FBBF24', points: D.errorTrend.map(d => ({ x: d.date, y: d.provider })) },       // gold
    { key: 'user_interrupt', color: '#06B6D4', points: D.errorTrend.map(d => ({ x: d.date, y: d.user_interrupt })) }, // sky
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
              <option value="state_db">STATE_DB</option>
              <option value="state_db_events">EVENTS</option>
            </select>
          </div>
          <div className="filter-item">
            <label>{t.misc.type}</label>
            <select value={filterSource} onChange={e => setFilterSource(e.target.value)}><option value="all">{t.misc.all}</option></select>
          </div>
          <div className="filter-item">
            <label>{t.misc.tool}</label>
            <select value={filterSource} onChange={e => setFilterSource(e.target.value)}><option value="all">{t.misc.all}</option></select>
          </div>

          <div className="filter-count">{filtered.reduce((s,e) => s + e.total, 0)} EVTS</div>
        </div>
      </Panel>
      <div style={{ height: 14 }} />

      <div className="stat-grid">
        <StatCard letter="A" eyebrow={t.kpi.errors_total} value={fmtNum(totalErr)} delta={`${allErrors.length} PATTERNS`} color="red" barPct={70} />
        <StatCard letter="B" eyebrow={t.kpi.sources_count} value={sourcesCount} delta="STATE_DB · EVENTS" color="cyan" barPct={80} />
        <StatCard letter="C" eyebrow={t.kpi.models} value={D.models.length} delta="MODELS" color="gold" barPct={80} barColor="gold" />
        <StatCard letter="D" eyebrow={t.kpi.success_rate} value={(totalErr > 0 ? 100 : 0).toFixed(1)} unit="%" delta="ERROR FREE SES" color="green" barPct={100} />
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
                <span className="cluster-num" style={{color:'var(--text-muted)'}}>—</span>
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
          { label: 'TOOL FAILURE',  color: '#E84848' },
          { label: 'MODEL BEHAVIOR',color: '#A855F7' },
          { label: 'PROVIDER',      color: '#FBBF24' },
          { label: 'USER INTERRUPT',color: '#06B6D4' },
        ]} />
      </Panel>
    </>
  );
}

// =================================================
// =================================================
// SECTION 05 — SESSION ANALYTICS
// =================================================
function SectionSessions({ t }) {
  const D = HERMES_DATA;
  const S = D.sessionMetrics;
  const AG = D.agentLog || {};

  if (!S || !S.totalSessions) {
    return <Panel label={t.labels.per_session} letter="A" meta="NO DATA"><div className="dim" style={{padding:20,textAlign:'center'}}>No session data available yet.</div></Panel>;
  }

  const sessionsPerDay = S.sessionsPerDay || [];
  const maxSpd = Math.max(...sessionsPerDay.map(d => d.count), 1);

  const modelsArr = D.models || [];
  const modelDist = (S.modelUsage || []).map((m, i) => ({
    label: m.model.split('/').pop(), value: m.count,
    color: modelsArr.length > 0 ? modelsArr[i % modelsArr.length].color : '#00D4B4',
  }));

  const modelStr = D.overviewExtras?.activeModels?.join(', ') || '—';

  return (
    <>
      <div className="stat-grid">
        <StatCard letter="A" eyebrow={t.kpi.avg_duration} value={fmtDuration(S.avgDurationS)} delta={`${D.totals?.sessions || S.totalSessions} ${t.misc.sessions}`} color="cyan" barPct={70} />
        <StatCard letter="B" eyebrow={t.kpi.avg_tokens_per_session} value={fmtCompact(S.avgTokens)} delta={t.kpi.per_session} color="amber" barPct={85} />
        <StatCard letter="C" eyebrow={t.kpi.throughput_per_session} value={S.avgThroughput} unit={t.kpi.throughput_label} delta={`PEAK · ${Math.round(S.avgThroughput * 2.5)}`} color="green" barPct={60} />
        <StatCard letter="D" eyebrow={t.kpi.avg_tools_per_session} value={S.avgTools} delta={`${S.avgApiCalls} API`} color="gold" barPct={75} barColor="gold" />
      </div>

      <div className="grid-2-1">
        <Panel label={t.labels.sessions_per_day} letter="A" meta={`${sessionsPerDay.length}D · PEAK ${maxSpd}`} gold>
          <div className="stack-bar-chart" style={{display:'flex',alignItems:'flex-end',gap:4,height:200,paddingBottom:1,borderBottom:'1px solid var(--amber-border)'}}>
            {sessionsPerDay.map((d, i) => (
              <div key={i} style={{flex:1,display:'flex',flexDirection:'column',alignItems:'center',height:'100%',justifyContent:'flex-end',minWidth:0}}>
                <span style={{fontFamily:'var(--font-m)',fontSize:9,color:'var(--text-dim)',marginBottom:3}}>{d.count}</span>
                <div style={{width:'100%',height:`${(d.count/maxSpd)*100}%`,background:'linear-gradient(180deg, #00D4B4, #00897B)',borderRadius:'2px 2px 0 0',transition:'filter 0.12s',minHeight:d.count>0?2:0}} onMouseEnter={e=>e.target.style.filter='brightness(1.3)'} onMouseLeave={e=>e.target.style.filter='none'} />
                <span style={{fontFamily:'var(--font-m)',fontSize:9,color:'var(--text-muted)',marginTop:3,whiteSpace:'nowrap',overflow:'hidden',textOverflow:'ellipsis',maxWidth:36}}>{d.day.slice(-5)}</span>
              </div>
            ))}
          </div>
        </Panel>

        <Panel label={t.labels.models_used} letter="B" meta={`${S.modelUsage.length} MODELS`}>
          <div style={{display:'flex',flexDirection:'column',gap:4,padding:'4px 0'}}>
            {modelDist.slice(0, 6).map((m, i) => (
              <div key={i} style={{display:'flex',alignItems:'center',gap:8,fontSize:11}}>
                <span style={{width:8,height:8,borderRadius:'50%',background:m.color}} />
                <span style={{flex:1,fontFamily:'var(--font-m)',color:'var(--text)',letterSpacing:'0.03em'}}>{m.label}</span>
                <span style={{fontFamily:'var(--font-m)',color:'var(--text-muted)'}}>{m.value} {t.misc.sessions}</span>
              </div>
            ))}
          </div>
          {D.overviewExtras?.activeModels?.length > 0 && (
            <div style={{marginTop:10,padding:'8px 10px',background:'var(--bg-card)',borderRadius:4,fontSize:10,color:'var(--text-muted)',wordBreak:'break-all',overflowWrap:'break-word',maxHeight:60,overflowY:'auto'}}>
              <span style={{color:'var(--teal)',fontWeight:600}}>{t.kpi.active_models}:</span> {modelStr}
            </div>
          )}
        </Panel>
      </div>

      <Panel label={t.labels.session_duration} letter="C" meta={`TOKENS · MESSAGES · API CALLS`} gold>
        <div style={{display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:12,padding:'8px 0'}}>
          <div style={{textAlign:'center'}}>
            <div style={{fontFamily:'var(--font-m)',fontSize:28,color:'var(--teal)'}}>{fmtCompact(S.avgTokens)}</div>
            <div style={{fontSize:10,color:'var(--text-muted)',marginTop:2}}>{t.kpi.tokens} / {t.misc.sessions}</div>
          </div>
          <div style={{textAlign:'center'}}>
            <div style={{fontFamily:'var(--font-m)',fontSize:28,color:'var(--cyan)'}}>{S.avgMessages}</div>
            <div style={{fontSize:10,color:'var(--text-muted)',marginTop:2}}>{t.misc.msgs} / {t.misc.sessions}</div>
          </div>
          <div style={{textAlign:'center'}}>
            <div style={{fontFamily:'var(--font-m)',fontSize:28,color:'var(--green)'}}>{S.avgApiCalls}</div>
            <div style={{fontSize:10,color:'var(--text-muted)',marginTop:2}}>{t.kpi.calls} / {t.misc.sessions}</div>
          </div>
        </div>
      </Panel>
    </>
  );
}

// =================================================
// SECTION 06 — SYSTEM PERFORMANCE
// =================================================
function SectionSystem({ t }) {
  const D = HERMES_DATA;
  const SH = D.systemHealth;
  const AG = D.agentLog || {};

  const heatmapMax = Math.max(...(D.heatmap.flat() || [0]), 1);
  const cellColor = (v) => {
    const intensity = v / heatmapMax;
    if (intensity < 0.05) return '#0a1e3d';
    if (intensity < 0.15) return '#1565C0';
    if (intensity < 0.3)  return '#00ACC1';
    if (intensity < 0.5)  return '#8E24AA';
    if (intensity < 0.70) return '#E64A19';
    if (intensity < 0.85) return '#D32F2F';
    return '#B71C1C';
  };
  const cellText = (v) => {
    const intensity = v / heatmapMax;
    return intensity < 0.25 ? '#9e9e9e' : '#ffffff';
  };

  // Sessions per hour from real data
  const hourly = D.sessionMetrics?.sessionsPerDay?.length
    ? (() => {
        // Extract hour patterns from session analytics
        const hours = Array(24).fill(0);
        let total = 0;
        D.recentSessions?.forEach(s => {
          const h = new Date(s.started).getHours();
          if (!isNaN(h)) { hours[h]++; total++; }
        });
        return hours.map((count, hour) => ({ hour, count, pct: total ? count / total : 0 }));
      })()
    : Array(24).fill(0).map((_, h) => ({ hour: h, count: 0, pct: 0 }));
  const maxHourly = Math.max(...hourly.map(h => h.count), 1);
  const nowH = new Date().getHours();

  // Error rate trend from systemHealth
  const errorRateSeries = [{
    key: 'errorRate',
    color: '#E84848',
    points: (SH.errorRateTrend || []).map(d => ({ x: d.date, y: d.errorRate })),
  }];

  return (
    <>
      <div className="stat-grid">
        <StatCard letter="A" eyebrow={t.kpi.global_throughput} value={SH.globalThroughput} unit={t.kpi.throughput_label} delta={`${SH.totalSessions} ${t.misc.sessions}`} color="cyan" barPct={75} />
        <StatCard letter="B" eyebrow={t.kpi.errors_total} value={SH.failedToolCalls} delta={`${SH.errorRate} / ${t.misc.sessions}`} color="red" barPct={Math.min(SH.errorRate * 10, 100)} />
        <StatCard letter="C" eyebrow={t.kpi.fallback_rate} value={SH.fallbackRate} delta={`${SH.fallbackCount} FALLBACKS · ${SH.sessionResetRate}% ${t.kpi.session_reset_rate}`} color="gold" barPct={Math.min(SH.fallbackRate*10, 100)} barColor="gold" />
        <StatCard letter="D" eyebrow={t.kpi.cron_status} value={SH.activeSessions > 0 ? `${SH.activeSessions} ACT` : 'OK'} delta={`${t.kpi.collector_status}: ${D.collector.lastRun.split(' ')[1] || D.collector.lastRun}`} color="green" barPct={100} />
      </div>

      {(D.heatmapModels?.length > 0 && D.heatmapTools?.length > 0) && (
        <Panel label={t.labels.heatmap} letter="A" meta={`${D.heatmapModels.length} × ${D.heatmapTools.length} · ERROR %`} gold>
          <div className="heatmap-grid" style={{ gridTemplateColumns: `100px repeat(${D.heatmapTools.length}, 1fr)` }}>
            <div />
            {D.heatmapTools.map((tl, i) => (
              <div key={i} className="heatmap-header">{tl}</div>
            ))}
            {D.heatmapModels.map((m, mi) => (
              <React.Fragment key={mi}>
                <div className="heatmap-rowlabel">{m}</div>
                {(D.heatmap[mi] || []).map((v, ti) => (
                  <div key={ti} className="heatmap-cell"
                    title={`${m} · ${D.heatmapTools[ti]} · ${(v*100).toFixed(1)}%`}
                    style={{ background: cellColor(v * heatmapMax) }}>
                    <span style={{ fontFamily: 'var(--font-m)', color: cellText(v * heatmapMax), fontSize: 11, fontWeight: 600 }}>
                      {(v*100).toFixed(1)}%
                    </span>
                  </div>
                ))}
              </React.Fragment>
            ))}
          </div>
        </Panel>
      )}

      {AG.totalResponses > 0 && (
        <div className="grid-2">
          <Panel label={t.kpi.avg_response_time} letter="B" meta={`${AG.totalResponses} RESPONSES`} gold>
            <div style={{display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:8,padding:'8px 0'}}>
              <div style={{textAlign:'center'}}>
                <div style={{fontFamily:'var(--font-m)',fontSize:22,color:'var(--teal)'}}>{AG.medianTime}s</div>
                <div style={{fontSize:9,color:'var(--text-muted)'}}>{t.kpi.median_response_time}</div>
              </div>
              <div style={{textAlign:'center'}}>
                <div style={{fontFamily:'var(--font-m)',fontSize:22,color:'var(--cyan)'}}>{AG.avgTime}s</div>
                <div style={{fontSize:9,color:'var(--text-muted)'}}>{t.kpi.avg_response_time}</div>
              </div>
              <div style={{textAlign:'center'}}>
                <div style={{fontFamily:'var(--font-m)',fontSize:22,color:'var(--red)'}}>{AG.p95Time}s</div>
                <div style={{fontSize:9,color:'var(--text-muted)'}}>{t.kpi.p95_response_time}</div>
              </div>
            </div>
          </Panel>

          {SH.errorRateTrend?.length > 0 && (
            <Panel label={t.labels.error_trend} letter="C" meta={`${SH.errorRate}% LATEST`}>
              <div style={{display:'flex',flexDirection:'column',gap:4,padding:'4px 0'}}>
                {[...SH.errorRateTrend].reverse().slice(0, 10).reverse().map((d, i) => (
                  <div key={i} style={{display:'flex',alignItems:'center',gap:8,fontSize:10}}>
                    <span style={{width:50,fontFamily:'var(--font-m)',color:'var(--text-muted)'}}>{d.date}</span>
                    <div style={{flex:1,height:12,background:'var(--text-faint)',position:'relative'}}>
                      <div style={{position:'absolute',inset:'0 auto 0 0',width:`${d.errorRate}%`,maxWidth:'100%',
                        background:d.errorRate > 30 ? '#E84848' : d.errorRate > 15 ? '#00D4B4' : '#39D966',
                        borderRadius:2}} />
                    </div>
                    <span style={{width:40,textAlign:'right',fontFamily:'var(--font-m)',color:`var(--${d.errorRate > 30 ? 'red' : d.errorRate > 15 ? 'amber' : 'green'})`}}>{d.errorRate}%</span>
                  </div>
                ))}
              </div>
            </Panel>
          )}
        </div>
      )}

      {hourly.some(h => h.count > 0) && (
        <Panel label={t.labels.sessions_per_hour} letter="D" meta="24H · REAL">
          <div className="stack-bar-chart" style={{display:'flex',alignItems:'flex-end',gap:2,height:200,paddingBottom:1,borderBottom:'1px solid var(--amber-border)'}}>
            {hourly.map((h, i) => (
              <div key={i} style={{flex:1,display:'flex',flexDirection:'column',alignItems:'center',height:'100%',justifyContent:'flex-end',minWidth:0}}>
                <span style={{fontFamily:'var(--font-m)',fontSize:8,color:'var(--text-dim)',marginBottom:2}}>{h.count || ''}</span>
                <div style={{width:'100%',height:`${(h.count/maxHourly)*100}%`,background:i===nowH?'linear-gradient(180deg, #00D4B4, #00897B)':'#006064',borderRadius:'2px 2px 0 0',transition:'filter 0.12s',minHeight:h.count>0?2:0}} onMouseEnter={e=>e.target.style.filter='brightness(1.3)'} onMouseLeave={e=>e.target.style.filter='none'} />
                <span style={{fontFamily:'var(--font-m)',fontSize:8,color:'var(--text-muted)',marginTop:2}}>{String(i).padStart(2,'0')}</span>
              </div>
            ))}
          </div>
        </Panel>
      )}

      {AG.totalResponses > 0 && AG.trend?.length > 1 && (
        <Panel label={t.kpi.avg_response_time} letter="E" meta={`${AG.trend.length} DAYS · LATENCY TREND`}>
          <div style={{display:'flex',flexDirection:'column',gap:3,padding:'4px 0'}}>
            {AG.trend.slice(-14).map((d, i) => (
              <div key={i} style={{display:'flex',alignItems:'center',gap:6,fontSize:10}}>
                <span style={{width:50,fontFamily:'var(--font-m)',color:'var(--text-muted)'}}>{d.date}</span>
                <span style={{width:35,textAlign:'right',fontFamily:'var(--font-m)',color:'var(--cyan)'}}>{d.avgTime}s</span>
                <div style={{flex:1,height:8,background:'var(--text-faint)',position:'relative'}}>
                  <div style={{position:'absolute',inset:'0 auto 0 0',width:`${d.avgTime/(AG.p95Time)*100}%`,maxWidth:'100%',
                    background: d.avgTime < AG.medianTime ? '#39D966' : d.avgTime < AG.p95Time ? '#00D4B4' : '#E84848',
                    borderRadius:2}} />
                </div>
                <span style={{width:20,textAlign:'right',fontFamily:'var(--font-m)',fontSize:9,color:'var(--text-faint)'}}>{d.count}</span>
              </div>
            ))}
          </div>
        </Panel>
      )}

      <Panel label={t.kpi.collector_status} letter="F" meta="SYSTEM INFO">
        <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fill,minmax(160px,1fr))',gap:8,padding:'6px 0',fontSize:10}}>
          <div><span style={{color:'var(--text-muted)'}}>{t.kpi.last_run}:</span> <span style={{fontFamily:'var(--font-m)',color:'var(--green)'}}>{D.collector.lastRun}</span></div>
          <div><span style={{color:'var(--text-muted)'}}>{t.kpi.next_run}:</span> <span style={{fontFamily:'var(--font-m)',color:'var(--teal)'}}>{D.collector.nextRun}</span></div>
          <div><span style={{color:'var(--text-muted)'}}>{t.misc.sessions}:</span> <span style={{fontFamily:'var(--font-m)'}}>{SH.totalSessions}</span></div>
          <div><span style={{color:'var(--text-muted)'}}>{t.kpi.tool_calls}:</span> <span style={{fontFamily:'var(--font-m)'}}>{fmtCompact(SH.totalToolCalls)}</span></div>
          <div><span style={{color:'var(--text-muted)'}}>WARNINGS:</span> <span style={{fontFamily:'var(--font-m)',color:'var(--teal)'}}>{AG.warningCount}</span></div>
          <div><span style={{color:'var(--text-muted)'}}>AUDIO:</span> <span style={{fontFamily:'var(--font-m)'}}>{AG.audioCount} {t.misc.calls}</span></div>
          <div><span style={{color:'var(--text-muted)'}}>FALLBACKS:</span> <span style={{fontFamily:'var(--font-m)',color:'var(--gold)'}}>{SH.fallbackCount}</span></div>
          <div><span style={{color:'var(--text-muted)'}}>{t.kpi.avg_api_calls}:</span> <span style={{fontFamily:'var(--font-m)'}}>{AG.avgApiCalls}</span></div>
        </div>
      </Panel>
    </>
  );
}
