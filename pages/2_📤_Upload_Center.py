import streamlit as st
from supabase import create_client
import requests
import mimetypes

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
# We need to know which job this resume is for
try:
    jobs = supabase.table("jobs").select("id, title, status").eq("status", "Active").execute()
    # Create a dictionary: {"Sales Manager": "ID-123", ...}
    job_map = {j['title']: j['id'] for j in jobs.data}
except:
    job_map = {}

if not job_map:
    st.warning("No active jobs found. Please create a job in the Job Manager first.")
    st.stop()

selected_job_title = st.selectbox("Select Role", list(job_map.keys()))
selected_job_id = job_map[selected_job_title]

# --- 2. MULTI-FORMAT UPLOADER ---
# Updated to accept docx, txt, and images
uploaded_file = st.file_uploader(
    "Drag & drop resume here", 
    type=["pdf", "docx", "txt", "png", "jpg", "jpeg"]
)

# --- 3. SUBMISSION LOGIC ---
if st.button("🚀 Analyze Candidate", type="primary"):
    if uploaded_file and selected_job_id:
        
        with st.spinner("Uploading and Analyzing... This may take a moment."):
            try:
                # 1. Prepare Payload
                # We send the file AND the job_id so n8n knows what requirements to match
                files = {
                    'resume': (
                        uploaded_file.name, 
                        uploaded_file.getvalue(), 
                        uploaded_file.type or mimetypes.guess_type(uploaded_file.name)[0]
                    )
                }
                
                data = {
                    'job_id': selected_job_id
                }

                # 2. Send to n8n Webhook
                webhook_url = st.secrets["n8n"]["webhook_url"]
                response = requests.post(webhook_url, files=files, data=data)

                # 3. Handle Response
                if response.status_code == 200:
                    st.success(f"✅ Analysis Complete! Candidate sent to {selected_job_title} pipeline.")
                    st.balloons()
                    
                    # Optional: Show a link to view the result immediately
                    # We can't link directly to the specific candidate easily without the ID returned, 
                    # but we can redirect to the analysis page.
                    if st.button("View Analysis Now"):
                        st.switch_page("pages/Candidate_Analysis.py")
                else:
                    st.error(f"Analysis Failed. Error: {response.text}")

            except Exception as e:
                st.error(f"Connection Error: {e}")
    else:
        st.warning("Please select a job and upload a file.")