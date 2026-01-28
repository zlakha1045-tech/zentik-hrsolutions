import streamlit as st
from supabase import create_client
import requests
import mimetypes
import time  # <--- Added for the buffer

# --- SETUP ---
st.set_page_config(page_title="Upload Center", layout="centered")

try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    st.error("Missing Supabase Secrets.")
    st.stop()

st.title("📂 Resume Upload Center")
st.markdown("Upload resumes in **PDF, Word, Text, or Image** formats for AI Analysis.")

# --- 1. JOB SELECTION ---
try:
    jobs = supabase.table("jobs").select("id, title, status").eq("status", "Active").execute()
    job_map = {j['title']: j['id'] for j in jobs.data}
except:
    job_map = {}

if not job_map:
    st.warning("No active jobs found. Please create a job in the Job Manager first.")
    st.stop()

selected_job_title = st.selectbox("Select Role", list(job_map.keys()))
selected_job_id = job_map[selected_job_title]

# --- 2. MULTI-FORMAT UPLOADER ---
uploaded_file = st.file_uploader(
    "Drag & drop resume here", 
    type=["pdf", "docx", "txt", "png", "jpg", "jpeg"]
)

# --- 3. SUBMISSION LOGIC ---
if st.button("🚀 Analyze Candidate", type="primary"):
    if uploaded_file and selected_job_id:
        
        # We use st.status to show a multi-step progress log
        with st.status("🚀 Starting AI Agent...", expanded=True) as status:
            
            try:
                # STEP 1: UPLOAD
                st.write("📤 Uploading file to secure server...")
                files = {
                    'resume': (
                        uploaded_file.name, 
                        uploaded_file.getvalue(), 
                        uploaded_file.type or mimetypes.guess_type(uploaded_file.name)[0]
                    )
                }
                data = {'job_id': selected_job_id}

                # STEP 2: SEND TO N8N (The 15s Wait)
                st.write("🤖 AI is interviewing the resume... (This takes ~15s)")
                webhook_url = st.secrets["n8n"]["webhook_url"]
                
                # This request blocks until n8n replies
                response = requests.post(webhook_url, files=files, data=data)

                if response.status_code == 200:
                    # STEP 3: THE SAFETY BUFFER
                    st.write("💾 Finalizing database entries...")
                    
                    # Create a visual progress bar for the buffer
                    progress_bar = st.progress(0)
                    for i in range(100):
                        time.sleep(0.03)  # 3 Second Safety Buffer
                        progress_bar.progress(i + 1)
                    
                    # Mark complete
                    status.update(label="✅ Analysis Complete!", state="complete", expanded=False)
                    
                    st.balloons()
                    st.success(f"Candidate successfully analyzed for {selected_job_title}!")
                    
                    # Button appears ONLY after the wait
                    if st.button("👉 View Analysis Result"):
                        st.switch_page("pages/Candidate_Analysis.py")
                        
                else:
                    status.update(label="❌ Error", state="error")
                    st.error(f"Analysis Failed. Error: {response.text}")

            except Exception as e:
                status.update(label="❌ Connection Error", state="error")
                st.error(f"System Error: {e}")
    else:
        st.warning("Please select a job and upload a file.")