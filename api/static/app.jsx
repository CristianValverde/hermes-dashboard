/* global React, ReactDOM, HERMES_DATA, HERMES_I18N,
   SectionOverview, SectionTools, SectionTokens, SectionErrors, SectionSystem,
   TweaksPanel, TweakSection, TweakRadio, useTweaks */
const { useState, useEffect } = React;

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "lang": "es"
}/*EDITMODE-END*/;

const NAV = [
  { id: 'overview', n: '01', badge: '14D' },
  { id: 'tools',    n: '02', badge: '12' },
  { id: 'tokens',   n: '03', badge: '65M' },
  { id: 'errors',   n: '04', badge: '198' },
  { id: 'system',   n: '05', badge: 'OK' },
];

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
    days: raw.days || [],
    tokensPerDay: raw.tokensPerDay || [],
    tools: raw.tools || [],
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
    totals,
  };
}

function LoadingScreen() {
  return React.createElement('div', { className: 'app' },
    React.createElement('div', { className: 'loading-screen' },
      React.createElement('div', { className: 'loading-diamond' }),
      React.createElement('div', { className: 'loading-text' }, 'HERMES'),
      React.createElement('div', { className: 'loading-sub' }, 'INITIALIZING TELEMETRY · FETCHING DATA')
    )
  );
}

function ErrorScreen({ message }) {
  return React.createElement('div', { className: 'app' },
    React.createElement('div', { className: 'loading-screen' },
      React.createElement('div', { className: 'loading-diamond', style: { borderColor: '#E84848' } }),
      React.createElement('div', { className: 'loading-text', style: { color: '#E84848' } }, 'CONNECTION ERROR'),
      React.createElement('div', { className: 'loading-sub' }, message || 'Could not reach Hermes API')
    )
  );
}

function Sidebar({ active, onSelect, t, tweaks, setTweak }) {
  const D = HERMES_DATA;
  const orPct = D.openRouter.totalCredits > 0 ? (D.openRouter.totalUsage / D.openRouter.totalCredits) * 100 : 0;
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-diamond" />
        <div>
          <div className="sidebar-brand-text">HERMES</div>
          <div className="sidebar-brand-sub">ANALYTICS · v2.6</div>
        </div>
      </div>
      <div className="sidebar-section-label">NAVIGATION</div>
      {NAV.map(n => (
        <button key={n.id} className={`nav-item ${active === n.id ? 'active' : ''}`} onClick={() => onSelect(n.id)}>
          <span className="nav-num">{n.n}</span>
          <span className="nav-label">{t.nav[n.id]}</span>
          <span className="nav-badge">{n.badge}</span>
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
        <div className="sb-card-label"><span className="sb-card-letter">B</span><span>OPENROUTER · CREDITS</span></div>
        <div className="sb-row"><span className="sb-row-key">USED</span><span className="sb-row-val amber">${(D.openRouter.totalUsage || 0).toFixed(2)}</span></div>
        <div className="sb-row"><span className="sb-row-key">LIMIT</span><span className="sb-row-val">${(D.openRouter.totalCredits || 0).toFixed(2)}</span></div>
        <div className="sb-progress"><div className="sb-progress-fill" style={{ width: Math.min(orPct, 100) + '%' }} /></div>
        <div className="sb-row" style={{ marginTop: 2 }}><span className="sb-row-key">{orPct.toFixed(1)}%</span><span className="sb-row-key">${Math.max(0, (D.openRouter.totalCredits - D.openRouter.totalUsage)).toFixed(2)} LEFT</span></div>
      </div>
      <div className="sb-card">
        <div className="sb-card-label"><span className="sb-card-letter">C</span><span>USAGE WINDOWS</span></div>
        <div className="sb-row"><span className="sb-row-key">{t.misc.today}</span><span className="sb-row-val code">${(D.openRouter.today || 0).toFixed(2)}</span></div>
        <div className="sb-row"><span className="sb-row-key">{t.misc.week}</span><span className="sb-row-val code">${(D.openRouter.week || 0).toFixed(2)}</span></div>
        <div className="sb-row"><span className="sb-row-key">{t.misc.month}</span><span className="sb-row-val code">${(D.openRouter.month || 0).toFixed(2)}</span></div>
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
        <span>ランダム 00{D.totals.sessions}</span>
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
  return (
    <div className="page-header">
      <div className="page-header-logo"><HermesLEDCanvas /></div>
      <div className="page-header-text">
        <div className="page-eyebrow">{t.section_eyebrow[active]}</div>
        <div className="page-title">{t.nav[active]}</div>
        <div className="page-sub">
          {active === 'overview' && 'PANEL DE CONTROL \u00b7 TELEMETR\u00cdA UNIFICADA'}
          {active === 'tools' && '12 HERRAMIENTAS \u00b7 2,875 LLAMADAS \u00b7 14 D\u00cdAS'}
          {active === 'tokens' && '6 MODELOS \u00b7 65M TOKENS \u00b7 BENCHMARKED'}
          {active === 'errors' && '198 INCIDENCIAS \u00b7 35 PENDIENTES \u00b7 CLUSTERED'}
          {active === 'system' && 'UPTIME 99.84% \u00b7 ERROR RATE 3.2% \u00b7 LATENCY 187MS'}
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

  if (loading) return <LoadingScreen />;
  if (error) return <ErrorScreen message={error} />;

  const lang = tweaks.lang || 'es';
  const t = HERMES_I18N[lang];

  return (
    <div className="app">
      <Sidebar active={active} onSelect={handleSelect} t={t} tweaks={tweaks} setTweak={setTweak} />
      <main className="main">
        <div className="matrix-bg" />
        <div className="main-inner">
          <UtilityBar active={active} t={t} />
          <PageHeader active={active} t={t} />
          {active === 'overview' && <SectionOverview t={t} />}
          {active === 'tools'    && <SectionTools t={t} />}
          {active === 'tokens'   && <SectionTokens t={t} />}
          {active === 'errors'   && <SectionErrors t={t} />}
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
