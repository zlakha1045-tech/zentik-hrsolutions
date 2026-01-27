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
    
    # Session State to hold questions during the editing process
    if 'current_questions' not in st.session_state:
        st.session_state.current_questions = ""

    auto_title, auto_desc, auto_reqs = "", "", ""
    
    if uploaded_jd:
        try:
            raw_text = read_pdf(uploaded_jd) if uploaded_jd.name.endswith(".pdf") else read_docx(uploaded_jd)
            lines = [l for l in raw_text.split('\n') if l.strip()]
            auto_title = lines[0].strip()[:60] if lines else ""
            auto_desc = raw_text
            st.success("✅ Document parsed!")
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()

    with st.form("job_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Job Title", value=auto_title)
            department = st.selectbox("Department", ["Engineering", "Marketing", "Sales", "HR", "Product", "Operations"])
        with col2:
            status = st.selectbox("Status", ["active", "draft", "closed"])
            
        description = st.text_area("Job Description", value=auto_desc, height=150)
        requirements = st.text_area("Strict Requirements (Internal Reference)", value=auto_reqs, height=100)

        # --- THE QUESTION EDITOR ---
        st.markdown("### ❓ Screening Questionnaire Designer")
        st.caption("Edit, add, or delete questions below. Place each question on a NEW line.")
        
        # If the user enters requirements, we can provide a button to generate a draft
        # But we let them type directly into this box to OVERRIDE everything
        manual_questions = st.text_area(
            "Final Screening Questions", 
            value=st.session_state.current_questions,
            height=200,
            help="These are the actual questions sent to candidates. Editing this does NOT change your requirements text above."
        )
        
        c1, c2 = st.columns([1, 4])
        # Button to 'Suggest' questions from the requirements box
        if c1.form_submit_button("🪄 Draft from Reqs"):
            lines = [r.strip().replace("-", "").strip() for r in requirements.split('\n') if len(r.strip()) > 10]
            st.session_state.current_questions = "\n".join(lines)
            st.rerun()

        submitted = st.form_submit_button("🚀 Save Job & Questionnaire", type="primary")
        
        if submitted:
            if title and description:
                # Turn the text area back into a list for the database
                q_list = [q.strip() for q in manual_questions.split('\n') if q.strip()]
                
                try:
                    data = {
                        "title": title,
                        "department": department,
                        "description": description,
                        "requirements": requirements,
                        "status": status,
                        "screening_questions": q_list
                    }
                    supabase.table("jobs").insert(data).execute()
                    st.success("Job and Custom Questionnaire saved!")
                    st.session_state.current_questions = "" # Reset
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

st.divider()

# --- SECTION 2: MANAGE JOBS ---
st.subheader("Manage Active Postings")
response = supabase.table("jobs").select("*").order("created_at", desc=True).execute()
for job in response.data:
    status_color = "🟢" if job['status'] == 'active' else "🟡" if job['status'] == 'draft' else "🔴"
    with st.expander(f"{status_color} {job['title']}"):
        # This ensures that even if Supabase returns None, we treat it as 0
        q_count = len(job.get('screening_questions') or [])
        st.write(f"**Questions Set:** {q_count}")
        if st.button(f"Delete {job['title']}", key=f"del_{job['id']}", type="primary"):
            supabase.table("jobs").delete().eq("id", job['id']).execute()
            st.rerun()