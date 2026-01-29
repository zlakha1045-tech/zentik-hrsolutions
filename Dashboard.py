import streamlit as st
from supabase import create_client
import pandas as pd
from styles import load_css, hero_section

# --- SETUP ---
st.set_page_config(page_title="Zentik HR", layout="wide", page_icon="🚀")
load_css()

# Connect to DB
try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except Exception as e:
    st.error(f"Database Connection Failed: {e}")
    st.stop()

# --- HERO SECTION ---
hero_section("assets/login_hero.jpg", "Zentik Talent Pipeline", "Real-time recruitment overview.")

# --- QUICK ACTIONS ---
# FIX: Updated page names to match the actual files we created
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("➕ Upload Resumes", use_container_width=True, type="primary"):
        st.switch_page("pages/5_📂_Upload_Center.py")
with c2:
    if st.button("💼 Manage Jobs", use_container_width=True):
        st.switch_page("pages/3_💼_Job_Manager.py")
with c3:
    if st.button("📊 Analysis Dashboard", use_container_width=True):
        st.switch_page("pages/4_📊_Analysis.py")

st.divider()

# --- FETCH DATA ---
try:
    # Explicitly asking for the foreign key relationship
    cands = supabase.table("candidates").select("*, jobs(title)").order("created_at", desc=True).execute().data
    
    if not cands:
        st.info("No candidates found yet. Go to 'Upload Center' to start.")
        st.stop()

    df = pd.DataFrame(cands)
    
    # Safe Extraction of Job Titles
    df['job_title'] = df['jobs'].apply(lambda x: x.get('title') if x else "Unassigned")
    # Handle missing scores/status
    df['match_score'] = pd.to_numeric(df['match_score'], errors='coerce').fillna(0)
    df['status'] = df['status'].fillna("New")

except Exception as e:
    st.error(f"Error fetching data: {e}")
    st.stop()

# --- METRICS ROW ---
total = len(df)
avg_score = df['match_score'].mean()
# Count pending approvals
pending_approval = len(df[df['status'] == 'Pending Final Approval'])
# Count new candidates
needs_review = len(df[df['status'].isin(['New', 'AI Analysis Complete', 'AI Analysis in Progress'])])

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Applicants", total)
m2.metric("Avg Quality Score", f"{avg_score:.1f}%")
m3.metric("Pending Approval", pending_approval, delta_color="off")
m4.metric("Needs Review", needs_review, delta="Urgent" if needs_review > 0 else "off")

st.divider()

# --- RECENT ACTIVITY FEED ---
st.subheader("🕒 Recent Applications")

roles = ["All Roles"] + sorted(df['job_title'].unique().tolist())
selected_role = st.selectbox("Filter by Role", roles)

filtered_df = df if selected_role == "All Roles" else df[df['job_title'] == selected_role]

for index, row in filtered_df.head(10).iterrows():  # Show only top 10 recent
    # Determine Status Color
    score = row['match_score']
    status = row['status']
    
    # Create a nice container for each candidate
    with st.container(border=True):
        cols = st.columns([4, 1, 2])
        
        with cols[0]:
            st.subheader(row['name'])
            st.caption(f"Role: {row['job_title']} | Status: {status}")
            summary = row.get('summary', '')
            if summary:
                st.write(f"_{summary[:120]}..._")
            
        with cols[1]:
            # Color-coded score
            color = "green" if score > 80 else "orange" if score > 50 else "red"
            st.markdown(f"## :{color}[{int(score)}%]")
            st.caption("Match Score")
            
        with cols[2]:
            st.markdown("<br>", unsafe_allow_html=True) # spacer
            c_btn1, c_btn2 = st.columns(2)
            with c_btn1:
                if row.get('resume_url'):
                    st.link_button("📄 Resume", row['resume_url'])
            with c_btn2:
                # FIX: "Analyze" button now works because we pass the right page name
                if st.button("🔍 Analyze", key=f"btn_{row['id']}"):
                    st.switch_page("pages/4_📊_Analysis.py")