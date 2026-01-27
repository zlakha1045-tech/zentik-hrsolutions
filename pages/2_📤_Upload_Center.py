import streamlit as st
from supabase import create_client
import requests
import mimetypes
import time
from styles import load_css, hero_section

st.set_page_config(page_title="Upload Center", layout="wide")
load_css()
supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

# Hero Image
hero_section(
    "assets/upload_hero.jpg",
    "Upload Center",
    "Bulk process resumes with our AI Engine"
)

# Instructions
with st.expander("ℹ️ How to use this tool"):
    st.write("1. Select the Job Opening you are hiring for.")
    st.write("2. Drag and drop up to 20 PDF resumes.")
    st.write("3. The AI will analyze skills, extracting names and emails automatically.")

# Fetch Jobs
try:
    jobs_response = supabase.table("jobs").select("id, title").eq("status", "active").execute()
    job_options = {job['title']: job['id'] for job in jobs_response.data}
except:
    job_options = {}

if not job_options:
    st.error("Please create a job in **Job Manager** first.")
    st.stop()

# Styled Selection Box
c1, c2 = st.columns([1, 2])
with c1:
    selected_job_name = st.selectbox("🎯 Target Role", list(job_options.keys()))
selected_job_id = job_options[selected_job_name]

# Uploader
if 'upload_key' not in st.session_state: st.session_state.upload_key = 0
uploaded_files = st.file_uploader("Drop PDFs here", type=["pdf"], accept_multiple_files=True, key=f"key_{st.session_state.upload_key}")

if st.button("🚀 Analyze Candidates", type="primary"):
    if uploaded_files:
        progress_bar = st.progress(0, text="Initializing AI...")
        
        for i, file in enumerate(uploaded_files):
            try:
                # Upload logic
                file_bytes = file.getvalue()
                path = f"{int(time.time())}_{file.name}"
                content_type = mimetypes.guess_type(file.name)[0] or "application/pdf"
                
                supabase.storage.from_("resumes").upload(path=path, file=file_bytes, file_options={"content-type": content_type, "upsert": "true"})
                public_url = supabase.storage.from_("resumes").get_public_url(path)

                payload = {
                    "job_id": selected_job_id, 
                    "candidate_name": "AI_Scanning...", 
                    "candidate_email": "pending_extraction",
                    "resume_url": public_url
                }
                requests.post(st.secrets["n8n"]["webhook_url"], json=payload)
                
            except Exception as e:
                st.error(f"Error: {e}")
            
            progress_bar.progress((i + 1) / len(uploaded_files), text=f"Analyzing {file.name}...")

        time.sleep(1)
        st.session_state.upload_key += 1
        st.success("✅ Batch processing complete!")
        st.balloons()
        time.sleep(2)
        st.rerun()