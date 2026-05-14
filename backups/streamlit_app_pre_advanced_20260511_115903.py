#!/usr/bin/env python3
"""
Hermes Dashboard — Rediseño con sistema de diseño Trade Republic
Cost & usage monitoring for Hermes Agent.
"""
import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime as dt, timedelta
import os

# ============================================
# CONFIGURACIÓN DEL TEMA Y CSS PERSONALIZADO
# ============================================

st.set_page_config(
    page_title="Hermes Dashboard Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para tema Trade Republic
st.markdown("""
<style>
    /* Estilos globales - Tema oscuro Trade Republic */
    .stApp {
        background-color: #000000;
        color: #FFFFFF;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        font-weight: 600;
        letter-spacing: -0.02em;
    }
    
    /* Cards estilo Trade Republic */
    .card {
        background-color: #1A1A1A;
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid #2A2A2A;
        transition: all 0.2s ease;
    }
    
    .card:hover {
        border-color: #3A3A3A;
        transform: translateY(-2px);
    }
    
    .card-title {
        color: #AAAAAA;
        font-size: 14px;
        font-weight: 500;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .card-value {
        color: #FFFFFF;
        font-size: 32px;
        font-weight: 600;
        margin-bottom: 0.25rem;
    }
    
    .card-delta {
        font-size: 14px;
        font-weight: 500;
    }
    
    .card-delta.positive {
        color: #4ADE80;
    }
    
    .card-delta.negative {
        color: #F87171;
    }
    
    /* Dataframes estilo Trade Republic */
    .dataframe {
        background-color: #1A1A1A !important;
        color: #FFFFFF !important;
        border: 1px solid #2A2A2A !important;
        border-radius: 12px !important;
        overflow: hidden !important;
    }
    
    .dataframe th {
        background-color: #2A2A2A !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-bottom: 1px solid #3A3A3A !important;
    }
    
    .dataframe td {
        border-bottom: 1px solid #2A2A2A !important;
        color: #CCCCCC !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# CONFIGURACIÓN DE DATOS
# ============================================

DB_PATH = os.path.join(os.path.dirname(__file__), "dashboard.db")

# Título principal
st.markdown("""
<div style="margin-bottom: 2rem;">
    <h1 style="margin-bottom: 0.25rem;">📊 Hermes Dashboard Pro</h1>
    <div style="color: #AAAAAA; font-size: 14px; font-weight: 400; text-transform: uppercase; letter-spacing: 0.05em;">
        Cost & usage monitoring for Hermes Agent + OpenRouter
    </div>
</div>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def load_data():
    """Load all dashboard data from SQLite"""
    conn = sqlite3.connect(DB_PATH)
    
    # sessions
    sessions_df = pd.read_sql_query("""
        SELECT *,
               datetime(started_at, 'unixepoch') as started_datetime,
               datetime(ended_at, 'unixepoch') as ended_datetime
        FROM sessions
        ORDER BY started_at DESC
    """, conn)
    
    # daily_stats
    daily_df = pd.read_sql_query("SELECT * FROM daily_stats ORDER BY date DESC", conn)
    
    # model_stats
    model_df = pd.read_sql_query("SELECT * FROM model_stats ORDER BY estimated_cost_usd DESC", conn)
    
    # account_snapshots
    account_df = pd.read_sql_query("""
        SELECT timestamp, total_credits, total_usage
        FROM account_snapshots
        ORDER BY timestamp DESC
    """, conn)
    
    # collector_runs
    runs_df = pd.read_sql_query("SELECT * FROM collector_runs ORDER BY started_at DESC", conn)
    
    conn.close()
    
    # Convert datetime strings to datetime objects
    if not sessions_df.empty and "started_datetime" in sessions_df.columns:
        sessions_df["started_datetime"] = pd.to_datetime(sessions_df["started_datetime"])
    if not sessions_df.empty and "ended_datetime" in sessions_df.columns:
        sessions_df["ended_datetime"] = pd.to_datetime(sessions_df["ended_datetime"])
    
    # Calculate remaining credits
    if not account_df.empty and "total_credits" in account_df.columns and "total_usage" in account_df.columns:
        account_df["remaining"] = account_df["total_credits"] - account_df["total_usage"]
    
    return {
        "sessions": sessions_df,
        "daily": daily_df,
        "models": model_df,
        "account": account_df,
        "runs": runs_df
    }

# Cargar datos
try:
    data = load_data()
    sessions_df = data["sessions"]
    daily_df = data["daily"]
    model_df = data["models"]
    account_df = data["account"]
    runs_df = data["runs"]
    
except Exception as e:
    st.error(f"❌ Could not load data: {e}")
    st.stop()

# ============================================
# SIDEBAR
# ============================================

with st.sidebar:
    st.markdown("""
    <div style="padding: 0 0 1.5rem 0;">
        <h3 style="color: #FFFFFF; margin-bottom: 1rem;">📅 Filtros</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Filtro de fecha
    if not sessions_df.empty:
        min_date = sessions_df["started_datetime"].min()
        max_date = sessions_df["started_datetime"].max()
        date_range = st.date_input(
            "Rango de fechas",
            [min_date.date() if hasattr(min_date, 'date') else dt.now().date(),
             max_date.date() if hasattr(max_date, 'date') else dt.now().date()],
            min_value=min_date.date() if hasattr(min_date, 'date') else dt.now().date(),
            max_value=max_date.date() if hasattr(max_date, 'date') else dt.now().date()
        )
        
        selected_models = st.multiselect(
            "Modelos",
            options=sessions_df["model"].unique(),
            default=sessions_df["model"].unique()
        )
    else:
        date_range = [dt.now().date() - timedelta(days=7), dt.now().date()]
        selected_models = []
    
    # KPIs de créditos
    st.markdown("---")
    st.markdown("""
    <div style="padding: 0 0 1rem 0;">
        <h3 style="color: #FFFFFF; margin-bottom: 1rem;">💰 Créditos</h3>
    </div>
    """, unsafe_allow_html=True)
    
    if not account_df.empty:
        if "remaining" not in account_df.columns:
            if "total_credits" in account_df.columns and "total_usage" in account_df.columns:
                account_df["remaining"] = account_df["total_credits"] - account_df["total_usage"]
        
        latest = account_df.iloc[0]
        
        st.markdown(f"""
        <div class="card">
            <div class="card-title">Créditos Restantes</div>
            <div class="card-value">${latest['remaining']:.2f}</div>
            <div class="card-delta negative">-${latest['total_usage']:.2f} gastados</div>
        </div>
        """, unsafe_allow_html=True)

# ============================================
# MAIN DASHBOARD
# ============================================

# Advertencia
st.markdown("""
<div style="background: linear-gradient(90deg, rgba(168, 85, 247, 0.15), rgba(139, 92, 246, 0.15)); 
            border-left: 4px solid #A855F7; 
            padding: 1rem 1.5rem; 
            border-radius: 0 12px 12px 0;
            margin-bottom: 2rem;">
    <div style="display: flex; align-items: center; gap: 0.75rem;">
        <div style="font-size: 20px;">⚠️</div>
        <div>
            <div style="font-weight: 600; color: #FFFFFF; margin-bottom: 0.25rem;">
                Precisión de costes estimados
            </div>
            <div style="color: #CCCCCC; font-size: 14px;">
                El coste estimado puede subestimar el coste real de OpenRouter 2-5×.
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Cards principales
st.markdown("""
<div style="margin-bottom: 1.5rem;">
    <h2 style="margin-bottom: 0.5rem;">📈 Métricas Principales</h2>
    <div style="color: #AAAAAA; font-size: 14px; font-weight: 400; text-transform: uppercase; letter-spacing: 0.05em;">
        Resumen de uso y costes
    </div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    session_count = len(sessions_df)
    st.markdown(f"""
    <div class="card">
        <div class="card-title">Sesiones Totales</div>
        <div class="card-value">{session_count:,}</div>
        <div class="card-delta">registradas</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    estimated_cost_usd = sessions_df["estimated_cost_usd"].fillna(0).sum()
    st.markdown(f"""
    <div class="card">
        <div class="card-title">Coste Total</div>
        <div class="card-value">${estimated_cost_usd:.2f}</div>
        <div class="card-delta negative">USD estimado</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    total_tokens = sessions_df["input_tokens"].fillna(0).sum() + sessions_df["output_tokens"].fillna(0).sum()
    st.markdown(f"""
    <div class="card">
        <div class="card-title">Tokens Totales</div>
        <div class="card-value">{total_tokens:,}</div>
        <div class="card-delta">input + output</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    if not daily_df.empty:
        today_cost = daily_df.iloc[0]["estimated_cost_usd"]
        st.markdown(f"""
        <div class="card">
            <div class="card-title">Coste Hoy</div>
            <div class="card-value">${today_cost:.2f}</div>
            <div class="card-delta">actual</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="card">
            <div class="card-title">Coste Hoy</div>
            <div class="card-value">$0.00</div>
            <div class="card-delta">sin datos</div>
        </div>
        """, unsafe_allow_html=True)

# Gráficos con colores alternativos
LINE_COLOR = "#A855F7"  # Violeta
BAR_COLOR = "#8B5CF6"   # Violeta claro

st.markdown("""
<div style="margin: 2rem 0 1rem 0;">
    <h2 style="margin-bottom: 0.5rem;">📊 Evolución de Costes</h2>
    <div style="color: #AAAAAA; font-size: 14px; font-weight: 400; text-transform: uppercase; letter-spacing: 0.05em;">
        Tendencia diaria
    </div>
</div>
""", unsafe_allow_html=True)

if not daily_df.empty:
    fig = px.bar(daily_df.head(30), x="date", y="estimated_cost_usd",
                 labels={"date": "Fecha", "estimated_cost_usd": "Coste (USD)"},
                 color_discrete_sequence=[BAR_COLOR])
    
    fig.update_layout(
        plot_bgcolor='#000000',
        paper_bgcolor='#000000',
        font_color='#FFFFFF',
        xaxis=dict(gridcolor='#2A2A2A', linecolor='#2A2A2A', tickfont=dict(color='#AAAAAA')),
        yaxis=dict(gridcolor='#2A2A2A', linecolor='#2A2A2A', tickfont=dict(color='#AAAAAA')),
        hoverlabel=dict(bgcolor="#1A1A1A", font_color="#FFFFFF")
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Sesiones recientes
st.markdown("""
<div style="margin: 2rem 0 1rem 0;">
    <h2 style="margin-bottom: 0.5rem;">📋 Sesiones Recientes</h2>
    <div style="color: #AAAAAA; font-size: 14px; font-weight: 400; text-transform: uppercase; letter-spacing: 0.05em;">
        Últimas ejecuciones
    </div>
</div>
""", unsafe_allow_html=True)

if not sessions_df.empty:
    recent = sessions_df.head(10)[["started_datetime", "model", "input_tokens", "output_tokens", "estimated_cost_usd"]]
    recent.columns = ["Fecha", "Modelo", "Input", "Output", "Coste"]
    
    recent["Fecha"] = recent["Fecha"].dt.strftime("%Y-%m-%d %H:%M")
    recent["Input"] = recent["Input"].apply(lambda x: f"{x:,}")
    recent["Output"] = recent["Output"].apply(lambda x: f"{x:,}")
    recent["Coste"] = recent["Coste"].apply(lambda x: f"${x:.4f}")
    
    st.dataframe(recent, use_container_width=True)

# Footer
st.markdown("""
<div style="margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid #2A2A2A;">
    <div style="color: #666666; font-size: 12px; line-height: 1.6;">
        <div>Hermes Dashboard Pro • Diseño inspirado en Trade Republic</div>
        <div>Gráficos con paleta alternativa: violeta (#A855F7)</div>
        <div>Actualizado: {timestamp}</div>
    </div>
</div>
""".format(timestamp=dt.now().strftime('%Y-%m-%d %H:%M:%S')), unsafe_allow_html=True)
