import streamlit as st
from supabase import create_client
import json
import time  # FIXED: Added missing import
from styles import load_css, hero_section

st.set_page_config(page_title="Deep Dive", layout="wide")
load_css()
supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

# Hero
hero_section(
    "assets/analysis_hero.jpg",
    "Candidate Deep Dive",
    "Detailed skills gap analysis and risk assessment"
)

# Sidebar Logic
with st.sidebar:
    st.header("Filters")
    try:
        jobs = supabase.table("jobs").select("id, title").eq("status", "active").execute()
        job_map = {j['title']: j['id'] for j in jobs.data}
    except:
        st.warning("Could not fetch jobs.")
        st.stop()
    
    if not job_map:
        st.warning("No jobs found.")
        st.stop()
        
    selected_job = st.selectbox("Role", list(job_map.keys()))
    job_id = job_map[selected_job]
    
    candidates = supabase.table("applications").select("id, match_score, candidates(name)").eq("job_id", job_id).order("match_score", desc=True).execute()
    
    if not candidates.data:
        st.warning("No candidates.")
        st.stop()
        
    cand_map = {f"{c['candidates']['name']} ({c['match_score']}%)": c['id'] for c in candidates.data}
    selected_cand_label = st.radio("Select Candidate", list(cand_map.keys()))
    app_id = cand_map[selected_cand_label]

# Fetch Data
app_data = supabase.table("applications").select("*, candidates(*), jobs(title)").eq("id", app_id).single().execute()
data = app_data.data

# Handle AI JSON
ai_json = data.get('ai_analysis_json', {})
if isinstance(ai_json, str): 
    try:
        ai_json = json.loads(ai_json)
    except:
        ai_json = {}

# --- VISUAL REPORT ---

# 1. Profile Header
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown(f"<h1>{data['candidates']['name']}</h1>", unsafe_allow_html=True)
    st.markdown(f"### {data['jobs']['title']}")
    st.caption(f"📧 {data['candidates']['email']}")

with c2:
    score = data['match_score']
    color = "#10B981" if score >= 80 else "#F59E0B" if score >= 50 else "#EF4444"
    st.markdown(f"""
        <div style="background-color: {color}; padding: 20px; border-radius: 15px; text-align: center; color: white;">
            <div style="font-size: 3rem; font-weight: 700;">{score}%</div>
            <div>MATCH SCORE</div>
        </div>
    """, unsafe_allow_html=True)

st.divider()

# 2. Executive Summary
st.markdown("### 🤖 AI Executive Summary & Reasoning")
summary_text = data.get('ai_summary', "No summary available.")

if "Logic:" in summary_text:
    parts = summary_text.split("Logic:", 1)[1].split("\n", 1)
    logic_part = parts[0]
    summary_part = parts[1] if len(parts) > 1 else ""
    with st.expander("👁️ View AI Reasoning (Chain of Thought)"):
        st.write(logic_part.strip())
    st.info(summary_part.strip())
else:
    st.info(summary_text)

# 3. Questionnaire Answers (New Feature Display)
q_answers = data.get('questionnaire_answers')
if q_answers:
    with st.expander("📝 View Screening Questionnaire Answers"):
        for q, a in q_answers.items():
            st.markdown(f"**Q:** {q}")
            st.write(f"**A:** {a}")
            st.divider()

# 4. Skills Visualization
c1, c2 = st.columns(2)

with c1:
    st.markdown("### ✅ Skills Detected")
    found = ai_json.get('skills_found', [])
    if found:
        for skill in found:
            st.markdown(f"**{skill}**")
            st.progress(100)
    else:
        st.write("No skills specifically extracted.")

with c2:
    st.markdown("### ⚠️ Critical Gaps")
    missing = ai_json.get('missing_critical_skills', [])
    if missing:
        for gap in missing:
            st.error(f"Missing: {gap}")
    else:
        st.success("No critical gaps found!")

# 5. Red Flags & Suggestions
flags = ai_json.get('red_flags', "None")
suggested = ai_json.get('suggested_fit', None)

if (flags and flags != "None") or suggested:
    st.divider()
    col_f, col_s = st.columns(2)
    with col_f:
        if flags and flags != "None":
            st.markdown("### 🚩 Risk Assessment")
            st.warning(flags)
    with col_s:
        if suggested:
            st.markdown("### 💡 Career Path Suggestion")
            st.info(f"**AI Recommendation:** {suggested}")

st.divider()
st.link_button("📄 Open Original Resume PDF", data['candidates']['resume_url'], use_container_width=True)

# --- HUMAN INTERVENTION SECTION ---
st.divider()
st.subheader("✍️ Recruiter Feedback & Manual Override")

with st.form("recruiter_feedback_form"):
    c1, c2 = st.columns([3, 1])
    with c1:
        existing_notes = data.get('recruiter_notes', "")
        new_notes = st.text_area("Internal Recruitment Notes", value=existing_notes, placeholder="Enter interview feedback...")
    with c2:
        existing_manual = data.get('manual_score')
        new_score = st.number_input("Manual Score Override", min_value=0, max_value=100, value=int(existing_manual) if existing_manual is not None else int(data['match_score']))
    
    if st.form_submit_button("💾 Save Feedback & Update Score"):
        try:
            supabase.table("applications").update({
                "recruiter_notes": new_notes,
                "manual_score": new_score,
                "match_score": new_score
            }).eq("id", app_id).execute()
            st.success("Feedback saved!")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Failed to save: {e}")