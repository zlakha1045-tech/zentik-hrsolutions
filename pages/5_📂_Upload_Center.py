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

# --- TEXT EXTRACTION HELPERS ---
def read_pdf(file):
    text = ""
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                extract = page.extract_text()
                if extract: text += extract + "\n"
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
hero_section("assets/login_hero.jpg", "Candidate Portal", "Fast-Track Bulk Upload.")

st.subheader("📂 Resume Upload")

# 1. SELECT JOB
try:
    jobs = supabase.table("jobs").select("id, title, department").eq("status", "Active").execute().data
except:
    st.stop()

if not jobs:
    st.info("⚠️ No Active Jobs found.")
    st.stop()

job_map = {f"{j['title']} ({j['department']})": j for j in jobs}
selected_label = st.selectbox("Assign to Role:", list(job_map.keys()))
selected_job = job_map[selected_label]

st.divider()

# 2. BULK UPLOAD
uploaded_files = st.file_uploader("Drag resumes here (PDF or Docx)", type=["pdf", "docx"], accept_multiple_files=True)

if uploaded_files:
    if st.button(f"🚀 Fast-Process {len(uploaded_files)} Resumes", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # --- THE FAST LOOP ---
        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Uploading ({i+1}/{len(uploaded_files)}): {uploaded_file.name}")
            
            try:
                # A. EXTRACT TEXT
                if uploaded_file.name.lower().endswith(".pdf"):
                    resume_text = read_pdf(uploaded_file)
                else:
                    resume_text = read_docx(uploaded_file)
                
                # B. UPLOAD FILE
                file_ext = uploaded_file.name.split('.')[-1]
                timestamp = int(time.time())
                file_path = f"candidates/{selected_job['id']}/{timestamp}_{i}.{file_ext}"
                mime = mimetypes.guess_type(uploaded_file.name)[0]

                supabase.storage.from_("resumes").upload(file_path, uploaded_file.getvalue(), {"content-type": mime})
                resume_url = supabase.storage.from_("resumes").get_public_url(file_path)

                # C. SAVE TO DB (Initial Status)
                final_email = f"processing_{timestamp}_{i}@zentiklabs.com"
                cand_data = {
                    "job_id": selected_job['id'],
                    "name": uploaded_file.name, 
                    "email": final_email,
                    "resume_url": resume_url,
                    "status": "AI Analysis in Progress" # <--- This is what you see in Dashboard
                }
                
                # Insert and get ID
                response = supabase.table("candidates").insert(cand_data).execute()
                new_row_id = response.data[0]['id']

                # D. TRIGGER N8N (FIRE AND FORGET)
                # We do NOT wait for the response. We just send it.
                payload = {
                    "candidate_id": new_row_id,
                    "resume_text": resume_text,
                    "resume_url": resume_url,
                    "job_id": selected_job['id']
                }
                try:
                    # timeout=1 ensures we don't hang if n8n is slow to acknowledge
                    requests.post(N8N_WEBHOOK, json=payload, timeout=2) 
                except requests.exceptions.ReadTimeout:
                    pass # This is expected behavior for "Fire and Forget"
                except Exception as e:
                    print(f"Webhook error: {e}")

            except Exception as e:
                st.error(f"❌ Error on {uploaded_file.name}: {e}")
            
            # Update Bar
            progress_bar.progress((i + 1) / len(uploaded_files))
            
        status_text.text("✅ Uploads Sent to AI Queue!")
        st.balloons()
        st.success(f"Sent {len(uploaded_files)} resumes to the AI Agent.")
        
        # Direct them to where the action is
        st.info("👉 Head over to the **Analysis Dashboard** to watch the scores update in real-time!")
        
        time.sleep(2)
        st.switch_page("6_🔍_Candidate_Analysis.py") # Auto-redirect to the dashboard