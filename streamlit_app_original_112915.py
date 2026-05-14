#!/usr/bin/env python3
"""
Hermes Dashboard — cost & usage monitoring for Hermes Agent.
"""
import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

st.set_page_config(
    page_title="Hermes Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Config
DB_PATH = os.path.join(os.path.dirname(__file__), "dashboard.db")

# Title
st.title("📊 Hermes Agent Dashboard")
st.caption("Cost & usage monitoring for Hermes Agent + OpenRouter")

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
    
    # Calculate remaining credits (column doesn't exist in DB)
    if not account_df.empty and "total_credits" in account_df.columns and "total_usage" in account_df.columns:
        account_df["remaining"] = account_df["total_credits"] - account_df["total_usage"]
    
    return {
        "sessions": sessions_df,
        "daily": daily_df,
        "models": model_df,
        "account": account_df,
        "runs": runs_df
    }

# Load data
try:
    data = load_data()
    sessions_df = data["sessions"]
    daily_df = data["daily"]
    model_df = data["models"]
    account_df = data["account"]
    runs_df = data["runs"]
    
except Exception as e:
    st.error(f"Could not load data: {e}")
    st.stop()

# === SIDEBAR: Filters & KPIs ===
st.sidebar.header("📅 Filter")
if not sessions_df.empty:
    min_date = sessions_df["started_datetime"].min()
    max_date = sessions_df["started_datetime"].max()
    date_range = st.sidebar.date_input(
        "Date range",
        [min_date.date() if hasattr(min_date, 'date') else datetime.now().date(),
         max_date.date() if hasattr(max_date, 'date') else datetime.now().date()],
        min_value=min_date.date() if hasattr(min_date, 'date') else datetime.now().date(),
        max_value=max_date.date() if hasattr(max_date, 'date') else datetime.now().date()
    )

    selected_models = st.sidebar.multiselect(
        "Models",
        options=sessions_df["model"].unique(),
        default=sessions_df["model"].unique()
    )
else:
    date_range = [datetime.now().date() - timedelta(days=7), datetime.now().date()]
    selected_models = []

# Credits KPI
st.sidebar.divider()
st.sidebar.header("💰 Credits")
if not account_df.empty:
    # Ensure remaining column exists
    if "remaining" not in account_df.columns:
        if "total_credits" in account_df.columns and "total_usage" in account_df.columns:
            account_df["remaining"] = account_df["total_credits"] - account_df["total_usage"]
        else:
            st.warning("Cannot calculate remaining credits: missing columns")
    latest = account_df.iloc[0]
    st.sidebar.metric(
        "Remaining",
        f"${latest['remaining']:.2f}",
        delta=f"-${latest['total_usage']:.2f} spent"
    )
    st.sidebar.caption(f"Total: ${latest['total_credits']:.2f} | Used: ${latest['total_usage']:.2f}")
else:
    st.sidebar.write("No credit data")

# Collector status
st.sidebar.divider()
st.sidebar.header("🔄 Collector")
if not runs_df.empty:
    latest_run = runs_df.iloc[0]
    st.sidebar.caption(f"Last run: {pd.to_datetime(latest_run['started_at'], unit='s').strftime('%Y-%m-%d %H:%M')}")
    st.sidebar.caption(f"{latest_run['sessions_added']} new sessions")
    st.sidebar.caption(f"Status: {latest_run['status']}")
else:
    st.sidebar.write("No collector runs")

# === MAIN DASHBOARD ===
col1, col2, col3, col4 = st.columns(4)

with col1:
    session_count = len(sessions_df)
    st.metric("Total Sessions", session_count, help="Número total de sesiones de Hermes registradas en la base de datos.")

with col2:
    estimated_cost_usd = sessions_df["estimated_cost_usd"].fillna(0).sum()
    st.metric("Total Cost", f"${estimated_cost_usd:.2f}"), help="Coste total estimado en USD. NOTA: Puede subestimar el coste real de OpenRouter 2-5×. Consulte créditos restantes en la barra lateral."

with col3:
    total_tokens = sessions_df["input_tokens"].fillna(0).sum() + sessions_df["output_tokens"].fillna(0).sum()
    st.metric("Total Tokens", f"{total_tokens:,}"), help="Suma de tokens de entrada y salida de todas las sesiones."

with col4:
    if not daily_df.empty:
        today_cost = daily_df.iloc[0]["estimated_cost_usd"]
        st.metric("Today's Cost", f"${today_cost:.2f}", help="Coste estimado para la fecha actual.")
    else:
        st.metric("Today's Cost", "$0.00", help="Coste estimado para la fecha actual.")

st.divider()

# Advertencia sobre exactitud de costes
st.warning("⚠️ El coste estimado puede subestimar el coste real de OpenRouter 2-5× debido a caché y tarifas actualizadas. Use los créditos restantes en la barra lateral como referencia precisa.", icon="⚠️")
st.subheader("📈 Cost Over Time")

if not daily_df.empty:
    fig = px.bar(daily_df, x="date", y="estimated_cost_usd",
                 title="Daily Cost",
                 labels={"date": "Date", "estimated_cost_usd": "Cost (USD)"})
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No daily stats yet. Collector runs hourly.")

st.subheader("🧠 Model Breakdown")

if not model_df.empty:
    col1, col2 = st.columns(2)
    with col1:
        fig = px.pie(model_df, values="estimated_cost_usd", names="model",
                     title="Cost by Model")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(model_df.head(10), x="model", y="total_tokens",
                     title="Tokens by Model (Top 10)")
        st.plotly_chart(fig, use_container_width=True)



    # Model efficiency (cost per million tokens)
    st.subheader("💰 Cost per Million Tokens")
    # Calculate cost per 1M tokens
    efficiency_df = model_df.copy()
    efficiency_df['cost_per_1M_input'] = efficiency_df['input_tokens'].apply(lambda x: (efficiency_df['estimated_cost_usd'] / (efficiency_df['input_tokens'] / 1_000_000)) if x > 0 else 0)
    efficiency_df['cost_per_1M_output'] = efficiency_df['output_tokens'].apply(lambda x: (efficiency_df['estimated_cost_usd'] / (efficiency_df['output_tokens'] / 1_000_000)) if x > 0 else 0)
    efficiency_df['cost_per_1M_total'] = efficiency_df['total_tokens'].apply(lambda x: (efficiency_df['estimated_cost_usd'] / (efficiency_df['total_tokens'] / 1_000_000)) if x > 0 else 0)
    
    # Select relevant columns
    eff_display = efficiency_df[['model', 'estimated_cost_usd', 'total_tokens', 'cost_per_1M_total']].copy()
    eff_display.columns = ['Model', 'Cost (USD)', 'Total Tokens', 'Cost per 1M tokens']
    eff_display = eff_display.sort_values('Cost per 1M tokens', ascending=True)
    
    st.dataframe(eff_display, use_container_width=True)
    st.caption("Nota: El coste por millón de tokens se calcula usando el coste estimado, que puede subestimar el coste real.")

# Exportar datos
if not sessions_df.empty:
    csv = sessions_df.to_csv(index=False)
    st.download_button(
        label="📥 Exportar sesiones a CSV",
        data=csv,
        file_name=f"hermes_sessions_{datetime.now().strftime("%Y%m%d")}.csv",
        mime="text/csv"
    )
st.subheader("📋 Recent Sessions")

if not sessions_df.empty:
    recent = sessions_df.head(20)[["started_datetime", "model", "input_tokens", "output_tokens", "estimated_cost_usd"]]
    recent.columns = ["Time", "Model", "Input Tokens", "Output Tokens", "Cost (USD)"]
    st.dataframe(recent, use_container_width=True)

st.divider()
st.caption(f"Dashboard data from {DB_PATH} | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
