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
    st.sidebar.caption(f"Last run: {latest_run['run_time']}")
    st.sidebar.caption(f"{latest_run['sessions_added']} new sessions")
    st.sidebar.caption(f"Status: {latest_run['status']}")
else:
    st.sidebar.write("No collector runs")

# === MAIN DASHBOARD ===
col1, col2, col3, col4 = st.columns(4)

with col1:
    session_count = len(sessions_df)
    st.metric("Total Sessions", session_count)

with col2:
    estimated_cost_usd = sessions_df["estimated_cost_usd"].fillna(0).sum()
    st.metric("Total Cost", f"${estimated_cost_usd:.2f}")

with col3:
    total_tokens = sessions_df["input_tokens"].fillna(0).sum() + sessions_df["output_tokens"].fillna(0).sum()
    st.metric("Total Tokens", f"{total_tokens:,}")

with col4:
    if not daily_df.empty:
        today_cost = daily_df.iloc[0]["estimated_cost_usd"]
        st.metric("Today's Cost", f"${today_cost:.2f}")
    else:
        st.metric("Today's Cost", "$0.00")

st.divider()
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

st.subheader("📋 Recent Sessions")

if not sessions_df.empty:
    recent = sessions_df.head(20)[["started_datetime", "model", "input_tokens", "output_tokens", "estimated_cost_usd"]]
    recent.columns = ["Time", "Model", "Input Tokens", "Output Tokens", "Cost (USD)"]
    st.dataframe(recent, use_container_width=True)

st.divider()
st.caption(f"Dashboard data from {DB_PATH} | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
/bin/bash: line 5: C:/Users/Cristian Valverde/AppData/Local/hermes/cache/terminal/hermes-snap-685077eb553c.sh: No such file or directory
/bin/bash: line 6: C:/Users/Cristian Valverde/AppData/Local/hermes/cache/terminal/hermes-cwd-685077eb553c.txt: No such file or directory
