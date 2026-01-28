import streamlit as st
from supabase import create_client
from styles import load_css, hero_section
import time

st.set_page_config(page_title="Placement Manager", layout="wide")
load_css()

try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    st.error("Missing Supabase Secrets.")
    st.stop()

hero_section(
    "assets/login_hero.jpg",
    "Placement & MRF Center",
    "Fill out the Digital Manpower Requisition Form (MRF) to initiate hiring."
)

# --- STEP 1: SELECT PENDING HIRE ---
st.subheader("1. Select Candidate for Placement")

# Fetch candidates marked as "Pending Hire" in the placements table
# Note: We look for status 'Pending Hire' to catch them BEFORE the MRF is filled
try:
    response = supabase.table("placements").select(
        "id, candidate_id, job_id, status, candidates(name, email), jobs(title, department)"
    ).eq("status", "Pending Hire").execute()
    
    pending_list = response.data
except Exception as e:
    st.error(f"Error fetching placements: {e}")
    st.stop()

if not pending_list:
    st.info("✅ No pending hires waiting for MRF. Go to 'Candidate Analysis' to select a hire.")
    st.stop()

# Dropdown Map
placement_map = {
    f"{p['candidates']['name']} - {p['jobs']['title']}": p 
    for p in pending_list
}

selected_label = st.selectbox("Select Candidate", list(placement_map.keys()))
selected_placement = placement_map[selected_label]

candidate_name = selected_placement['candidates']['name']
job_title = selected_placement['jobs']['title']
dept = selected_placement['jobs'].get('department', 'General')
placement_id = selected_placement['id']

st.info(f"Drafting MRF for: **{candidate_name}** | Role: **{job_title}**")

# --- STEP 2: DIGITAL MRF FORM ---
st.divider()
st.subheader("2. Digital MRF Requisition")
st.caption("Fill out the hiring details below. This will be sent to Management for approval.")

with st.form("digital_mrf_form"):
    c1, c2 = st.columns(2)
    with c1:
        hiring_manager = st.text_input("Hiring Manager Name", placeholder="e.g. Sarah Connor")
        emp_type = st.selectbox("Employment Type", ["Full-Time", "Contract", "Internship", "Part-Time"])
    with c2:
        proposed_salary = st.text_input("Proposed Salary / Rate", placeholder="e.g. $85,000/yr")
        start_date = st.date_input("Target Start Date")

    justification = st.text_area("Hiring Justification", placeholder="Reason for hire (e.g. Replacement for X, New Role for Q3 growth...)", height=100)
    
    submitted = st.form_submit_button("🚀 Submit for Approval", type="primary")

    if submitted:
        if not hiring_manager or not proposed_salary:
            st.error("Please fill in the Hiring Manager and Salary fields.")
        else:
            try:
                # Update the placement record with the form data
                # Change status to 'Pending Approval' so it moves to the next page
                supabase.table("placements").update({
                    "hiring_manager": hiring_manager,
                    "employment_type": emp_type,
                    "proposed_salary": proposed_salary,
                    "start_date": str(start_date),
                    "justification": justification,
                    "status": "Pending Approval"  # <--- Moves it to Approval Inbox
                }).eq("id", placement_id).execute()

                st.balloons()
                st.success("MRF Submitted Successfully! Sent to Management Approval.")
                time.sleep(2)
                st.rerun()

            except Exception as e:
                st.error(f"Error submitting MRF: {e}")

# --- VIEW HISTORY ---
st.divider()
st.markdown("### 🕒 Recent Submissions")
try:
    history = supabase.table("placements").select(
        "created_at, status, candidates(name), jobs(title)"
    ).neq("status", "Pending Hire").order("created_at", desc=True).limit(5).execute().data

    for h in history:
        st.caption(f"{h['created_at'][:10]} | {h['candidates']['name']} ({h['jobs']['title']}) - **{h['status']}**")
except:
    pass