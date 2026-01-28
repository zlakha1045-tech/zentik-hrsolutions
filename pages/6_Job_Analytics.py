import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- SETUP ---
st.set_page_config(page_title="Job Performance Analytics", layout="wide")

try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    st.error("Missing Supabase Secrets.")
    st.stop()

st.title("📊 Recruitment Analytics & Insights")
st.markdown("Deep dive into job performance, candidate quality pools, and hiring velocity.")

# --- 1. SIDEBAR: SCOPE SELECTION ---
st.sidebar.header("Analysis Scope")

# Fetch Jobs
jobs_resp = supabase.table("jobs").select("id, title").execute()
jobs_dict = {j['title']: j['id'] for j in jobs_resp.data}
selected_job_title = st.sidebar.selectbox("Select Role to Analyze", ["All Roles"] + list(jobs_dict.keys()))

# Date Filter
time_range = st.sidebar.selectbox("Time Range", ["Last 30 Days", "Last 90 Days", "All Time"])

# --- 2. DATA FETCHING ---
# Build Query based on selection
query = supabase.table("candidates").select("id, created_at, match_score, status, job_id, name, email")

if selected_job_title != "All Roles":
    job_id = jobs_dict[selected_job_title]
    query = query.eq("job_id", job_id)

data = query.execute().data

if not data:
    st.warning("No data found for this selection.")
    st.stop()

df = pd.DataFrame(data)
df['created_at'] = pd.to_datetime(df['created_at'])
df['date'] = df['created_at'].dt.date

# Filter by Time Range
if time_range == "Last 30 Days":
    cutoff = datetime.now() - timedelta(days=30)
    df = df[df['created_at'] >= cutoff]
elif time_range == "Last 90 Days":
    cutoff = datetime.now() - timedelta(days=90)
    df = df[df['created_at'] >= cutoff]

# --- 3. TOP LEVEL METRICS ---
st.divider()
m1, m2, m3, m4 = st.columns(4)

total_apps = len(df)
avg_score = df['match_score'].mean()
# Count "Qualified" candidates (Score > 70)
qualified_count = len(df[df['match_score'] >= 70])
qualified_rate = (qualified_count / total_apps * 100) if total_apps > 0 else 0
# Count Hired/Placed
hired_count = len(df[df['status'].isin(['Hired', 'Placed', 'Pending Hire'])])

with m1:
    st.metric("Total Applicants", total_apps)
with m2:
    st.metric("Avg. Match Quality", f"{avg_score:.1f}%", delta_color="normal")
with m3:
    st.metric("Qualified Leads (>70%)", f"{qualified_count} ({qualified_rate:.0f}%)")
with m4:
    st.metric("Hires / Pending", hired_count)

st.divider()

# --- 4. CHARTS & VISUALIZATIONS ---

# ROW 1: TIME SERIES & FUNNEL
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📈 Application Volume Over Time")
    # Group by Date
    daily_counts = df.groupby('date').size().reset_index(name='Applicants')
    
    if not daily_counts.empty:
        fig_line = px.line(daily_counts, x='date', y='Applicants', markers=True, 
                           title="Daily Application Trend", template="plotly_dark")
        fig_line.update_layout(xaxis_title="Date", yaxis_title="Number of Applicants")
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Not enough data for trend analysis.")

with col_right:
    st.subheader("🔻 Recruitment Funnel")
    # Status Distribution
    status_counts = df['status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    
    # Custom colors for status
    color_map = {
        'New': '#3498db', 'Rejected': '#e74c3c', 
        'Hired': '#2ecc71', 'Pending Hire': '#f1c40f'
    }
    
    fig_pie = px.pie(status_counts, names='Status', values='Count', hole=0.4,
                     color='Status', color_discrete_map=color_map)
    st.plotly_chart(fig_pie, use_container_width=True)

# ROW 2: QUALITY ANALYSIS
st.subheader("🎯 Candidate Quality Pool")
st.caption("How good is the talent pool? This histograms shows the distribution of AI Match Scores.")

if not df.empty:
    # Color bins based on score
    fig_hist = px.histogram(df, x="match_score", nbins=20, 
                            title="Score Distribution (0-100%)",
                            labels={'match_score': 'AI Match Score'},
                            color_discrete_sequence=['#9b59b6'])
    
    fig_hist.update_layout(bargap=0.1)
    st.plotly_chart(fig_hist, use_container_width=True)

# ROW 3: RECENT ACTIVITY TABLE
with st.expander("📄 View Raw Data (Recent Applicants)"):
    st.dataframe(
        df[['name', 'email', 'match_score', 'status', 'created_at']]
        .sort_values(by='created_at', ascending=False)
        .style.highlight_max(axis=0, color='darkgreen', subset=['match_score']),
        use_container_width=True
    )