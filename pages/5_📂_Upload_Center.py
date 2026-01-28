import streamlit as st
from supabase import create_client
from styles import load_css
import requests
import time
import mimetypes

st.set_page_config(page_title="Candidate Upload", layout="wide")
load_css()

# --- CONNECT DB ---
try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    st.error("Missing Secrets.")
    st.stop()

# --- CONNECT N8N ---
# Make sure this is in your secrets.toml
N8N_WEBHOOK = st.secrets["n8n"]["webhook_url"]

st.title("📂 Candidate Application Portal")
st.markdown("Upload candidate resumes here. The AI will automatically analyze them against the job description.")

# --- 1. SELECT JOB ---
try:
    # Only fetch ACTIVE jobs
    jobs = supabase.table("jobs").select("id, title, department, location").eq("status", "Active").execute().data
except:
    st.error("Database connection failed.")
    st.stop()

if not jobs:
    st.info("⚠️ No Active Jobs found. Publish a job in the Job Manager first.")
    st.stop()

job_map = {f"{j['title']} ({j['department']})": j for j in jobs}
selected_label = st.selectbox("Select Role", list(job_map.keys()))
selected_job = job_map[selected_label]

st.divider()

# --- 2. UPLOAD RESUME ---
c1, c2 = st.columns([1, 1])

with c1:
    st.subheader("📄 Upload Resume")
    uploaded_file = st.file_uploader("Format: PDF or Docx", type=["pdf", "docx"])

    # Basic Name/Email Input (Optional - AI will extract too, but good to have backup)
    cand_name = st.text_input("Candidate Name (Optional)")
    cand_email = st.text_input("Candidate Email (Optional)")

with c2:
    st.subheader("🚀 Start Analysis")
    st.info(f"Applying for: **{selected_job['title']}**")
    
    if st.button("Upload & Analyze", type="primary", disabled=(not uploaded_file)):
        with st.spinner("Uploading to Secure Storage..."):
            try:
                # 1. UPLOAD TO SUPABASE STORAGE
                # Create unique path: job_id/timestamp_filename
                file_ext = uploaded_file.name.split('.')[-1]
                timestamp = int(time.time())
                file_path = f"candidates/{selected_job['id']}/{timestamp}_{cand_name.replace(' ', '_')}.{file_ext}"
                mime = mimetypes.guess_type(uploaded_file.name)[0]

                supabase.storage.from_("resumes").upload(
                    file_path, 
                    uploaded_file.getvalue(), 
                    {"content-type": mime}
                )

                # 2. GET PUBLIC URL
                resume_url = supabase.storage.from_("resumes").get_public_url(file_path)

                # 3. CREATE DATABASE RECORD (Initial Entry)
                # We create the candidate entry now so we have an ID to track
                cand_data = {
                    "job_id": selected_job['id'],
                    "name": cand_name if cand_name else "Processing...",
                    "email": cand_email if cand_email else "processing@example.com",
                    "resume_url": resume_url,
                    "status": "AI Analysis in Progress"
                }
                
                # Insert and get the new Candidate ID
                res = supabase.table("candidates").insert(cand_data).execute()
                # Note: In some Supabase versions .execute().data returns a list. 
                # If this fails, we can just query by resume_url, but insert usually returns data.
                
            except Exception as e:
                st.error(f"Upload Error: {e}")
                st.stop()

        # 4. TRIGGER AI (N8N)
        with st.spinner("🤖 AI is reading the resume..."):
            try:
                # --- THIS WAS THE MISSING PART ---
                payload = {
                    "resume_url": resume_url,   # <--- n8n needs this!
                    "job_id": selected_job['id'],
                    "candidate_name": cand_name # Context helper
                }
                
                # Send as JSON (cleaner than form-data)
                response = requests.post(N8N_WEBHOOK, json=payload)
                
                if response.status_code == 200:
                    st.balloons()
                    st.success("✅ Analysis Started! Check 'Candidate Analysis' page in 30 seconds.")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"AI Connection Failed: {response.text}")
                    
            except Exception as e:
                st.error(f"Webhook Error: {e}")