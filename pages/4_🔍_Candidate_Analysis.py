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
    selected_job_title = "All" # Fallback if jobs table is empty

# Fetch Candidates
# We fetch 'name' and 'email' (matching your actual DB columns)
query = supabase.table("candidates").select("*").order("match_score", desc=True)

# (Optional: Add filtering logic here if you add a job_id column later)
response = query.execute()
candidates = response.data

if not candidates:
    st.info("No candidates found. Go to 'Upload Center' to add some!")
    st.stop()

# Convert to DataFrame
df = pd.DataFrame(candidates)
df['created_at'] = pd.to_datetime(df['created_at']).dt.date

# List Selection (FIXED: Uses 'name' instead of 'candidate_name')
selected_candidate_id = st.sidebar.radio(
    "Select Candidate", 
    options=df['id'].tolist(),
    format_func=lambda x: f"{df[df['id']==x]['name'].values[0]} ({df[df['id']==x]['match_score'].values[0]}%)"
)

# Get the specific candidate object
candidate = df[df['id'] == selected_candidate_id].iloc[0]

# --- 2. MAIN DASHBOARD ---

# Header Section
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    score = candidate.get('match_score', 0) # Safe get
    color = "green" if score > 80 else "orange" if score > 50 else "red"
    st.markdown(f"## Score: :{color}[{score}%]")
with col2:
    st.header(candidate['name'])
    st.caption(f"Applied: {candidate['created_at']} | Email: {candidate['email']}")
with col3:
    red_flags = candidate.get('red_flags', 'None')
    if red_flags and red_flags != "None":
        st.error(f"🚩 {red_flags}")
    else:
        st.success("✅ No Major Red Flags")

st.divider()

# Two-Column Layout
left_col, right_col = st.columns(2)

# --- LEFT COLUMN: THE RESUME ANALYSIS ---
with left_col:
    st.subheader("📄 AI Resume Analysis")
    
    with st.expander("Executive Summary", expanded=True):
        st.write(candidate.get('summary', 'No summary available.'))
    
    with st.expander("Skills Identified"):
        skills = candidate.get('skills_found', [])
        if isinstance(skills, str):
            st.write(skills)
        elif isinstance(skills, list):
            st.markdown(" ".join([f"`{s}`" for s in skills]))

    st.markdown("###  Missing / Critical Gaps")
    missing = candidate.get('missing_critical_skills')
    if missing:
        if isinstance(missing, list):
            for m in missing:
                st.warning(f"⚠️ Missing: {m}")
        else:
            st.warning(f"⚠️ {missing}")

# --- RIGHT COLUMN: THE INTERVIEW COPILOT ---
with right_col:
    st.subheader("📞 Interview Guide")
    st.info("The AI generated these questions based on gaps in the resume.")

    # 1. DISPLAY GENERATED QUESTIONS
    questions = candidate.get('suggested_questions')
    
    if questions:
        if isinstance(questions, str):
            try:
                questions = json.loads(questions)
            except:
                questions = [questions] 
        
        # Ensure it is a list before looping
        if isinstance(questions, list):
            for i, q in enumerate(questions):
                st.markdown(f"**Q{i+1}:** {q}")
        else:
             st.write(questions)
    else:
        st.markdown("*No specific questions generated.*")

    st.divider()

    # 2. INTERVIEW NOTES
    st.write("📝 **Recruiter Notes**")
    
    existing_notes = candidate.get('interview_notes') or ""
    
    with st.form("notes_form"):
        new_notes = st.text_area("Record candidate's answers here...", value=existing_notes, height=200)
        save_btn = st.form_submit_button("💾 Save Interview Notes")
        
        if save_btn:
            try:
                supabase.table("candidates").update({"interview_notes": new_notes}).eq("id", candidate['id']).execute()
                st.success("Notes saved successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error saving notes: {e}")