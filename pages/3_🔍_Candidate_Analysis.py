import streamlit as st
from supabase import create_client
import pandas as pd
import json

# --- SETUP ---
st.set_page_config(page_title="Candidate Analysis", layout="wide")

try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    st.error("Missing Supabase Secrets.")
    st.stop()

st.title("🕵️ HR Analysis & Interview Copilot")

# --- 1. SIDEBAR: FILTER & SELECT ---
st.sidebar.header("Filter Candidates")

# Fetch Jobs for Filter
try:
    jobs_response = supabase.table("jobs").select("id, title").execute()
    jobs_dict = {j['title']: j['id'] for j in jobs_response.data}
    selected_job_title = st.sidebar.selectbox("Filter by Role", ["All"] + list(jobs_dict.keys()))
except:
    selected_job_title = "All"
    jobs_dict = {}

# Fetch Candidates (Only Active ones, ignore Placed/Rejected if you want)
query = supabase.table("candidates").select("*").order("match_score", desc=True)
response = query.execute()
candidates = response.data

if not candidates:
    st.info("No candidates found. Go to 'Upload Center' to add some!")
    st.stop()

# Convert to DataFrame
df = pd.DataFrame(candidates)
df['created_at'] = pd.to_datetime(df['created_at']).dt.date

# List Selection
# We add an icon based on status
def format_func(x):
    row = df[df['id']==x].iloc[0]
    name = row['name']
    score = row['match_score']
    status = row.get('status', 'New')
    icon = "✅" if status == 'Hired' else "❌" if status == 'Rejected' else "🆕"
    return f"{icon} {name} ({score}%)"

selected_candidate_id = st.sidebar.radio(
    "Select Candidate", 
    options=df['id'].tolist(),
    format_func=format_func
)

# Get the specific candidate object
candidate = df[df['id'] == selected_candidate_id].iloc[0]

# --- 2. MAIN DASHBOARD ---

# Header Section
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    score = candidate.get('match_score', 0) 
    color = "green" if score > 80 else "orange" if score > 50 else "red"
    st.markdown(f"## Score: :{color}[{score}%]")
with col2:
    st.header(candidate.get('name', 'Unknown Name'))
    st.caption(f"📅 Applied: {candidate['created_at']} | Status: **{candidate.get('status', 'New')}**")
with col3:
    red_flags = candidate.get('red_flags', 'None')
    if red_flags and red_flags != "None":
        st.error(f"🚩 {red_flags}")
    else:
        st.success("✅ No Major Red Flags")

st.divider()

# Two-Column Layout
left_col, right_col = st.columns(2)

# --- LEFT COLUMN: PROFILE & ANALYSIS ---
with left_col:
    # Contact Details
    with st.expander("👤 Contact & Personal Details", expanded=True):
        p_col1, p_col2 = st.columns(2)
        with p_col1:
            st.markdown(f"**📞 Phone:** \n{candidate.get('phone', 'Not Found')}")
            st.markdown(f"**📧 Email:** \n{candidate.get('email', 'Not Found')}")
        with p_col2:
            st.markdown(f"**🌍 Nationality:** \n{candidate.get('nationality', 'Not Found')}")
            st.markdown(f"**🏠 Residence:** \n{candidate.get('residence', 'Not Found')}")

        st.divider()
        l_col1, l_col2 = st.columns(2)
        with l_col1:
            linkedin = candidate.get('linkedin_url')
            if linkedin and isinstance(linkedin, str) and len(linkedin) > 5:
                st.markdown(f"**🔗 LinkedIn:** [Open Profile]({linkedin})")
            else:
                st.markdown("**🔗 LinkedIn:** Not Found")
        with l_col2:
            suggested_fit = candidate.get('suggested_fit')
            if suggested_fit:
                st.markdown(f"**💡 AI Suggested Role:** \n`{suggested_fit}`")

    # Analysis
    st.subheader("📄 AI Resume Analysis")
    with st.expander("Executive Summary", expanded=True):
        st.write(candidate.get('summary', 'No summary available.'))
    
    with st.expander("Skills Identified"):
        skills = candidate.get('skills_found', [])
        if isinstance(skills, str): st.write(skills)
        elif isinstance(skills, list): st.markdown(" ".join([f"`{s}`" for s in skills]))

    st.markdown("###  Missing / Critical Gaps")
    missing = candidate.get('missing_critical_skills')
    if missing:
        if isinstance(missing, list):
            for m in missing: st.warning(f"⚠️ Missing: {m}")
        else: st.warning(f"⚠️ {missing}")

# --- RIGHT COLUMN: INTERVIEW & ACTIONS ---
with right_col:
    st.subheader("📞 Interview Guide")
    st.info("The AI generated these questions based on gaps in the resume.")

    questions = candidate.get('suggested_questions')
    if questions:
        if isinstance(questions, str):
            try: questions = json.loads(questions)
            except: questions = [questions] 
        
        if isinstance(questions, list):
            for i, q in enumerate(questions):
                st.markdown(f"**Q{i+1}:** {q}")
        else: st.write(questions)
    else:
        st.markdown("*No specific questions generated.*")

    st.divider()

    # Recruiter Notes
    st.write("📝 **Recruiter Notes**")
    existing_notes = candidate.get('interview_notes') or ""
    with st.form("notes_form"):
        new_notes = st.text_area("Record answers here...", value=existing_notes, height=150)
        if st.form_submit_button("💾 Save Notes"):
            supabase.table("candidates").update({"interview_notes": new_notes}).eq("id", candidate['id']).execute()
            st.success("Notes saved!")
            st.rerun()

    st.divider()

    # --- ACTION CONSOLE ---
    st.subheader("⚙️ Decision Console")
    
    # Check current status
    status = candidate.get('status', 'New')
    is_hired = status in ['Hired', 'Pending Hire', 'Placed']

    act_col1, act_col2, act_col3 = st.columns(3)
    
    with act_col1:
        if not is_hired:
            if st.button("🚀 Hire / Place", use_container_width=True, type="primary"):
                # 1. Update Candidate Status to "Pending Hire"
                supabase.table("candidates").update({"status": "Pending Hire"}).eq("id", candidate['id']).execute()
                
                # 2. Add to Placements Table
                job_id = candidate.get('job_id') 
                placement_data = {
                    "candidate_id": candidate['id'],
                    "job_id": job_id,
                    "status": "Pending Hire", # Also set placement status
                    "salary_offered": "Pending" 
                }
                supabase.table("placements").insert(placement_data).execute()
                
                st.balloons()
                st.success("Candidate moved to Placement Manager (Pending Hire)!")
                st.rerun()
        else:
            st.success(f"Status: {status} ✅")

    with act_col2:
        if st.button("🚫 Reject", use_container_width=True):
            supabase.table("candidates").update({"status": "Rejected"}).eq("id", candidate['id']).execute()
            st.warning("Candidate Rejected.")
            st.rerun()

    with act_col3:
        if st.button("🗑️ Delete", type="primary", use_container_width=True):
            # Delete from DB
            supabase.table("candidates").delete().eq("id", candidate['id']).execute()
            st.error("Candidate Deleted.")
            st.rerun()