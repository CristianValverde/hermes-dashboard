#!/usr/bin/env python3
"""
HERMES ANALYTICS - Dashboard Avanzado con Sistema de Diseño Trade Republic
Sistema de control total para Hermes Agent con análisis profundo de:
- Tokens por modelo (gráficos de barras apilados)
- Uso de herramientas (tools) por día y distribución
- Costes reales vs estimados (OpenRouter API)
- Errores y métricas de performance
- Datos crudos de sesiones y logs
"""

import streamlit as st
import streamlit.components.v1 as components
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime as dt, timedelta
import os
import json
from pathlib import Path

# ============================================
# CONFIGURACIÓN DEL TEMA Y CSS PERSONALIZADO
# ============================================

st.set_page_config(
    page_title="Hermes Analytics Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para tema Trade Republic con mejoras
st.markdown("""
<style>
    /* Estilos globales - Tema oscuro Trade Republic */
    :root {
        --primary-bg: #000000;
        --secondary-bg: #1A1A1A;
        --card-bg: #1A1A1A;
        --text-primary: #FFFFFF;
        --text-secondary: #AAAAAA;
        --accent: #F59E0B;
        --accent-light: #FBBF24;
        --positive: #4ADE80;
        --negative: #F87171;
        --border: #2A2A2A;
    }
    
    .stApp {
        background-color: var(--primary-bg);
        color: var(--text-primary);
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: var(--text-primary) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        font-weight: 600;
        letter-spacing: -0.02em;
    }
    
    /* Cards estilo Trade Republic */
    .custom-card {
        background-color: var(--card-bg);
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid var(--border);
        transition: all 0.2s ease;
        margin-bottom: 1rem;
    }
    
    .custom-card:hover {
        border-color: #3A3A3A;
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    }
    
    .card-title {
        color: var(--text-secondary);
        font-size: 14px;
        font-weight: 500;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .card-value {
        color: var(--text-primary);
        font-size: 32px;
        font-weight: 600;
        margin-bottom: 0.25rem;
    }
    
    .card-delta {
        font-size: 14px;
        font-weight: 500;
    }
    
    .card-delta.positive {
        color: var(--positive);
    }
    
    .card-delta.negative {
        color: var(--negative);

    /* Card color variants */
    .card-amber { border-left: 4px solid #F59E0B !important; }
    .card-blue { border-left: 4px solid #3B82F6 !important; }
    .card-green { border-left: 4px solid #4ADE80 !important; }
    .card-purple { border-left: 4px solid #A855F7 !important; }
    .card-pink { border-left: 4px solid #EC4899 !important; }
    .card-gold { border-left: 4px solid #EAB308 !important; }
    
    .card-value-amber { color: #F59E0B !important; }
    .card-value-green { color: #4ADE80 !important; }
    .card-value-red { color: #F87171 !important; }
    .card-value-blue { color: #3B82F6 !important; }
    
    /* Section headers with icon */
    .section-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--border);
    }
    .section-header h3 {
        margin: 0 !important;
        color: var(--accent) !important;
        font-size: 1.3rem;
    }
    
    /* Better dataframes */
    .stDataFrame {
        border: 1px solid var(--border);
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* Divider styling */
    .stDivider {
        border-color: var(--border) !important;
        margin: 1.5rem 0 !important;
    }
    
    /* Info boxes */
    .stInfo {
        background-color: var(--secondary-bg) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        color: var(--text-secondary) !important;
    }
    }
    
    /* Dataframes estilo Trade Republic */
    .dataframe {
        background-color: var(--secondary-bg) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
    }
    
    /* Tabs personalizados */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: var(--secondary-bg);
        padding: 8px;
        border-radius: 12px;
        border: 1px solid var(--border);
        margin-bottom: 1.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: var(--text-secondary);
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
        border: none;
        transition: all 0.2s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--accent) !important;
        color: white !important;
    }
    
    /* Metricas */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        color: var(--text-primary) !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
        color: var(--text-secondary) !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Sliders y controles */
    .stSlider > div > div > div {
        background-color: var(--accent) !important;
    }
    
    /* Tooltips */
    [data-testid="stTooltip"] {
        background-color: var(--secondary-bg) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border);
        border-radius: 8px;
    }
    
    /* Banner de advertencia */
    .warning-banner {
        background: linear-gradient(135deg, #F59E0B, #D97706);
        border: none;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    
    /* Sidebar cards */
    .sidebar-card {
        background-color: var(--secondary-bg);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid var(--border);
    }

    /* ===== LOGO ANIMADO HERMES ===== */
    @keyframes logoGlow {
        0% { filter: brightness(1) saturate(1); }
        25% { filter: brightness(1.15) saturate(1.2) drop-shadow(0 0 8px rgba(245, 158, 11, 0.4)); }
        50% { filter: brightness(1.05) saturate(1.1) drop-shadow(0 0 12px rgba(251, 191, 36, 0.3)); }
        75% { filter: brightness(1.2) saturate(1.3) drop-shadow(0 0 15px rgba(245, 158, 11, 0.5)); }
        100% { filter: brightness(1) saturate(1); }
    }
    
    @keyframes gradientSweep {
        0% { background-position: -200% center; }
        100% { background-position: 200% center; }
    }
    
    @keyframes pulseAmber {
        0%, 100% { opacity: 0.9; }
        50% { opacity: 1; }
    }
    
    /* Todos los headers en amber */
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #F59E0B !important;
    }
    
    /* Tab selected amber */
    .stTabs [aria-selected="true"] {
        background-color: #F59E0B !important;
        color: #000 !important;
        font-weight: 700 !important;
    }
    
    /* Selectbox focus amber */
    div[data-baseweb="select"]:focus-within > div {
        border-color: #F59E0B !important;
        box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.2) !important;
    }


    /* Optimización KPI cards - sin espacio desperdiciado */
    div[data-testid="stHorizontalBlock"] {
        gap: 0.5rem !important;
    }
    div[data-testid="column"] .custom-card {
        padding: 1.2rem 1rem;
        width: 100%;
        box-sizing: border-box;
    }
    div[data-testid="column"] .card-value {
        font-size: 2.2rem !important;
        letter-spacing: -0.02em;
    }
    /* Forzar ancho completo del contenedor principal */
    .stMainBlockContainer, .main .block-container {
        max-width: 100% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    /* Asegurar que las columnas Streamlit usen todo el ancho */
    div[data-testid="stHorizontalBlock"] {
        gap: 0.75rem !important;
        width: 100% !important;
    }
    div[data-testid="column"] {
        width: 100% !important;
        flex: 1 1 0 !important;
    }
    div[data-testid="column"] .custom-card {
        width: 100% !important;
        min-width: 0 !important;
    }
    .stMainBlockContainer {
        max-width: 100% !important;
        padding: 1rem 1.5rem !important;
    }

    /* === ALINEACIÓN GLOBAL === */
    /* Quitar padding extra de Streamlit que desalinea */
    .stApp .main .block-container {
        max-width: 100% !important;
        padding: 0.5rem 2rem 2rem 2rem !important;
    }
    
    /* Logo iframe: margen izquierdo para que no esté pegado */
    iframe[title="st.iframe"] {
        margin-left: 0 !important;
        margin-top: 0.5rem !important;
        display: block !important;
    }
    
    /* Pestañas alineadas con el logo */
    div[data-testid="stTabs"] {
        margin-left: 0 !important;
        padding-left: 0 !important;
    }
    
    /* Columnas KPI: ancho completo sin espacio desperdiciado */
    div[data-testid="stHorizontalBlock"] {
        gap: 0.5rem !important;
        width: 100% !important;
    }
    div[data-testid="column"] {
        flex: 1 1 0 !important;
        min-width: 0 !important;
    }
    div[data-testid="column"] .custom-card {
        width: 100% !important;
    }
    
    /* Tarjetas compactas */
    .custom-card {
        padding: 1rem 0.8rem !important;
    }
    .card-value {
        font-size: 2rem !important;
    }

    /* === ALINEACIÓN GLOBAL === */
    /* Contenedor principal sin padding lateral excesivo */
    .stMainBlockContainer, .block-container {
        max-width: 100% !important;
        padding-top: 0.5rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
    
    /* Logo iframe: margen izquierdo consistente */
    iframe[title="st.iframe"] {
        margin-left: 0.5rem !important;
        margin-top: 0.5rem !important;
        display: block !important;
    }
    
    /* Título centrado con aire */
    
    /* Columnas KPI: ancho completo */
    div[data-testid="stHorizontalBlock"] {
        gap: 0.5rem !important;
        width: 100% !important;
    }
    div[data-testid="column"] {
        flex: 1 1 0 !important;
        min-width: 0 !important;
    }
    div[data-testid="column"] .custom-card {
        width: 100% !important;
        padding: 0.8rem 0.5rem !important;
    }
    .card-value {
        font-size: 1.8rem !important;
    }

    /* Alinear verticalmente columnas del header */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# FUNCIONES DE CONEXIÓN A BASE DE DATOS
# ============================================

def get_db_connection():
    """Obtener conexión a la base de datos"""
    db_path = Path(__file__).parent / "dashboard.db"
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    return conn

def load_real_spend():
    """Cargar gasto real de OpenRouter desde account_snapshots"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT total_usage, total_credits FROM account_snapshots ORDER BY timestamp DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()
    if row:
        return {'usage': row[0], 'total': row[1]}
    return {'usage': 0, 'total': 0}

# ============================================
# FUNCIONES DE CARGA DE DATOS
# ============================================

def load_sessions_data():
    """Cargar datos de sesiones"""
    conn = get_db_connection()
    query = """
    SELECT 
        id, source, model, started_at, ended_at,
        message_count, tool_call_count, api_call_count,
        input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, reasoning_tokens,
        estimated_cost_usd, actual_cost_calculated, date,
        (COALESCE(input_tokens, 0) + COALESCE(output_tokens, 0) + 
         COALESCE(cache_read_tokens, 0) + COALESCE(cache_write_tokens, 0) + 
         COALESCE(reasoning_tokens, 0)) as total_tokens
    FROM sessions
    ORDER BY started_at DESC
    """
    df = pd.read_sql_query(query, conn)
    if not df.empty:
        df['started_at'] = pd.to_datetime(df['started_at'], unit='s')
        df['ended_at'] = pd.to_datetime(df['ended_at'], unit='s')
        df['duration_seconds'] = (df['ended_at'] - df['started_at']).dt.total_seconds()
        df['duration_seconds'] = df['duration_seconds'].clip(lower=1)
        df['tokens_per_second'] = df['total_tokens'] / df['duration_seconds']
    return df

def load_tool_usage_data():
    """Cargar datos de uso de herramientas"""
    conn = get_db_connection()
    query = """
    SELECT 
        id, session_id, tool_name, timestamp, success,
        error_message, duration_ms, arguments, result_summary
    FROM tool_usage
    ORDER BY timestamp DESC
    """
    df = pd.read_sql_query(query, conn)
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df['date'] = df['timestamp'].dt.date
    return df

def load_openrouter_costs_data():
    """Cargar datos de costes de OpenRouter"""
    conn = get_db_connection()
    query = """
    SELECT 
        id, timestamp, model, input_tokens, output_tokens,
        total_tokens, actual_cost_usd, estimated_cost_usd,
        discrepancy_percent, request_id, session_id, source
    FROM openrouter_costs
    ORDER BY timestamp DESC
    """
    df = pd.read_sql_query(query, conn)
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df['date'] = df['timestamp'].dt.date
    return df

def load_errors_data():
    """Cargar datos de errores"""
    conn = get_db_connection()
    query = """
    SELECT 
        id, timestamp, source, error_type, message,
        session_id, tool_name, stack_trace, resolved
    FROM errors_log
    ORDER BY timestamp DESC
    """
    df = pd.read_sql_query(query, conn)
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df['date'] = df['timestamp'].dt.date
    return df

def load_daily_stats():
    """Cargar estadísticas diarias"""
    conn = get_db_connection()
    query = """
    SELECT 
        date, session_count, message_count,
        input_tokens, output_tokens, total_tokens,
        estimated_cost_usd, models_used, sources_used
    FROM daily_stats
    ORDER BY date DESC
    """
    df = pd.read_sql_query(query, conn)
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df

def load_model_stats():
    """Cargar estadísticas por modelo"""
    conn = get_db_connection()
    query = """
    SELECT 
        model, session_count, input_tokens, output_tokens,
        total_tokens, estimated_cost_usd, last_used
    FROM model_stats
    ORDER BY total_tokens DESC
    """
    df = pd.read_sql_query(query, conn)
    if not df.empty:
        df['last_used'] = pd.to_datetime(df['last_used'], unit='s')
    return df

# ============================================
# FUNCIONES DE VISUALIZACIÓN
# ============================================

def create_tokens_by_model_chart(df_sessions):
    """Gráfico de barras apilado de tokens por modelo por día"""
    if df_sessions.empty:
        return None
    
    df_sessions['date_only'] = df_sessions['started_at'].dt.date
    grouped = df_sessions.groupby(['date_only', 'model'])['total_tokens'].sum().reset_index()
    pivot = grouped.pivot(index='date_only', columns='model', values='total_tokens').fillna(0)
    
    fig = go.Figure()
    colors = ['#3B82F6', '#EC4899', '#22C55E', '#EAB308', '#F97316', '#A855F7', '#06B6D4', '#84CC16', '#D946EF', '#14B8A6']
    
    for i, (model, values) in enumerate(pivot.items()):
        fig.add_trace(go.Bar(
            x=pivot.index,
            y=values,
            name=model,
            marker_color=colors[i % len(colors)],
            opacity=0.9,
            hovertemplate=f'<b>%{{x}}</b><br>%{{y:,.0f}} tokens<br><span style="color:{colors[i % len(colors)]}">●</span> {model}<extra></extra>' 
        ))
    
    fig.update_layout(
        barmode='stack',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#AAAAAA', size=12),
        height=400,
        margin=dict(l=10, r=10, t=10, b=30),
        xaxis=dict(
            gridcolor='#1A1A1A', showgrid=True, zeroline=False,
            title=None, tickfont=dict(size=11)
        ),
        yaxis=dict(
            gridcolor='#1A1A1A', showgrid=True, zeroline=False,
            title='Tokens', tickformat=',', tickfont=dict(size=11)
        ),
        legend=dict(
            orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
            font=dict(size=11, color='#AAAAAA'),
            bgcolor='rgba(0,0,0,0)'
        ),
        hovermode='x unified',
        hoverlabel=dict(bgcolor='#1A1A1A', font_size=12, font_color='#FFFFFF')
    )
    return fig

def create_tool_usage_chart(df_tools):
    """Grafico de barras apilado de uso de herramientas por dia"""
    if df_tools.empty:
        return None
    
    grouped = df_tools.groupby(['date', 'tool_name']).size().reset_index(name='count')
    pivot = grouped.pivot(index='date', columns='tool_name', values='count').fillna(0)
    
    fig = go.Figure()
    colors = ['#3B82F6', '#EC4899', '#22C55E', '#EAB308', '#F97316', '#A855F7', '#06B6D4', '#84CC16', '#D946EF', '#14B8A6']
    
    for i, (tool, values) in enumerate(pivot.items()):
        fig.add_trace(go.Bar(
            x=pivot.index,
            y=values,
            name=tool,
            marker_color=colors[i % len(colors)],
            opacity=0.9,
                        hovertemplate=f'<b>%{{x}}</b><br>%{{y:,.0f}} llamadas<br><span style="color:{colors[i % len(colors)]}">●</span> {tool}<extra></extra>'
        ))
    
    fig.update_layout(
        barmode='stack',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#AAAAAA', size=12),
        height=400,
        margin=dict(l=10, r=10, t=10, b=30),
        xaxis=dict(gridcolor='#1A1A1A', showgrid=True, zeroline=False, title=None, tickfont=dict(size=11)),
        yaxis=dict(gridcolor='#1A1A1A', showgrid=True, zeroline=False, title='Llamadas', tickformat=',', tickfont=dict(size=11)),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=11, color='#AAAAAA'), bgcolor='rgba(0,0,0,0)'),
        hovermode='x unified',
        hoverlabel=dict(bgcolor='#1A1A1A', font_size=12, font_color='#FFFFFF')
    )
    return fig

def create_tool_distribution_chart(df_tools):
    """Grafico de pastel de distribucion de herramientas"""
    if df_tools.empty:
        return None
    
    tool_counts = df_tools['tool_name'].value_counts()
    
    # Filtrar <1% como "Otros"
    total = tool_counts.sum()
    threshold = total * 0.01
    significant = tool_counts[tool_counts >= threshold]
    others = tool_counts[tool_counts < threshold].sum()
    if others > 0:
        significant['Otros'] = others
    
    colors = ['#3B82F6', '#EC4899', '#22C55E', '#EAB308', '#F97316', '#A855F7', '#06B6D4', '#84CC16', '#D946EF', '#14B8A6']
    
    fig = go.Figure(data=[go.Pie(
        labels=significant.index,
        values=significant.values,
        hole=0.45,
        marker=dict(
            colors=colors[:len(significant)],
            line=dict(color='#000000', width=2)
        ),
        textinfo='label+percent',
        textfont=dict(size=12, color='#FFFFFF'),
        hovertemplate='<b>%{label}</b><br>%{value:,.0f} llamadas (%{percent})<extra></extra>'
    )])
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#AAAAAA', size=12),
        height=400,
        margin=dict(l=10, r=10, t=10, b=30),
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=11, color='#AAAAAA'), bgcolor='rgba(0,0,0,0)'),
        hoverlabel=dict(bgcolor='#1A1A1A', font_size=12, font_color='#FFFFFF')
    )
    return fig

def create_cost_comparison_chart(df_costs):
    """Gráfico de comparación costes reales vs estimados"""
    if df_costs.empty:
        return None
    
    grouped = df_costs.groupby('date').agg({
        'actual_cost_usd': 'sum',
        'estimated_cost_usd': 'sum'
    }).reset_index()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=grouped['date'], y=grouped['estimated_cost_usd'],
        mode='lines+markers', name='Estimado',
        line=dict(color='#F87171', width=3), marker=dict(size=8)
    ))
    fig.add_trace(go.Scatter(
        x=grouped['date'], y=grouped['actual_cost_usd'],
        mode='lines+markers', name='Real',
        line=dict(color='#4ADE80', width=3), marker=dict(size=8)
    ))
    
    fig.update_layout(
        title="Costes Estimados vs Reales",
        plot_bgcolor='#000000',
        paper_bgcolor='#000000',
        font_color='#FFFFFF',
        xaxis_title="Fecha", yaxis_title="Coste (USD)",
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def create_error_trend_chart(df_errors):
    """Gráfico de tendencia de errores"""
    if df_errors.empty:
        return None
    
    error_trend = df_errors.groupby(['date', 'error_type']).size().reset_index(name='count')
    
    fig = go.Figure()
    for error_type in error_trend['error_type'].unique()[:5]:
        subset = error_trend[error_trend['error_type'] == error_type]
        fig.add_trace(go.Scatter(
            x=subset['date'], y=subset['count'],
            mode='lines+markers', name=error_type,
            line=dict(width=2)
        ))
    
    fig.update_layout(
        title="Tendencia de Errores",
        plot_bgcolor='#000000',
        paper_bgcolor='#000000',
        font_color='#FFFFFF',
        xaxis_title="Fecha", yaxis_title="Número de Errores",
        hovermode='x unified'
    )
    return fig

def create_model_performance_chart(df_sessions):
    """Gráfico de performance por modelo"""
    if df_sessions.empty:
        return None
    
    performance = df_sessions.groupby('model').agg({
        'duration_seconds': 'mean',
        'tokens_per_second': 'mean',
        'total_tokens': 'sum',
        'id': 'count'
    }).rename(columns={'id': 'session_count'}).reset_index()
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=performance['model'], y=performance['tokens_per_second'],
        name='Tokens/segundo', marker_color='#3B82F6'
    ))
    
    fig.update_layout(
        title="Performance por Modelo (Tokens/segundo)",
        plot_bgcolor='#000000',
        paper_bgcolor='#000000',
        font_color='#FFFFFF',
        xaxis_title="Modelo",
        yaxis_title="Tokens/segundo",
        showlegend=False
    )
    return fig

def create_source_distribution_chart(df_sessions):
    """Gráfico de distribución por fuente"""
    if df_sessions.empty:
        return None
    
    source_counts = df_sessions['source'].value_counts()
    
    # Filtrar fuentes con <1% y agrupar como "Otros"
    total = source_counts.sum()
    threshold = total * 0.01
    significant = source_counts[source_counts >= threshold]
    others = source_counts[source_counts < threshold].sum()
    if others > 0:
        significant['Otros'] = others
    
    colors = ['#3B82F6', '#EC4899', '#22C55E', '#EAB308', '#F97316', '#A855F7', '#06B6D4', '#84CC16', '#D946EF', '#14B8A6']
    
    fig = go.Figure(data=[go.Pie(
        labels=significant.index,
        values=significant.values,
        hole=0.45,
        marker=dict(
            colors=colors[:len(significant)],
            line=dict(color='#000000', width=2)
        ),
        textinfo='label+percent',
        textfont=dict(size=12, color='#FFFFFF'),
        hovertemplate='<b>%{label}</b><br>%{value:,.0f} sesiones (%{percent})<extra></extra>'
    )])
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#AAAAAA', size=12),
        height=400,
        margin=dict(l=10, r=10, t=10, b=30),
        showlegend=True,
        legend=dict(
            orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
            font=dict(size=11, color='#AAAAAA'),
            bgcolor='rgba(0,0,0,0)'
        ),
        hoverlabel=dict(bgcolor='#1A1A1A', font_size=12, font_color='#FFFFFF')
    )

    return fig

# ============================================
# PESTAÑA: OVERVIEW
# ============================================

def render_overview_tab(df_sessions, df_daily, df_models, real_spend):
    """Renderizar pestaña de overview"""
    
    # Métricas principales (cards personalizadas)
    total_sessions = len(df_sessions)
    total_tokens = df_sessions['total_tokens'].sum() if not df_sessions.empty else 0

    unique_models = df_sessions['model'].nunique() if not df_sessions.empty else 0
    days_active = df_sessions['started_at'].dt.date.nunique() if not df_sessions.empty else 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f'''
        <div class="custom-card" style="border-left: 4px solid #F59E0B !important;">
            <div class="card-title">Sesiones Totales</div>
            <div class="card-value card-value-amber">{total_sessions:,}</div>
            <div class="card-delta">{days_active} d\u00edas activos</div>
        </div>''', unsafe_allow_html=True)

    with col2:
        st.markdown(f'''
        <div class="custom-card" style="border-left: 4px solid #3B82F6 !important;">
            <div class="card-title">Tokens Totales</div>
            <div class="card-value card-value-blue">{total_tokens:,}</div>
            <div class="card-delta">{total_tokens/1_000_000:.1f}M tokens</div>
        </div>''', unsafe_allow_html=True)

    with col3:
        or_used = real_spend['usage']
        or_total = real_spend['total']
        if or_used > 0:
            remaining = or_total - or_used
            pct = (or_used / or_total * 100) if or_total > 0 else 0
            st.markdown(f'''
        <div class="custom-card" style="border-left: 4px solid #4ADE80 !important;">
            <div class="card-title">Gastado en OpenRouter</div>
            <div class="card-value card-value-green">\u20ac{or_used * 0.92:.2f}</div>
            <div class="card-delta">${or_used:.2f} USD \u00b7 {pct:.0f}% de ${or_total:.0f}</div>
        </div>''', unsafe_allow_html=True)
        else:
            st.markdown('''
        <div class="custom-card">
            <div class="card-title">Gastado en OpenRouter</div>
            <div class="card-value" style="font-size: 18px;">Sin datos</div>
            <div class="card-delta">Ejecuta el collector</div>
        </div>''', unsafe_allow_html=True)

    with col4:
        st.markdown(f'''
        <div class="custom-card" style="border-left: 4px solid #A855F7 !important;">
            <div class="card-title">Modelos Usados</div>
            <div class="card-value">{unique_models}</div>
            <div class="card-delta">{df_sessions['source'].nunique() if not df_sessions.empty else 0} fuentes</div>
        </div>''', unsafe_allow_html=True)

    
    st.divider()
    
    # Gráficos principales
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="section-header"><h3>📊 Tokens por Modelo (Diario)</h3></div>', unsafe_allow_html=True)
        if not df_sessions.empty:
            fig = create_tokens_by_model_chart(df_sessions)
            if fig:
                st.plotly_chart(fig, use_container_width=True, key="chart_tokens_by_model")
        else:
            st.info("No hay datos de sesiones disponibles")
    
    with col2:
        st.markdown('<div class="section-header"><h3>🔀 Uso por Fuente</h3></div>', unsafe_allow_html=True)
        if not df_sessions.empty:
            fig = create_source_distribution_chart(df_sessions)
            if fig:
                st.plotly_chart(fig, use_container_width=True, key="chart_source_dist")
        else:
            st.info("No hay datos de sesiones disponibles")
    
    # Tabla de sesiones recientes
    st.markdown('<div class="section-header"><h3>📋 Sesiones Recientes</h3></div>', unsafe_allow_html=True)
    if not df_sessions.empty:
        recent = df_sessions.head(10)[[
            'started_at', 'model', 'source', 'message_count',
            'tool_call_count', 'total_tokens'
        ]].copy()
        recent['started_at'] = recent['started_at'].dt.strftime('%Y-%m-%d %H:%M')

        st.dataframe(
            recent,
            column_config={
                "started_at": "Fecha", "model": "Modelo", "source": "Fuente",
                "message_count": "Mensajes", "tool_call_count": "Tools",
                "total_tokens": "Tokens"
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hay sesiones disponibles")

# ============================================
# PESTAÑA: TOOLS ANALYTICS
# ============================================

def render_tools_tab(df_tools, df_sessions):
    """Renderizar pestaña de análisis de herramientas"""

    st.markdown('<div class="section-header"><h3>📊 Análisis de Uso de Herramientas</h3></div>', unsafe_allow_html=True)
    st.markdown('<p style="color:#888; margin-top:-0.5rem; margin-bottom:1.5rem;">Visualización detallada del uso de herramientas por día, tipo y sesión</p>', unsafe_allow_html=True)

    if df_tools.empty:
        st.warning("No se encontraron datos de uso de herramientas. Ejecuta el collector primero.")
        return

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="custom-card" style="border-left: 4px solid #3B82F6 !important;"><div class="card-title">Llamadas a Tools</div><div class="card-value card-value-blue">{len(df_tools):,}</div><div class="card-delta">Total acumulado</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="custom-card" style="border-left: 4px solid #A855F7 !important;"><div class="card-title">Tools Únicos</div><div class="card-value">{df_tools["tool_name"].nunique()}</div><div class="card-delta">Tipos distintos</div></div>', unsafe_allow_html=True)
    with col3:
        success_rate = (df_tools["success"].sum() / len(df_tools)) * 100 if len(df_tools) > 0 else 0
        st.markdown(f'<div class="custom-card" style="border-left: 4px solid #4ADE80 !important;"><div class="card-title">Tasa de Éxito</div><div class="card-value card-value-green">{success_rate:.1f}%</div><div class="card-delta">Operaciones exitosas</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="custom-card" style="border-left: 4px solid #F59E0B !important;"><div class="card-title">Sesiones con Tools</div><div class="card-value card-value-amber">{df_tools["session_id"].nunique()}</div><div class="card-delta">Sesiones activas</div></div>', unsafe_allow_html=True)

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-header"><h3>📈 Uso de Herramientas por Día</h3></div>', unsafe_allow_html=True)
        fig = create_tool_usage_chart(df_tools)
        if fig: st.plotly_chart(fig, use_container_width=True, key="chart_tools_daily")
        else: st.info("No hay datos suficientes para el gráfico")

    with col2:
        st.markdown('<div class="section-header"><h3>🧩 Distribución de Herramientas</h3></div>', unsafe_allow_html=True)
        fig = create_tool_distribution_chart(df_tools)
        if fig: st.plotly_chart(fig, use_container_width=True, key="chart_tools_pie")
        else: st.info("No hay datos suficientes para el gráfico")

    st.markdown('<div class="section-header"><h3>🏆 Herramientas Más Utilizadas</h3></div>', unsafe_allow_html=True)
    tool_stats = df_tools.groupby('tool_name').agg({
        'id': 'count', 'success': 'mean', 'duration_ms': 'mean'
    }).rename(columns={'id': 'count', 'success': 'success_rate'}).reset_index()
    tool_stats = tool_stats.sort_values('count', ascending=False)
    tool_stats['success_rate'] = (tool_stats['success_rate'] * 100).round(1)
    tool_stats['duration_ms'] = pd.to_numeric(tool_stats['duration_ms'], errors='coerce').round(1)

    st.dataframe(
        tool_stats,
        column_config={
            "tool_name": "Herramienta", "count": "Llamadas",
            "success_rate": "Éxito (%)", "duration_ms": "Duración (ms)"
        },
        use_container_width=True,
        hide_index=True
    )

def render_tokens_tab(df_sessions):
    """Renderizar pestaña de análisis de tokens — estilo OpenRouter rankings"""
    
    st.markdown("## 📊 Análisis de Tokens")
    st.markdown("Ranking de modelos por uso, consumo diario y eficiencia de costes")

    if df_sessions.empty:
        st.info("No hay datos de sesiones disponibles")
        return

    # === DATOS ===
    total_input = df_sessions["input_tokens"].sum()
    total_output = df_sessions["output_tokens"].sum()
    total_cache_read = df_sessions["cache_read_tokens"].sum() if "cache_read_tokens" in df_sessions.columns else 0
    total_cache_write = df_sessions["cache_write_tokens"].sum() if "cache_write_tokens" in df_sessions.columns else 0
    total_reasoning = df_sessions["reasoning_tokens"].sum() if "reasoning_tokens" in df_sessions.columns else 0
    total_all = total_input + total_output + total_cache_read + total_cache_write + total_reasoning

    or_spend = load_real_spend()
    or_used = or_spend["usage"]
    or_total = or_spend["total"]
    remaining = or_total - or_used if or_used > 0 else 0
    days_active = df_sessions["started_at"].dt.date.nunique()

    cost_per_million = (or_used / total_all * 1_000_000) if total_all > 0 else 0

    # === KPI ROW (4 cards compactas) ===
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="custom-card" style="border-left: 4px solid #3B82F6 !important;">
            <div class="card-title">Total Tokens</div>
            <div class="card-value">{total_all:,.0f}</div>
            <div class="card-delta">Input {total_input/total_all*100:.0f}% · Output {total_output/total_all*100:.0f}%</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        pct_used = (or_used / or_total * 100) if or_total > 0 else 0
        st.markdown(f"""
        <div class="custom-card" style="border-left: 4px solid #EC4899 !important;">
            <div class="card-title">Crédito Usado</div>
            <div class="card-value" style="color:#F87171;">${or_used:.2f}</div>
            <div class="card-delta">{pct_used:.1f}% de ${or_total:.0f}</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="custom-card" style="border-left: 4px solid #4ADE80 !important;">
            <div class="card-title">Crédito Restante</div>
            <div class="card-value" style="color:#4ADE80;">${remaining:.2f}</div>
            <div class="card-delta">{or_total - remaining:.2f} gastado</div>
        </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="custom-card" style="border-left: 4px solid #EAB308 !important;">
            <div class="card-title">Coste / Millón Tokens</div>
            <div class="card-value">${cost_per_million:.2f}</div>
            <div class="card-delta">{days_active} días activos</div>
        </div>""", unsafe_allow_html=True)

    st.divider()

    # === RANKING DE MODELOS (como OpenRouter leaderboard) ===
    st.markdown("### 🏆 Ranking de Modelos por Tokens")
    
    model_stats = df_sessions.groupby("model").agg(
        tokens=("total_tokens", "sum"),
        sesiones=("id", "nunique"),
        coste=("actual_cost_calculated", "sum")
    ).reset_index().sort_values("tokens", ascending=False)
    
    # Filter insignificant (< 1% of total)
    threshold = model_stats["tokens"].sum() * 0.01
    model_stats["pct"] = (model_stats["tokens"] / model_stats["tokens"].sum() * 100).round(1)
    
    colors_palette = ["#3B82F6", "#EC4899", "#22C55E", "#EAB308", "#F97316", "#A855F7", "#06B6D4", "#84CC16", "#D946EF", "#14B8A6"]
    
    # Build ranking HTML
    rank_html = '<div style="display:flex; flex-direction:column; gap:0.3rem;">'
    for i, (_, row) in enumerate(model_stats.iterrows()):
        color = colors_palette[i % len(colors_palette)]
        bar_pct = min(row["pct"] * 2, 100)  # Scale bar
        cost_str = f"${row['coste']:.2f}" if row["coste"] > 0 else "—"
        rank_html += f"""
        <div style="display:flex; align-items:center; gap:0.5rem; padding:0.4rem 0.8rem; background:#1A1A1A; border-radius:8px; border-left:3px solid {color};">
            <span style="color:#666; font-weight:700; min-width:1.5rem;">#{i+1}</span>
            <span style="color:#FFF; font-weight:500; flex:1; font-size:0.85rem;">{row['model']}</span>
            <span style="color:#FFF; font-weight:600; min-width:6rem; text-align:right;">{row['tokens']:,.0f}</span>
            <span style="color:#AAA; min-width:3rem; text-align:right; font-size:0.8rem;">{row['pct']}%</span>
            <span style="color:#4ADE80; min-width:4rem; text-align:right; font-size:0.8rem;">{cost_str}</span>
            <div style="width:4rem; height:6px; background:#333; border-radius:3px;">
                <div style="width:{bar_pct}%; height:100%; background:{color}; border-radius:3px;"></div>
            </div>
            <span style="color:#666; font-size:0.75rem; min-width:2rem;">{row['sesiones']} ses</span>
        </div>"""
    rank_html += '</div>'
    
    st.markdown(rank_html, unsafe_allow_html=True)

    st.divider()

    # === TOKENS POR MODELO (STACKED BAR - OpenRouter style) ===
    st.markdown("### 📈 Consumo Diario por Modelo")
    fig = create_tokens_by_model_chart(df_sessions)
    if fig:
        st.plotly_chart(fig, use_container_width=True, key="chart_tokens")
    
    st.divider()

    # === DESGLOSE + COSTES (2 columnas) ===
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📊 Desglose por Tipo")
        token_types = pd.DataFrame({
            'Tipo': ['Input', 'Output', 'Cache Read', 'Cache Write', 'Reasoning'],
            'Tokens': [total_input, total_output, total_cache_read, total_cache_write, total_reasoning]
        })
        token_types = token_types[token_types["Tokens"] > 0]
        # Filter < 1%
        total_tt = token_types["Tokens"].sum()
        threshold_tt = total_tt * 0.01
        sig = token_types[token_types["Tokens"] >= threshold_tt]
        others = token_types[token_types["Tokens"] < threshold_tt]
        if not others.empty:
            sig = pd.concat([sig, pd.DataFrame([{'Tipo': 'Otros', 'Tokens': others["Tokens"].sum()}])])
        
        if not sig.empty:
            used_colors = [["#3B82F6", "#EC4899", "#22C55E", "#EAB308", "#F97316", "#666"][i % 6] for i in range(len(sig))]
            fig = go.Figure(data=[go.Pie(
                labels=sig['Tipo'],
                values=sig['Tokens'],
                hole=0.4,
                marker_colors=used_colors,
                textinfo='label+percent',
                textfont=dict(color='white', size=11),
                textposition='outside'
            )])
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#AAAAAA', size=12),
                showlegend=False,
                margin=dict(t=0, b=0, l=0, r=0)
            )
            st.plotly_chart(fig, use_container_width=True, key="chart_breakdown")

    with col2:
        st.markdown("### 💰 Coste Real por Modelo")
        if "actual_cost_calculated" in df_sessions.columns:
            real_by_model = df_sessions[df_sessions["actual_cost_calculated"].notna()]                 .groupby("model")["actual_cost_calculated"].sum().reset_index()
            real_by_model.columns = ['model', 'coste_real_usd']
            real_by_model = real_by_model.sort_values('coste_real_usd', ascending=False)
            # Filter < 1%
            total_cost = real_by_model["coste_real_usd"].sum()
            thresh_cost = total_cost * 0.01 if total_cost > 0 else 0
            sig_cost = real_by_model[real_by_model["coste_real_usd"] >= thresh_cost]
            
            if not sig_cost.empty:
                c_colors = [colors_palette[i % len(colors_palette)] for i in range(len(sig_cost))]
                fig = go.Figure(data=[go.Bar(
                    x=sig_cost['model'],
                    y=sig_cost['coste_real_usd'],
                    marker_color=c_colors,
                    text=[f"${v:.2f}" for v in sig_cost['coste_real_usd']],
                    textposition='outside',
                    textfont=dict(color='white', size=10)
                )])
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#AAAAAA', size=12),
                    xaxis=dict(tickangle=45, tickfont=dict(size=9), gridcolor='#1A1A1A'),
                    yaxis=dict(gridcolor='#1A1A1A'),
                    yaxis_title='USD',
                    margin=dict(t=0, b=80, l=0, r=0),
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True, key="chart_real_cost")
            else:
                st.info('Sin datos de coste real')
        else:
            st.info('Costes reales no disponibles — ejecuta el collector')

    st.divider()

    # === MANAGEMENT KEY (compacto) ===
    with st.expander("🔑 OpenRouter Management Key — activar comparativa exacta"):
        st.markdown("""
        <div class="custom-card" style="padding:0.8rem 1rem;">
            <p style="color:#AAA; margin:0; font-size:0.85rem;">
                Añade tu <strong>Management Key</strong> en <code style="color:#3B82F6;">~/.hermes/.env</code> como
                <code style="color:#3B82F6;">OPENROUTER_MANAGEMENT_KEY=sk-or-v1-...</code>
                para ver la comparativa exacta Hermes vs OpenRouter.
                <a href="https://openrouter.ai/settings/keys" style="color:#3B82F6;" target="_blank">Conseguir key →</a>
            </p>
        </div>
        """, unsafe_allow_html=True)


def render_errors_tab(df_errors, df_sessions):
    """Renderizar pestaña de errores y performance con filtros, clustering y priorización"""
    
    st.markdown('<div class="section-header"><h3>⚠️ Errores & Performance</h3></div>', unsafe_allow_html=True)
    st.markdown('<p style="color:#888; margin-top:-0.5rem; margin-bottom:1.5rem;">Seguimiento de errores, clustering por patrón y métricas de performance</p>', unsafe_allow_html=True)
    
    # =============================================
    # FILTROS INTERACTIVOS (Sidebar + Inline)
    # =============================================
    if not df_errors.empty:
        with st.expander("🔍 Filtros de Errores", expanded=not df_errors.empty):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                sources = ["Todas"] + sorted(df_errors['source'].dropna().unique().tolist())
                sel_source = st.selectbox("Fuente", sources, key="err_filter_source")
            with col2:
                types = ["Todos"] + sorted(df_errors['error_type'].dropna().unique().tolist())
                sel_type = st.selectbox("Tipo", types, key="err_filter_type")
            with col3:
                tools = ["Todas"] + sorted(df_errors['tool_name'].dropna().unique().tolist())
                sel_tool = st.selectbox("Herramienta", tools, key="err_filter_tool")
            with col4:
                sel_resolved = st.selectbox(
                    "Estado", ["Todos", "❌ No Resueltos", "✅ Resueltos"],
                    key="err_filter_resolved"
                )
        
        # Aplicar filtros
        filtered = df_errors.copy()
        if sel_source != "Todas":
            filtered = filtered[filtered['source'] == sel_source]
        if sel_type != "Todos":
            filtered = filtered[filtered['error_type'] == sel_type]
        if sel_tool != "Todas":
            filtered = filtered[filtered['tool_name'] == sel_tool]
        if sel_resolved == "❌ No Resueltos":
            filtered = filtered[filtered['resolved'] == 0]
        elif sel_resolved == "✅ Resueltos":
            filtered = filtered[filtered['resolved'] == 1]
        
        filt_label = f" ({len(filtered)} de {len(df_errors)} errores)" if len(filtered) < len(df_errors) else ""
    else:
        filtered = df_errors
        filt_label = ""
    
    # =============================================
    # MÉTRICAS (sobre datos filtrados)
    # =============================================
        col1, col2, col3, col4 = st.columns(4)
    with col1:
        err_count = len(filtered) if not filtered.empty else 0
        st.markdown(f'<div class="custom-card" style="border-left: 4px solid #EC4899 !important;"><div class="card-title">Errores Totales{filt_label}</div><div class="card-value card-value-red">{err_count:,}</div><div class="card-delta">Total registrados</div></div>', unsafe_allow_html=True)
    with col2:
        src_count = filtered["source"].nunique() if not filtered.empty else 0
        st.markdown(f'<div class="custom-card" style="border-left: 4px solid #A855F7 !important;"><div class="card-title">Fuentes de Error</div><div class="card-value">{src_count}</div><div class="card-delta">Origenes distintos</div></div>', unsafe_allow_html=True)
    with col3:
        unresolved = filtered[filtered["resolved"] == 0].shape[0] if not filtered.empty else 0
        st.markdown(f'<div class="custom-card" style="border-left: 4px solid #F59E0B !important;"><div class="card-title">Sin Resolver</div><div class="card-value card-value-amber">{unresolved:,}</div><div class="card-delta">Pendientes de revision</div></div>', unsafe_allow_html=True)
    with col4:
        tool_errors = filtered[filtered["source"] == "tool_call"].shape[0] if not filtered.empty else 0
        st.markdown(f'<div class="custom-card" style="border-left: 4px solid #3B82F6 !important;"><div class="card-title">Errores de Tools</div><div class="card-value card-value-blue">{tool_errors}</div><div class="card-delta">Fallos en tool calls</div></div>', unsafe_allow_html=True)
    st.divider()
    
    # =============================================
    # CLUSTERING Y PRIORIZACIÓN
    # =============================================
    if not filtered.empty:
        st.markdown("### 📊 Clustering por Patrón de Error (Priorizado)")
        
        # Limpiar mensaje: minúsculas, quitar espacios, primeros 100 chars
        df_cluster = filtered.copy()
        df_cluster['msg_clean'] = (
            df_cluster['message']
            .str.lower()
            .str.strip()
            .str.replace(r'\s+', ' ', regex=True)
            .str[:100]
        )
        
        # Agrupar por patrón
        clusters = df_cluster.groupby('msg_clean').agg(
            total=('id', 'count'),
            unresolved=('resolved', lambda x: int((x == 0).sum())),
            first_seen=('timestamp', 'min'),
            last_seen=('timestamp', 'max'),
            sources=('source', lambda x: ', '.join(x.dropna().unique())),
            sample_msg=('message', 'first'),
            sample_tool=('tool_name', lambda x: ', '.join(x.dropna().unique()[:3]))
        ).reset_index()
        
        # Priorización: frecuencia × (1 + peso_no_resueltos)
        clusters['priority'] = (clusters['total'] * (1 + clusters['unresolved'] / clusters['total'].clip(lower=1))).round(1)
        clusters = clusters.sort_values('priority', ascending=False)
        
        # Top 15 clusters
        top_clusters = clusters.head(15)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Gráfico de barras: prioridad por cluster
            short_labels = top_clusters['sample_msg'].str[:50].tolist()
            fig = go.Figure(data=[go.Bar(
                x=top_clusters['priority'],
                y=short_labels,
                orientation='h',
                marker_color='#3B82F6',
                text=top_clusters['total'].astype(str) + ' err' + 
                     ' · ' + top_clusters['unresolved'].astype(str) + ' sin resolver',
                textposition='outside',
                hovertemplate=(
                    '<b>Patrón:</b> %{customdata}<br>'
                    '<b>Total:</b> %{text}<br>'
                    '<b>Prioridad:</b> %{x}<br>'
                    '<b>Fuentes:</b> %{customdata[1]}<extra></extra>'
                ),
                customdata=list(zip(top_clusters['sample_msg'], top_clusters['sources']))
            )])
            fig.update_layout(
                title="Top Patrones de Error por Prioridad",
                height=500,
                xaxis_title="Puntuación de Prioridad",
                yaxis=dict(autorange='reversed', showgrid=False),
                plot_bgcolor='#000000', paper_bgcolor='#000000',
                font_color='#FFFFFF',
                margin=dict(l=0, r=0, t=40, b=0)
            )
            st.plotly_chart(fig, use_container_width=True, key="chart_error_clusters")
        
        with col2:
            st.markdown("**Leyenda de Prioridad**")
            st.caption(
                "La prioridad combina **frecuencia** y **errores sin resolver**: "
                "`total × (1 + unresolved/total)`. "
                "Un patrón con 10 errores y 8 sin resolver puntúa más alto "
                "que uno con 20 errores y 2 sin resolver."
            )
            st.markdown("**Top 5 patrones**")
            for _, row in top_clusters.head(5).iterrows():
                pct_unres = int(row['unresolved'] / row['total'] * 100) if row['total'] > 0 else 0
                st.markdown(
                    f"<div style='background:#1A1A1A;border-radius:8px;padding:0.5rem;margin-bottom:0.3rem;border-left:3px solid #3B82F6;'>"
                    f"<div style='color:#FFF;font-size:0.85rem;font-weight:600;'>{row['total']} err · {pct_unres}% sin resolver</div>"
                    f"<div style='color:#AAA;font-size:0.75rem;'>{row['sample_msg'][:80]}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        
        # Tabla detallada de clusters
        with st.expander("📋 Ver tabla completa de clusters"):
            display_clusters = clusters.copy()
            display_clusters['sample_msg'] = display_clusters['sample_msg'].str[:100]
            display_clusters['first_seen'] = display_clusters['first_seen'].dt.strftime('%Y-%m-%d')
            display_clusters['last_seen'] = display_clusters['last_seen'].dt.strftime('%Y-%m-%d')
            st.dataframe(
                display_clusters[['priority', 'total', 'unresolved', 'sample_msg', 'sources', 'first_seen', 'last_seen']].head(50),
                column_config={
                    "priority": st.column_config.NumberColumn("Prioridad", format="%.1f"),
                    "total": "Total", "unresolved": "Sin Resolver",
                    "sample_msg": st.column_config.TextColumn("Patrón (primeros 100 chars)", width="large"),
                    "sources": "Fuentes", "first_seen": "Primer", "last_seen": "Último"
                },
                use_container_width=True,
                hide_index=True
            )
        
        st.divider()
    
    # =============================================
    # GRÁFICOS (sobre datos filtrados)
    # =============================================
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Tendencia de Errores")
        fig = create_error_trend_chart(filtered)
        if fig: st.plotly_chart(fig, use_container_width=True, key="chart_error_trend")
        elif not filtered.empty:
            st.info("No hay suficientes datos para el gráfico de tendencias")
        else:
            st.info("No hay datos de errores disponibles")
    
    with col2:
        st.markdown("### Performance por Modelo")
        fig = create_model_performance_chart(df_sessions)
        if fig: st.plotly_chart(fig, use_container_width=True, key="chart_model_perf")
        elif not df_sessions.empty:
            st.info("No hay suficientes datos para el gráfico de performance")
        else:
            st.info("No hay datos de sesiones disponibles")
    
    # Gráfico de errores por hora del día
    if not filtered.empty:
        st.markdown("### 📈 Errores por Hora del Día")
        hour_data = filtered.copy()
        hour_data['hour'] = hour_data['timestamp'].dt.hour
        hourly = hour_data.groupby('hour').size().reset_index(name='count')
        fig = go.Figure(data=[go.Bar(x=hourly['hour'], y=hourly['count'], marker_color='#3B82F6')])
        fig.update_layout(
            plot_bgcolor='#000000', paper_bgcolor='#000000', font_color='#FFFFFF',
            xaxis=dict(tickmode='linear', dtick=1),
            xaxis_title="Hora del día (0‑23)", yaxis_title="Errores", bargap=0.1
        )
        st.plotly_chart(fig, use_container_width=True, key="chart_error_hourly")
        st.divider()

    # =============================================
    # TABLA DE ERRORES RECIENTES (filtrados)
    # =============================================
    if not filtered.empty:
        st.markdown("### Errores Recientes" + filt_label)
        recent_errors = filtered.head(20).copy()
        recent_errors['timestamp'] = recent_errors['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
        recent_errors['resolved'] = recent_errors['resolved'].map({0: "❌", 1: "✅"})
        
        st.dataframe(
            recent_errors[['timestamp', 'source', 'error_type', 'message', 
                          'tool_name', 'resolved']],
            column_config={
                "timestamp": "Fecha", "source": "Fuente", "error_type": "Tipo",
                "message": st.column_config.TextColumn("Mensaje", width="large"),
                "tool_name": "Tool", "resolved": "Resuelto"
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hay errores registrados" + (" con los filtros actuales" if filt_label else ""))

# ============================================
# FUNCIÓN PRINCIPAL
# ============================================


def load_system_performance_data():
    """Cargar datos de rendimiento del sistema (tool_usage + sessions para modelo)"""
    conn = get_db_connection()
    query = """
    SELECT 
        t.id, t.session_id, t.tool_name, t.timestamp, t.success,
        t.error_message, t.duration_ms,
        s.model, s.source, s.started_at as session_started
    FROM tool_usage t
    LEFT JOIN sessions s ON t.session_id = s.id
    ORDER BY t.timestamp DESC
    """
    df = pd.read_sql_query(query, conn)
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df['date'] = df['timestamp'].dt.date
    return df

def render_system_performance_tab(df_perf, df_sessions):
    """Renderizar pestaña System Performance (errores por modelo/herramienta)"""
    
    st.markdown('<div class="section-header"><h3>⚡ System Performance</h3></div>', unsafe_allow_html=True)
    st.markdown('<p style="color:#888; margin-top:-0.5rem; margin-bottom:1.5rem;">Métricas de rendimiento por modelo, errores y tiempos de ejecución</p>', unsafe_allow_html=True)
    
    # ── KPIs ──
    if not df_perf.empty:
        total_calls = len(df_perf)
        success_rate = (df_perf['success'].sum() / total_calls * 100) if total_calls > 0 else 0
        failed = total_calls - df_perf['success'].sum()
        models_with_errors = df_perf[df_perf['success'] == False]['model'].nunique() if failed > 0 else 0
    else:
        total_calls = 0; success_rate = 0; failed = 0; models_with_errors = 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="custom-card" style="border-left: 4px solid #3B82F6 !important;"><div class="card-title">Tool Calls</div><div class="card-value card-value-blue">{total_calls:,}</div><div class="card-delta">Total llamadas</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="custom-card" style="border-left: 4px solid #4ADE80 !important;"><div class="card-title">Tasa Exito</div><div class="card-value card-value-green">{success_rate:.1f}%</div><div class="card-delta">Operaciones exitosas</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="custom-card" style="border-left: 4px solid #EC4899 !important;"><div class="card-title">Fallos</div><div class="card-value card-value-red">{failed:,}</div><div class="card-delta">Errores detectados</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="custom-card" style="border-left: 4px solid #F59E0B !important;"><div class="card-title">Modelos con Fallos</div><div class="card-value card-value-amber">{models_with_errors}</div><div class="card-delta">Afectados</div></div>', unsafe_allow_html=True)
    
    st.divider()
    
    # ── Error Rate por Modelo + Herramienta ──
    if not df_perf.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Error Rate por Modelo")
            model_err = df_perf.groupby('model').agg(
                total_calls=('success', 'count'),
                failed=('success', lambda x: (x == 0).sum())
            ).reset_index()
            model_err['error_rate'] = (model_err['failed'] / model_err['total_calls'] * 100).round(1)
            model_err = model_err.sort_values('error_rate', ascending=False).head(15)
            
            if not model_err.empty:
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=model_err['model'], y=model_err['error_rate'],
                    marker_color='#F87171',
                    text=model_err['error_rate'].apply(lambda x: f"{x:.1f}%"),
                    textposition='outside',
                    hovertemplate='<b>%{x}</b><br>Error rate: %{y:.1f}%<br>Total: %{customdata[0]}<br>Failed: %{customdata[1]}<extra></extra>',
                    customdata=model_err[['total_calls', 'failed']].values
                ))
                fig.update_layout(
                    title="Error Rate por Modelo",
                    xaxis_tickangle=-45, height=400,
                    plot_bgcolor='#000000', paper_bgcolor='#000000',
                    font_color='#FFFFFF',
                    xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#333333')
                )
                st.plotly_chart(fig, use_container_width=True, key="chart_sys_error_rate")
            else:
                st.info("No hay datos suficientes para error rate por modelo")
        
        with col2:
            st.markdown("### Fallos por Herramienta")
            tool_err = df_perf[df_perf['success'] == False].groupby('tool_name').agg(
                failed_calls=('success', 'count')
            ).reset_index().sort_values('failed_calls', ascending=False).head(15)
            
            if not tool_err.empty:
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=tool_err['failed_calls'], y=tool_err['tool_name'],
                    orientation='h', marker_color='#3B82F6',
                    text=tool_err['failed_calls'],
                    textposition='outside'
                ))
                fig.update_layout(
                    title="Fallos por Herramienta",
                    height=400,
                    plot_bgcolor='#000000', paper_bgcolor='#000000',
                    font_color='#FFFFFF',
                    xaxis=dict(showgrid=True, gridcolor='#333333'),
                    yaxis=dict(showgrid=False, autorange='reversed')
                )
                st.plotly_chart(fig, use_container_width=True, key="chart_sys_tool_failures")
            else:
                st.info("No hay fallos registrados")
    
    st.divider()
    
    # ── Detalle: qué modelo falla con qué herramienta ──
    if not df_perf.empty and not df_perf[df_perf['success'] == False].empty:
        st.markdown("### 🔍 Matriz Modelo × Herramienta (Fallos)")
        
        failed_df = df_perf[df_perf['success'] == False].copy()
        matrix = failed_df.groupby(['model', 'tool_name']).size().reset_index(name='count')
        pivot = matrix.pivot_table(
            index='model', columns='tool_name', values='count',
            fill_value=0, aggfunc='sum'
        )
        
        # Show as heatmap
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=list(pivot.columns),
            y=list(pivot.index),
            colorscale=[[0, '#1A1A1A'], [0.5, '#3B82F6'], [1, '#F87171']],
            hovertemplate='<b>%{y}</b> × <b>%{x}</b><br>Fallos: %{z}<extra></extra>',
            showscale=False
        ))
        fig.update_layout(
            title="Matriz de Fallos: Modelo × Herramienta",
            height=400,
            xaxis_tickangle=-45,
            plot_bgcolor='#000000', paper_bgcolor='#000000',
            font_color='#FFFFFF',
            xaxis=dict(showgrid=False), yaxis=dict(showgrid=False)
        )
        st.plotly_chart(fig, use_container_width=True, key="chart_sys_matrix")
        
        # Detalle textual: top 10 pares modelo-herramienta fallidos
        st.markdown("### Top Fallos Modelo → Herramienta")
        top_fails = failed_df.groupby(['model', 'tool_name']).size().reset_index(name='count')
        top_fails = top_fails.sort_values('count', ascending=False).head(10)
        
        cols = st.columns([1, 2, 1, 3])
        cols[0].markdown("**#**")
        cols[1].markdown("**Modelo**")
        cols[2].markdown("**Herramienta**")
        cols[3].markdown("**Fallos**")
        st.markdown("---")
        for i, (_, row) in enumerate(top_fails.iterrows()):
            c1, c2, c3, c4 = st.columns([1, 2, 1, 3])
            c1.markdown(f"**{i+1}**")
            c2.markdown(f"`{row['model'][:40]}...`" if len(str(row['model'])) > 40 else f"`{row['model']}`")
            c3.markdown(f"`{row['tool_name']}`")
            c4.progress(min(row['count']/top_fails['count'].max(), 1.0), text=str(int(row['count'])))
    else:
        st.info("No hay datos de fallos disponibles. El collector aún no ha procesado tool_usage desde state.db.")
    
    st.divider()
    
    # ── Tendencia de Errores en el Tiempo ──
    if not df_perf.empty:
        st.markdown("### Tendencia de Fallos por Modelo")
        
        # Daily error rate by model
        df_perf['date'] = pd.to_datetime(df_perf['timestamp']).dt.date
        daily = df_perf.groupby(['date', 'model']).agg(
            total=('success', 'count'),
            failed=('success', lambda x: (x == 0).sum())
        ).reset_index()
        daily['error_rate'] = (daily['failed'] / daily['total'] * 100).round(1)
        
        # Top 5 models with most activity
        top_models = daily.groupby('model')['total'].sum().nlargest(5).index.tolist()
        daily_top = daily[daily['model'].isin(top_models)]
        
        fig = go.Figure()
        colors = ['#3B82F6', '#EC4899', '#F87171', '#22C55E', '#EAB308']
        for j, model in enumerate(top_models):
            m_data = daily_top[daily_top['model'] == model]
            if not m_data.empty:
                fig.add_trace(go.Scatter(
                    x=m_data['date'], y=m_data['error_rate'],
                    mode='lines+markers', name=model[:30],
                    line=dict(width=2, color=colors[j % len(colors)]),
                    hovertemplate='<b>%{x}</b><br>%{y:.1f}% error rate<extra></extra>'
                ))
        
        if fig.data:
            fig.update_layout(
                title="Error Rate Diario por Modelo (Top 5)",
                height=350,
                plot_bgcolor='#000000', paper_bgcolor='#000000',
                font_color='#FFFFFF',
                xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#333333', title='Error Rate (%)')
            )
            st.plotly_chart(fig, use_container_width=True, key="chart_sys_trend")
    
    st.divider()
    
    # ── Últimos errores ──
    if not df_perf.empty:
        st.markdown("### Últimos Fallos Registrados")
        recent_fails = df_perf[df_perf['success'] == False].head(15).copy()
        if not recent_fails.empty:
            recent_fails['time'] = recent_fails['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
            display = recent_fails[['time', 'model', 'tool_name', 'error_message']].rename(
                columns={'time': 'Timestamp', 'model': 'Modelo', 'tool_name': 'Tool', 'error_message': 'Error'}
            )
            st.dataframe(display, use_container_width=True, hide_index=True)
        else:
            st.success("✅ No se han registrado fallos")

def main():
    """Función principal del dashboard"""
    
        # Header: título centrado, logo + tabs lado a lado debajo
    import streamlit.components.v1 as components
    
    # Título centrado (full width)
    st.markdown('<div style="text-align:center;"><h1 style="display:inline-block; color:#F59E0B; margin:1rem 0 1.5rem 0; font-size:3.2rem; font-weight:800; letter-spacing:-0.03em;">Hermes Analytics Dashboard</h1></div>', unsafe_allow_html=True)
    
    # Fila: logo a la izquierda, tabs a la derecha
    col_logo, col_tabs = st.columns([3, 14])
    with col_logo:
        components.html("""<canvas id="c"></canvas>
<script>
const c=document.getElementById('c'),ctx=c.getContext('2d');
const GW=54,GH=54,CW=3,CH=3,DR=1.3;
c.width=GW*CW;c.height=GH*CH;
const PX=[[0,8],[1,8],[1,9],[2,7],[2,8],[2,9],[3,7],[3,8],[3,9],[4,6],[4,7],[4,8],[4,9],[5,6],[5,7],[5,8],[5,9],[6,6],[6,7],[6,8],[7,5],[7,6],[7,7],[7,10],[7,11],[8,5],[8,6],[8,7],[8,10],[8,11],[9,5],[9,6],[9,9],[9,10],[9,11],[10,4],[10,5],[10,9],[10,10],[11,4],[11,5],[11,8],[11,9],[11,10],[12,3],[12,4],[12,5],[12,7],[12,8],[12,9],[13,3],[13,4],[13,5],[13,6],[13,7],[13,8],[14,2],[14,3],[14,4],[14,5],[14,6],[14,7],[15,2],[15,3],[15,4],[15,5],[15,6],[15,7],[15,8],[15,9],[16,1],[16,2],[16,3],[16,4],[16,5],[16,6],[16,7],[16,8],[16,9],[17,1],[17,2],[17,3],[17,4],[17,5],[17,6],[17,7],[17,8],[17,15],[17,16],[17,17],[17,18],[17,19],[18,0],[18,1],[18,2],[18,3],[18,4],[18,5],[18,6],[18,7],[18,14],[18,15],[18,16],[18,17],[18,18],[18,19],[19,0],[19,1],[19,2],[19,3],[19,4],[19,5],[19,6],[19,13],[19,14],[19,15],[19,16],[19,17],[19,18],[19,19],[19,20],[20,0],[20,1],[20,2],[20,3],[20,4],[20,5],[20,6],[20,7],[20,12],[20,13],[20,14],[20,15],[20,16],[20,17],[20,18],[20,19],[20,20],[20,21],[20,31],[20,32],[20,33],[20,34],[20,35],[21,0],[21,1],[21,2],[21,3],[21,4],[21,5],[21,6],[21,7],[21,8],[21,12],[21,13],[21,14],[21,15],[21,16],[21,18],[21,19],[21,20],[21,21],[21,31],[21,32],[21,33],[21,34],[21,35],[21,36],[21,45],[21,46],[21,47],[21,48],[22,4],[22,5],[22,6],[22,7],[22,8],[22,9],[22,12],[22,13],[22,14],[22,15],[22,19],[22,20],[22,21],[22,25],[22,26],[22,30],[22,31],[22,32],[22,33],[22,34],[22,35],[22,36],[22,44],[22,45],[22,46],[22,47],[22,48],[22,49],[23,5],[23,6],[23,7],[23,8],[23,9],[23,12],[23,13],[23,14],[23,19],[23,20],[23,21],[23,22],[23,25],[23,26],[23,27],[23,30],[23,31],[23,35],[23,36],[23,37],[23,44],[23,45],[23,49],[23,50],[24,1],[24,2],[24,3],[24,12],[24,13],[24,14],[24,19],[24,20],[24,21],[24,22],[24,23],[24,26],[24,27],[24,28],[24,31],[24,35],[24,36],[24,37],[24,44],[24,50],[24,51],[25,0],[25,1],[25,2],[25,3],[25,4],[25,12],[25,13],[25,20],[25,21],[25,22],[25,23],[25,26],[25,27],[25,28],[25,36],[25,37],[25,38],[25,41],[26,0],[26,1],[26,2],[26,3],[26,4],[26,7],[26,8],[26,9],[26,16],[26,17],[26,20],[26,21],[26,22],[26,23],[26,24],[26,27],[26,28],[26,29],[26,33],[26,37],[26,38],[26,42],[26,46],[26,47],[26,48],[26,49],[26,53],[27,0],[27,1],[27,2],[27,3],[27,4],[27,7],[27,8],[27,9],[27,16],[27,17],[27,21],[27,22],[27,23],[27,24],[27,28],[27,29],[27,33],[27,37],[27,38],[27,39],[27,42],[27,43],[27,46],[27,47],[27,48],[27,49],[27,52],[28,0],[28,1],[28,2],[28,3],[28,4],[28,12],[28,13],[28,21],[28,22],[28,23],[28,24],[28,25],[28,28],[28,29],[28,30],[28,38],[28,39],[28,42],[28,43],[28,44],[28,51],[28,52],[29,1],[29,2],[29,3],[29,12],[29,13],[29,14],[29,22],[29,23],[29,24],[29,25],[29,26],[29,29],[29,30],[29,31],[29,35],[29,39],[29,43],[29,44],[29,50],[29,51],[30,5],[30,6],[30,7],[30,8],[30,9],[30,12],[30,13],[30,14],[30,19],[30,20],[30,23],[30,24],[30,25],[30,26],[30,29],[30,30],[30,31],[30,35],[30,36],[30,44],[30,45],[30,49],[30,50],[31,4],[31,5],[31,6],[31,7],[31,8],[31,9],[31,12],[31,13],[31,14],[31,15],[31,19],[31,20],[31,21],[31,24],[31,25],[31,26],[31,30],[31,31],[31,32],[31,33],[31,34],[31,35],[31,36],[31,44],[31,45],[31,46],[31,47],[31,48],[31,49],[32,0],[32,1],[32,2],[32,3],[32,4],[32,5],[32,6],[32,7],[32,8],[32,12],[32,13],[32,14],[32,15],[32,16],[32,18],[32,19],[32,20],[32,21],[32,31],[32,32],[32,33],[32,34],[32,35],[32,36],[32,45],[32,46],[32,47],[33,0],[33,1],[33,2],[33,3],[33,4],[33,5],[33,6],[33,7],[33,12],[33,13],[33,14],[33,15],[33,16],[33,17],[33,18],[33,19],[33,20],[33,21],[33,31],[33,32],[33,33],[33,34],[33,35],[34,0],[34,1],[34,2],[34,3],[34,4],[34,5],[34,6],[34,13],[34,14],[34,15],[34,16],[34,17],[34,18],[34,19],[34,20],[35,0],[35,1],[35,2],[35,3],[35,4],[35,5],[35,6],[35,7],[35,14],[35,15],[35,16],[35,17],[35,18],[35,19],[36,1],[36,2],[36,3],[36,4],[36,5],[36,6],[36,7],[36,8],[36,15],[36,16],[36,17],[36,18],[36,19],[37,1],[37,2],[37,3],[37,4],[37,5],[37,6],[37,7],[37,8],[37,9],[38,2],[38,3],[38,4],[38,5],[38,6],[38,7],[38,8],[38,9],[39,2],[39,3],[39,4],[39,5],[39,6],[39,7],[40,3],[40,4],[40,5],[40,6],[40,7],[40,8],[41,3],[41,4],[41,5],[41,7],[41,8],[41,9],[42,4],[42,5],[42,8],[42,9],[42,10],[43,4],[43,5],[43,9],[43,10],[44,5],[44,6],[44,9],[44,10],[44,11],[45,5],[45,6],[45,7],[45,10],[45,11],[46,5],[46,6],[46,7],[46,10],[46,11],[47,6],[47,7],[47,8],[48,6],[48,7],[48,8],[48,9],[49,6],[49,7],[49,8],[49,9],[50,7],[50,8],[50,9],[51,7],[51,8],[51,9],[52,8],[52,9],[53,8]];;
const PS=[[0,255,234,0],[.2,201,176,0],[.4,204,150,0],[.6,210,130,64],[.8,154,80,32],[1,255,234,0]];
function pa(t){t=((t%1)+1)%1;for(let i=0;i<PS.length-1;i++){const[t0,r0,g0,b0]=PS[i];const[t1,r1,g1,b1]=PS[i+1];if(t>=t0&&t<=t1){const f=(t-t0)/(t1-t0);return[Math.round(r0+(r1-r0)*f),Math.round(g0+(g1-g0)*f),Math.round(b0+(b1-b0)*f)]}}return[255,234,0]}
const FC=10,SS=GH/FC;
function dc(gy,f){return pa(((gy+f*SS)/GH)%1)}
function dt(gx,gy,f){const cx=(gx+.5)*CW,cy=(gy+.5)*CH;[r,g,b]=dc(gy,f);const co=`rgb(${r},${g},${b})`;const bl=ctx.createRadialGradient(cx,cy,0,cx,cy,DR*3.5);bl.addColorStop(0,`rgba(${r},${g},${b},.7)`);bl.addColorStop(.38,`rgba(${r},${g},${b},.18)`);bl.addColorStop(1,`rgba(${r},${g},${b},0)`);ctx.beginPath();ctx.arc(cx,cy,DR*3.5,0,Math.PI*2);ctx.fillStyle=bl;ctx.fill();const co2=ctx.createRadialGradient(cx-DR*.4,cy-DR*.4,0,cx,cy,DR);co2.addColorStop(0,'rgba(255,255,255,.88)');co2.addColorStop(.3,co);co2.addColorStop(1,co);ctx.beginPath();ctx.arc(cx,cy,DR,0,Math.PI*2);ctx.fillStyle=co2;ctx.fill()}
const bg=document.createElement('canvas');bg.width=c.width;bg.height=c.height;const b2=bg.getContext('2d');b2.fillStyle='#000';b2.fillRect(0,0,bg.width,bg.height);b2.fillStyle='rgba(22,5,0,.4)';for(let gx=0;gx<GW;gx++)for(let gy=0;gy<GH;gy++){b2.beginPath();b2.arc((gx+.5)*CW,(gy+.5)*CH,.45,0,Math.PI*2);b2.fill()}
let f=0,lt=0;
function rd(ts){requestAnimationFrame(rd);if(ts-lt<125)return;lt=ts;ctx.drawImage(bg,0,0);for(const[x,y]of PX)dt(x,y,f);f=(f+1)%FC}
requestAnimationFrame(rd);
</script>
""", height=280)
    with col_tabs:
        st.markdown('<p style="color:#888; margin:0.2rem 0 0.3rem 0; font-size:0.9rem;">v5.4.1 &bull; OpenRouter &bull; Hermes Dashboard</p>', unsafe_allow_html=True)
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 Overview",
            "🛠️ Tools Analytics",
            "📊 Token Analytics",
            "⚠️ Errors & Performance",
            "⚡ System Performance"
        ])
    
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div class="custom-card sidebar-card">
            <h3 style="margin: 0 0 0.5rem 0;">📈 Estado del Sistema</h3>
        </div>
        """, unsafe_allow_html=True)
        
        db_path = Path(__file__).parent / "dashboard.db"
        if db_path.exists():
            db_size = db_path.stat().st_size
            st.markdown(f'<div class="custom-card" style="border-left: 4px solid #3B82F6 !important;" style="padding:0.6rem 1rem;"><div class="card-title">Base de Datos</div><div class="card-value card-value-blue" style="font-size:1.2rem;">{db_size:,} bytes</div></div>', unsafe_allow_html=True)
        else:
            st.error("❌ Base de datos no encontrada")
        
        if st.button("🔄 Ejecutar Collector Avanzado", use_container_width=True, type="primary"):
            st.info("Ejecutando collector... Esto puede tardar unos minutos.")
            st.code("python collector_advanced.py", language="bash")
            st.success("Collector ejecutado. Actualiza la página para ver datos nuevos.")
        
        st.divider()
        
        st.markdown("""
        <div class="custom-card sidebar-card">
            <h4 style="margin: 0 0 0.5rem 0;">💡 Uso Rápido</h4>
            <ul style="margin: 0; padding-left: 1.2rem; color: #AAAAAA; font-size: 0.9rem;">
                <li><strong>📈 Overview:</strong> Visión general y tokens por modelo</li>
                <li><strong>🛠️ Tools Analytics:</strong> Uso de herramientas (requires collector)</li>
                <li><strong>💰 Cost Analysis:</strong> Costes reales vs estimados</li>
                <li><strong>⚠️ Errors & Performance:</strong> Errores y métricas</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    # Cargar datos
    with st.spinner("Cargando datos..."):
        df_sessions = load_sessions_data()
        df_daily = load_daily_stats()
        df_models = load_model_stats()
        df_tools = load_tool_usage_data()
        df_errors = load_errors_data()
    
    # Load system performance data
    df_perf = load_system_performance_data() if not df_tools.empty else pd.DataFrame()
    
    
    # Renderizar pestañas
    # Load real OpenRouter spend
    real_spend = load_real_spend()
    
    with tab1:
        render_overview_tab(df_sessions, df_daily, df_models, real_spend)
    
    with tab2:
        render_tools_tab(df_tools, df_sessions)
    
    with tab3:
        render_tokens_tab(df_sessions)
    
    with tab4:
        render_errors_tab(df_errors, df_sessions)
    
    with tab5:
        render_system_performance_tab(df_perf, df_sessions)
    
    # Footer
    st.divider()
    st.markdown("""
    <div style="text-align: center; color: #666666; font-size: 0.9rem; margin-top: 2rem;">
        <p>
            Hermes Analytics Dashboard v5.4.1 • 
            Diseño Trade Republic • 
            Análisis avanzado de tokens, tools, costes y errores
        </p>
        <p style="font-size: 0.8rem;">
            ⚠️ Los costes mostrados son estimaciones. Los costes reales de OpenRouter pueden variar.
            Este dashboard procesa datos crudos de sesiones, tools, logs de errores y requests de API.
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
