import streamlit as st
from supabase import create_client
from styles import load_css, hero_section
import requests

st.set_page_config(page_title="Internal Screening", layout="wide")
load_css()
supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

hero_section(
    "assets/login_hero.jpg", 
    "Screening & Interview",
    "Gather missing details to perfect the AI analysis"
)

# 1. SELECT JOB
try:
    jobs = supabase.table("jobs").select("id, title, screening_questions").eq("status", "active").execute()
    job_map = {j['title']: j for j in jobs.data}
except:
    st.error("No jobs found.")
    st.stop()

selected_job_name = st.selectbox("Job Opening", list(job_map.keys()))
selected_job = job_map[selected_job_name]
questions = selected_job.get('screening_questions', [])

# 2. SELECT CANDIDATE
try:
    apps = supabase.table("applications").select(
        "id, candidate_id, resume_url, candidates(name)"
    ).eq("job_id", selected_job['id']).execute()
    cand_map = {app['candidates']['name']: app for app in apps.data}
except:
    cand_map = {}

if not cand_map:
    st.info("No candidates found for this job.")
    st.stop()

selected_cand_name = st.selectbox("Candidate", list(cand_map.keys()))
selected_app = cand_map[selected_cand_name]

# --- NEW: PUBLIC LINK GENERATOR ---
st.divider()
# Use your actual deployed URL here once live
public_base_url = "https://your-app-url.streamlit.app/Public_Questionnaire" 
personal_link = f"{public_base_url}?id={selected_app['id']}"

st.markdown("### 🔗 Remote Screening")
st.write("Copy this link to send to the candidate if they are filling it out themselves:")
st.code(personal_link, language="text")

st.divider()

# 3. INTERNAL FORM (For Phone Screens)
st.markdown(f"### 📞 Live Interview: {selected_cand_name}")
with st.form("internal_screening_form"):
    answers = {}
    for i, q in enumerate(questions):
        st.markdown(f"**Q{i+1}: {q}**")
        answers[q] = st.text_area("Candidate's Response", key=f"int_{i}")
    
    if st.form_submit_button("Update Analysis"):
        payload = {
            "job_id": selected_job['id'],
            "candidate_name": selected_cand_name,
            "resume_url": selected_app['resume_url'],
            "questionnaire_answers": answers,
            "re_analysis_mode": True
        }
        requests.post(st.secrets["n8n"]["webhook_url"], json=payload)
        st.success("Re-analysis triggered!")