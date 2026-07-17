import streamlit as st
from supabase import create_client
import pandas as pd
import json
import time

# --- SETUP FOR DEMO ---
# Centered layout and collapsed sidebar mimic a mobile/standalone app experience
st.set_page_config(page_title="Candidate Analysis | Zentik Labs", layout="centered", initial_sidebar_state="collapsed")

# --- CUSTOM STYLING ---
st.markdown("""
<style>
    /* Hide Streamlit Clutter */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Global App Styling */
    .stApp { background-color: #0e1117; color: #ffffff; font-family: 'Inter', 'Segoe UI', sans-serif; }
    
    /* Modern Profile Card */
    .profile-card {
        background-color: #1a1c24; 
        border: 1px solid #2b303b;
        border-radius: 12px; 
        padding: 24px; 
        margin-bottom: 20px;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
        display: flex; 
        flex-wrap: wrap; 
        justify-content: space-between; 
        align-items: center;
        gap: 20px;
    }
    
    /* Animated Score Circle */
    .score-circle {
        width: 90px; 
        height: 90px; 
        border-radius: 50%;
        display: flex; 
        align-items: center; 
        justify-content: center;
        font-size: 28px; 
        font-weight: 800; 
        color: #ffffff; 
        margin: 0 auto;
        box-shadow: 0 0 15px rgba(0,0,0,0.5);
    }
    
    /* Modern UI Tags */
    .skill-chip {
        display: inline-block; 
        background-color: #2b303b; 
        color: #a6c1ee;
        padding: 6px 12px; 
        border-radius: 20px; 
        font-size: 0.85em;
        margin: 4px 4px 0 0; 
        border: 1px solid #3e4c5e;
        font-weight: 500;
    }
    
    .status-badge {
        color: #ffffff; 
        background-color: #3b82f6; 
        padding: 3px 10px; 
        border-radius: 12px; 
        font-size: 0.8em;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
</style>
""", unsafe_allow_html=True)

try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    st.error("Missing Supabase Secrets.")
    st.stop()

# --- 1. SIDEBAR: SELECTION ---
st.sidebar.title("🔍 Candidate Pool")

# Fetch Jobs
try:
    jobs_response = supabase.table("jobs").select("id, title").execute()
    jobs_dict = {j['title']: j['id'] for j in jobs_response.data}
    selected_job_title = st.sidebar.selectbox("Filter by Role", ["All"] + list(jobs_dict.keys()))
except:
    selected_job_title = "All"
    jobs_dict = {}

# Fetch Candidates with Job Title
query = supabase.table("candidates").select("*, jobs(title)").order("match_score", desc=True)

if selected_job_title != "All":
    job_id = jobs_dict[selected_job_title]
    query = query.eq("job_id", job_id)

response = query.execute()
candidates = response.data

if not candidates:
    st.info("No candidates found for this selection.")
    st.stop()

df = pd.DataFrame(candidates)

# Candidate Selector
def format_func(x):
    row = df[df['id']==x].iloc[0]
    m_score = row.get('match_score', 0) if row.get('match_score') is not None else 0
    return f"{row['name']} ({m_score}%)"

selected_candidate_id = st.sidebar.radio(
    "Select Candidate", 
    options=df['id'].tolist(),
    format_func=format_func
)

candidate = df[df['id'] == selected_candidate_id].iloc[0]

# --- 2. HEADER PROFILE CARD ---
score = candidate.get('match_score', 0) if candidate.get('match_score') is not None else 0
score_color = "#2ecc71" if score > 80 else "#f1c40f" if score > 50 else "#e74c3c"
job_title = candidate.get('jobs', {}).get('title', 'Unknown Role') if candidate.get('jobs') else 'Unknown Role'

st.markdown(f"""
<div class="profile-card">
    <div style="flex: 1; min-width: 250px;">
        <p style="color: #4da6ff; font-weight: 700; margin: 0 0 5px 0; text-transform: uppercase; letter-spacing: 1px; font-size: 0.85em;">
            {job_title}
        </p>
        <h1 style="margin: 0; padding: 0; font-size: 2.2em; line-height: 1.1;">{candidate.get('name', 'Unknown')}</h1>
        <p style="color: #a0a0a0; font-size: 0.95em; margin: 8px 0 15px 0;">
            📅 Applied: {str(candidate.get('created_at', ''))[:10]} &nbsp;|&nbsp; 
            <span class="status-badge">{candidate.get('status', 'New')}</span>
        </p>
        <div>
            {' '.join([f'<span class="skill-chip">📞 {candidate.get("phone", "N/A")}</span>', 
                       f'<span class="skill-chip">📧 {candidate.get("email", "N/A")}</span>',
                       f'<span class="skill-chip">🌍 {candidate.get("residence", "N/A")}</span>'])}
        </div>
    </div>
    <div style="text-align: center; min-width: 120px;">
        <div class="score-circle" style="background-color: {score_color}; border: 4px solid #1a1c24;">
            {score}%
        </div>
        <p style="margin-top: 8px; font-weight: 700; font-size: 0.9em; color: {score_color}; text-transform: uppercase; letter-spacing: 1px;">Match Score</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Red Flags Alert (Moved up for better visibility)
red_flags = candidate.get('red_flags', 'None')
if red_flags and red_flags not in ["None", "System Error"]:
    st.error(f"🚩 **Critical Red Flag Detected:** {red_flags}")

# Resume Quick Link
if candidate.get('resume_url'):
    st.link_button("📄 View Original Resume Document", candidate['resume_url'], use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- 3. MAIN CONTENT (TABS) ---
tab_analysis, tab_interview, tab_actions = st.tabs(["📄 Resume Analysis", "📞 Interview Guide", "⚙️ Actions"])

# --- TAB 1: ANALYSIS ---
with tab_analysis:
    with st.container(border=True):
        st.markdown("#### 📊 Executive AI Summary")
        st.info(candidate.get('summary', 'No summary available.'))
        
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("#### ✅ Extracted Skills")
            skills = candidate.get('skills_found', [])
            if isinstance(skills, str):
                try: skills = json.loads(skills)
                except: skills = [skills]
                
            if isinstance(skills, list) and skills:
                chips_html = " ".join([f'<span class="skill-chip">{s}</span>' for s in skills])
                st.markdown(chips_html, unsafe_allow_html=True)
            else:
                st.caption("No skills extracted.")

    with col2:
        with st.container(border=True):
            st.markdown("#### ⚠️ Critical Gaps")
            missing = candidate.get('missing_critical_skills', [])
            if isinstance(missing, str):
                try: missing = json.loads(missing)
                except: missing = [missing]
                
            if missing:
                if isinstance(missing, list):
                    for m in missing: st.warning(m, icon="⚠️")
                else: st.warning(missing, icon="⚠️")
            else:
                st.success("No critical gaps identified. Candidate meets requirements.", icon="✅")
            
    suggested_fit = candidate.get('suggested_fit')
    if suggested_fit:
        with st.container(border=True):
            st.markdown("#### 💡 AI Alternate Role Recommendation")
            st.caption(f"Based on their skills, this candidate might also be a strong fit for:")
            st.success(f"**{suggested_fit}**")

# --- TAB 2: INTERVIEW GUIDE ---
with tab_interview:
    with st.container(border=True):
        st.markdown("#### 🤖 AI-Suggested Interview Questions")
        st.caption("Tailored questions based on the candidate's resume gaps and strengths.")
        questions = candidate.get('suggested_questions')
        if questions:
            if isinstance(questions, str):
                try: questions = json.loads(questions)
                except: questions = [questions]
            if isinstance(questions, list):
                for i, q in enumerate(questions): 
                    st.markdown(f"**Q{i+1}:** {q}")
                    st.divider()
            else: st.write(questions)
        else:
            st.write("No questions generated.")
            
    with st.container(border=True):
        st.markdown("#### 📝 HR Interview Notes")
        existing_notes = candidate.get('interview_notes') or ""
        with st.form("notes_form"):
            new_notes = st.text_area("Record your observations here:", value=existing_notes, height=150, label_visibility="collapsed")
            if st.form_submit_button("💾 Save Notes", type="primary", use_container_width=True):
                supabase.table("candidates").update({"interview_notes": new_notes}).eq("id", candidate['id']).execute()
                st.toast("Notes Saved successfully!", icon="✅")

# --- TAB 3: ACTIONS ---
with tab_actions:
    with st.container(border=True):
        st.markdown("#### ⚖️ Decision Console")
        st.caption("Move the candidate forward in the pipeline or reject their application.")
        status = candidate.get('status', 'New')
        
        # Logic: Can only shortlist if they are New or In Progress
        can_shortlist = status in ['New', 'AI Analysis Complete', 'AI Analysis in Progress']
        
        c1, c2, c3 = st.columns(3)
        with c1:
            if can_shortlist:
                if st.button("✨ Shortlist", use_container_width=True, type="primary"):
                    supabase.table("candidates").update({"status": "Shortlisted"}).eq("id", candidate['id']).execute()
                    st.balloons()
                    st.success("Candidate Shortlisted!")
                    time.sleep(1.5)
                    st.rerun()
            else:
                st.info(f"Status: {status}")

        with c2:
            if st.button("🚫 Reject", use_container_width=True):
                supabase.table("candidates").update({"status": "Rejected"}).eq("id", candidate['id']).execute()
                st.warning("Candidate Rejected.")
                time.sleep(1)
                st.rerun()

        with c3:
            if st.button("🗑️ Delete", use_container_width=True):
                supabase.table("candidates").delete().eq("id", candidate['id']).execute()
                st.error("Record Deleted.")
                time.sleep(1)
                st.rerun()