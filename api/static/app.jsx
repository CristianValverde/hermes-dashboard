/* global React, ReactDOM, HERMES_DATA, HERMES_I18N,
   SectionOverview, SectionTools, SectionTokens, SectionErrors, SectionSystem,
   TweaksPanel, TweakSection, TweakRadio, useTweaks */
const { useState, useEffect } = React;

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "lang": "es"
}/*EDITMODE-END*/;

const NAV = [
  { id: 'overview', n: '01' },
  { id: 'tools',    n: '02' },
  { id: 'tokens',   n: '03' },
  { id: 'errors',   n: '04' },
  { id: 'sessions', n: '05' },
  { id: 'system',   n: '06' },
];

function isTypingTarget(target) {
  if (!target) return false;
  const tag = (target.tagName || '').toLowerCase();
  return tag === 'input' || tag === 'textarea' || tag === 'select' || target.isContentEditable;
}

function formatCompact(value) {
  if (!value) return '0';
  if (value >= 1000000) return `${(value / 1000000).toFixed(value >= 10000000 ? 0 : 1)}M`;
  if (value >= 1000) return `${(value / 1000).toFixed(value >= 100000 ? 0 : 1)}K`;
  return String(value);
}

function normalizeData(raw) {
  const t = raw.totals || {};
  const totals = {
    sessions: t.sessions || 0,
    models: t.models || 0,
    tokens: t.tokens || 0,
    toolCalls: t.tool_calls || 0,
    daysActive: t.daysActive || 0,
    inputTokens: t.input_tokens || 0,
    outputTokens: t.output_tokens || 0,
    cacheReadTokens: t.cache_read || 0,
    cacheWriteTokens: t.cache_write || 0,
    reasoningTokens: t.reasoning || 0,
  };
  const hm = raw.heatmap || {};
  return {
    models: raw.models || [],
    economicBreakdown: raw.economicBreakdown || [],
    economicProviderUsage: raw.economicProviderUsage || [],
    days: raw.days || [],
    tokensPerDay: raw.tokensPerDay || [],
    tools: raw.tools || [],
    toolTokenUsage: raw.toolTokenUsage || [],
    toolColors: raw.toolColors || [],
    sources: raw.sources || [],
    recentSessions: raw.recentSessions || [],
    errors: raw.errors || [],
    errorTrend: raw.errorTrend || [],
    heatmap: hm.matrix || [],
    heatmapModels: hm.models || [],
    heatmapTools: hm.tools || [],
    openRouter: raw.openRouter || {},
    collector: raw.collector || {},
    sessionMetrics: raw.sessionMetrics || {},
    systemHealth: raw.systemHealth || {},
    modelCosts: raw.modelCosts || [],
    agentLog: raw.agentLog || {},
    overviewExtras: raw.overviewExtras || {},
    toolDaily: raw.toolDaily || {},
    totals,
  };
}

function LoadingScreen() {
  return React.createElement('div', { className: 'app' },
    React.createElement('div', { className: 'loading-screen' },
      React.createElement('canvas', { id: 'loading-logo', className: 'loading-logo' }),
      React.createElement('div', { className: 'loading-text' }, 'HERMES'),
      React.createElement('div', { className: 'loading-sub' }, 'INITIALIZING TELEMETRY · FETCHING DATA')
    )
  );
}

function ErrorScreen({ message }) {
  return React.createElement('div', { className: 'app' },
    React.createElement('div', { className: 'loading-screen' },
      React.createElement('canvas', { id: 'error-logo', className: 'loading-logo' }),
      React.createElement('div', { className: 'loading-text', style: { color: '#E84848' } }, 'CONNECTION ERROR'),
      React.createElement('div', { className: 'loading-sub' }, message || 'Could not reach Hermes API')
    )
  );
}

function Sidebar({ active, onSelect, t, tweaks, setTweak }) {
  const D = HERMES_DATA;
  const navBadges = {
    overview: `${D.totals?.daysActive || 0}D`,
    tools: String(D.tools?.length || 0),
    tokens: formatCompact(D.totals?.tokens || 0),
    errors: String(D.errors?.length || 0),
    sessions: String(D.totals?.sessions || 0),
    system: (D.systemHealth?.status || 'OK').toUpperCase(),
  };
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <canvas id="side-logo" className="sidebar-logo" />
        <div className="sidebar-brand-copy">
          <div className="sidebar-brand-text">HERMES</div>
          <div className="sidebar-brand-sub">ANALYTICS · v2.6</div>
        </div>
      </div>
      <div className="sidebar-section-label">NAVIGATION</div>
      {NAV.map(n => (
        <button
          key={n.id}
          className={`nav-item ${active === n.id ? 'active' : ''}`}
          onClick={() => onSelect(n.id)}
          title={`${t.nav[n.id]} · ${navBadges[n.id] || '—'}`}
        >
          <span className="nav-num">{n.n}</span>
          <span className="nav-label">{t.nav[n.id]}</span>
          <span className="nav-badge">{navBadges[n.id] || '—'}</span>
        </button>
      ))}
      <div className="sidebar-divider" />
      <div className="sidebar-section-label">SYSTEM STATUS</div>
      <div className="sb-card">
        <div className="sb-card-label"><span className="sb-card-letter">A</span><span>COLECTOR · CRON</span></div>
        <div className="sb-row"><span className="sb-row-key">STATUS</span><span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><span className="sb-pulse" /><span className="sb-row-val green">ACTIVE</span></span></div>
        <div className="sb-row"><span className="sb-row-key">CRON</span><span className="sb-row-val code">{D.collector.cronId ? D.collector.cronId.slice(0, 8) : '\u2014'}</span></div>
        <div className="sb-row"><span className="sb-row-key">LAST</span><span className="sb-row-val code">{D.collector.lastRun ? D.collector.lastRun.split(' ')[1] : '\u2014'}</span></div>
        <div className="sb-row"><span className="sb-row-key">NEXT</span><span className="sb-row-val code">{D.collector.nextRun ? D.collector.nextRun.split(' ')[1] : '\u2014'}</span></div>
      </div>
      <div className="sb-card">
        <div className="sb-card-label"><span className="sb-card-letter">B</span><span>SESSION · FOOTPRINT</span></div>
        <div className="sb-row"><span className="sb-row-key">SES</span><span className="sb-row-val code">{D.totals.sessions || 0}</span></div>
        <div className="sb-row"><span className="sb-row-key">TOKENS</span><span className="sb-row-val amber">{formatCompact(D.totals.tokens || 0)}</span></div>
        <div className="sb-row"><span className="sb-row-key">CALLS</span><span className="sb-row-val">{(D.totals.toolCalls || 0).toLocaleString('es-ES')}</span></div>
      </div>
      <div className="sb-card">
        <div className="sb-card-label"><span className="sb-card-letter">C</span><span>MODEL · COVERAGE</span></div>
        <div className="sb-row"><span className="sb-row-key">MODELS</span><span className="sb-row-val amber">{D.totals.models || 0}</span></div>
        <div className="sb-row"><span className="sb-row-key">PROVIDERS</span><span className="sb-row-val">{D.economicProviderUsage?.length || 0}</span></div>
        <div className="sb-row"><span className="sb-row-key">ACTIVE</span><span className="sb-row-val code">{D.totals.daysActive || 0}D</span></div>
      </div>
      <div className="sidebar-footer">
        <span>BUILD 26.05.14</span>
        <div className="lang-toggle">
          <button className={`lang-btn ${tweaks.lang === 'es' ? 'active' : ''}`} onClick={() => setTweak('lang', 'es')}>ES</button>
          <button className={`lang-btn ${tweaks.lang === 'en' ? 'active' : ''}`} onClick={() => setTweak('lang', 'en')}>EN</button>
        </div>
      </div>
    </aside>
  );
}

function UtilityBar({ active, t }) {
  const D = HERMES_DATA;
  const navIdx = NAV.findIndex(n => n.id === active);
  return (
    <div className="utility-bar">
      <div className="utility-bar-left">
        <span className="util-status"><span className="dot" /> AGENT ONLINE</span>
        <span>HERMES_AGENT · v2.6.1</span>
        <span>{t.flavor.slice(0, 60)}</span>
      </div>
      <div className="utility-bar-right">
        <span>{String(navIdx + 1).padStart(2, '0')} / {String(NAV.length).padStart(2, '0')}  {t.misc.page}</span>
        <span>{new Date().toLocaleString()}</span>
        <span>SESSIONS 00{D.totals.sessions}</span>
      </div>
    </div>
  );
}

function HermesLEDCanvas() {
  const ref = React.useRef(null);
  React.useEffect(() => {
    if (ref.current && window.mountHermesLogo) {
      window.mountHermesLogo(ref.current);
    }
  }, []);
  return <canvas ref={ref} className="logo-canvas" />;
}

function PageHeader({ active, t }) {
  const D = HERMES_DATA;
  return (
    <div className="page-header">
      <div className="page-header-logo"><HermesLEDCanvas /></div>
      <div className="page-header-text">
        <div className="page-eyebrow">{t.section_eyebrow[active]}</div>
        <div className="page-title">{t.nav[active]}</div>
        <div className="page-sub">
          {active === 'overview' && t.misc.overview_focus}
          {active === 'tools' && `${D.tools?.length || 0} HERRAMIENTAS · ${(D.totals?.toolCalls || 0).toLocaleString('es-ES')} LLAMADAS · ${D.totals?.daysActive || 0} DÍAS`}
          {active === 'tokens' && `${D.totals?.models || 0} MODELOS · ${formatCompact(D.totals?.tokens || 0)} TOKENS · ${formatCompact(D.totals?.cacheReadTokens || 0)} CACHE`}
          {active === 'errors' && `${D.errors?.length || 0} INCIDENCIAS · ${(D.errorTrend || []).length} DÍAS CON TRAZA · LOG-BASED`}
          {active === 'system' && `GLOBAL THROUGHPUT ${HERMES_DATA?.systemHealth?.globalThroughput || '—'} · ERRORS ${HERMES_DATA?.systemHealth?.failedToolCalls || 0} · FALLBACKS ${HERMES_DATA?.systemHealth?.fallbackCount || 0}`}
        </div>
      </div>
    </div>
  );
}

function App() {
  const [tweaks, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [active, setActive] = useState(() => {
    const h = location.hash.replace('#', '');
    return NAV.find(n => n.id === h) ? h : 'overview';
  });
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const onHash = () => {
      const h = location.hash.replace('#', '');
      if (NAV.find(n => n.id === h)) setActive(h);
    };
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  useEffect(() => {
    const onKeyDown = (event) => {
      if (!(event.ctrlKey || event.metaKey) || event.key.toLowerCase() !== 'b') return;
      if (isTypingTarget(event.target)) return;
      event.preventDefault();
      setSidebarCollapsed((value) => !value);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  useEffect(() => {
    fetch('/api/all')
      .then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(raw => { window.HERMES_DATA = normalizeData(raw); setLoading(false); })
      .catch(err => { console.error('API fetch failed:', err); setError(err.message); setLoading(false); });
  }, []);

  const handleSelect = (id) => {
    setActive(id);
    location.hash = id;
    const main = document.querySelector('.main');
    if (main) main.scrollTop = 0;
  };

  const toggleSidebar = () => setSidebarCollapsed((value) => !value);

  if (loading) return <LoadingScreen />;
  if (error) return <ErrorScreen message={error} />;

  const lang = tweaks.lang || 'es';
  const t = HERMES_I18N[lang];

  return (
    <div className={`app ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
      <Sidebar active={active} onSelect={handleSelect} t={t} tweaks={tweaks} setTweak={setTweak} />
      <button
        className={`sidebar-edge-toggle ${sidebarCollapsed ? 'collapsed' : ''}`}
        type="button"
        onClick={toggleSidebar}
        aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        title={sidebarCollapsed ? 'Expand sidebar (Ctrl+B)' : 'Collapse sidebar (Ctrl+B)'}
      >
        <span>{sidebarCollapsed ? '\u00BB' : '\u00AB'}</span>
      </button>
      <main className="main">
        <div className="matrix-bg" />
        <div className="main-inner">
          <UtilityBar active={active} t={t} />
          <PageHeader active={active} t={t} />
          {active === 'overview' && <SectionOverview t={t} />}
          {active === 'tools'    && <SectionTools t={t} />}
          {active === 'tokens'   && <SectionTokens t={t} />}
          {active === 'errors'   && <SectionErrors t={t} />}
          {active === 'sessions' && <SectionSessions t={t} />}
          {active === 'system'   && <SectionSystem t={t} />}
        </div>
      </main>
      <TweaksPanel title="TWEAKS \u00b7 HERMES">
        <TweakSection label="Idioma / Language" />
        <TweakRadio label="UI Language" value={tweaks.lang} options={['es', 'en']} onChange={(v) => setTweak('lang', v)} />
      </TweaksPanel>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);



// Mount Caduceus logos with MutationObserver
(function() {
  var observer = new MutationObserver(function() {
    var els = ['loading-logo', 'error-logo', 'side-logo'];
    var allFound = true;
    els.forEach(function(id) {
      var el = document.getElementById(id);
      if (el && window.mountHermesLogo && el.width === 0) {
        try { window.mountHermesLogo(el); } catch(e) {}
      }
      if (!document.getElementById(id)) allFound = false;
    });
    if (allFound) observer.disconnect();
  });
  observer.observe(document.body || document.documentElement, {
    childList: true, subtree: true
  });
  // Also try immediately
  setTimeout(function() {
    var els = ['loading-logo', 'error-logo', 'side-logo'];
    els.forEach(function(id) {
      var el = document.getElementById(id);
      if (el && window.mountHermesLogo) {
        try { window.mountHermesLogo(el); } catch(e) {}
      }
    });
  }, 500);
})();
