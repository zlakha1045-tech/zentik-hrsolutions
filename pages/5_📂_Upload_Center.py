import streamlit as st
from supabase import create_client
from styles import load_css
import requests
import time
import mimetypes
import pdfplumber
import docx

st.set_page_config(page_title="Candidate Upload", layout="wide")
load_css()

# --- CONNECT DB ---
try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    st.error("Missing Secrets.")
    st.stop()

N8N_WEBHOOK = st.secrets["n8n"]["webhook_url"]

# --- TEXT EXTRACTION HELPERS ---
def read_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            extract = page.extract_text()
            if extract: text += extract + "\n"
    return text

def read_docx(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

# --- MAIN APP ---
st.title("📂 Candidate Application Portal")
st.markdown("Upload candidate resumes here. The system will extract text and analyze it.")

# 1. SELECT JOB
try:
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

# 2. UPLOAD & PROCESS
c1, c2 = st.columns([1, 1])

with c1:
    st.subheader("📄 Upload Resume")
    uploaded_file = st.file_uploader("Format: PDF or Docx", type=["pdf", "docx"])
    cand_name = st.text_input("Candidate Name (Optional)")
    cand_email = st.text_input("Candidate Email (Optional)")

with c2:
    st.subheader("🚀 Start Analysis")
    st.info(f"Applying for: **{selected_job['title']}**")
    
    if st.button("Upload & Analyze", type="primary", disabled=(not uploaded_file)):
        with st.spinner("Processing Document..."):
            try:
                # A. EXTRACT TEXT LOCALLY
                # This solves the n8n Docx issue
                if uploaded_file.name.endswith(".pdf"):
                    resume_text = read_pdf(uploaded_file)
                else:
                    resume_text = read_docx(uploaded_file)
                
                # B. UPLOAD TO STORAGE
                file_ext = uploaded_file.name.split('.')[-1]
                timestamp = int(time.time())
                file_path = f"candidates/{selected_job['id']}/{timestamp}_{cand_name.replace(' ', '_')}.{file_ext}"
                mime = mimetypes.guess_type(uploaded_file.name)[0]

                supabase.storage.from_("resumes").upload(file_path, uploaded_file.getvalue(), {"content-type": mime})
                resume_url = supabase.storage.from_("resumes").get_public_url(file_path)
                
                # C. SAVE TO DB
                # FIX: Generate a unique dummy email if the user didn't type one.
                # This prevents the "Duplicate Key" error in the database.
                if cand_email:
                    final_email = cand_email
                else:
                    # Create a unique email using the timestamp
                    final_email = f"processing_{int(time.time())}@example.com"

                cand_data = {
                    "job_id": selected_job['id'],
                    "name": cand_name if cand_name else "Processing...",
                    "email": final_email,  # <--- USES THE UNIQUE EMAIL
                    "resume_url": resume_url,
                    "status": "AI Analysis in Progress"
                }
                supabase.table("candidates").insert(cand_data).execute()

                # D. SEND TEXT TO AI (The Fix)
                payload = {
                    "resume_text": resume_text, # <--- Sending Raw Text!
                    "resume_url": resume_url,
                    "job_id": selected_job['id'],
                    "candidate_name": cand_name
                }
                
                response = requests.post(N8N_WEBHOOK, json=payload)
                
                if response.status_code == 200:
                    st.balloons()
                    st.success("✅ Analysis Started!")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"AI Connection Failed: {response.text}")

            except Exception as e:
                st.error(f"Error: {e}")