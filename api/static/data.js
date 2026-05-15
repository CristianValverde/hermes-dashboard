// Placeholder data for Hermes Dashboard — based on Blueprint cifras reales
// 78 sesiones, 6 modelos, 65M tokens, 2,875 tool calls

window.HERMES_DATA = (() => {
  const models = [
    { id: 'deepseek/deepseek-v4-pro',   short: 'DSV4 PRO',   color: '#F59E0B' }, // amber
    { id: 'deepseek/deepseek-v4-flash', short: 'DSV4 FLASH', color: '#00D4B4' }, // cyan
    { id: 'deepseek/deepseek-v3.2',     short: 'DSV3.2',     color: '#E84848' }, // coral red
    { id: 'anthropic/claude-haiku-4.5', short: 'HAIKU 4.5',  color: '#39D966' }, // hud green
    { id: 'openai/gpt-5-mini',          short: 'GPT-5 MINI', color: '#A855F7' }, // purple
    { id: 'google/gemini-3-flash',      short: 'GMN-3 FL',   color: '#EAB308' }, // gold-bright
  ];

  // 14 days back from May 14, 2026
  const days = [];
  const today = new Date('2026-05-14');
  for (let i = 13; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    days.push(d.toISOString().slice(0, 10));
  }

  // Deterministic-ish noise
  const rng = (seed) => {
    let x = Math.sin(seed) * 10000;
    return x - Math.floor(x);
  };

  // Tokens per model per day (sums approx 65M total)
  const tokensPerDay = days.map((date, i) => {
    const row = { date };
    models.forEach((m, j) => {
      const base = [2400000, 1900000, 1300000, 700000, 350000, 180000][j];
      const noise = 0.5 + rng(i * 7 + j * 13) * 1.0;
      row[m.id] = Math.round(base * noise);
    });
    return row;
  });

  // Tools data
  const tools = [
    { name: 'read_file',     count: 612, success: 0.988, durMs: 47  },
    { name: 'write_file',    count: 421, success: 0.971, durMs: 92  },
    { name: 'edit_file',     count: 387, success: 0.949, durMs: 71  },
    { name: 'bash',          count: 354, success: 0.892, durMs: 184 },
    { name: 'grep',          count: 298, success: 0.997, durMs: 38  },
    { name: 'list_files',    count: 241, success: 0.999, durMs: 22  },
    { name: 'web_search',    count: 187, success: 0.913, durMs: 412 },
    { name: 'web_fetch',     count: 143, success: 0.825, durMs: 631 },
    { name: 'eval_js',       count: 98,  success: 0.954, durMs: 156 },
    { name: 'show_html',     count: 67,  success: 1.000, durMs: 84  },
    { name: 'save_screenshot', count: 49, success: 0.918, durMs: 287 },
    { name: 'run_script',    count: 18,  success: 0.889, durMs: 1024 },
  ];
  // total = 2875

  const toolColors = [
    '#F59E0B', // amber
    '#00D4B4', // cyan
    '#E84848', // coral red
    '#39D966', // hud green
    '#A855F7', // purple
    '#EAB308', // gold-bright
    '#EC4899', // neon pink
    '#F97316', // orange
    '#06B6D4', // cyan-light
    '#84CC16', // lime
    '#FBBF24', // amber-bright
    '#D946EF', // magenta
  ];

  // Sources
  const sources = [
    { name: 'telegram', count: 52, color: '#00D4B4' }, // cyan
    { name: 'cli',      count: 21, color: '#F59E0B' }, // amber
    { name: 'api',      count: 5,  color: '#A855F7' }, // purple
  ];

  // Recent sessions (10)
  const recentSessions = [
    { id: 'a4dc..ae3f', started: '2026-05-14 18:42', model: 'deepseek/deepseek-v4-pro',   source: 'telegram', msgs: 47, tools: 32, tokens: 1842300, cost: 1.24 },
    { id: '7b2e..91cf', started: '2026-05-14 17:18', model: 'deepseek/deepseek-v4-flash', source: 'cli',      msgs: 22, tools: 14, tokens: 612400,  cost: 0.31 },
    { id: 'f1aa..82bd', started: '2026-05-14 15:03', model: 'anthropic/claude-haiku-4.5', source: 'telegram', msgs: 18, tools: 8,  tokens: 287100,  cost: 0.42 },
    { id: '9c41..70b1', started: '2026-05-14 13:27', model: 'deepseek/deepseek-v4-pro',   source: 'telegram', msgs: 64, tools: 51, tokens: 2104800, cost: 1.61 },
    { id: '3e88..ad42', started: '2026-05-14 11:55', model: 'deepseek/deepseek-v3.2',     source: 'cli',      msgs: 12, tools: 5,  tokens: 184200,  cost: 0.08 },
    { id: 'b6f3..29e7', started: '2026-05-14 10:31', model: 'deepseek/deepseek-v4-flash', source: 'telegram', msgs: 31, tools: 19, tokens: 891700,  cost: 0.44 },
    { id: '5a17..ff8c', started: '2026-05-14 09:12', model: 'openai/gpt-5-mini',          source: 'api',      msgs: 8,  tools: 3,  tokens: 92400,   cost: 0.19 },
    { id: '2d99..614a', started: '2026-05-13 22:48', model: 'deepseek/deepseek-v4-pro',   source: 'telegram', msgs: 55, tools: 41, tokens: 1721000, cost: 1.18 },
    { id: 'e0c5..73d2', started: '2026-05-13 20:14', model: 'deepseek/deepseek-v4-flash', source: 'cli',      msgs: 27, tools: 16, tokens: 743200,  cost: 0.37 },
    { id: '8f4b..a063', started: '2026-05-13 18:01', model: 'anthropic/claude-haiku-4.5', source: 'telegram', msgs: 14, tools: 6,  tokens: 219800,  cost: 0.34 },
  ];

  // Errors data (for Errors & Performance tab)
  const errors = [
    { pattern: 'rate limit exceeded for model anthropic',     total: 47, unresolved: 12, sources: 'api,tool_call',  firstSeen: '2026-05-08', lastSeen: '2026-05-14' },
    { pattern: 'connection timeout to openrouter endpoint',    total: 34, unresolved: 8,  sources: 'api',            firstSeen: '2026-05-06', lastSeen: '2026-05-14' },
    { pattern: 'tool execution failed: web_fetch invalid url', total: 28, unresolved: 5,  sources: 'tool_call',      firstSeen: '2026-05-09', lastSeen: '2026-05-13' },
    { pattern: 'json decode error in response payload',        total: 21, unresolved: 3,  sources: 'collector',      firstSeen: '2026-05-04', lastSeen: '2026-05-12' },
    { pattern: 'session terminated: max_turns reached',        total: 19, unresolved: 0,  sources: 'agent',          firstSeen: '2026-05-02', lastSeen: '2026-05-14' },
    { pattern: 'context length exceeded for deepseek model',   total: 16, unresolved: 4,  sources: 'api',            firstSeen: '2026-05-07', lastSeen: '2026-05-13' },
    { pattern: 'database lock timeout on state.db',             total: 12, unresolved: 2,  sources: 'agent',          firstSeen: '2026-05-05', lastSeen: '2026-05-11' },
    { pattern: 'auth: invalid bearer token',                    total: 9,  unresolved: 1,  sources: 'api',            firstSeen: '2026-05-03', lastSeen: '2026-05-10' },
    { pattern: 'shell command exited with code 127',           total: 7,  unresolved: 0,  sources: 'tool_call',      firstSeen: '2026-05-09', lastSeen: '2026-05-12' },
    { pattern: 'subprocess killed by sigterm',                  total: 5,  unresolved: 0,  sources: 'tool_call',      firstSeen: '2026-05-06', lastSeen: '2026-05-09' },
  ];
  errors.forEach(e => e.priority = +(e.total * (1 + e.unresolved / e.total)).toFixed(1));

  // Error trend per day
  const errorTrend = days.map((date, i) => {
    const noise = (n) => Math.max(0, Math.round(n + rng(i * 31 + n) * 6 - 2));
    return {
      date,
      api:      noise(8),
      tool:     noise(5),
      agent:    noise(3),
      collector: noise(1),
    };
  });

  // Heatmap: error rate per model x tool (system performance)
  const heatmapModels = ['DSV4 PRO', 'DSV4 FLASH', 'DSV3.2', 'HAIKU 4.5', 'GPT-5 MINI', 'GMN-3 FL'];
  const heatmapTools = ['read_file', 'write_file', 'edit_file', 'bash', 'grep', 'web_fetch', 'web_search'];
  const heatmap = heatmapModels.map((m, mi) =>
    heatmapTools.map((t, ti) => {
      // base rate per tool
      const baseFail = [0.012, 0.029, 0.051, 0.108, 0.003, 0.175, 0.087][ti];
      const modelMult = [0.8, 1.0, 1.1, 0.9, 1.2, 1.4][mi];
      return +(baseFail * modelMult).toFixed(3);
    })
  );

  // OpenRouter credits
  const openRouter = {
    totalCredits: 50.00,
    totalUsage:   30.52,
    today:        0.6512,
    week:         12.959,
    month:        30.520,
    keyLimit:     50.00,
  };

  // Collector status
  const collector = {
    cronId: 'a4dcdae4dd65',
    lastRun: '2026-05-14 18:55:23',
    lastStatus: 'success',
    sessionsAdded: 3,
    nextRun: '2026-05-14 19:55:00',
  };

  // Totals (derived but pinned to Blueprint cifras)
  const totals = {
    sessions: 78,
    models: 6,
    tokens: 65_000_000,
    toolCalls: 2_875,
    daysActive: 14,
    inputTokens: 24_700_000,
    outputTokens: 21_450_000,
    cacheReadTokens: 11_700_000,
    cacheWriteTokens: 4_550_000,
    reasoningTokens: 2_600_000,
  };

  return { models, days, tokensPerDay, tools, toolColors, sources, recentSessions, errors, errorTrend, heatmap, heatmapModels, heatmapTools, openRouter, collector, totals };
})();

// i18n strings (ES default, EN alt)
window.HERMES_I18N = {
  es: {
    nav: { overview: 'OVERVIEW', tools: 'HERRAMIENTAS', tokens: 'TOKENS', errors: 'ERRORES', system: 'SISTEMA' },
    section_eyebrow: {
      overview: 'PANEL GENERAL · SUMMARY',
      tools: 'ANALÍTICA DE HERRAMIENTAS · TOOL OPS',
      tokens: 'ANALÍTICA DE TOKENS · CONSUMPTION',
      errors: 'INCIDENCIAS · ERROR LOG',
      system: 'PERFORMANCE DE SISTEMA · DIAGNOSTICS',
    },
    kpi: {
      sessions: 'SESIONES', tokens: 'TOKENS TOTALES', spent: 'GASTADO', models: 'MODELOS',
      tool_calls: 'LLAMADAS A HERRAMIENTAS', unique_tools: 'TOOLS ÚNICOS', success_rate: 'TASA DE ÉXITO', sessions_with_tools: 'SESIONES CON TOOLS',
      credit_used: 'CRÉDITO USADO', credit_remaining: 'CRÉDITO RESTANTE', cost_per_million: 'USD / 1M TOKENS',
      errors_total: 'ERRORES TOTALES', sources_count: 'ORÍGENES', unresolved: 'SIN RESOLVER', tool_errors: 'ERRORES DE TOOLS',
      uptime: 'UPTIME', avg_latency: 'LATENCIA MEDIA', error_rate: 'ERROR RATE', cron_status: 'COLECTOR',
    },
    labels: {
      tokens_by_model: 'TOKENS POR MODELO · DIARIO',
      source_dist: 'DISTRIBUCIÓN POR ORIGEN',
      recent_sessions: 'SESIONES RECIENTES',
      tool_usage: 'USO DE HERRAMIENTAS · DIARIO',
      tool_dist: 'DISTRIBUCIÓN DE HERRAMIENTAS',
      top_tools: 'RANKING DE HERRAMIENTAS',
      model_ranking: 'RANKING DE MODELOS POR TOKENS',
      daily_consumption: 'CONSUMO DIARIO POR MODELO',
      token_breakdown: 'DESGLOSE POR TIPO',
      cost_by_model: 'COSTE REAL POR MODELO',
      filters: 'FILTROS',
      clustering: 'CLUSTERING POR PATRÓN · PRIORIZADO',
      error_trend: 'TENDENCIA DE ERRORES · 14D',
      heatmap: 'MATRIZ ERROR RATE · MODELO × HERRAMIENTA',
      daily_error_rate: 'ERROR RATE DIARIO',
      latency_dist: 'DISTRIBUCIÓN DE LATENCIA',
      sessions_per_hour: 'SESIONES POR HORA DEL DÍA',
      collector_status: 'COLECTOR · STATUS',
      openrouter_credits: 'OPENROUTER · CRÉDITOS',
    },
    table: { date: 'FECHA', model: 'MODELO', source: 'ORIGEN', msgs: 'MSG', tools: 'TOOLS', tokens: 'TOKENS', cost: 'COSTE', id: 'ID', tool: 'HERRAMIENTA', calls: 'LLAMADAS', success: 'ÉXITO', duration: 'DURACIÓN', pct: 'PCT', priority: 'PRIO', total: 'TOT', unresolved: 'PEND', pattern: 'PATRÓN', first_seen: 'PRIMER', last_seen: 'ÚLTIMO', sessions: 'SES' },
    misc: {
      active: 'ACTIVO', last_run: 'ÚLTIMA EJECUCIÓN', next_run: 'PRÓXIMA', cron: 'CRON', used: 'USADO', remaining: 'RESTANTE',
      today: 'HOY', week: 'SEMANA', month: 'MES', total: 'TOTAL',
      mgmt_key: 'MANAGEMENT KEY · COMPARATIVA EXACTA',
      mgmt_key_msg: 'Añade tu Management Key en ~/.hermes/.env como OPENROUTER_MANAGEMENT_KEY=sk-or-v1-... para ver comparativa Hermes vs OpenRouter.',
      get_key: 'CONSEGUIR KEY',
      page: 'PÁG',
      all: 'TODAS',
      resolved_all: 'ESTADO',
      resolved_yes: '✓ RESUELTOS',
      resolved_no: '✗ NO RESUELTOS',
      filtered_of: 'FILTRADOS DE',
      source: 'ORIGEN',
      type: 'TIPO',
      tool: 'TOOL',
    },
    flavor: 'HERMES AGENT TELEMETRY · MONITORED INSTANCE · CC35 CERTIFIED · CORE TEAM MEMBERS ONLY',
  },
  en: {
    nav: { overview: 'OVERVIEW', tools: 'TOOLS', tokens: 'TOKENS', errors: 'ERRORS', system: 'SYSTEM' },
    section_eyebrow: {
      overview: 'GENERAL PANEL · SUMMARY',
      tools: 'TOOL ANALYTICS · OPS',
      tokens: 'TOKEN ANALYTICS · CONSUMPTION',
      errors: 'INCIDENTS · ERROR LOG',
      system: 'SYSTEM PERFORMANCE · DIAGNOSTICS',
    },
    kpi: {
      sessions: 'SESSIONS', tokens: 'TOTAL TOKENS', spent: 'SPENT', models: 'MODELS',
      tool_calls: 'TOOL CALLS', unique_tools: 'UNIQUE TOOLS', success_rate: 'SUCCESS RATE', sessions_with_tools: 'SESSIONS W/ TOOLS',
      credit_used: 'CREDIT USED', credit_remaining: 'CREDIT REMAINING', cost_per_million: 'USD / 1M TOKENS',
      errors_total: 'TOTAL ERRORS', sources_count: 'SOURCES', unresolved: 'UNRESOLVED', tool_errors: 'TOOL ERRORS',
      uptime: 'UPTIME', avg_latency: 'AVG LATENCY', error_rate: 'ERROR RATE', cron_status: 'COLLECTOR',
    },
    labels: {
      tokens_by_model: 'TOKENS BY MODEL · DAILY',
      source_dist: 'SOURCE DISTRIBUTION',
      recent_sessions: 'RECENT SESSIONS',
      tool_usage: 'TOOL USAGE · DAILY',
      tool_dist: 'TOOL DISTRIBUTION',
      top_tools: 'TOOL RANKING',
      model_ranking: 'MODELS BY TOKENS · RANKING',
      daily_consumption: 'DAILY CONSUMPTION BY MODEL',
      token_breakdown: 'BREAKDOWN BY TYPE',
      cost_by_model: 'REAL COST BY MODEL',
      filters: 'FILTERS',
      clustering: 'PATTERN CLUSTERING · PRIORITIZED',
      error_trend: 'ERROR TREND · 14D',
      heatmap: 'ERROR RATE MATRIX · MODEL × TOOL',
      daily_error_rate: 'DAILY ERROR RATE',
      latency_dist: 'LATENCY DISTRIBUTION',
      sessions_per_hour: 'SESSIONS BY HOUR OF DAY',
      collector_status: 'COLLECTOR · STATUS',
      openrouter_credits: 'OPENROUTER · CREDITS',
    },
    table: { date: 'DATE', model: 'MODEL', source: 'SRC', msgs: 'MSG', tools: 'TOOLS', tokens: 'TOKENS', cost: 'COST', id: 'ID', tool: 'TOOL', calls: 'CALLS', success: 'OK%', duration: 'DURATION', pct: 'PCT', priority: 'PRIO', total: 'TOT', unresolved: 'OPEN', pattern: 'PATTERN', first_seen: 'FIRST', last_seen: 'LAST', sessions: 'SES' },
    misc: {
      active: 'ACTIVE', last_run: 'LAST RUN', next_run: 'NEXT', cron: 'CRON', used: 'USED', remaining: 'LEFT',
      today: 'TODAY', week: 'WEEK', month: 'MONTH', total: 'TOTAL',
      mgmt_key: 'MANAGEMENT KEY · EXACT COMPARISON',
      mgmt_key_msg: 'Add your Management Key in ~/.hermes/.env as OPENROUTER_MANAGEMENT_KEY=sk-or-v1-... for exact Hermes vs OpenRouter comparison.',
      get_key: 'GET KEY',
      page: 'PG',
      all: 'ALL',
      resolved_all: 'STATUS',
      resolved_yes: '✓ RESOLVED',
      resolved_no: '✗ UNRESOLVED',
      filtered_of: 'FILTERED OF',
      source: 'SOURCE',
      type: 'TYPE',
      tool: 'TOOL',
    },
    flavor: 'HERMES AGENT TELEMETRY · MONITORED INSTANCE · CC35 CERTIFIED · CORE TEAM MEMBERS ONLY',
  },
};
