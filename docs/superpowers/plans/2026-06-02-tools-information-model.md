# Tools Information Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign only the `Tools` tab so `Tool calls` is the primary identity metric while preserving breadth, reliability, latency, concentration, and per-tool inspection.

**Architecture:** Keep the current Flask API and runtime React/Babel frontend. Reuse the existing chart primitives and tooltip-offloading support already added for `Overview`; reshape only `SectionTools`, scoped i18n labels, and narrowly scoped CSS.

**Tech Stack:** Python/Flask backend data source, React 18 UMD with runtime JSX, CSS custom properties in `api/static/styles.css`, existing `StackedBar`, `DonutWithLegend`, `Legend`, `Panel`, and `OverviewMetricCard` components.

---

## File Map

- Modify `api/static/sections.jsx`: Replace `SectionTools` calculations and layout with the approved information model. Add a small `ToolIdentityCard` helper near `SectionTools`.
- Modify `api/static/i18n.js`: Add English and Spanish labels for calls/session, active tool days, failed calls, average/day, most used, and top tools.
- Modify `api/static/styles.css`: Add scoped styles for the `Tools` identity card and top KPI grid. Reuse existing table/chart classes.
- No backend files change in this implementation.
- No tests are required for pure runtime JSX layout, but verification must include `/api/all`, browser render, tooltip behavior, and console errors.

## Implementation Tasks

### Task 1: Add Tool-Specific Calculation Helpers

**Files:**
- Modify: `api/static/sections.jsx`

- [ ] **Step 1: Locate the existing `SectionTools` block**

Run:

```powershell
rg -n --hidden -A 120 "function SectionTools" "C:/Users/Cristian Valverde/Git Repos/hermes-dashboard/api/static/sections.jsx"
```

Expected: Output starts at `function SectionTools({ t })` and shows the current stat cards, chips, stacked bar, donut, and ranking table.

- [ ] **Step 2: Add `ToolIdentityCard` before `SectionTools`**

Insert this helper immediately above `function SectionTools({ t })`:

```jsx
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
```

- [ ] **Step 3: Replace the calculation section at the top of `SectionTools`**

Replace the lines from `const totalCalls = ...` through `const toolDist = ...` with this code:

```jsx
  const totalCalls = D.tools.reduce((s, x) => s + (x.count || 0), 0);
  const totalSessions = Math.max(D.totals.sessions || 0, 1);
  const activeToolDays = Object.values(D.toolDaily || {}).filter((dailyTools) =>
    Object.values(dailyTools || {}).reduce((sum, value) => sum + (value || 0), 0) > 0
  ).length;
  const avgDailyCalls = Math.round(totalCalls / Math.max(activeToolDays || D.totals.daysActive || 1, 1));
  const callsPerSession = totalCalls / totalSessions;
  const avgSuccess = totalCalls > 0
    ? D.tools.reduce((s, x) => s + ((x.success || 0) * (x.count || 0)), 0) / totalCalls
    : 0;
  const failedCalls = Math.round(totalCalls * (1 - avgSuccess));
  const avgDurationMs = Math.round(
    D.tools.reduce((s, x) => s + ((x.durMs || 0) * (x.count || 0)), 0) / Math.max(totalCalls, 1)
  );
  const topToolName = D.tools[0]?.name || '—';
  const topTools = [...D.tools].slice(0, 6);
  const topToolCount = D.tools[0]?.count || 1;
  const toolDaily = D.days.map((date) => ({
    x: date,
    series: topTools.map((tool, ti) => {
      const dayCount = D.toolDaily && D.toolDaily[date] ? D.toolDaily[date][tool.name] || 0 : 0;
      return { key: tool.name, label: tool.name, value: dayCount, color: D.toolColors[ti] || donutColor(ti) };
    }),
  }));
  const toolDist = D.tools.map((tool, i) => ({
    label: tool.name,
    value: tool.count || 0,
    color: D.toolColors[i] || donutColor(i),
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
```

- [ ] **Step 4: Run a syntax-focused source scan**

Run:

```powershell
rg -n --hidden "ToolIdentityCard|dailyToolTooltip|toolLegendTooltip|toolDistributionTooltip|topToolCount" "C:/Users/Cristian Valverde/Git Repos/hermes-dashboard/api/static/sections.jsx"
```

Expected: Each helper name appears in `sections.jsx`. `topToolCount` appears in calculations and table bar width after Task 4.

### Task 2: Replace the Top Tools Layer

**Files:**
- Modify: `api/static/sections.jsx`

- [ ] **Step 1: Replace the first `<div className="stat-grid">...</div>` in `SectionTools`**

Replace the current four `StatCard` top row with:

```jsx
      <div className="tools-top-grid">
        <ToolIdentityCard
          totalCalls={totalCalls}
          avgDailyCalls={avgDailyCalls}
          activeToolDays={activeToolDays}
          callsPerSession={callsPerSession}
          t={t}
        />
        <OverviewMetricCard letter="B" label={t.kpi.unique_tools} value={fmtNum(D.tools.length)} color="gold">
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
```

- [ ] **Step 2: Confirm no old ambiguous top metric remains**

Run:

```powershell
rg -n --hidden "sessions_with_tools|AVG .*TOOLS / SES|MOST USED ·" "C:/Users/Cristian Valverde/Git Repos/hermes-dashboard/api/static/sections.jsx"
```

Expected: No matches inside `SectionTools`.

### Task 3: Apply Tooltip Offloading to Tools Charts

**Files:**
- Modify: `api/static/sections.jsx`

- [ ] **Step 1: Remove the repeated chip cards from the daily usage panel**

Delete this block from the `t.labels.tool_usage` panel:

```jsx
          <div className="tools-chip-grid">
            <div className="tools-chip-card">
              <span>MOST USED</span>
              <strong>{topToolName}</strong>
            </div>
            <div className="tools-chip-card">
              <span>{t.kpi.success_rate}</span>
              <strong>{(avgSuccess * 100).toFixed(1)}%</strong>
            </div>
            <div className="tools-chip-card">
              <span>AVG DURATION</span>
              <strong>{avgDurationMs} ms</strong>
            </div>
          </div>
```

- [ ] **Step 2: Replace the chart and legend calls in the daily usage panel**

Use this code:

```jsx
          <StackedBar data={toolDaily} valueFormat={fmtCompact} tooltipFormat={dailyToolTooltip} />
          <Legend
            items={topTools.map((tool, i) => ({
              label: tool.name,
              color: D.toolColors[i] || donutColor(i),
              value: tool.count || 0,
            }))}
            tooltipFormat={toolLegendTooltip}
          />
```

- [ ] **Step 3: Replace the distribution donut call**

Use this code:

```jsx
          <DonutWithLegend
            data={toolDist.slice(0, 8)}
            centerValue={fmtCompact(totalCalls)}
            centerLabel="CALLS"
            showLegendValues={false}
            tooltipFormat={toolDistributionTooltip}
          />
```

- [ ] **Step 4: Confirm chart tooltip props are present**

Run:

```powershell
rg -n --hidden "tooltipFormat=\\{dailyToolTooltip\\}|tooltipFormat=\\{toolLegendTooltip\\}|tooltipFormat=\\{toolDistributionTooltip\\}|showLegendValues=\\{false\\}" "C:/Users/Cristian Valverde/Git Repos/hermes-dashboard/api/static/sections.jsx"
```

Expected: Four matches.

### Task 4: Tighten the Ranking Table Calculations

**Files:**
- Modify: `api/static/sections.jsx`

- [ ] **Step 1: Replace the table body row mapping**

Replace the current `{D.tools.map((tool, i) => (` table body mapping with this version:

```jsx
              {D.tools.map((tool, i) => {
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
                      <div className="tool-bar-fill" style={{ width: `${(toolCount / topToolCount) * 100}%`, background: D.toolColors[i % D.toolColors.length] || donutColor(i) }} />
                    </div>
                  </td>
                </tr>
              )})}
```

- [ ] **Step 2: Confirm success values visibly include `%`**

Run:

```powershell
rg -n --hidden "successPct|\\{successPct\\}%" "C:/Users/Cristian Valverde/Git Repos/hermes-dashboard/api/static/sections.jsx"
```

Expected: Both `successPct` assignment and `{successPct}%` appear.

### Task 5: Add Missing i18n Labels

**Files:**
- Modify: `api/static/i18n.js`

- [ ] **Step 1: Add Spanish KPI keys**

In the Spanish `kpi` object, add these keys near the existing tool keys:

```js
      tool_invocations: 'INVOCACIONES DE HERRAMIENTAS',
      active_tool_days: 'DÍAS CON TOOLS',
      avg_daily_calls: 'MEDIA / DÍA',
      calls_per_session: 'CALLS / SESIÓN',
      failed_calls: 'CALLS FALLIDAS',
      most_used: 'MÁS USADA',
```

- [ ] **Step 2: Add English KPI keys**

In the English `kpi` object, add these keys near the existing tool keys:

```js
      tool_invocations: 'TOOL INVOCATIONS',
      active_tool_days: 'ACTIVE TOOL DAYS',
      avg_daily_calls: 'AVG / DAY',
      calls_per_session: 'CALLS / SESSION',
      failed_calls: 'FAILED CALLS',
      most_used: 'MOST USED',
```

- [ ] **Step 3: Confirm all new keys exist twice**

Run:

```powershell
rg -n --hidden "tool_invocations|active_tool_days|avg_daily_calls|calls_per_session|failed_calls|most_used" "C:/Users/Cristian Valverde/Git Repos/hermes-dashboard/api/static/i18n.js"
```

Expected: Twelve matches: six keys in Spanish and six keys in English.

### Task 6: Add Scoped Tools Layout CSS

**Files:**
- Modify: `api/static/styles.css`

- [ ] **Step 1: Add desktop styles near the existing `.stat-grid` and `.overview-kpi-card` blocks**

Add this CSS:

```css
.tools-top-grid {
  display: grid;
  grid-template-columns: 1.35fr repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
  animation: statFadeIn 500ms var(--ease) both;
}

.tools-identity-card {
  min-height: 164px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  border-color: var(--amber-border);
  background:
    linear-gradient(135deg, rgba(232, 197, 71, 0.14), rgba(0, 212, 180, 0.05)),
    var(--panel-bg);
}

.tools-identity-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-family: var(--font-m);
  font-size: 10px;
  color: var(--text-muted);
  letter-spacing: 0;
  text-transform: uppercase;
}

.tools-identity-value {
  font-family: var(--font-m);
  font-size: 40px;
  line-height: 1;
  color: var(--amber);
  text-shadow: 0 0 14px var(--amber-dim);
}

.tools-identity-caption {
  font-family: var(--font-m);
  font-size: 11px;
  color: var(--text);
  text-transform: uppercase;
}

.tools-identity-foot {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tools-identity-foot span {
  padding: 5px 7px;
  border: 1px solid var(--line);
  background: rgba(244, 241, 232, 0.04);
  color: var(--text-muted);
  font-family: var(--font-m);
  font-size: 10px;
  line-height: 1.2;
  text-transform: uppercase;
}
```

- [ ] **Step 2: Add responsive styles inside the existing max-width media sections**

Inside the media query that collapses dashboard grids, add:

```css
  .tools-top-grid {
    grid-template-columns: 1fr 1fr;
  }
```

Inside the narrow mobile media query, add:

```css
  .tools-top-grid {
    grid-template-columns: 1fr;
  }

  .tools-identity-value {
    font-size: 34px;
  }
```

- [ ] **Step 3: Confirm scoped CSS exists**

Run:

```powershell
rg -n --hidden "tools-top-grid|tools-identity-card|tools-identity-value|tools-identity-foot" "C:/Users/Cristian Valverde/Git Repos/hermes-dashboard/api/static/styles.css"
```

Expected: Desktop and responsive rules are present.

### Task 7: Verify API and Browser Behavior

**Files:**
- Read-only verification

- [ ] **Step 1: Verify `/api/all` is healthy**

Run:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:8590/api/all
```

Expected: HTTP status code `200`.

- [ ] **Step 2: If the server is not running, start it with the Hermes venv Python**

Run:

```powershell
python "C:/Users/Cristian Valverde/Git Repos/hermes-dashboard/api/flask_app.py"
```

Expected: Flask serves the dashboard on `http://localhost:8590`.

- [ ] **Step 3: Open the local dashboard and select `Tools`**

Use the Browser plugin to open:

```text
http://127.0.0.1:8590/
```

Expected visible state:

- Top layer shows one dominant `Tool calls` identity card.
- Supporting cards show `Unique tools`, `Success rate`, and `Avg duration`.
- Daily chart legend shows tool names without visible accumulated totals.
- Distribution donut legend shows tool names without visible accumulated totals.
- Ranking table shows calls, share, success with `%`, duration with `ms`, and volume bars.

- [ ] **Step 4: Verify tooltip offloading**

In the browser, hover or focus:

- A daily stacked bar column.
- A tool legend item.
- A donut segment or donut legend row.

Expected:

- Daily tooltip includes date, total calls for that day, and per-tool daily calls.
- Legend tooltip includes accumulated calls and percentage share.
- Donut tooltip includes total calls, percentage share, success percentage, and duration.

- [ ] **Step 5: Check browser console**

Expected:

- No runtime errors from `sections.jsx`.
- The known Babel standalone warning may remain.

### Task 8: Commit the UI Change

**Files:**
- Commit: `api/static/sections.jsx`
- Commit: `api/static/i18n.js`
- Commit: `api/static/styles.css`

- [ ] **Step 1: Review changed files**

Run:

```powershell
git -C "C:/Users/Cristian Valverde/Git Repos/hermes-dashboard" diff -- api/static/sections.jsx api/static/i18n.js api/static/styles.css
```

Expected: Diff only changes the `Tools` tab, scoped i18n keys, and scoped CSS. It must not redesign other tabs.

- [ ] **Step 2: Stage only the Tools UI files**

Run:

```powershell
git -C "C:/Users/Cristian Valverde/Git Repos/hermes-dashboard" add -- api/static/sections.jsx api/static/i18n.js api/static/styles.css
```

Expected: Only those three files are staged.

- [ ] **Step 3: Confirm staged files**

Run:

```powershell
git -C "C:/Users/Cristian Valverde/Git Repos/hermes-dashboard" diff --cached --name-only
```

Expected:

```text
api/static/i18n.js
api/static/sections.jsx
api/static/styles.css
```

- [ ] **Step 4: Commit**

Run:

```powershell
git -C "C:/Users/Cristian Valverde/Git Repos/hermes-dashboard" commit -m "feat: refine tools information model"
```

Expected: Commit succeeds with only the three staged UI files.

## Self-Review Notes

- Spec coverage: The plan implements `Tool calls` as the primary identity metric, four supporting metrics, daily tooltip offloading, distribution tooltip offloading, legend totals in tooltips, ranking table inspection, and terminology cleanup.
- Marker scan: This plan contains no unresolved markers, empty test instructions, or deferred implementation steps.
- Type consistency: All new frontend labels are accessed through `t.kpi.*`; chart tooltip callbacks use the existing `StackedBar`, `Legend`, and `DonutWithLegend` callback shapes already present in `components.jsx`.
