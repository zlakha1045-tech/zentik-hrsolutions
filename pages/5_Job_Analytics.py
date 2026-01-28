import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, timezone

# --- SETUP ---
st.set_page_config(page_title="Job Performance Analytics", layout="wide")

try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    st.error("Missing Supabase Secrets.")
    st.stop()

st.title("📊 Recruitment Analytics & Insights")

# --- 1. SIDEBAR ---
st.sidebar.header("Analysis Scope")
jobs_resp = supabase.table("jobs").select("id, title").execute()
jobs_dict = {j['title']: j['id'] for j in jobs_resp.data}
selected_job_title = st.sidebar.selectbox("Select Role", ["All Roles"] + list(jobs_dict.keys()))
time_range = st.sidebar.selectbox("Time Range", ["Last 30 Days", "Last 90 Days", "All Time"])

# --- 2. DATA FETCHING ---
query = supabase.table("candidates").select("id, created_at, match_score, status, job_id, name, email")

if selected_job_title != "All Roles":
    job_id = jobs_dict[selected_job_title]
    query = query.eq("job_id", job_id)

data = query.execute().data

if not data:
    st.warning("No data found for this selection.")
    st.stop()

df = pd.DataFrame(data)

# --- FIX: ROBUST DATE CONVERSION ---
# Convert to datetime with UTC to handle Supabase timestamps correctly
df['created_at'] = pd.to_datetime(df['created_at'], utc=True)
df['date'] = df['created_at'].dt.date

# Filter by Time Range using timezone-aware current time
now = datetime.now(timezone.utc)

if time_range == "Last 30 Days":
    cutoff = now - timedelta(days=30)
    df = df[df['created_at'] >= cutoff]
elif time_range == "Last 90 Days":
    cutoff = now - timedelta(days=90)
    df = df[df['created_at'] >= cutoff]

# --- 3. METRICS ---
st.divider()
total_apps = len(df)
avg_score = df['match_score'].mean()
qualified_count = len(df[df['match_score'] >= 70])
hired_count = len(df[df['status'].isin(['Hired', 'Placed', 'Pending Hire'])])

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Applicants", total_apps)
m2.metric("Avg Match Score", f"{avg_score:.1f}%")
m3.metric("Qualified (>70%)", qualified_count)
m4.metric("Hires / Pending", hired_count)

st.divider()

# --- 4. CHARTS ---
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📈 Application Trend")
    # Group by Date
    daily_counts = df.groupby('date').size().reset_index(name='Applicants')
    
    if not daily_counts.empty:
        # USE BAR CHART INSTEAD OF LINE
        fig = px.bar(
            daily_counts, 
            x='date', 
            y='Applicants', 
            title="Daily Volume",
            template="plotly_dark",
            color_discrete_sequence=['#4da6ff']
        )
        # Force the Y-axis to show integers (0, 1, 2...) instead of decimals
        fig.update_yaxes(dtick=1) 
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data for trend analysis.")

with col_right:
    st.subheader("🔻 Funnel Status")
    status_counts = df['status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    fig_pie = px.pie(status_counts, names='Status', values='Count', hole=0.4)
    st.plotly_chart(fig_pie, use_container_width=True)