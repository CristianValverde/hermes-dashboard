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
const PROVIDER_SIGNAL_RE = /provider|openrouter|codex|oauth|auth|credential|rate[_ -]?limit|429/i;
const AUTH_SIGNAL_RE = /oauth|auth|credential|refresh|login/i;
const RATE_LIMIT_SIGNAL_RE = /rate[_ -]?limit|429/i;
const DONUT_COLORS = [
  '#00D4B4', // teal
  '#A855F7', // violet
  '#E84848', // red
  '#FBBF24', // amber
  '#39D966', // green
  '#EC4899', // pink
  '#8B5CF6', // purple
  '#FF6B6B', // coral
  '#06B6D4', // cyan
  '#34D399', // emerald
  '#A78BFA', // lavender
  '#22D3EE', // electric cyan
];
const donutColor = (index) => DONUT_COLORS[index % DONUT_COLORS.length];

function getActiveModelEntries(D) {
  const activeEntries = (D.models || []).filter((model) =>
    (D.tokensPerDay || []).some((row) => (row[model.id] || 0) > 0)
  );

  if (activeEntries.length > 0) return activeEntries;

  return (D.overviewExtras?.activeModels || []).map((modelId) => ({
    id: modelId,
    short: modelId.split('/').pop(),
  }));
}

const ECONOMIC_CLASS_COLORS = {
  usage_billable: '#00D4B4',
  oss: '#39D966',
  subscription_based: '#A855F7',
  unknown: '#E84848',
};

function getEconomicTokenBreakdown(D) {
  const rows = (D.economicBreakdown || []);
  const fallbackRows = [
    { class: 'usage_billable', label: 'Usage-billable', tokens: 0 },
    { class: 'oss', label: 'OSS', tokens: 0 },
    { class: 'subscription_based', label: 'Subscription-based', tokens: 0 },
    { class: 'unknown', label: 'Unknown', tokens: 0 },
  ];
  return (rows.length ? rows : fallbackRows).map((item) => ({
    label: item.label,
    value: item.tokens || 0,
    color: ECONOMIC_CLASS_COLORS[item.class] || ECONOMIC_CLASS_COLORS.unknown,
  }));
}

function CompactDonutCard({ title, data, centerValue, centerLabel, valueFormat = fmtCompact }) {
  const visible = data.filter((item) => item.value > 0);
  const chartData = visible.length > 0 ? visible : data;
  const total = data.reduce((sum, item) => sum + (item.value || 0), 0);
  const tooltipFor = (item) => [
    item.label,
    `TOTAL ${valueFormat(item.value || 0)}`,
    `${pct(item.value || 0, total, 1)}%`,
  ].join('\n');
  return (
    <div className="overview-donut-card">
      <div className="overview-donut-title">{title}</div>
      <div className="overview-donut-content">
        <div className="overview-donut-chart">
          <Donut
            data={chartData}
            size={136}
            thickness={16}
            centerValue={centerValue}
            centerLabel={centerLabel}
            tooltipFormat={tooltipFor}
          />
        </div>
        <div className="overview-donut-list">
          {data.map((item) => {
            const itemTooltip = tooltipFor(item);
            return (
            <div
              key={item.label}
              className="overview-donut-row tooltip-anchor"
              title={itemTooltip}
              data-tooltip={itemTooltip}
              aria-label={itemTooltip}
              tabIndex={0}
            >
              <span className="overview-donut-swatch" style={{ background: item.color }} />
              <span className="overview-donut-label">{item.label}</span>
            </div>
          )})}
        </div>
      </div>
    </div>
  );
}

function OverviewMetricCard({ letter, label, value, unit, color = 'amber', children }) {
  return (
    <div className="cp overview-kpi-card">
      <div className="overview-kpi-label">
        <span>{label}</span>
        <span className="stat-letter">{letter}</span>
      </div>
      <div className="overview-kpi-main">
        <span className={`overview-kpi-value ${color}`}>{value}</span>
        {unit && <span className="overview-kpi-unit">{unit}</span>}
      </div>
      <div className="overview-kpi-foot">{children}</div>
    </div>
  );
}

// =================================================
// SECTION 01 — OVERVIEW
// =================================================
function SectionOverview({ t }) {
  const D = HERMES_DATA;
  const totalTokens = D.totals.tokens || 0;
  const totalSessions = D.totals.sessions || 0;
  const daysActive = D.totals.daysActive || 0;
  const sourceCount = D.sources.length;
  const cacheTotal = (D.totals.cacheReadTokens || 0) + (D.totals.cacheWriteTokens || 0);
  const activeModelEntries = getActiveModelEntries(D);
  const activeModels = activeModelEntries.length || D.totals.models || 0;
  const totalModelCount = D.totals.models || D.models.length || activeModels;
  const avgTokensPerSession = Math.round(totalTokens / Math.max(totalSessions, 1));
  const avgTokensPerDay = Math.round(totalTokens / Math.max(daysActive, 1));
  const sessionsPerDay = totalSessions / Math.max(daysActive, 1);
  const avgTokensPerSecond = D.systemHealth?.globalThroughput || 0;
  const peakTokensPerSecond = D.systemHealth?.peakThroughput || 0;
  const avgResponseTime = D.agentLog?.avgTime || 0;
  const toolUsageTotal = (D.tools || []).reduce((sum, tool) => sum + (tool.count || 0), 0);
  const weightedToolSuccess = toolUsageTotal > 0
    ? (D.tools || []).reduce((sum, tool) => sum + ((tool.success || 0) * (tool.count || 0)), 0) / toolUsageTotal
    : 0;
  const successRate = weightedToolSuccess * 100;
  const totalErrorEvents = (D.errors || []).reduce((sum, error) => sum + (error.total || 0), 0);
  const healthColor = weightedToolSuccess >= 0.8 ? 'green' : weightedToolSuccess >= 0.5 ? 'gold' : 'red';
  const tokenMix = [
    { label: t.kpi.token_input, value: D.totals.inputTokens || 0, color: donutColor(0) },
    { label: t.kpi.token_output, value: D.totals.outputTokens || 0, color: donutColor(1) },
    { label: t.kpi.token_context, value: cacheTotal, color: donutColor(2) },
    { label: t.kpi.token_reasoning, value: D.totals.reasoningTokens || 0, color: donutColor(3) },
  ];
  const economicMix = getEconomicTokenBreakdown(D);
  const tokensByModelStacked = D.tokensPerDay.map(row => ({
    x: row.date,
    series: D.models.map(m => ({ key: m.id, label: m.short, value: row[m.id], color: m.color })),
  }));
  const sourceDonut = D.sources.map((s, i) => ({ label: s.name.toUpperCase(), value: s.count, color: donutColor(i) }));
  const modelLegend = D.models.map(m => {
    const tot = D.tokensPerDay.reduce((s, r) => s + (r[m.id] || 0), 0);
    const activeDaysForModel = D.tokensPerDay.filter((row) => (row[m.id] || 0) > 0).length;
    return { label: m.short, fullLabel: m.id, color: m.color, value: tot, activeDays: activeDaysForModel };
  });
  const dailyModelTooltip = ({ row, total, valueFormat }) => [
    row.x,
    `TOTAL ${valueFormat(total)}`,
    ...row.series
      .filter((segment) => (segment.value || 0) > 0)
      .sort((a, b) => b.value - a.value)
      .map((segment) => `${segment.label || segment.key} | ${valueFormat(segment.value)}`),
  ].join('\n');
  const modelLegendTooltip = (item) => [
    item.fullLabel || item.label,
    `TOTAL ${fmtCompact(item.value)} (${fmtNum(item.value)})`,
    `${pct(item.value, totalTokens, 1)}% GLOBAL`,
    `${item.activeDays || 0} DÍAS CON ACTIVIDAD`,
  ].join('\n');
  const sourceTooltip = (item, total) => [
    item.label,
    `TOTAL ${fmtNum(item.value)}`,
    `${pct(item.value, total, 1)}%`,
  ].join('\n');

  return (
    <div className="section-unified section-unified--overview">
      <Panel label={t.labels.global_telemetry} letter="A" meta={t.misc.all_providers} gold className="overview-hero-panel">
        <div className="overview-hero">
          <div className="overview-hero-main">
            <div className="overview-hero-kicker">{t.section_eyebrow.overview}</div>
            <div className="overview-hero-value">{fmtCompact(totalTokens)}</div>
            <div className="overview-hero-caption">{t.kpi.raw_tokens}</div>
          </div>

          <div className="overview-breakdown-grid">
            <CompactDonutCard title={t.kpi.token_mix} data={tokenMix} centerValue={fmtCompact(totalTokens)} centerLabel={t.misc.total} />
            <CompactDonutCard title={t.kpi.economic_class} data={economicMix} centerValue={`${pct(economicMix[0].value, totalTokens)}%`} centerLabel="BILLABLE" />
          </div>
        </div>
      </Panel>

      <div className="stat-grid overview-stat-grid">
        <OverviewMetricCard letter="A" label={t.kpi.activity} value={fmtNum(daysActive)} unit={t.misc.active_days} color="amber">
          <span>{fmtNum(totalSessions)} {t.misc.sessions.toLowerCase()}</span>
          <span>{sessionsPerDay.toFixed(1)} {t.kpi.sessions_per_day.toLowerCase()}</span>
        </OverviewMetricCard>
        <OverviewMetricCard letter="B" label={t.kpi.throughput} value={fmtNum(avgTokensPerSecond)} unit={t.kpi.throughput_label} color="green">
          <span>{fmtCompact(avgTokensPerDay)} {t.kpi.tokens_per_day.toLowerCase()}</span>
          <span>{fmtCompact(avgTokensPerSession)} {t.kpi.avg_tokens_per_session.toLowerCase()}</span>
          <span>{fmtNum(peakTokensPerSecond)} {t.kpi.peak_tokens_sec.toLowerCase()}</span>
        </OverviewMetricCard>
        <OverviewMetricCard letter="C" label={t.kpi.system_health} value={successRate.toFixed(1)} unit={`% ${t.misc.success.toLowerCase()}`} color={healthColor}>
          <span>{fmtCompact(D.totals.toolCalls || 0)} {t.kpi.tool_calls.toLowerCase()}</span>
          <span>{fmtCompact(totalErrorEvents)} {t.kpi.errors_total.toLowerCase()}</span>
          <span>{avgResponseTime ? `${avgResponseTime}s ${t.kpi.avg_response_time.toLowerCase()}` : `0s ${t.kpi.avg_response_time.toLowerCase()}`}</span>
        </OverviewMetricCard>
        <OverviewMetricCard letter="D" label={t.kpi.models} value={fmtNum(activeModels)} unit={t.kpi.active_models} color="amber">
          <span>{fmtNum(totalModelCount)} {t.kpi.total_models_used.toLowerCase()}</span>
          <span>{fmtNum(sourceCount)} {t.kpi.sources_count.toLowerCase()}</span>
        </OverviewMetricCard>
      </div>

      <div className="grid-2-1">
        <Panel label={t.labels.tokens_by_model} letter="B" meta={`14D · ${fmtCompact(totalTokens)} TOT`} gold>
          <StackedBar data={tokensByModelStacked} valueFormat={fmtCompact} tooltipFormat={dailyModelTooltip} />
          <Legend items={modelLegend} valueFormat={fmtCompact} tooltipFormat={modelLegendTooltip} />
        </Panel>

        <Panel label={t.labels.source_dist} letter="C" meta={`${D.totals.sessions} SES`}>
          <DonutWithLegend
            data={sourceDonut}
            centerValue={D.totals.sessions}
            centerLabel="SESSIONS"
            showLegendValues={false}
            tooltipFormat={sourceTooltip}
          />
        </Panel>
      </div>

      <Panel label={t.labels.recent_sessions} letter="D" meta={`10 / ${D.totals.sessions}`} gold>
        <div className="table-shell">
          <table className="dtable dtable-sessions">
            <colgroup>
              <col className="col-id" />
              <col className="col-date" />
              <col className="col-model" />
              <col className="col-source" />
              <col className="col-stat" />
              <col className="col-stat" />
              <col className="col-tokens" />
              <col className="col-cost" />
            </colgroup>
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
              {D.recentSessions.map((session, i) => {
                const sessionId = session.id || '—';
                const sessionDate = session.date || session.started || '—';
                const sessionModel = session.modelShort || (session.model ? session.model.split('/').pop() : '—');
                const sessionMessages = session.messages ?? session.msgs ?? 0;
                return (
                <tr key={i}>
                  <td className="code" title={sessionId}>
                    <div className="cell-id">
                      <span className="cell-id-primary">{sessionId.slice(0, 15)}</span>
                      <span className="cell-id-tail">{sessionId.slice(-6)}</span>
                    </div>
                  </td>
                  <td>
                    <div className="cell-stack">
                      <span className="cell-primary">{sessionDate}</span>
                    </div>
                  </td>
                  <td className="amber">
                    <div className="cell-stack">
                      <span className="cell-primary cell-strong">{sessionModel}</span>
                    </div>
                  </td>
                  <td>
                    <span className="source-pill">{session.source}</span>
                  </td>
                  <td className="r code cell-metric">{sessionMessages}</td>
                  <td className="r code cell-metric">{session.tools}</td>
                  <td className="r code cell-metric cell-metric-strong">{fmtNum(session.tokens)}</td>
                  <td className="r amber cell-metric cell-metric-strong">{fmtUsd(session.cost)}</td>
                </tr>
              )})}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}

// =================================================
// SECTION 02 — TOOLS ANALYTICS
// =================================================
function ToolIdentityCard({ totalCalls, avgDailyCalls, activeToolDays, callsPerSession, t }) {
  return (
    <div className="cp tools-identity-card">
      <div className="tools-identity-label">
        <span>{t.kpi.tool_calls}</span>
        <span className="stat-letter">A</span>
      </div>
      <div className="tools-identity-value">{fmtNum(totalCalls)}</div>
      <div className="tools-identity-caption">{t.kpi.tool_invocations}</div>
      <div className="tools-identity-foot">
        <span>{fmtNum(activeToolDays)} {t.kpi.active_tool_days.toLowerCase()}</span>
        <span>{fmtNum(avgDailyCalls)} {t.kpi.avg_daily_calls.toLowerCase()}</span>
        <span>{callsPerSession.toFixed(1)} {t.kpi.calls_per_session.toLowerCase()}</span>
      </div>
    </div>
  );
}

function TokenIdentityCard({ totalTokens, inputTokens, outputTokens, contextTokens, activeDays, avgPerDay, avgPerSession, t }) {
  return (
    <div className="cp tokens-identity-card">
      <div className="tokens-identity-label">
        <span>{t.kpi.tokens}</span>
        <span className="stat-letter">A</span>
      </div>
      <div className="tokens-identity-value">{fmtCompact(totalTokens)}</div>
      <div className="tokens-identity-caption">{t.kpi.raw_tokens}</div>
      <div className="tokens-identity-foot">
        <span>{fmtNum(activeDays)} {t.misc.active_days.toLowerCase()}</span>
        <span>{fmtCompact(avgPerDay)} {t.misc.avg_per_day.toLowerCase()}</span>
        <span>{fmtCompact(avgPerSession)} {t.kpi.avg_tokens_per_session.toLowerCase()}</span>
      </div>
      <div className="tokens-identity-mix" aria-label={t.kpi.token_mix}>
        <span>{t.kpi.token_input} {pct(inputTokens, totalTokens)}%</span>
        <span>{t.kpi.token_output} {pct(outputTokens, totalTokens)}%</span>
        <span>{t.kpi.token_context} {pct(contextTokens, totalTokens)}%</span>
      </div>
    </div>
  );
}

function TokenInsightList({ items, total, valueFormat = fmtCompact, valueLabel }) {
  if (!items.length) {
    return <div className="dim" style={{ padding: '12px 0' }}>No data available.</div>;
  }
  const max = Math.max(...items.map((item) => item.value || 0), 1);
  return (
    <div className="tokens-insight-list">
      {items.map((item, i) => (
        <div key={`${item.label}-${i}`} className="tokens-insight-row" style={{ borderLeftColor: item.color }}>
          <div className="tokens-insight-rank">#{String(i + 1).padStart(2, '0')}</div>
          <div className="tokens-insight-main">
            <div className="tokens-insight-name">{item.label}</div>
            {item.meta && <div className="tokens-insight-meta">{item.meta}</div>}
          </div>
          <div className="tokens-insight-value">
            <strong>{valueFormat(item.value || 0)}</strong>
            <span>{valueLabel || `${pct(item.value || 0, total, 1)}%`}</span>
          </div>
          <div className="tokens-insight-bar">
            <div className="tokens-insight-fill" style={{ width: `${((item.value || 0) / max) * 100}%`, background: item.color }} />
          </div>
        </div>
      ))}
    </div>
  );
}

const ERROR_CLASS_META = {
  tool_failure: { key: 'tool_failure', label: 'TOOL FAILURE', color: '#E84848' },
  model_behavior: { key: 'model_behavior', label: 'MODEL / RESPONSE', color: '#A855F7' },
  provider: { key: 'provider', label: 'PROVIDER SIGNAL', color: '#FBBF24' },
  interruption: { key: 'interruption', label: 'INTERRUPTION', color: '#06B6D4' },
};

function classifyErrorPattern(error) {
  const haystack = `${error.pattern || ''} ${error.sources || ''} ${error.tools || ''}`.toLowerCase();
  if (PROVIDER_SIGNAL_RE.test(haystack)) return 'provider';
  if (/previous_turn_interrupted|nudging_to_continue|interrupt|cancel|aborted|stopped|user[_ -]?interrupt/.test(haystack)) {
    return 'interruption';
  }
  if (/empty_response|model_returned_empty|returned_empty|no[_ -]?response|switching_fallback|primary_model_failed|fallback|model[_ -]?behavior/.test(haystack)) {
    return 'model_behavior';
  }
  return 'tool_failure';
}

function formatTrendRange(rows) {
  if (!rows || rows.length === 0) return 'NO RANGE';
  const start = rows[0]?.date || '—';
  const end = rows[rows.length - 1]?.date || '—';
  return `${start} -> ${end}`;
}

function parseDateValue(value) {
  const parsed = Date.parse(value || '');
  return Number.isNaN(parsed) ? null : parsed;
}

function normalizeErrorTagLabel(label) {
  return String(label || '')
    .toUpperCase()
    .replace(/[^A-Z0-9]+/g, '');
}

function getErrorOwnerHint(error) {
  const ownerClass = error.errorClass || classifyErrorPattern(error);
  const primaryTool = (error.tools || '').split(',').map((tool) => tool.trim()).filter(Boolean)[0];

  if (ownerClass === 'provider') {
    return {
      label: 'PROVIDER/API',
      action: 'Check rate limits, auth state, and upstream availability.',
    };
  }
  if (ownerClass === 'interruption') {
    return {
      label: 'UX/FLOW',
      action: 'Review cancel/continue flows and whether these should count as incidents.',
    };
  }
  if (ownerClass === 'model_behavior') {
    return {
      label: 'MODEL/RESPONSE',
      action: 'Inspect fallback routing, empty-response handling, and prompt-level recovery.',
    };
  }
  return {
    label: primaryTool ? `TOOL/${primaryTool}` : 'TOOL RUNTIME',
    action: primaryTool ? `Audit ${primaryTool} failures and its retry/error handling path.` : 'Audit tool runtime failures and retry/error handling.',
  };
}

function getErrorNextStep(error) {
  const ownerClass = error.errorClass || classifyErrorPattern(error);
  const haystack = `${error.pattern || ''} ${error.sources || ''} ${error.tools || ''}`.toLowerCase();
  const primaryTool = (error.tools || '').split(',').map((tool) => tool.trim()).filter(Boolean)[0];

  if (ownerClass === 'provider') {
    if (RATE_LIMIT_SIGNAL_RE.test(haystack)) {
      return {
        label: 'RETRY STRATEGY',
        detail: 'Check backoff, concurrency caps, and provider failover before escalating deeper.',
      };
    }
    if (AUTH_SIGNAL_RE.test(haystack)) {
      return {
        label: 'PROVIDER CONFIG',
        detail: 'Validate credentials, tenant state, and token refresh before treating it as runtime instability.',
      };
    }
    return {
      label: 'PROVIDER CONFIG',
      detail: 'Verify quotas, upstream health, and routing defaults for the affected provider path.',
    };
  }

  if (ownerClass === 'interruption') {
    return {
      label: 'UX RECLASSIFICATION',
      detail: 'Decide whether this flow should stop counting as an incident or move to separate telemetry.',
    };
  }

  if (ownerClass === 'model_behavior') {
    if (/empty_response|model_returned_empty|returned_empty|no[_ -]?response/.test(haystack)) {
      return {
        label: 'FALLBACK HARDENING',
        detail: 'Tighten empty-response recovery and ensure fallback paths always return a usable response.',
      };
    }
    return {
      label: 'RETRY STRATEGY',
      detail: 'Review retry thresholds, timeout budgets, and fallback order for model-response failures.',
    };
  }

  return {
    label: 'TOOL HARDENING',
    detail: primaryTool
      ? `Audit ${primaryTool} contracts, retries, and partial-failure handling first.`
      : 'Audit tool contracts, retries, and partial-failure handling first.',
  };
}

function getErrorLane(error) {
  if (error.errorClass === 'interruption') {
    return {
      key: 'noise',
      label: 'NOISE / RECLASSIFY',
      reason: 'Likely flow or operator noise, not a hard system failure.',
    };
  }

  const isFresh = error.daysSinceLastSeen !== null ? error.daysSinceLastSeen <= 2 : false;
  const isPersistent = (error.spanDays || 0) >= 7;
  const isHeavy = (error.total || 0) >= 10;
  const isCritical = (error.priority || 0) >= 30;
  const isElevated = (error.priority || 0) >= 15;

  if (isCritical || (error.errorClass === 'provider' && isFresh) || (isPersistent && isHeavy)) {
    return {
      key: 'fix_now',
      label: 'FIX NOW',
      reason: 'High impact, active now, or persistent enough to deserve direct intervention.',
    };
  }

  if (isElevated || isFresh || isHeavy) {
    return {
      key: 'monitor',
      label: 'MONITOR',
      reason: 'Relevant signal, but not yet the highest-priority corrective queue.',
    };
  }

  return {
    key: 'noise',
    label: 'NOISE / RECLASSIFY',
    reason: 'Low signal-to-noise or stale enough to avoid front-line triage.',
  };
}

function SectionTools({ t }) {
  const D = HERMES_DATA;
  const tools = D.tools || [];
  const days = D.days || [];
  const toolColors = D.toolColors || [];
  const totalCalls = tools.reduce((s, x) => s + (x.count || 0), 0);
  const totalSessions = Math.max(D.totals.sessions || 0, 1);
  const activeToolDays = Object.values(D.toolDaily || {}).filter((dailyTools) =>
    Object.values(dailyTools || {}).reduce((sum, value) => sum + (value || 0), 0) > 0
  ).length;
  const avgDailyCalls = Math.round(totalCalls / Math.max(activeToolDays || D.totals.daysActive || 1, 1));
  const callsPerSession = totalCalls / totalSessions;
  const avgSuccess = totalCalls > 0
    ? tools.reduce((s, x) => s + ((x.success || 0) * (x.count || 0)), 0) / totalCalls
    : 0;
  const failedCalls = Math.round(totalCalls * (1 - avgSuccess));
  const avgDurationMs = Math.round(
    tools.reduce((s, x) => s + ((x.durMs || 0) * (x.count || 0)), 0) / Math.max(totalCalls, 1)
  );
  const topToolName = tools[0]?.name || '—';
  const topTools = [...tools].slice(0, 6);
  const topToolCount = tools[0]?.count || 0;
  const toolDaily = days.map((date) => ({
    x: date,
    series: topTools.map((tool, ti) => {
      const dayCount = D.toolDaily && D.toolDaily[date] ? D.toolDaily[date][tool.name] || 0 : 0;
      return { key: tool.name, label: tool.name, value: dayCount, color: toolColors[ti] || donutColor(ti) };
    }),
  }));
  const toolDist = tools.map((tool, i) => ({
    label: tool.name,
    value: tool.count || 0,
    color: toolColors[i] || donutColor(i),
    success: tool.success || 0,
    durMs: tool.durMs || 0,
  }));
  const dailyToolTooltip = ({ row, total, valueFormat }) => [
    row.x,
    `TOTAL ${valueFormat(total)}`,
    ...row.series
      .filter((segment) => (segment.value || 0) > 0)
      .sort((a, b) => b.value - a.value)
      .map((segment) => `${segment.label || segment.key} | ${valueFormat(segment.value)}`),
  ].join('\n');
  const toolLegendTooltip = (item) => [
    item.label,
    `TOTAL ${fmtNum(item.value || 0)} ${t.table.calls}`,
    `${pct(item.value || 0, totalCalls, 1)}%`,
  ].join('\n');
  const toolDistributionTooltip = (item, total) => [
    item.label,
    `TOTAL ${fmtNum(item.value || 0)} ${t.table.calls}`,
    `${pct(item.value || 0, total, 1)}%`,
    `${((item.success || 0) * 100).toFixed(1)}% ${t.table.success}`,
    `${fmtNum(item.durMs || 0)} ms ${t.table.duration}`,
  ].join('\n');

  return (
    <div className="section-unified section-unified--tools">
      <div className="tools-top-grid">
        <ToolIdentityCard
          totalCalls={totalCalls}
          avgDailyCalls={avgDailyCalls}
          activeToolDays={activeToolDays}
          callsPerSession={callsPerSession}
          t={t}
        />
        <OverviewMetricCard letter="B" label={t.kpi.unique_tools} value={fmtNum(tools.length)} color="gold">
          <span>{t.kpi.most_used}: {topToolName}</span>
          <span>{fmtNum(topToolCount)} {t.table.calls.toLowerCase()}</span>
        </OverviewMetricCard>
        <OverviewMetricCard letter="C" label={t.kpi.success_rate} value={(avgSuccess * 100).toFixed(1)} unit="%" color={avgSuccess >= 0.8 ? 'green' : avgSuccess >= 0.5 ? 'gold' : 'red'}>
          <span>{fmtNum(failedCalls)} {t.kpi.failed_calls.toLowerCase()}</span>
          <span>{fmtNum(totalCalls)} {t.kpi.tool_calls.toLowerCase()}</span>
        </OverviewMetricCard>
        <OverviewMetricCard letter="D" label={t.kpi.avg_duration} value={fmtNum(avgDurationMs)} unit="ms" color="amber">
          <span>{callsPerSession.toFixed(1)} {t.kpi.calls_per_session.toLowerCase()}</span>
          <span>{fmtNum(avgDailyCalls)} {t.kpi.avg_daily_calls.toLowerCase()}</span>
        </OverviewMetricCard>
      </div>

      <div className="tools-chart-grid">
        <Panel label={t.labels.tool_usage} letter="A" meta={`14D · TOP 6`} gold className="tools-usage-panel">
          <StackedBar data={toolDaily} valueFormat={fmtCompact} tooltipFormat={dailyToolTooltip} />
          <Legend
            items={topTools.map((tool, i) => ({
              label: tool.name,
              color: toolColors[i] || donutColor(i),
              value: tool.count || 0,
            }))}
            tooltipFormat={toolLegendTooltip}
          />
        </Panel>

        <Panel label={t.labels.tool_dist} letter="B" meta={`${tools.length} TOOLS`} className="tools-distribution-panel">
          <DonutWithLegend
            data={toolDist.slice(0, 8)}
            centerValue={fmtCompact(totalCalls)}
            centerLabel="CALLS"
            showLegendValues={false}
            tooltipFormat={toolDistributionTooltip}
            compact
          />
        </Panel>
      </div>

      <Panel label={t.labels.top_tools} letter="C" meta="RANKED · CALL FREQ" gold>
        <div className="table-shell">
          <table className="dtable dtable-tools">
            <colgroup>
              <col className="col-rank" />
              <col className="col-tool" />
              <col className="col-calls" />
              <col className="col-pct" />
              <col className="col-success" />
              <col className="col-duration" />
              <col className="col-bar" />
            </colgroup>
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
              {tools.map((tool, i) => {
                const toolCount = tool.count || 0;
                const share = pct(toolCount, totalCalls, 1);
                const successPct = ((tool.success || 0) * 100).toFixed(1);
                const durationMs = Math.round(tool.durMs || 0);
                return (
                <tr key={i} className="tool-row" style={{animation: 'statFadeIn 300ms ease both', animationDelay: (i*20)+'ms'}}>
                  <td className="dim">{String(i+1).padStart(2,'0')}</td>
                  <td className="amber">
                    <div className="cell-stack">
                      <span className="cell-primary cell-strong">{tool.name}</span>
                    </div>
                  </td>
                  <td className="r code cell-metric cell-metric-strong">{fmtNum(toolCount)}</td>
                  <td className="r dim cell-metric">{share.toFixed(1)}%</td>
                  <td className="r code cell-metric">{successPct}%</td>
                  <td className="r code cell-metric">{fmtNum(durationMs)} ms</td>
                  <td>
                    <div className="tool-bar-track">
                      <div className="tool-bar-fill" style={{ width: `${(toolCount / Math.max(topToolCount, 1)) * 100}%`, background: toolColors[i % toolColors.length] || donutColor(i) }} />
                    </div>
                  </td>
                </tr>
              )})}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}

// =================================================
// SECTION 03 — TOKEN ANALYTICS
// =================================================
function SectionTokens({ t }) {
  const D = HERMES_DATA;
  const totalAll = D.totals.tokens || 0;
  const totalSessions = Math.max(D.totals.sessions || 0, 1);
  const hasOpenRouterData = (D.openRouter.totalCredits || 0) > 0
    || (D.openRouter.totalUsage || 0) > 0
    || (D.openRouter.today || 0) > 0
    || (D.openRouter.week || 0) > 0
    || (D.openRouter.month || 0) > 0
    || D.modelCosts.some((m) => (m.real_cost || 0) > 0);
  const billedTokenTotal = D.modelCosts.reduce((sum, m) => sum + (m.input_tokens || 0) + (m.output_tokens || 0) + (m.cache_read_tokens || 0) + (m.reasoning_tokens || 0), 0);
  const coveragePct = pct(billedTokenTotal, totalAll, 0);
  const billingScopeLabel = coveragePct > 100
    ? t.misc.openrouter_only.toLowerCase()
    : `${coveragePct}% ${t.misc.tracked_share.toLowerCase()}`;
  const costPerM = billedTokenTotal > 0 ? (D.openRouter.totalUsage / billedTokenTotal) * 1_000_000 : 0;
  const avgPerDay = Math.round(totalAll / Math.max(D.totals.daysActive || 1, 1));
  const avgPerSession = Math.round(totalAll / totalSessions);
  const contextTokens = (D.totals.cacheReadTokens || 0) + (D.totals.cacheWriteTokens || 0);
  const dailyTokenTotals = D.tokensPerDay.map((row) => D.models.reduce((sum, m) => sum + (row[m.id] || 0), 0));
  const activeTokenDays = dailyTokenTotals.filter((value) => value > 0).length;
  const todayTokens = dailyTokenTotals[dailyTokenTotals.length - 1] || 0;
  const weekTokens = dailyTokenTotals.slice(-7).reduce((sum, value) => sum + value, 0);
  const monthTokens = dailyTokenTotals.slice(-30).reduce((sum, value) => sum + value, 0);
  const totalToolCalls = (D.tools || []).reduce((sum, tool) => sum + (tool.count || 0), 0);
  const toolTokenUsage = D.toolTokenUsage || [];
  const totalToolTokens = toolTokenUsage.reduce((sum, tool) => sum + (tool.tokens || 0), 0);
  const toolActiveDays = Object.values(D.toolDaily || {}).filter((dailyTools) =>
    Object.values(dailyTools || {}).reduce((sum, value) => sum + (value || 0), 0) > 0
  ).length;
  const providerUsage = (D.economicProviderUsage || [])
    .filter((provider) => (provider.tokens || 0) > 0)
    .map((provider, i) => ({
      label: provider.label || provider.provider || 'Provider',
      value: provider.tokens || 0,
      sessions: provider.sessions || 0,
      models: provider.models || [],
      economicLabel: provider.economicLabel || provider.economicClass || '',
      color: donutColor(i),
    }))
    .sort((a, b) => b.value - a.value);
  const providerTotal = providerUsage.reduce((sum, provider) => sum + provider.value, 0) || totalAll;
  const topProvider = providerUsage[0];
  const topTool = toolTokenUsage[0] || D.tools?.[0];

  const modelRanking = D.models.map((m) => {
    const globalTokens = D.tokensPerDay.reduce((s, r) => s + (r[m.id] || 0), 0);
    const mc = D.modelCosts.find(c => c.model === m.id);
    const cost = mc ? mc.real_cost : 0;
    return { name: m.id, value: globalTokens, pct: pct(globalTokens, totalAll, 1), color: m.color, cost: cost };
  }).sort((a, b) => b.value - a.value);

  const tokensByModelStacked = D.tokensPerDay.map(row => ({
    x: row.date,
    series: D.models.map(m => ({ key: m.id, label: m.short, value: row[m.id], color: m.color })),
  }));

  const breakdown = [
    { label: t.kpi.token_input,         value: D.totals.inputTokens,      color: donutColor(0) },
    { label: t.kpi.token_output,        value: D.totals.outputTokens,     color: donutColor(1) },
    { label: t.kpi.token_context_read,  value: D.totals.cacheReadTokens,  color: donutColor(2) },
    { label: t.kpi.token_context_write, value: D.totals.cacheWriteTokens, color: donutColor(3) },
    { label: t.kpi.token_reasoning,     value: D.totals.reasoningTokens,  color: donutColor(4) },
  ].filter(d => d.value > 0);

  const modelLegend = D.models.map(m => ({
    label: m.short,
    color: m.color,
    value: D.tokensPerDay.reduce((s, r) => s + (r[m.id] || 0), 0),
    id: m.id,
  }));
  const dailyModelTooltip = ({ row, total, valueFormat }) => [
    row.x,
    `TOTAL ${valueFormat(total)}`,
    ...row.series
      .filter((segment) => (segment.value || 0) > 0)
      .sort((a, b) => b.value - a.value)
      .map((segment) => `${segment.label || segment.key} | ${valueFormat(segment.value)}`),
  ].join('\n');
  const modelLegendTooltip = (item) => [
    item.id || item.label,
    `TOTAL ${fmtCompact(item.value || 0)} (${fmtNum(item.value || 0)})`,
    `${pct(item.value || 0, totalAll, 1)}% ${t.misc.tracked_share.toLowerCase()}`,
  ].join('\n');
  const providerTooltip = (item, total) => [
    item.label,
    `TOTAL ${fmtCompact(item.value || 0)} (${fmtNum(item.value || 0)})`,
    `${pct(item.value || 0, total, 1)}% provider`,
    `${fmtNum(item.sessions || 0)} ${t.misc.sessions.toLowerCase()}`,
    item.economicLabel,
  ].join('\n');
  const providerInsightItems = providerUsage.map((provider) => ({
    label: provider.label,
    value: provider.value,
    color: provider.color,
    meta: `${provider.economicLabel} · ${fmtNum(provider.sessions)} ${t.misc.sessions.toLowerCase()} · ${provider.models.length} ${t.kpi.models.toLowerCase()}`,
  }));
  const modelInsightItems = modelRanking.map((model) => ({
    label: model.name,
    value: model.value,
    color: model.color,
    meta: `${model.pct.toFixed(1)}% ${t.table.tokens.toLowerCase()}`,
  }));
  const toolInsightItems = (toolTokenUsage.length ? toolTokenUsage : D.tools || []).slice(0, 10).map((tool, i) => ({
    label: tool.name,
    value: tool.tokens || tool.count || 0,
    color: D.toolColors?.[i] || tool.color || donutColor(i),
    meta: `${fmtCompact(tool.calls || tool.count || 0)} ${t.kpi.tool_calls.toLowerCase()} · ${fmtNum(tool.sessions || 0)} ${t.misc.sessions.toLowerCase()} · ${((tool.success || 0) * 100).toFixed(1)}% ${t.misc.success.toLowerCase()}`,
  }));

  return (
    <div className="section-unified section-unified--tokens">
      <div className="tokens-top-grid">
        <TokenIdentityCard
          totalTokens={totalAll}
          inputTokens={D.totals.inputTokens || 0}
          outputTokens={D.totals.outputTokens || 0}
          contextTokens={contextTokens}
          activeDays={activeTokenDays || D.totals.daysActive || 0}
          avgPerDay={avgPerDay}
          avgPerSession={avgPerSession}
          t={t}
        />
        <OverviewMetricCard
          letter="B"
          label={t.misc.active_days}
          value={fmtNum(activeTokenDays || D.totals.daysActive || 0)}
          color="gold"
        >
          <span>{fmtCompact(todayTokens)} {t.misc.today.toLowerCase()}</span>
          <span>{fmtCompact(weekTokens)} {t.misc.week.toLowerCase()}</span>
          <span>{fmtCompact(monthTokens)} {t.misc.month.toLowerCase()}</span>
        </OverviewMetricCard>
        <OverviewMetricCard
          letter="C"
          label="PROVIDERS"
          value={fmtNum(providerUsage.length)}
          color="amber"
        >
          <span>{topProvider ? topProvider.label : '—'}</span>
          <span>{topProvider ? `${fmtCompact(topProvider.value)} ${t.table.tokens.toLowerCase()}` : `0 ${t.table.tokens.toLowerCase()}`}</span>
        </OverviewMetricCard>
        <OverviewMetricCard
          letter="D"
          label={t.kpi.unique_tools}
          value={fmtNum(D.tools?.length || 0)}
          color="green"
        >
          <span>{topTool ? topTool.name : '—'}</span>
          <span>{fmtCompact(totalToolTokens || totalToolCalls)} {t.table.tokens.toLowerCase()}</span>
          <span>{fmtNum(toolActiveDays)} {t.kpi.active_tool_days.toLowerCase()}</span>
        </OverviewMetricCard>
      </div>

      <div className="tokens-chart-grid">
        <Panel label={t.labels.daily_consumption} letter="A" meta={`14D · ${fmtCompact(totalAll)} ${t.misc.total}`} className="tokens-consumption-panel" gold>
          <StackedBar data={tokensByModelStacked} valueFormat={fmtCompact} tooltipFormat={dailyModelTooltip} />
          <Legend items={modelLegend} valueFormat={fmtCompact} tooltipFormat={modelLegendTooltip} />
        </Panel>
        <Panel label="TOKENS POR PROVIDER" letter="B" meta={`${providerUsage.length} PROVIDERS`} className="tokens-breakdown-panel">
          <DonutWithLegend
            data={providerUsage}
            centerValue={fmtCompact(providerTotal)}
            centerLabel="TOKENS"
            valueFormat={fmtCompact}
            showLegendValues={false}
            tooltipFormat={providerTooltip}
            compact
          />
        </Panel>
      </div>

      <div className="tokens-support-grid">
        <Panel label={t.labels.model_ranking} letter="C" meta={`${D.models.length} MODELS · GLOBAL TOKENS`} gold>
          <TokenInsightList items={modelInsightItems} total={totalAll} valueFormat={fmtCompact} />
        </Panel>
        <Panel label="TOKENS ATRIBUIDOS POR HERRAMIENTA" letter="D" meta={`${fmtCompact(totalToolTokens || totalToolCalls)} ${t.table.tokens}`} className="tokens-tools-panel">
          <TokenInsightList items={toolInsightItems} total={totalToolTokens || totalToolCalls} valueFormat={fmtCompact} />
        </Panel>
      </div>

      <div className="tokens-secondary-grid">
        <Panel label="TOKENS POR PROVIDER · RANKING" letter="E" meta={t.misc.all_providers}>
          <TokenInsightList items={providerInsightItems} total={providerTotal} valueFormat={fmtCompact} />
        </Panel>
        {hasOpenRouterData && (
          <Panel label={t.labels.openrouter_billing_scope} letter="F" meta={t.misc.openrouter_only} className="tokens-billing-panel">
            <div className="mini-kpi-row">
              <div className="mini-kpi"><div className="label">{t.kpi.credit_used}</div><div className="val">{fmtUsd(D.openRouter.totalUsage || 0)}</div></div>
              <div className="mini-kpi"><div className="label">{t.kpi.cost_per_million}</div><div className="val">{fmtUsd(costPerM)}</div></div>
              <div className="mini-kpi"><div className="label">{t.kpi.billed_tokens}</div><div className="val">{fmtCompact(billedTokenTotal)}</div></div>
              <div className="mini-kpi"><div className="label">{t.misc.tracked_share}</div><div className="val">{billingScopeLabel}</div></div>
            </div>
          </Panel>
        )}
      </div>
    </div>
  );
}

// =================================================
// SECTION 04 — ERRORS & PERFORMANCE
// =================================================
function SectionErrors({ t }) {
  const D = HERMES_DATA;
  const [filterSource, setFilterSource] = useStateS('all');
  const [filterTool, setFilterTool] = useStateS('all');

  const allErrors = D.errors || [];
  const errorTrend = D.errorTrend || [];
  const sourceOptions = [...new Set(allErrors.flatMap((e) => (e.sources || '').split(',').map((s) => s.trim()).filter(Boolean)))];
  const toolOptions = [...new Set(allErrors.flatMap((e) => (e.tools || '').split(',').map((s) => s.trim()).filter(Boolean)))];
  const filtered = useMemoS(() => {
    return allErrors.filter((e) => {
      if (filterSource !== 'all' && !(e.sources || '').includes(filterSource)) return false;
      if (filterTool !== 'all' && !(e.tools || '').includes(filterTool)) return false;
      return true;
    });
  }, [filterSource, filterTool]);

  const trendEndDateValue = parseDateValue(errorTrend[errorTrend.length - 1]?.date);
  const classifiedPatterns = filtered.map((error) => {
    const startValue = parseDateValue(error.firstSeen);
    const endValue = parseDateValue(error.lastSeen);
    const spanDays = startValue !== null && endValue !== null
      ? Math.max(1, Math.round((endValue - startValue) / 86400000) + 1)
      : 1;
    const daysSinceLastSeen = trendEndDateValue !== null && endValue !== null
      ? Math.max(0, Math.round((trendEndDateValue - endValue) / 86400000))
      : null;

    return {
      ...error,
      errorClass: classifyErrorPattern(error),
      spanDays,
      daysSinceLastSeen,
      isRecent: daysSinceLastSeen !== null ? daysSinceLastSeen <= 2 : false,
    };
  });
  const incidentPatterns = classifiedPatterns.filter((error) => error.errorClass !== 'interruption');
  const interruptionPatterns = classifiedPatterns.filter((error) => error.errorClass === 'interruption');
  const filteredEventTotal = incidentPatterns.reduce((sum, e) => sum + (e.total || 0), 0);
  const filteredSourcesCount = new Set(
    incidentPatterns.flatMap((error) => (error.sources || '').split(',').map((s) => s.trim()).filter(Boolean))
  ).size;
  const filteredToolCount = new Set(
    incidentPatterns.flatMap((error) => (error.tools || '').split(',').map((tool) => tool.trim()).filter(Boolean))
  ).size;
  const classSummaries = Object.values(ERROR_CLASS_META)
    .filter((meta) => meta.key !== 'interruption')
    .map((meta) => {
      const patterns = incidentPatterns.filter((error) => error.errorClass === meta.key);
      return {
        ...meta,
        patterns,
        total: patterns.reduce((sum, error) => sum + (error.total || 0), 0),
        patternCount: patterns.length,
        maxPriority: patterns.reduce((max, error) => Math.max(max, error.priority || 0), 0),
        sources: new Set(
          patterns.flatMap((error) => (error.sources || '').split(',').map((s) => s.trim()).filter(Boolean))
        ).size,
      };
    })
    .filter((summary) => summary.patternCount > 0 || summary.total > 0)
    .sort((a, b) => (b.total - a.total) || (b.maxPriority - a.maxPriority));
  const dominantClass = classSummaries[0] || { ...ERROR_CLASS_META.tool_failure, total: 0, patternCount: 0, sources: 0, patterns: [] };
  const interruptionSummary = {
    ...ERROR_CLASS_META.interruption,
    patterns: interruptionPatterns,
    total: interruptionPatterns.reduce((sum, error) => sum + (error.total || 0), 0),
    patternCount: interruptionPatterns.length,
    maxPriority: interruptionPatterns.reduce((max, error) => Math.max(max, error.priority || 0), 0),
    sources: new Set(
      interruptionPatterns.flatMap((error) => (error.sources || '').split(',').map((s) => s.trim()).filter(Boolean))
    ).size,
  };
  const providerSummary = classSummaries.find((summary) => summary.key === 'provider') || { ...ERROR_CLASS_META.provider, total: 0, patternCount: 0, sources: 0, patterns: [] };
  const activeIncidentDays = errorTrend.filter((day) =>
    ((day.tool_failure || 0) + (day.model_behavior || 0) + (day.provider || 0)) > 0
  ).length;
  const criticalPatterns = incidentPatterns.filter((e) => (e.priority || 0) >= 30).length;
  const rateLimitEvents = incidentPatterns
    .filter((e) => RATE_LIMIT_SIGNAL_RE.test(`${e.pattern} ${e.sources} ${e.tools || ''}`))
    .reduce((sum, e) => sum + (e.total || 0), 0);
  const authEvents = incidentPatterns
    .filter((e) => AUTH_SIGNAL_RE.test(`${e.pattern} ${e.sources} ${e.tools || ''}`))
    .reduce((sum, e) => sum + (e.total || 0), 0);
  const hasProviderSignals = providerSummary.total > 0 || errorTrend.some((day) => (day.provider || 0) > 0);
  const trendRangeLabel = formatTrendRange(errorTrend);
  const visibleSeries = [
    { key: 'tool_failure', label: ERROR_CLASS_META.tool_failure.label, color: ERROR_CLASS_META.tool_failure.color, points: errorTrend.map((d) => ({ x: d.date, y: d.tool_failure || 0 })) },
    { key: 'model_behavior', label: ERROR_CLASS_META.model_behavior.label, color: ERROR_CLASS_META.model_behavior.color, points: errorTrend.map((d) => ({ x: d.date, y: d.model_behavior || 0 })) },
    { key: 'provider', label: ERROR_CLASS_META.provider.label, color: ERROR_CLASS_META.provider.color, points: errorTrend.map((d) => ({ x: d.date, y: d.provider || 0 })) },
  ].filter((series) => series.key !== 'provider' || hasProviderSignals)
    .filter((series) => series.points.some((point) => point.y > 0));
  const trendSeries = visibleSeries.length > 0 ? visibleSeries : [
    { key: 'tool_failure', label: ERROR_CLASS_META.tool_failure.label, color: ERROR_CLASS_META.tool_failure.color, points: errorTrend.map((d) => ({ x: d.date, y: d.tool_failure || 0 })) },
  ];
  const triageItems = incidentPatterns
    .map((error) => ({
      ...error,
      ownerHint: getErrorOwnerHint(error),
      nextStep: getErrorNextStep(error),
      lane: getErrorLane(error),
    }))
    .sort((a, b) => ((b.priority || 0) - (a.priority || 0)) || ((b.total || 0) - (a.total || 0)));
  const laneLoad = triageItems.reduce((acc, item) => {
    const key = item.lane.key;
    acc[key] = (acc[key] || 0) + (item.total || 0);
    return acc;
  }, { fix_now: 0, monitor: 0, noise: 0 });
  const triageColumns = [
    { key: 'fix_now', label: t.labels.fix_now || 'FIX NOW', items: triageItems.filter((item) => item.lane.key === 'fix_now').slice(0, 4) },
    { key: 'monitor', label: t.labels.monitor || 'MONITOR', items: triageItems.filter((item) => item.lane.key === 'monitor').slice(0, 4) },
    { key: 'noise', label: t.labels.noise_reclassify || 'NOISE / RECLASSIFY', items: triageItems.filter((item) => item.lane.key === 'noise').slice(0, 4) },
  ];
  const providerDiagnosticItems = providerSummary.patterns
    .slice()
    .sort((a, b) => (b.total || 0) - (a.total || 0))
    .slice(0, 4)
    .map((error, index) => ({
      label: error.pattern,
      value: error.total || 0,
      color: donutColor(index + 3),
      meta: `${error.sources.toUpperCase()} · ${(error.tools || 'NO TOOL').split(',').map((tool) => tool.trim()).filter(Boolean)[0] || 'NO TOOL'}`,
    }));
  const interruptionDiagnosticItems = interruptionSummary.patterns
    .slice()
    .sort((a, b) => (b.total || 0) - (a.total || 0))
    .slice(0, 4)
    .map((error, index) => ({
      label: error.pattern,
      value: error.total || 0,
      color: donutColor(index + 7),
      meta: `${error.sources.toUpperCase()} · ${error.firstSeen} -> ${error.lastSeen}`,
    }));
  const interruptionMeta = interruptionSummary.total > 0
    ? ` · ${fmtNum(interruptionSummary.total)} FLOW INTERRUPT EXCLUDED`
    : '';
  const filterMeta = filtered.length < allErrors.length
    ? `${incidentPatterns.length} ${t.misc.filtered_of} ${allErrors.length} · ${fmtNum(filteredEventTotal)} EVTS${interruptionMeta}`
    : `${incidentPatterns.length} INCIDENT PATTERNS · ${fmtNum(filteredEventTotal)} EVTS${interruptionMeta}`;
  const providerShare = pct(providerSummary.total, Math.max(filteredEventTotal, 1), 1);
  const topPattern = triageItems[0] || null;
  const topPatternShare = pct(topPattern?.total || 0, Math.max(filteredEventTotal, 1), 1);
  const persistentPatterns = incidentPatterns.filter((error) => error.spanDays >= 7);
  const persistentLoad = persistentPatterns.reduce((sum, error) => sum + (error.total || 0), 0);
  const persistentShare = pct(persistentLoad, Math.max(filteredEventTotal, 1), 1);
  const recentPatterns = incidentPatterns.filter((error) => error.isRecent);
  const recentLoad = recentPatterns.reduce((sum, error) => sum + (error.total || 0), 0);
  const recentShare = pct(recentLoad, Math.max(filteredEventTotal, 1), 1);
  const sourceImpactMap = {};
  const toolImpactMap = {};

  incidentPatterns.forEach((error) => {
    (error.sources || '').split(',').map((source) => source.trim()).filter(Boolean).forEach((source) => {
      sourceImpactMap[source] = (sourceImpactMap[source] || 0) + (error.total || 0);
    });
    (error.tools || '').split(',').map((tool) => tool.trim()).filter(Boolean).forEach((tool) => {
      toolImpactMap[tool] = (toolImpactMap[tool] || 0) + (error.total || 0);
    });
  });

  const topSourceImpact = Object.entries(sourceImpactMap).sort((a, b) => b[1] - a[1])[0] || ['—', 0];
  const topToolImpact = Object.entries(toolImpactMap).sort((a, b) => b[1] - a[1])[0] || ['—', 0];
  const topSourceShare = pct(topSourceImpact[1], Math.max(filteredEventTotal, 1), 1);
  const topToolShare = pct(topToolImpact[1], Math.max(filteredEventTotal, 1), 1);
  const fixNowShare = pct(laneLoad.fix_now, Math.max(filteredEventTotal, 1), 1);
  const topFixNow = triageColumns[0].items[0] || null;
  const nextMove = topFixNow?.nextStep || topPattern?.nextStep || { label: 'NO ACTIVE PLAY', detail: 'No high-priority incident currently needs immediate remediation.' };
  const actionableInsights = [
    {
      title: 'Concentration',
      value: topPattern ? `${topPatternShare}%` : '0%',
      tone: 'red',
      detail: topPattern ? `${topPattern.pattern} dominates the queue` : 'No dominant pattern',
    },
    {
      title: 'Persistence',
      value: `${persistentPatterns.length}`,
      tone: 'amber',
      detail: `${persistentShare}% of load lasted 7+ days`,
    },
    {
      title: 'Fix-Now Load',
      value: `${fixNowShare}%`,
      tone: fixNowShare >= 45 ? 'red' : fixNowShare >= 20 ? 'amber' : 'green',
      detail: `${fmtNum(laneLoad.fix_now)} events already justify direct remediation`,
    },
    {
      title: 'Live Now',
      value: `${recentShare}%`,
      tone: recentShare >= 50 ? 'red' : 'green',
      detail: `${recentPatterns.length} patterns still active in the last 72h`,
    },
    {
      title: 'Top Radius',
      value: topSourceImpact[0].toUpperCase(),
      tone: 'cyan',
      detail: `${topToolImpact[0]} absorbs ${topToolShare}% of load · ${topSourceShare}% sits on the top source`,
    },
    {
      title: 'Flow Interrupts',
      value: fmtNum(interruptionSummary.total),
      tone: interruptionSummary.total > 0 ? 'cyan' : 'green',
      detail: interruptionSummary.total > 0
        ? `${interruptionSummary.patternCount} patterns excluded from incident load and triage`
        : 'No interruption-only patterns in the current filters',
    },
    {
      title: 'Next Move',
      value: nextMove.label,
      tone: 'amber',
      detail: topFixNow ? `${topFixNow.pattern} · ${nextMove.detail}` : nextMove.detail,
    },
  ];

  return (
    <div className="section-unified section-unified--errors">
      <Panel label={t.kpi.incident_load || 'INCIDENT LOAD'} letter="A" meta={trendRangeLabel} gold className="errors-hero-panel">
        <div className="errors-hero">
          <div className="errors-hero-main">
            <div className="errors-hero-kicker">{t.section_eyebrow.errors}</div>
            <div className="errors-hero-value">{fmtNum(filteredEventTotal)}</div>
            <div className="errors-hero-caption">
              {filtered.length < allErrors.length ? 'INCIDENT EVENTS MATCHING CURRENT FILTERS' : 'INCIDENT EVENTS ACROSS THE CURRENT RANGE'}
            </div>
            <div className="errors-hero-lenses">
              <div className="errors-hero-lens">
                <span>FIX NOW LOAD</span>
                <strong>{fixNowShare}%</strong>
              </div>
              <div className="errors-hero-lens">
                <span>FLOW INTERRUPTS</span>
                <strong>{fmtNum(interruptionSummary.total)}</strong>
              </div>
              <div className="errors-hero-lens">
                <span>RECENT 72H</span>
                <strong>{recentShare}%</strong>
              </div>
            </div>
          </div>
          <div className="errors-hero-side">
            <div className="errors-hero-stat">
              <span>{t.kpi.dominant_class || 'DOMINANT CLASS'}</span>
              <strong style={{ color: dominantClass.color }}>{dominantClass.label}</strong>
              <small>{dominantClass.patternCount} PATTERNS · {pct(dominantClass.total, Math.max(filteredEventTotal, 1), 1)}% LOAD</small>
            </div>
            <div className="errors-hero-stat">
              <span>{t.misc.active_days}</span>
              <strong>{fmtNum(activeIncidentDays)}</strong>
              <small>{filteredSourcesCount} SOURCES · {filteredToolCount} TOOLS</small>
            </div>
            <div className="errors-hero-stat">
              <span>{t.kpi.active_patterns || 'ACTIVE PATTERNS'}</span>
              <strong>{fmtNum(criticalPatterns)}</strong>
              <small>{incidentPatterns.length} INCIDENT PATTERNS · {providerSummary.patternCount} PROVIDER-RELATED</small>
            </div>
          </div>
        </div>

        <div className="filter-shell errors-filter-shell">
          <div className="filter-bar">
            <div className="filter-item">
              <label>{t.misc.source}</label>
              <select value={filterSource} onChange={(e) => setFilterSource(e.target.value)}>
                <option value="all">{t.misc.all}</option>
                {sourceOptions.map((source) => (
                  <option key={source} value={source}>{source.toUpperCase()}</option>
                ))}
              </select>
            </div>
            <div className="filter-item">
              <label>{t.misc.tool}</label>
              <select value={filterTool} onChange={(e) => setFilterTool(e.target.value)}>
                <option value="all">{t.misc.all}</option>
                {toolOptions.map((tool) => (
                  <option key={tool} value={tool}>{tool}</option>
                ))}
              </select>
            </div>
            <div className="filter-count">{filterMeta}</div>
          </div>

        </div>
      </Panel>

      <div className="grid-2-1 errors-main-grid">
        <Panel label={t.labels.error_trend} letter="B" meta={`${trendRangeLabel} · ${trendSeries.length} CLASSES`} gold>
          <div className="line-chart-wrap">
            <LineChart series={trendSeries} xLabels={errorTrend.map((day) => day.date)} />
          </div>
          <Legend items={trendSeries.map((series) => ({ label: series.label, color: series.color }))} />
        </Panel>

        <Panel label={t.labels.actionable_signals || 'ACTIONABLE SIGNALS'} letter="C" meta={`${fmtNum(incidentPatterns.length)} INCIDENTS · ${fmtNum(filteredToolCount)} TOOLS`}>
          <div className="errors-insight-list">
            {actionableInsights.map((insight) => (
              <div key={insight.title} className="errors-insight-row">
                <div className="errors-insight-copy">
                  <div className="errors-insight-title">{insight.title}</div>
                  <div className="errors-insight-detail">{insight.detail}</div>
                </div>
                <div className={`errors-insight-value ${insight.tone}`}>{insight.value}</div>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <div className="grid-2 errors-diagnostics-grid">
        <Panel label={t.labels.triage_queue || 'TRIAGE QUEUE'} letter="D" meta={`${triageColumns[0].items.length} FIX NOW · ${triageColumns[1].items.length} MONITOR · ${fixNowShare}% LOAD`} gold>
          <div className="errors-triage-grid">
            {triageColumns.map((column) => (
              <div key={column.key} className={`errors-triage-lane ${column.key}`}>
                <div className="errors-triage-header">
                  <span>{column.label}</span>
                  <strong>{column.items.length}</strong>
                </div>
                <div className="errors-triage-body">
                  {column.items.length === 0 && (
                    <div className="errors-triage-empty">No patterns in this lane.</div>
                  )}
                  {column.items.map((item, index) => {
                    const classMeta = ERROR_CLASS_META[item.errorClass] || ERROR_CLASS_META.tool_failure;
                    const sourceLabel = (item.sources || 'UNKNOWN').toUpperCase();
                    const showOwnerTag = normalizeErrorTagLabel(item.ownerHint.label) !== normalizeErrorTagLabel(classMeta.label);
                    return (
                      <div key={`${column.key}-${index}-${item.pattern}`} className="errors-triage-card">
                        <div className="errors-triage-topline">
                          <span className="errors-triage-score">{item.priority}</span>
                          <span className="errors-triage-total">{fmtNum(item.total)} EVTS</span>
                        </div>
                        <div className="errors-triage-pattern">{item.pattern}</div>
                        <div className="errors-triage-meta">
                          {sourceLabel} · {item.firstSeen} -> {item.lastSeen}
                        </div>
                        <div className="errors-triage-tags">
                          <span className="cluster-tag" style={{ borderColor: `${classMeta.color}33`, color: classMeta.color, background: `${classMeta.color}14` }}>{classMeta.label}</span>
                          {showOwnerTag && <span className="cluster-tag subtle">{item.ownerHint.label}</span>}
                          <span className="cluster-tag subtle">{item.nextStep.label}</span>
                        </div>
                        <div className="errors-triage-reason">{item.lane.reason}</div>
                        <div className="errors-triage-action">{item.nextStep.detail}</div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel label={t.labels.provider_diagnostics || 'PROVIDER & FLOW DIAGNOSTICS'} letter="E" meta={`${providerShare}% PROVIDER · ${fmtNum(rateLimitEvents)} RATE LIMIT · ${fmtNum(interruptionSummary.total)} FLOW INTERRUPT`}>
          <div className="errors-diagnostic-columns">
            <div className="errors-diagnostic-column">
              <div className="errors-diagnostic-heading">PROVIDER PATTERNS</div>
              <TokenInsightList items={providerDiagnosticItems} total={Math.max(providerSummary.total, 1)} valueFormat={fmtNum} />
            </div>
            <div className="errors-diagnostic-column">
              <div className="errors-diagnostic-heading">FLOW INTERRUPTIONS</div>
              <TokenInsightList items={interruptionDiagnosticItems} total={Math.max(interruptionSummary.total, 1)} valueFormat={fmtNum} />
            </div>
          </div>
        </Panel>
      </div>
    </div>
  );
}

// =================================================
// =================================================
// SECTION 05 — SESSION ANALYTICS
// =================================================
function SectionSessions({ t }) {
  const D = HERMES_DATA;
  const S = D.sessionMetrics;

  if (!S || !S.totalSessions) {
    return <Panel label={t.labels.per_session} letter="A" meta="NO DATA"><div className="dim" style={{padding:20,textAlign:'center'}}>No session data available yet.</div></Panel>;
  }

  const totalSessions = D.totals?.sessions || S.totalSessions || 0;
  const sessionsPerDay = S.sessionsPerDay || [];
  const activeDays = Math.max(sessionsPerDay.length, 1);
  const sessionsPerActiveDay = totalSessions / activeDays;
  const maxSpd = Math.max(...sessionsPerDay.map(d => d.count), 1);

  const modelsArr = D.models || [];
  const modelDist = (S.modelUsage || []).map((m, i) => ({
    label: m.model.split('/').pop(), value: m.count,
    color: modelsArr.length > 0 ? modelsArr[i % modelsArr.length].color : '#00D4B4',
  }));

  const activeModelEntries = getActiveModelEntries(D);
  const modelStr = activeModelEntries.map((model) => model.short || model.id.split('/').pop()).join(', ') || '—';
  const peakSessionDay = sessionsPerDay.reduce((peak, day) => (day.count > peak.count ? day : peak), sessionsPerDay[0] || { day: '—', count: 0 });
  const latestSessionDay = sessionsPerDay[sessionsPerDay.length - 1] || { day: '—', count: 0 };
  const peakShare = totalSessions ? peakSessionDay.count / totalSessions : 0;
  const topModelNames = modelDist.slice(0, 2).map((m) => m.label).join(' + ') || '—';
  const leadModelShare = modelDist.length > 0
    ? modelDist.slice(0, 2).reduce((sum, model) => sum + model.value, 0) / Math.max(modelDist.reduce((sum, model) => sum + model.value, 0), 1)
    : 0;
  const sessionLoadStacked = sessionsPerDay.map((d) => ({
    x: d.day,
    series: [{ key: 'sessions', label: t.kpi.sessions, value: d.count, color: '#19d3d1' }],
  }));
  const sessionLoadTooltip = ({ row, total, valueFormat }) => `${row.x} · ${valueFormat(total)} ${t.misc.sessions.toLowerCase()}`;

  return (
    <div className="sessions-section">
      <div className="stat-grid">
        <StatCard letter="A" eyebrow={t.kpi.sessions} value={fmtNum(totalSessions)} delta={`${fmtNum(peakSessionDay.count)} ${t.misc.peak_load.toLowerCase()}`} color="cyan" barPct={78} />
        <StatCard letter="B" eyebrow={t.misc.active_days} value={activeDays} delta={`${latestSessionDay.day === '—' ? '—' : latestSessionDay.day.slice(-5)} · ${fmtNum(latestSessionDay.count)} ${t.misc.sessions.toLowerCase()}`} color="amber" barPct={64} />
        <StatCard letter="C" eyebrow={t.kpi.sessions_per_day} value={sessionsPerActiveDay.toFixed(1)} delta={t.misc.avg_per_day} color="green" barPct={72} />
        <StatCard letter="D" eyebrow={t.kpi.avg_duration} value={fmtDuration(S.avgDurationS)} delta={`${S.avgMessages} ${t.misc.msgs.toLowerCase()} · ${S.avgApiCalls} API`} color="gold" barPct={70} barColor="gold" />
      </div>

      <div className="grid-2-1">
        <Panel label={t.labels.session_load} letter="A" meta={`${activeDays}D · PEAK ${maxSpd} · ${t.misc.avg_per_day} ${sessionsPerActiveDay.toFixed(1)}`} gold className="sessions-panel sessions-panel-load">
          <div className="session-chip-grid session-chip-grid--wide">
            <div className="session-chip-card">
              <span>{t.misc.peak_day}</span>
              <strong>{peakSessionDay.day === '—' ? '—' : peakSessionDay.day.slice(-5)}</strong>
            </div>
            <div className="session-chip-card">
              <span>{t.misc.peak_load}</span>
              <strong>{peakSessionDay.count}</strong>
            </div>
            <div className="session-chip-card">
              <span>{t.misc.peak_share}</span>
              <strong>{(peakShare * 100).toFixed(0)}%</strong>
            </div>
            <div className="session-chip-card">
              <span>{t.misc.latest_load}</span>
              <strong>{latestSessionDay.count}</strong>
            </div>
          </div>
          <StackedBar data={sessionLoadStacked} height={200} valueFormat={fmtNum} tooltipFormat={sessionLoadTooltip} />
        </Panel>

        <Panel label={t.labels.typical_session} letter="B" meta={`${fmtDuration(S.avgDurationS)} · ${S.avgMessages} ${t.misc.msgs}`} className="sessions-panel sessions-panel-typical">
          <div className="session-metric-grid session-metric-grid--compact">
            <div className="session-metric-card">
              <div className="session-metric-value teal">{fmtCompact(S.avgTokens)}</div>
              <div className="session-metric-label">{t.kpi.tokens} / {t.misc.sessions}</div>
            </div>
            <div className="session-metric-card">
              <div className="session-metric-value cyan">{S.avgMessages}</div>
              <div className="session-metric-label">{t.misc.msgs} / {t.misc.sessions}</div>
            </div>
            <div className="session-metric-card">
              <div className="session-metric-value green">{S.avgApiCalls}</div>
              <div className="session-metric-label">{t.kpi.calls} / {t.misc.sessions}</div>
            </div>
            <div className="session-metric-card">
              <div className="session-metric-value amber">{S.avgTools}</div>
              <div className="session-metric-label">{t.kpi.tool_calls} / {t.misc.sessions}</div>
            </div>
          </div>
          <div className="session-model-callout">
            <span className="session-model-callout-label">{t.kpi.throughput_per_session}:</span> {S.avgThroughput} {t.kpi.throughput_label}
          </div>
        </Panel>
      </div>

      <Panel label={t.labels.model_mix} letter="C" meta={`${S.modelUsage.length} MODELS · TOP 2 ${(leadModelShare * 100).toFixed(0)}%`} gold className="sessions-panel sessions-panel-models">
        <div className="session-model-list">
          {modelDist.slice(0, 6).map((m, i) => (
            <div key={i} className="session-model-row">
              <span className="session-model-dot" style={{background:m.color}} />
              <span className="session-model-name">{m.label}</span>
              <span className="session-model-value">{m.value} {t.misc.sessions}</span>
            </div>
          ))}
        </div>
        <div className="session-model-callout">
          <span className="session-model-callout-label">{t.misc.lead_models}:</span> {topModelNames}
        </div>
        {activeModelEntries.length > 0 && (
          <div className="session-model-callout">
            <span className="session-model-callout-label">{t.kpi.active_models}:</span> {modelStr}
          </div>
        )}
      </Panel>
    </div>
  );
}

// =================================================
// SECTION 06 — SYSTEM PERFORMANCE
// =================================================
function SectionSystem({ t }) {
  const D = HERMES_DATA;
  const SH = D.systemHealth || {};
  const AG = D.agentLog || {};
  const collector = D.collector || {};
  const providerPatterns = (D.errors || []).filter((e) => PROVIDER_SIGNAL_RE.test(`${e.pattern} ${e.sources} ${e.tools || ''}`));
  const providerEventTotal = providerPatterns.reduce((sum, e) => sum + e.total, 0);
  const rateLimitEvents = providerPatterns
    .filter((e) => RATE_LIMIT_SIGNAL_RE.test(`${e.pattern} ${e.sources} ${e.tools || ''}`))
    .reduce((sum, e) => sum + e.total, 0);
  const authEvents = providerPatterns
    .filter((e) => AUTH_SIGNAL_RE.test(`${e.pattern} ${e.sources} ${e.tools || ''}`))
    .reduce((sum, e) => sum + e.total, 0);
  const hasProviderSignals = providerEventTotal > 0 || (SH.fallbackCount || 0) > 0;
  const collectorStatus = String(collector.lastStatus || 'unknown').toUpperCase();
  const latestCollectorTime = (collector.lastRun || '—').split(' ')[1] || collector.lastRun || '—';
  const nextCollectorTime = (collector.nextRun || '—').split(' ')[1] || collector.nextRun || '—';

  const heatmapValues = Array.isArray(D.heatmap) ? D.heatmap.flat().map((value) => Number(value) || 0) : [];
  const heatmapMax = Math.max(...heatmapValues, 1);
  const cellColor = (value) => {
    const intensity = (Number(value) || 0) / heatmapMax;
    if (intensity < 0.05) return '#0a1e3d';
    if (intensity < 0.15) return '#1565C0';
    if (intensity < 0.3)  return '#00ACC1';
    if (intensity < 0.5)  return '#8E24AA';
    if (intensity < 0.70) return '#E64A19';
    if (intensity < 0.85) return '#D32F2F';
    return '#B71C1C';
  };
  const cellText = (value) => {
    const intensity = (Number(value) || 0) / heatmapMax;
    return intensity < 0.25 ? '#9e9e9e' : '#ffffff';
  };

  const hourly = D.sessionMetrics?.sessionsPerDay?.length
    ? (() => {
        const hours = Array(24).fill(0);
        let total = 0;
        D.recentSessions?.forEach((s) => {
          const h = new Date(s.started).getHours();
          if (!isNaN(h)) { hours[h]++; total++; }
        });
        return hours.map((count, hour) => ({ hour, count, pct: total ? count / total : 0 }));
      })()
    : Array(24).fill(0).map((_, h) => ({ hour: h, count: 0, pct: 0 }));
  const maxHourly = Math.max(...hourly.map((h) => h.count), 1);
  const activeHourlyWindows = hourly.filter((h) => h.count > 0).length;
  const peakHourly = hourly.reduce(
    (peak, bucket) => (bucket.count > peak.count ? bucket : peak),
    hourly[0] || { hour: 0, count: 0, pct: 0 }
  );
  const nowH = new Date().getHours();
  const currentHourLoad = hourly[nowH] || { hour: nowH, count: 0, pct: 0 };
  const hourlyStacked = hourly.map((bucket) => ({
    x: `${String(bucket.hour).padStart(2, '0')}:00`,
    series: [{
      key: 'sessions',
      label: t.misc.sessions,
      value: bucket.count,
      color: bucket.hour === peakHourly.hour ? '#A855F7' : bucket.hour === nowH ? '#00D4B4' : '#0F766E',
    }],
  }));
  const hourlyTooltip = ({ row, total, valueFormat }) => `${row.x} · ${valueFormat(total)} ${t.misc.sessions.toLowerCase()}`;

  const errorTrend = SH.errorRateTrend || [];
  const latestErrorRate = errorTrend[errorTrend.length - 1]?.errorRate ?? SH.errorRate ?? 0;
  const errorRateSeries = errorTrend.length > 1
    ? [{
        key: 'errorRate',
        color: '#E84848',
        points: errorTrend.map((day) => ({ x: day.date, y: day.errorRate })),
      }]
    : [];

  const latencyTrend = (AG.trend || []).slice(-14);
  const latencySeries = latencyTrend.length > 1
    ? [{
        key: 'avgLatency',
        color: '#00D4B4',
        points: latencyTrend.map((day) => ({ x: day.date, y: day.avgTime })),
      }]
    : [];

  const otherProviderSignals = Math.max(providerEventTotal - rateLimitEvents - authEvents, 0);
  const providerMix = [
    { label: 'Rate limit', value: rateLimitEvents, color: '#E84848' },
    { label: 'Auth / OAuth', value: authEvents, color: '#06B6D4' },
    { label: 'Fallbacks', value: SH.fallbackCount || 0, color: '#FBBF24' },
    { label: 'Other provider', value: otherProviderSignals, color: '#A855F7' },
  ].filter((item) => item.value > 0);
  const providerMixTotal = providerMix.reduce((sum, item) => sum + item.value, 0);
  const providerMixTooltip = (item, total) => [
    item.label,
    `TOTAL ${fmtNum(item.value || 0)} incidents`,
    `${pct(item.value || 0, total, 1)}% ${t.kpi.provider_signals.toLowerCase()}`,
  ].join('\n');

  return (
    <div className="system-section">
      <div className="stat-grid">
        <StatCard letter="A" eyebrow={t.kpi.global_throughput} value={SH.globalThroughput} unit={t.kpi.throughput_label} delta={`${SH.totalSessions} ${t.misc.sessions}`} color="cyan" barPct={75} />
        <StatCard letter="B" eyebrow={t.kpi.tool_errors} value={SH.failedToolCalls} delta={`${SH.errorRate} / ${t.misc.sessions}`} color="red" barPct={Math.min(SH.errorRate * 10, 100)} />
        <StatCard letter="C" eyebrow={t.kpi.fallback_rate} value={SH.fallbackRate} delta={`${SH.fallbackCount} FALLBACKS · ${SH.sessionResetRate}% ${t.kpi.session_reset_rate}`} color="gold" barPct={Math.min(SH.fallbackRate*10, 100)} barColor="gold" />
        <StatCard
          letter="D"
          eyebrow={t.kpi.collector_status}
          value={SH.activeSessions > 0 ? `${SH.activeSessions} ACT` : collectorStatus}
          delta={`${t.kpi.last_run}: ${latestCollectorTime}${hasProviderSignals ? ` · ${fmtNum(providerEventTotal)} ${t.kpi.provider_signals.toLowerCase()}` : ''}`}
          color="green"
          barPct={100}
        />
      </div>

      <div className="grid-2-1">
        <Panel
          label={t.labels.sessions_per_hour}
          letter="A"
          meta={`24H · PEAK ${String(peakHourly.hour).padStart(2, '0')}:00 · ${fmtNum(peakHourly.count)} ${t.misc.sessions.toLowerCase()}`}
          gold
          className="system-panel system-panel--pulse"
        >
          <div className="system-chip-grid">
            <div className="system-chip-card">
              <span>Peak hour</span>
              <strong>{String(peakHourly.hour).padStart(2, '0')}:00</strong>
            </div>
            <div className="system-chip-card">
              <span>Peak load</span>
              <strong>{fmtNum(peakHourly.count)}</strong>
            </div>
            <div className="system-chip-card">
              <span>Current hour</span>
              <strong>{fmtNum(currentHourLoad.count)}</strong>
            </div>
            <div className="system-chip-card">
              <span>Active windows</span>
              <strong>{fmtNum(activeHourlyWindows)}</strong>
            </div>
          </div>
          {hourly.some((bucket) => bucket.count > 0) ? (
            <StackedBar data={hourlyStacked} height={200} valueFormat={fmtNum} tooltipFormat={hourlyTooltip} />
          ) : (
            <div className="system-empty-state">No session data by hour yet.</div>
          )}
        </Panel>

        <Panel
          label={t.kpi.avg_response_time}
          letter="B"
          meta={`${fmtNum(AG.totalResponses || 0)} RESPONSES · P95 ${AG.p95Time || 0}s`}
          className="system-panel system-panel--latency"
        >
          {AG.totalResponses > 0 ? (
            <>
              <div className="system-latency-grid">
                <div className="system-latency-card">
                  <div className="system-latency-value teal">{AG.medianTime}s</div>
                  <div className="system-latency-label">{t.kpi.median_response_time}</div>
                </div>
                <div className="system-latency-card">
                  <div className="system-latency-value cyan">{AG.avgTime}s</div>
                  <div className="system-latency-label">{t.kpi.avg_response_time}</div>
                </div>
                <div className="system-latency-card">
                  <div className="system-latency-value red">{AG.p95Time}s</div>
                  <div className="system-latency-label">{t.kpi.p95_response_time}</div>
                </div>
              </div>
              <div className="system-callout-grid">
                <div className="system-callout">
                  <span>Collector pulse</span>
                  <strong className="green">{collectorStatus}</strong>
                  <small>{latestCollectorTime} last run · {nextCollectorTime} next</small>
                </div>
                <div className="system-callout">
                  <span>Error pressure</span>
                  <strong className={latestErrorRate > 30 ? 'red' : latestErrorRate > 15 ? 'amber' : 'teal'}>{latestErrorRate}%</strong>
                  <small>{fmtNum(SH.failedToolCalls || 0)} failed tool calls</small>
                </div>
                <div className="system-callout">
                  <span>Fallback pressure</span>
                  <strong className="gold">{SH.fallbackCount || 0}</strong>
                  <small>{SH.sessionResetRate || 0}% {t.kpi.session_reset_rate.toLowerCase()}</small>
                </div>
              </div>
            </>
          ) : (
            <div className="system-empty-state">No response-time data available yet.</div>
          )}
        </Panel>
      </div>

      {(errorRateSeries.length > 0 || providerMix.length > 0 || latencySeries.length > 0) && (
        <div className="grid-2">
          {errorRateSeries.length > 0 && (
            <Panel
              label={t.labels.error_trend}
              letter="C"
              meta={`${latestErrorRate}% LATEST · ${errorTrend.length} DAYS`}
              gold
              className="system-panel system-panel--trend"
            >
              <div className="line-chart-wrap system-line-shell">
                <LineChart
                  series={errorRateSeries}
                  xLabels={errorTrend.map((day) => day.date)}
                  valueFormat={(value) => `${Math.round(value)}%`}
                />
              </div>
              <div className="system-panel-note">
                Latest incident pressure is <strong>{latestErrorRate}%</strong> with <strong>{fmtNum(SH.failedToolCalls || 0)}</strong> failed tool calls and <strong>{SH.sessionResetRate || 0}%</strong> interruptions.
              </div>
            </Panel>
          )}

          {providerMix.length > 0 ? (
            <Panel
              label={t.labels.provider_diagnostics}
              letter="D"
              meta={`${fmtNum(providerMixTotal)} SIGNALS · PROVIDER AWARE`}
              className="system-panel system-panel--providers"
            >
              <DonutWithLegend
                data={providerMix}
                centerValue={fmtNum(providerMixTotal)}
                centerLabel="SIGNALS"
                showLegendValues={false}
                tooltipFormat={providerMixTooltip}
                compact
              />
              <div className="system-provider-callouts">
                <div className="system-callout">
                  <span>{t.kpi.provider_signals}</span>
                  <strong className="gold">{fmtNum(providerEventTotal)}</strong>
                  <small>{fmtNum(rateLimitEvents)} rate-limit · {fmtNum(authEvents)} auth</small>
                </div>
                <div className="system-callout">
                  <span>{t.kpi.fallback_rate}</span>
                  <strong className="amber">{SH.fallbackRate || 0}</strong>
                  <small>{SH.fallbackCount || 0} fallbacks total</small>
                </div>
              </div>
            </Panel>
          ) : latencySeries.length > 0 ? (
            <Panel
              label={t.kpi.avg_response_time}
              letter="D"
              meta={`${latencyTrend.length} DAYS · LATENCY TREND`}
              className="system-panel system-panel--trend"
            >
              <div className="line-chart-wrap system-line-shell">
                <LineChart
                  series={latencySeries}
                  xLabels={latencyTrend.map((day) => day.date)}
                  valueFormat={(value) => `${value}s`}
                />
              </div>
              <div className="system-panel-note">
                Median is <strong>{AG.medianTime}s</strong>, average is <strong>{AG.avgTime}s</strong>, and current p95 sits at <strong>{AG.p95Time}s</strong>.
              </div>
            </Panel>
          ) : null}
        </div>
      )}

      {(D.heatmapModels?.length > 0 && D.heatmapTools?.length > 0) && (
        <Panel
          label={t.labels.heatmap}
          letter="E"
          meta={`${D.heatmapModels.length} × ${D.heatmapTools.length} · ERROR %`}
          gold
          className="system-panel system-panel--heatmap"
        >
          <div className="system-panel-note system-panel-note--heatmap">
            Scan for the hottest model × tool combinations first; saturated reds indicate the highest error-rate pockets in the current matrix.
          </div>
          <div className="heatmap-grid" style={{ gridTemplateColumns: `100px repeat(${D.heatmapTools.length}, 1fr)` }}>
            <div />
            {D.heatmapTools.map((toolName, index) => (
              <div key={index} className="heatmap-header">{toolName}</div>
            ))}
            {D.heatmapModels.map((modelName, modelIndex) => (
              <React.Fragment key={modelIndex}>
                <div className="heatmap-rowlabel">{modelName}</div>
                {(D.heatmap[modelIndex] || []).map((value, toolIndex) => (
                  <div
                    key={toolIndex}
                    className="heatmap-cell"
                    title={`${modelName} · ${D.heatmapTools[toolIndex]} · ${(value * 100).toFixed(1)}%`}
                    style={{ background: cellColor(value) }}
                  >
                    <span style={{ fontFamily: 'var(--font-m)', color: cellText(value), fontSize: 11, fontWeight: 600 }}>
                      {(value * 100).toFixed(1)}%
                    </span>
                  </div>
                ))}
              </React.Fragment>
            ))}
          </div>
        </Panel>
      )}

      <Panel
        label={t.kpi.collector_status}
        letter="F"
        meta={hasProviderSignals ? 'SYSTEM · PROVIDER AWARE' : 'SYSTEM INFO'}
        className="system-panel system-panel--facts"
      >
        <div className="system-info-grid">
          <div className="system-info-card"><span>{t.kpi.last_run}</span><strong className="green">{collector.lastRun}</strong></div>
          <div className="system-info-card"><span>{t.kpi.next_run}</span><strong className="teal">{collector.nextRun}</strong></div>
          <div className="system-info-card"><span>{t.misc.sessions}</span><strong>{SH.totalSessions}</strong></div>
          <div className="system-info-card"><span>{t.kpi.tool_calls}</span><strong>{fmtCompact(SH.totalToolCalls)}</strong></div>
          <div className="system-info-card"><span>WARNINGS</span><strong className="teal">{AG.warningCount}</strong></div>
          <div className="system-info-card"><span>AUDIO</span><strong>{AG.audioCount} {t.misc.calls}</strong></div>
          <div className="system-info-card"><span>FALLBACKS</span><strong className="gold">{SH.fallbackCount}</strong></div>
          <div className="system-info-card"><span>{t.kpi.avg_api_calls}</span><strong>{AG.avgApiCalls}</strong></div>
          {hasProviderSignals && (
            <>
              <div className="system-info-card"><span>{t.kpi.provider_signals}</span><strong className="gold">{fmtNum(providerEventTotal)}</strong></div>
              <div className="system-info-card"><span>RATE LIMIT</span><strong className="amber">{fmtNum(rateLimitEvents)}</strong></div>
              <div className="system-info-card"><span>AUTH/OAUTH</span><strong className="cyan">{fmtNum(authEvents)}</strong></div>
            </>
          )}
        </div>
      </Panel>
    </div>
  );
}
