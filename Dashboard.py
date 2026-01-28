import streamlit as st
from supabase import create_client
import pandas as pd

# --- SETUP ---
st.set_page_config(page_title="Zentik HR", layout="wide", page_icon="🚀")

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

# --- FETCH DATA ---
try:
    # Explicitly asking for the foreign key relationship
    cands = supabase.table("candidates").select("*, jobs(title)").order("created_at", desc=True).execute().data
    
    if not cands:
        st.info("No data found. Go to 'Upload Center' to start.")
        st.stop()

    df = pd.DataFrame(cands)
    
    # Safe Extraction
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

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Applicants", total)
m2.metric("Avg Quality Score", f"{avg_score:.1f}%")
m3.metric("Hired / Pending", hired)
m4.metric("Need Review", pending)

st.divider()

# --- RECENT ACTIVITY FEED ---
st.subheader("🕒 Recent Applications")

roles = ["All Roles"] + sorted(df['job_title'].unique().tolist())
selected_role = st.selectbox("Filter by Role", roles)

filtered_df = df if selected_role == "All Roles" else df[df['job_title'] == selected_role]

for index, row in filtered_df.iterrows():
    # Determine Status Color
    score = row['match_score']
    status = row['status']
    
    # Create a nice container for each candidate
    with st.container(border=True):
        cols = st.columns([4, 1, 2])
        
        with cols[0]:
            st.subheader(row['name'])
            st.caption(f"Role: {row['job_title']} | Status: {status}")
            st.write(f"_{row.get('summary', '')[:120]}..._")
            
        with cols[1]:
            # Color-coded score
            color = "green" if score > 80 else "orange" if score > 50 else "red"
            st.markdown(f"## :{color}[{int(score)}%]")
            st.caption("Match Score")
            
        with cols[2]:
            st.markdown("<br>", unsafe_allow_html=True) # spacer
            c_btn1, c_btn2 = st.columns(2)
            with c_btn1:
                st.link_button("📄 Resume", row['resume_url'])
            with c_btn2:
                if st.button("🔍 Analyze", key=f"btn_{row['id']}"):
                    st.switch_page("pages/Candidate_Analysis.py")