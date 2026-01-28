import streamlit as st
from supabase import create_client
from styles import load_css
import pdfplumber
import docx

st.set_page_config(page_title="Job Manager", layout="wide")
load_css()

# Connect DB
try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    st.error("Check your secrets.toml file.")
    st.stop()

st.title("📋 Job Posting Manager")

# --- HELPER FUNCTIONS ---
def read_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def read_docx(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

# --- SECTION 1: CREATE/EDIT JOB ---
with st.expander("➕ Create or Edit Job Posting", expanded=True):
    
    # 1. Document Upload for Auto-fill
    uploaded_jd = st.file_uploader("Optional: Auto-fill from JD", type=["pdf", "docx"])
    
    auto_title, auto_desc = "", ""
    
    if uploaded_jd:
        try:
            raw_text = read_pdf(uploaded_jd) if uploaded_jd.name.endswith(".pdf") else read_docx(uploaded_jd)
            lines = [l for l in raw_text.split('\n') if l.strip()]
            auto_title = lines[0].strip()[:60] if lines else ""
            auto_desc = raw_text
            st.success("✅ Document parsed!")
        except Exception as e:
            st.error(f"Error parsing document: {e}")

    st.divider()

    with st.form("job_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Job Title", value=auto_title)
            department = st.selectbox("Department", ["Engineering", "Marketing", "Sales", "HR", "Product", "Operations"])
        with col2:
            status = st.selectbox("Status", ["active", "draft", "closed"])
            
        description = st.text_area("Job Description", value=auto_desc, height=250, help="The AI will use this text to generate interview questions.")
        
        # We keep 'Requirements' as a separate field just for internal reference if needed
        requirements = st.text_area("Strict Requirements (Internal Reference)", height=100)

        submitted = st.form_submit_button("🚀 Save Job Role", type="primary")
        
        if submitted:
            if title and description:
                try:
                    data = {
                        "title": title,
                        "department": department,
                        "description": description,
                        "requirements": requirements,
                        "status": status
                    }
                    supabase.table("jobs").insert(data).execute()
                    st.success(f"Job '{title}' saved successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving to database: {e}")
            else:
                st.warning("Please provide at least a Job Title and Description.")

st.divider()

# --- SECTION 2: MANAGE JOBS ---
st.subheader("Manage Active Postings")

# Fetch jobs
response = supabase.table("jobs").select("*").order("created_at", desc=True).execute()

if response.data:
    for job in response.data:
        status_color = "🟢" if job['status'] == 'active' else "🟡" if job['status'] == 'draft' else "🔴"
        
        with st.expander(f"{status_color} {job['title']} ({job['department']})"):
            st.caption(f"Status: {job['status']} | Created: {job['created_at'][:10]}")
            st.text_area("Description Preview", job['description'], height=100, disabled=True, key=f"desc_{job['id']}")
            
            if st.button(f"Delete {job['title']}", key=f"del_{job['id']}", type="secondary"):
                supabase.table("jobs").delete().eq("id", job['id']).execute()
                st.rerun()
else:
    st.info("No jobs found. Create one above!")