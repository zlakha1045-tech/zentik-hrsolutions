import streamlit as st
from supabase import create_client
import requests
import time
import mimetypes

# --- SECURITY: HIDE SIDEBAR NAVIGATION ---
st.set_page_config(page_title="Screening", layout="centered", initial_sidebar_state="collapsed")

st.markdown(
    """
    <style>
        /* Hide the sidebar navigation */
        [data-testid="stSidebarNav"] {display: none !important;}
        /* Hide the sidebar collapse button */
        [data-testid="collapsedControl"] {display: none !important;}
    </style>
    """,
    unsafe_allow_html=True,
)
# -----------------------------------------

# Minimalist config for a public-facing form
st.set_page_config(page_title="Zentik Labs - Candidate Screening", layout="centered")

# Connect to Supabase
supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

# 1. Get Application ID from URL
query_params = st.query_params
app_id = query_params.get("id")

if not app_id:
    st.error("❌ Invalid Link. Please contact your recruiter.")
    st.stop()

# 2. Fetch Job and Candidate Info
try:
    app_data = supabase.table("applications").select(
        "*, jobs(title, screening_questions), candidates(name)"
    ).eq("id", app_id).single().execute()
    
    data = app_data.data
    questions = data['jobs']['screening_questions']
except:
    st.error("Application not found.")
    st.stop()

# --- THE UI ---
st.image("assets/logo.png", width=120)
st.title(f"Screening: {data['jobs']['title']}")
st.markdown(f"Hello **{data['candidates']['name']}**, please provide a bit more detail regarding your experience to help us move your application forward.")

with st.form("public_screening_form"):
    user_answers = {}
    for i, q in enumerate(questions):
        st.write(f"**{q}**")
        user_answers[q] = st.text_area("Your response", key=f"ans_{i}", label_visibility="collapsed")
    
    if st.form_submit_button("Submit Responses", type="primary"):
        try:
            # Save to Database
            supabase.table("applications").update({
                "questionnaire_answers": user_answers
            }).eq("id", app_id).execute()
            
            # Trigger AI Re-Analysis via Webhook
            payload = {
                "job_id": data['job_id'],
                "candidate_name": data['candidates']['name'],
                "resume_url": data['resume_url'],
                "questionnaire_answers": user_answers,
                "re_analysis_mode": True
            }
            requests.post(st.secrets["n8n"]["webhook_url"], json=payload)
            
            st.success("✅ Thank you! Your responses have been sent to our recruitment team.")
            st.balloons()
            time.sleep(2)
        except Exception as e:
            st.error("Submission failed. Please try again.")