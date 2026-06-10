# Tools Information Model Design

Date: 2026-06-02
Scope: `Tools` tab only

## Decision

The `Tools` tab identity metric is total `Tool calls`. The page should treat tool usage as an operational volume map, then explain that volume through breadth, reliability, latency, concentration, and per-tool inspection.

## User Goal

The first scan should answer how much tool usage happened. The rest of the page should include all important aspects of tool usage without making secondary details compete with the main metric.

## Information Model

Primary metric:

- `Tool calls`: total tool invocations across the selected data window.

Supporting first-scan metrics:

- `Unique tools`: number of distinct tool names used.
- `Success rate`: weighted by call count, not a simple unweighted average across tools.
- `Avg duration`: weighted by call count, using the current average duration data.
- `Calls / session`: tool usage intensity across sessions.

Secondary context:

- Most used tool.
- Failed call count.
- Average calls per active day.
- Active tool days derived from `D.toolDaily` dates whose per-tool counts sum above zero.

Tooltip-only details:

- Daily stacked bar totals and per-tool daily breakdown.
- Distribution donut exact counts and percentage share.
- Legend accumulated totals for each tool.
- Exact supporting values when they are useful for inspection but not part of first-scan reading.

## Layout

Top layer:

- A `Tool calls` identity card with the largest metric on the page.
- Four supporting KPI cards for unique tools, success rate, average duration, and calls per session.
- Avoid repeating `Tool calls` as both a large metric and a visible total in every chart legend.

Middle layer:

- Daily stacked tool usage for the top six tools.
- Visible chart answers when usage happened and which tools drove it.
- Tooltip exposes the daily total and per-tool call counts.
- Legend shows color plus tool name only; accumulated totals move to tooltips.

Side layer:

- Tool distribution donut for the top eight tools.
- Visible chart answers concentration and relative dominance.
- Tooltip exposes exact calls and percentage share.
- Center label can show compact total calls because this chart interprets the same metric as distribution, not as a duplicate KPI card.

Inspection layer:

- Ranking table remains visible because it is the detailed operational inspection surface.
- Columns: rank, tool name, calls, share, success %, average duration, and volume bar.
- Table remains sorted by call count descending.

## Terminology

- Use `Tool calls` when referring to invocation counts.
- Use `Calls` in compact table/chart contexts where the surrounding section is already about tools.
- Use `Unique tools` for count of distinct tool names.
- Use `Tool` or actual tool names only for identifiers, not invocation counts.
- Avoid plain `Tools` for counts because it is ambiguous between unique tools and calls.

## Data Requirements

Current frontend/API data is sufficient for the first implementation:

- `D.tools`: per-tool name, count, success ratio, average duration, and color.
- `D.toolDaily`: per-day counts by tool.
- `D.days`: date axis.
- `D.totals.toolCalls`, `D.totals.sessions`, and `D.totals.daysActive`.

No backend change is required for the initial UI pass. If a later version needs slowest frequent tool, active tool days, or tool/session coverage as canonical fields, add those as explicit API fields instead of recomputing them inconsistently in multiple components.

## Component Strategy

Reuse existing primitives:

- `StackedBar` already supports `tooltipFormat`.
- `DonutWithLegend` already supports `tooltipFormat` and hidden legend values.
- `Legend` already supports `tooltipFormat`.
- Existing KPI/card styling from the validated `Overview` tab can guide the first-scan card pattern.

Add only narrowly scoped `Tools` classes if needed for the identity card and supporting KPI row. Do not redesign other tabs.

## Verification

After implementation:

- Verify `/api/all` returns HTTP 200.
- Open `http://127.0.0.1:8590/` and inspect the `Tools` tab.
- Clear or bypass runtime Babel cache if JSX output appears stale.
- Confirm visible labels distinguish `Tool calls`, `Unique tools`, and tool names.
- Confirm stacked bar, donut, and legend tooltips expose the offloaded totals.
- Confirm no runtime errors appear in browser console.

## Out of Scope

- Redesigning `Tokens`, `Errors`, `Sessions`, or `System`.
- Changing backend schema or collector behavior.
- General dashboard-wide style refactors.
