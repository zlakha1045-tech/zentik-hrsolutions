import streamlit as st
from supabase import create_client
import pandas as pd
from styles import load_css, hero_section

# 1. Page Configuration
st.set_page_config(page_title="Zentik HR", layout="wide", page_icon="🚀")
load_css()

# 2. Connect to Database
try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except Exception as e:
    st.error(f"Database Connection Failed: {e}")
    st.stop()

# 3. Dashboard Hero Section
hero_section(
    "assets/dashboard_hero.jpg", 
    "Talent Pipeline", 
    "Real-time AI analysis of incoming applications"
)

# 4. Fetch Data
try:
    # Added manual_score and recruiter_notes to the select query
    apps = supabase.table("applications").select(
        "match_score, manual_score, ai_summary, recruiter_notes, status, created_at, candidates(name, email, resume_url), jobs(title)"
    ).order("match_score", desc=True).execute()
    
    df = pd.DataFrame(apps.data)
except Exception as e:
    st.error(f"Error fetching data: {e}")
    st.stop()

if not df.empty:
    # Clean Data
    df['name'] = df['candidates'].apply(lambda x: x.get('name') if x else "Unknown")
    df['email'] = df['candidates'].apply(lambda x: x.get('email') if x else "Unknown")
    df['resume_url'] = df['candidates'].apply(lambda x: x.get('resume_url') if x else "#")
    df['job_title'] = df['jobs'].apply(lambda x: x.get('title') if x else "Unknown")
    df['match_score'] = df['match_score'].fillna(0)

    # Filter Logic
    st.markdown("### Filter by Role")
    roles = ["All Roles"] + sorted(df['job_title'].unique().tolist())
    selected_role = st.selectbox("Select a role to filter the dashboard", roles, label_visibility="collapsed")
    
    filtered_df = df if selected_role == "All Roles" else df[df['job_title'] == selected_role]

    # 5. Metrics Row (HTML Cards)
    total_cands = len(filtered_df)
    top_talent = len(filtered_df[filtered_df['match_score'] >= 80])
    avg_score = int(filtered_df['match_score'].mean()) if not filtered_df.empty else 0
    pending_review = len(filtered_df[filtered_df['match_score'] < 50])
    
    st.markdown(f"""
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px;">
        <div class="metric-card">
            <div class="metric-value">{total_cands}</div>
            <div class="metric-label">Total Candidates</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{top_talent}</div>
            <div class="metric-label">Top Talent (>80%)</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{pending_review}</div>
            <div class="metric-label">Pending Review</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{avg_score}%</div>
            <div class="metric-label">Avg Match Score</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 6. Candidate Cards Loop
    for index, row in filtered_df.iterrows():
        score = int(row['match_score'])
        score_class = "score-green" if score >= 80 else "score-orange" if score >= 50 else "score-red"
        
        # Check if score was manually overridden
        is_manual = row.get('manual_score') is not None
        badge_suffix = " 👤" if is_manual else ""
        
        with st.container():
            c1, c2, c3 = st.columns([1, 5, 2])
            
            with c1:
                st.markdown(f'<div class="score-badge {score_class}">{score}%{badge_suffix}</div>', unsafe_allow_html=True)
                st.caption("Match" if not is_manual else "Verified")
            
            with c2:
                st.subheader(row['name'])
                st.markdown(f"**Role:** {row['job_title']} | **Email:** {row['email']}")
                
                with st.expander("✨ See AI Analysis"):
                    st.info(row['ai_summary'])
                    if row.get('recruiter_notes'):
                        st.warning(f"**Recruiter Note:** {row['recruiter_notes']}")
            
            with c3:
                st.markdown("<br>", unsafe_allow_html=True)
                st.link_button("📄 Open Resume", row['resume_url'], use_container_width=True)
            
            st.divider()

else:
    st.info("No candidates found. Go to the **Upload Center** to add resumes.")