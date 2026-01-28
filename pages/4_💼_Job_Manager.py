import streamlit as st
from supabase import create_client
from styles import load_css
import pdfplumber
import docx

st.set_page_config(page_title="Job Manager", layout="wide")
load_css()

# --- CONNECT DB ---
try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    st.error("Missing Supabase Secrets.")
    st.stop()

# --- SESSION STATE INITIALIZATION ---
# We use this to hold the data for the form, regardless of where it came from (MRF, File, or Manual)
defaults = ["job_title", "job_dept", "job_desc", "job_reqs", "job_id", "req_id_link"]
for key in defaults:
    if key not in st.session_state:
        st.session_state[key] = ""

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

def clear_form():
    for key in defaults:
        st.session_state[key] = ""

st.title("📋 Job Posting Manager")
st.markdown("Create, Draft, and Publish job roles. Select a source below to pre-fill the posting.")

# =========================================================
# 1. INPUT SOURCE SELECTION (The 3 Paths)
# =========================================================

# We use columns to make the selection look like a dashboard
st.subheader("Step 1: Choose Source")
input_method = st.radio(
    "How would you like to draft this job?",
    ["🚀 From Approved MRF", "📂 Upload Job Description", "✍️ Manual Entry"],
    horizontal=True,
    label_visibility="collapsed"
)

st.divider()

# --- LOGIC: PATH 1 (FROM MRF) ---
if input_method == "🚀 From Approved MRF":
    st.info("Select an Approved Manpower Requisition to auto-fill the job details.")
    
    # Fetch Approved MRFs that are NOT yet linked to a job (optional filter)
    try:
        # Get MRFs
        mrfs = supabase.table("requisitions").select("*").eq("status", "Approved").order("created_at", desc=True).execute().data
        
        if not mrfs:
            st.warning("No Approved MRFs found.")
        else:
            # Create a map for the dropdown
            mrf_map = {f"{m['job_title']} (Req by: {m['requisitor_name']})": m for m in mrfs}
            selected_mrf_label = st.selectbox("Select Requisition", list(mrf_map.keys()))
            
            # Load Button
            if st.button("⬇️ Load Data from MRF"):
                m_data = mrf_map[selected_mrf_label]
                
                # Pre-fill Session State
                st.session_state.job_title = m_data['job_title']
                st.session_state.job_dept = m_data['requisitor_dept']
                st.session_state.job_desc = m_data.get('responsibilities', '')
                # Combine distinct MRF fields into one "Strict Requirements" block for AI
                st.session_state.job_reqs = f"- Education: {m_data.get('education_req')}\n- Skills: {m_data.get('skills_req')}\n- Experience: {m_data.get('experience_req')}"
                st.session_state.req_id_link = m_data['id']
                st.session_state.job_id = "" # Clear ID to ensure it creates a NEW job
                
                st.toast("Data Loaded from MRF!", icon="✅")
                
    except Exception as e:
        st.error(f"Error fetching MRFs: {e}")

# --- LOGIC: PATH 2 (FROM FILE) ---
elif input_method == "📂 Upload Job Description":
    st.info("Upload a PDF or Word doc. We will extract the text to populate the Description.")
    uploaded_file = st.file_uploader("Upload JD", type=["pdf", "docx"])
    
    if uploaded_file:
        if st.button("⬇️ Parse & Load"):
            try:
                raw_text = read_pdf(uploaded_file) if uploaded_file.name.endswith(".pdf") else read_docx(uploaded_file)
                
                # Basic parsing logic
                lines = [l for l in raw_text.split('\n') if l.strip()]
                extracted_title = lines[0].strip()[:60] if lines else ""
                
                st.session_state.job_title = extracted_title
                st.session_state.job_desc = raw_text
                st.session_state.job_reqs = "Extracting requirements from description..." # Placeholder
                st.session_state.req_id_link = "" # No MRF link
                st.session_state.job_id = "" 
                
                st.toast("Document Parsed!", icon="✅")
            except Exception as e:
                st.error(f"Error parsing file: {e}")

# --- LOGIC: PATH 3 (MANUAL) ---
elif input_method == "✍️ Manual Entry":
    if st.button("🔄 Reset / Clear Form"):
        clear_form()
        st.toast("Form Cleared", icon="🧹")

# =========================================================
# 2. THE EDITOR (Unified Form)
# =========================================================
st.subheader("Step 2: Review & Publish")

with st.form("job_editor_form"):
    c1, c2 = st.columns(2)
    
    # We use session_state for 'value' so it updates when "Load" is clicked above
    title = c1.text_input("Job Title", value=st.session_state.job_title)
    
    # Department handling
    depts = ["Engineering", "Marketing", "Sales", "HR", "Operations", "Finance", "Legal"]
    # If MRF has a weird dept, add it to list or default to 0
    curr_dept = st.session_state.job_dept if st.session_state.job_dept in depts else depts[0]
    department = c1.selectbox("Department", depts, index=depts.index(curr_dept))
    
    status = c2.selectbox("Status", ["Draft", "Active", "Closed"])
    location = c2.text_input("Location", value="Headquarters")

    st.markdown("### 🤖 AI Requirements")
    st.caption("Crucial: The AI uses this section to score candidates (0-100%). Bullet points are best.")
    requirements = st.text_area("Strict Requirements", value=st.session_state.job_reqs, height=150)

    st.markdown("### 📄 Job Description")
    description = st.text_area("Full Description (Public)", value=st.session_state.job_desc, height=250)

    # Hidden ID field to track if we are updating an existing job or creating new
    job_id_tracker = st.session_state.job_id 

    # SUBMIT
    submitted = st.form_submit_button("💾 Save Job Posting", type="primary")

    if submitted:
        if not title or not requirements:
            st.warning("Job Title and Requirements are required.")
        else:
            job_data = {
                "title": title,
                "department": department,
                "status": status,
                "location": location,
                "requirements": requirements,
                "description": description,
                "requisition_id": st.session_state.req_id_link if st.session_state.req_id_link else None
            }
            
            try:
                if job_id_tracker:
                    # UPDATE Existing
                    supabase.table("jobs").update(job_data).eq("id", job_id_tracker).execute()
                    st.success(f"Job '{title}' Updated!")
                else:
                    # INSERT New
                    supabase.table("jobs").insert(job_data).execute()
                    st.success(f"Job '{title}' Created!")
                
                # Clear form after save
                clear_form()
                st.rerun()
                
            except Exception as e:
                st.error(f"Database Error: {e}")

# =========================================================
# 3. MANAGE EXISTING JOBS
# =========================================================
st.divider()
st.subheader("📂 Job History & Management")

# Fetch all jobs
jobs_response = supabase.table("jobs").select("*").order("created_at", desc=True).execute()

if jobs_response.data:
    for job in jobs_response.data:
        # Status Badge
        color = "green" if job['status'] == "Active" else "orange" if job['status'] == "Draft" else "red"
        
        with st.expander(f":{color}[{job['status']}] {job['title']} ({job.get('department', 'General')})"):
            c_info, c_act = st.columns([3, 1])
            
            with c_info:
                st.caption(f"Posted: {job['created_at'][:10]} | ID: {job['id']}")
                st.write(job.get('requirements', '')[:150] + "...")
            
            with c_act:
                # EDIT BUTTON
                if st.button("✏️ Edit", key=f"edit_{job['id']}"):
                    # Populate session state with this job's data
                    st.session_state.job_title = job['title']
                    st.session_state.job_dept = job.get('department', '')
                    st.session_state.job_desc = job.get('description', '')
                    st.session_state.job_reqs = job.get('requirements', '')
                    st.session_state.job_id = job['id'] # Important: Set ID so we update, not create
                    st.session_state.req_id_link = job.get('requisition_id')
                    st.toast("Job Loaded into Editor!", icon="⬆️")
                    st.rerun()

                # DELETE BUTTON
                if st.button("🗑️ Delete", key=f"del_{job['id']}"):
                    supabase.table("jobs").delete().eq("id", job['id']).execute()
                    st.error("Job Deleted.")
                    st.rerun()
else:
    st.info("No jobs found.")