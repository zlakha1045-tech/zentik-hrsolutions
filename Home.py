import streamlit as st
from supabase import create_client
import pandas as pd

# --- SETUP ---
st.set_page_config(page_title="Zentik HR", layout="wide", page_icon="🚀")

# --- CUSTOM STYLING ---
st.markdown("""
<style>
    .metric-card {
        background-color: #1a1c24;
        border: 1px solid #2b303b;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
        color: #4da6ff;
    }
    .metric-label {
        font-size: 14px;
        color: #a0a0a0;
        margin-top: 5px;
    }
    .candidate-card {
        background-color: #0e1117;
        border-left: 5px solid #4da6ff;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Connect to DB
try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except Exception as e:
    st.error(f"Database Connection Failed: {e}")
    st.stop()

# --- HERO SECTION ---
st.title("🚀 Talent Pipeline Dashboard")
st.markdown("Welcome to **Zentik HR**. Here is your real-time overview of recruitment activity.")

# --- QUICK ACTIONS ---
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("➕ Upload New Resume", use_container_width=True, type="primary"):
        st.switch_page("pages/Upload_Center.py")
with c2:
    if st.button("📊 View Analytics", use_container_width=True):
        st.switch_page("pages/Job_Analytics.py")
with c3:
    if st.button("🔍 Analyze Candidates", use_container_width=True):
        st.switch_page("pages/Candidate_Analysis.py")

st.divider()

# --- FETCH DATA (New Logic) ---
# We fetch candidates and join with jobs to get the job title
try:
    # Fetch Candidates
    cands = supabase.table("candidates").select("*, jobs(title)").order("created_at", desc=True).execute().data
    
    if not cands:
        st.info("No data found. Go to 'Upload Center' to start.")
        st.stop()

    df = pd.DataFrame(cands)
    
    # Extract Job Title safely
    df['job_title'] = df['jobs'].apply(lambda x: x.get('title') if x else "Unassigned")
    df['match_score'] = df['match_score'].fillna(0)
    df['status'] = df['status'].fillna("New")

except Exception as e:
    st.error(f"Error fetching data: {e}")
    st.stop()

# --- METRICS ROW ---
total = len(df)
avg_score = df['match_score'].mean()
hired = len(df[df['status'].isin(['Hired', 'Pending Hire', 'Placed'])])
pending = len(df[df['status'] == 'New'])

col1, col2, col3, col4 = st.columns(4)
col1.markdown(f'<div class="metric-card"><div class="metric-value">{total}</div><div class="metric-label">Total Applicants</div></div>', unsafe_allow_html=True)
col2.markdown(f'<div class="metric-card"><div class="metric-value">{avg_score:.1f}%</div><div class="metric-label">Avg Quality Score</div></div>', unsafe_allow_html=True)
col3.markdown(f'<div class="metric-card"><div class="metric-value">{hired}</div><div class="metric-label">Hired / Pending</div></div>', unsafe_allow_html=True)
col4.markdown(f'<div class="metric-card"><div class="metric-value">{pending}</div><div class="metric-label">Need Review</div></div>', unsafe_allow_html=True)

st.divider()

# --- RECENT ACTIVITY FEED ---
st.subheader("🕒 Recent Applications")

# Filter by Job Role
roles = ["All Roles"] + sorted(df['job_title'].unique().tolist())
selected_role = st.selectbox("Filter by Role", roles)

filtered_df = df if selected_role == "All Roles" else df[df['job_title'] == selected_role]

for index, row in filtered_df.iterrows():
    # Dynamic Color for Border
    score = row['match_score']
    border_color = "#2ecc71" if score > 80 else "#f1c40f" if score > 50 else "#e74c3c"
    
    with st.container():
        # HTML Card Layout
        st.markdown(f"""
        <div style="
            background-color: #1a1c24; 
            border-left: 5px solid {border_color}; 
            padding: 15px; 
            border-radius: 8px; 
            margin-bottom: 15px; 
            display: flex; 
            justify-content: space-between; 
            align-items: center;">
            
            <div style="flex: 3;">
                <h3 style="margin: 0; color: white;">{row['name']}</h3>
                <p style="margin: 5px 0; color: #a0a0a0;">
                    {row['job_title']} | <span style="color: #4da6ff;">{row['status']}</span> | {str(row['created_at'])[:10]}
                </p>
                <p style="font-size: 0.9em; color: #888;">{row.get('summary', '')[:120]}...</p>
            </div>
            
            <div style="flex: 1; text-align: center;">
                <h2 style="margin: 0; color: {border_color};">{int(score)}%</h2>
                <small style="color: #888;">Match Score</small>
            </div>
            
        </div>
        """, unsafe_allow_html=True)
        
        # Action Buttons (Hidden inside expander to keep clean)
        with st.expander("👉 View Actions"):
            ac1, ac2 = st.columns([1, 4])
            with ac1:
                st.link_button("📄 Resume", row['resume_url'])
            with ac2:
                if st.button(f"🔍 Analyze {row['name'].split()[0]}", key=f"btn_{row['id']}"):
                    # NOTE: To jump to specific candidate, we normally use query params
                    # But for now, we just redirect to the page
                    st.switch_page("pages/Candidate_Analysis.py")