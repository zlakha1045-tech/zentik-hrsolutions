import streamlit as st
from supabase import create_client
import pandas as pd
import json

# --- SETUP ---
st.set_page_config(page_title="Candidate Analysis", layout="wide")

# --- CUSTOM STYLING ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .profile-card {
        background-color: #1a1c24; border: 1px solid #2b303b;
        border-radius: 10px; padding: 20px; margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .score-circle {
        width: 100px; height: 100px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 32px; font-weight: bold; color: white; margin: 0 auto;
    }
    .skill-chip {
        display: inline-block; background-color: #2b303b; color: #a6c1ee;
        padding: 5px 10px; border-radius: 15px; font-size: 0.85em;
        margin: 2px; border: 1px solid #3e4c5e;
    }
    h1, h2, h3 { color: #ffffff !important; }
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
# We add ', jobs(title)' to the query
query = supabase.table("candidates").select("*, jobs(title)").order("match_score", desc=True)

# Apply Filter
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
    return f"{row['name']} ({row['match_score']}%)"

selected_candidate_id = st.sidebar.radio(
    "Select Candidate", 
    options=df['id'].tolist(),
    format_func=format_func
)

candidate = df[df['id'] == selected_candidate_id].iloc[0]

# --- 2. HEADER PROFILE CARD ---
score = candidate.get('match_score', 0)
score_color = "#2ecc71" if score > 80 else "#f1c40f" if score > 50 else "#e74c3c"
# Extract Job Title safely
job_title = candidate.get('jobs', {}).get('title', 'Unknown Role') if candidate.get('jobs') else 'Unknown Role'

st.markdown(f"""
<div class="profile-card">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div style="flex: 1;">
            <p style="color: #4da6ff; font-weight: bold; margin: 0; text-transform: uppercase; letter-spacing: 1px;">
                {job_title}
            </p>
            <h1 style="margin:5px 0; padding:0;">{candidate.get('name', 'Unknown')}</h1>
            <p style="color: #a0a0a0; font-size: 1.1em; margin: 5px 0;">
                📅 Applied: {str(candidate.get('created_at', ''))[:10]} | 
                <span style="color: #ffffff; background-color: #333; padding: 2px 8px; border-radius: 4px;">{candidate.get('status', 'New')}</span>
            </p>
            <div style="margin-top: 10px;">
                {' '.join([f'<span class="skill-chip">📞 {candidate.get("phone", "N/A")}</span>', 
                           f'<span class="skill-chip">📧 {candidate.get("email", "N/A")}</span>',
                           f'<span class="skill-chip">🌍 {candidate.get("residence", "N/A")}</span>'])}
            </div>
        </div>
        <div style="text-align: center;">
            <div class="score-circle" style="background-color: {score_color}; border: 4px solid #1a1c24; box-shadow: 0 0 10px {score_color};">
                {score}%
            </div>
            <p style="margin-top: 5px; font-weight: bold; color: {score_color};">Match Score</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Red Flags Alert
red_flags = candidate.get('red_flags', 'None')
if red_flags and red_flags not in ["None", "System Error"]:
    st.error(f"🚩 **Critical Red Flag:** {red_flags}")

# --- 3. MAIN CONTENT (TABS) ---
tab_analysis, tab_interview, tab_actions = st.tabs(["📄 Resume Analysis", "📞 Interview Guide", "⚙️ Actions"])

# --- TAB 1: ANALYSIS ---
with tab_analysis:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Executive Summary")
        st.info(candidate.get('summary', 'No summary available.'))
        st.subheader("Skill Match")
        skills = candidate.get('skills_found', [])
        if isinstance(skills, list) and skills:
            chips_html = " ".join([f'<span class="skill-chip">{s}</span>' for s in skills])
            st.markdown(chips_html, unsafe_allow_html=True)
        else:
            st.write("No skills extracted.")

    with col2:
        st.subheader("⚠️ Critical Gaps")
        missing = candidate.get('missing_critical_skills', [])
        if missing:
            if isinstance(missing, list):
                for m in missing: st.warning(m, icon="⚠️")
            else: st.warning(missing, icon="⚠️")
        else:
            st.success("No critical gaps!")
        
        suggested_fit = candidate.get('suggested_fit')
        if suggested_fit:
            st.markdown(f"**💡 AI Recommendation:**")
            st.info(f"Consider for: **{suggested_fit}**")

# --- TAB 2: INTERVIEW GUIDE ---
with tab_interview:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🤖 Suggested Questions")
        questions = candidate.get('suggested_questions')
        if questions:
            if isinstance(questions, str):
                try: questions = json.loads(questions)
                except: questions = [questions]
            if isinstance(questions, list):
                for i, q in enumerate(questions): st.markdown(f"**Q{i+1}:** {q}")
            else: st.write(questions)
        else: st.write("No questions generated.")
            
    with col2:
        st.markdown("### 📝 Notes")
        existing_notes = candidate.get('interview_notes') or ""
        with st.form("notes_form"):
            new_notes = st.text_area("Interview Notes", value=existing_notes, height=200)
            if st.form_submit_button("💾 Save", type="primary"):
                supabase.table("candidates").update({"interview_notes": new_notes}).eq("id", candidate['id']).execute()
                st.toast("Saved!", icon="✅")

# --- TAB 3: ACTIONS ---
with tab_actions:
    st.subheader("Decision Console")
    status = candidate.get('status', 'New')
    is_hired = status in ['Hired', 'Pending Hire', 'Placed']
    
    c1, c2, c3 = st.columns(3)
    with c1:
        if not is_hired:
            if st.button("🚀 Hire / Move to Placement", use_container_width=True, type="primary"):
                # Update Candidate Status
                supabase.table("candidates").update({"status": "Pending Hire"}).eq("id", candidate['id']).execute()
                
                # Insert into Placements
                job_id = candidate.get('job_id')
                placement_data = {
                    "candidate_id": candidate['id'],
                    "job_id": job_id,
                    "status": "Pending Hire",
                    "salary_offered": "Pending"
                }
                supabase.table("placements").insert(placement_data).execute()
                
                st.balloons()
                st.success("Moved to Placement Manager!")
                st.rerun()
        else:
            st.success(f"Status: {status} ✅")

    with c2:
        if st.button("🚫 Reject", use_container_width=True):
            supabase.table("candidates").update({"status": "Rejected"}).eq("id", candidate['id']).execute()
            st.warning("Rejected.")
            st.rerun()

    with c3:
        if st.button("🗑️ Delete", use_container_width=True):
            supabase.table("candidates").delete().eq("id", candidate['id']).execute()
            st.error("Deleted.")
            st.rerun()