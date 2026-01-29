import streamlit as st
from supabase import create_client
from styles import load_css, hero_section
import requests
import time
import mimetypes
import pdfplumber
import docx

st.set_page_config(page_title="Bulk Candidate Upload", layout="wide")
load_css()

# --- CONNECT DB ---
try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    st.error("Missing Secrets.")
    st.stop()

N8N_WEBHOOK = st.secrets["n8n"]["webhook_url"]

# --- ROBUST TEXT EXTRACTION HELPERS ---
def read_pdf(file):
    text = ""
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                extract = page.extract_text()
                if extract: 
                    text += extract + "\n"
    except Exception as e:
        return f"Error reading PDF: {e}"
    return text

def read_docx(file):
    try:
        doc = docx.Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        return f"Error reading Word Doc: {e}"

# --- MAIN APP UI ---
hero_section("assets/login_hero.jpg", "Candidate Portal", "Upload resumes in bulk for AI-powered analysis.")

st.subheader("📂 Bulk Resume Processor")
st.markdown("Drop multiple resumes (PDF or Docx) below. ZentikLabs AI will process them all in a queue.")

# 1. SELECT JOB
try:
    # Only fetch active jobs for candidates to apply to
    jobs = supabase.table("jobs").select("id, title, department").eq("status", "Active").execute().data
except Exception as e:
    st.error(f"Database connection failed: {e}")
    st.stop()

if not jobs:
    st.info("⚠️ No Active Jobs found. Please publish a job in the Job Manager first.")
    st.stop()

job_map = {f"{j['title']} ({j['department']})": j for j in jobs}
selected_label = st.selectbox("Assign to Role:", list(job_map.keys()))
selected_job = job_map[selected_label]

st.divider()

# 2. BULK UPLOAD SELECTION
# Added: accept_multiple_files=True
uploaded_files = st.file_uploader("Drag and drop resumes here", type=["pdf", "docx"], accept_multiple_files=True)

if uploaded_files:
    st.info(f"📋 {len(uploaded_files)} files selected for processing.")
    
    # 3. START ANALYSIS LOOP
    if st.button("🚀 Analyze All Resumes", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Iterate through every uploaded file
        for i, uploaded_file in enumerate(uploaded_files):
            # Update status for the user
            status_text.text(f"Processing ({i+1}/{len(uploaded_files)}): {uploaded_file.name}")
            
            try:
                # A. EXTRACT TEXT
                if uploaded_file.name.lower().endswith(".pdf"):
                    resume_text = read_pdf(uploaded_file)
                else:
                    resume_text = read_docx(uploaded_file)
                
                # B. UPLOAD TO STORAGE
                file_ext = uploaded_file.name.split('.')[-1]
                timestamp = int(time.time())
                # Using a unique path including index to avoid collisions in high-speed uploads
                file_path = f"candidates/{selected_job['id']}/{timestamp}_{i}.{file_ext}"
                mime = mimetypes.guess_type(uploaded_file.name)[0]

                supabase.storage.from_("resumes").upload(file_path, uploaded_file.getvalue(), {"content-type": mime})
                resume_url = supabase.storage.from_("resumes").get_public_url(file_path)

                # C. SAVE TO DB
                # Create the unique email to avoid blocks
                final_email = f"processing_{timestamp}_{i}@zentiklabs.com"

                cand_data = {
                    "job_id": selected_job['id'],
                    "name": uploaded_file.name, 
                    "email": final_email,
                    "resume_url": resume_url,
                    "status": "AI Analysis in Progress"
                }
                
                # --- CRITICAL CHANGE HERE ---
                # 1. Execute the insert and capture the response data
                response = supabase.table("candidates").insert(cand_data).execute()
                
                # 2. Extract the actual UUID ('id') from the database response
                # Response.data is a list, so we take the first item [0]
                new_row_id = response.data[0]['id'] 

                # D. SEND TO N8N
                payload = {
                    "candidate_id": new_row_id,  # <--- We label it 'candidate_id' for n8n
                    "resume_text": resume_text,
                    "resume_url": resume_url,
                    "job_id": selected_job['id']
                }
                requests.post(N8N_WEBHOOK, json=payload)
                
            except Exception as e:
                st.error(f"❌ Failed to process {uploaded_file.name}: {e}")
            
            # Update visual progress
            progress_bar.progress((i + 1) / len(uploaded_files))
            
        status_text.text("✅ Bulk Upload Complete!")
        st.balloons()
        st.success(f"Successfully sent {len(uploaded_files)} resumes for AI analysis. You can monitor progress in the 'Candidate Analysis' page.")
        time.sleep(3)
        st.rerun()