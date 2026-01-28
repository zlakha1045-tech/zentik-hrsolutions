import streamlit as st
from supabase import create_client
from styles import load_css
import pdfplumber
import docx
import re 

st.set_page_config(page_title="Job Manager", layout="wide")
load_css()

# --- CONNECT DB ---
try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    st.error("Missing Supabase Secrets.")
    st.stop()

# --- SESSION STATE INITIALIZATION ---
# ADDED: 'job_status' and 'job_location' to this list so they don't disappear
defaults = ["job_title", "job_dept", "job_desc", "job_reqs", "job_id", "req_id_link", "job_status", "job_location"]
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

def parse_job_text(raw_text):
    """Splits text into Title, Description, and Requirements automatically."""
    lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
    title = lines[0] if lines else ""
    split_keywords = ["Strict Requirements", "Requirements", "Qualifications", "Skills & Experience", "Technical Skills"]
    desc_text = raw_text
    reqs_text = ""
    for keyword in split_keywords:
        if re.search(f"(?i){keyword}", raw_text):
            parts = re.split(f"(?i){keyword}", raw_text, maxsplit=1)
            if len(parts) > 1:
                desc_text = parts[0].strip()
                reqs_text = parts[1].strip()
                if not reqs_text.startswith("-") and not reqs_text.startswith("*"):
                    reqs_text = "- " + reqs_text.replace("\n", "\n- ")
                break
    return title, desc_text, reqs_text


st.title("📋 Job Posting Manager")
st.markdown("Create, Draft, and Publish job roles.")

# =========================================================
# 1. INPUT SOURCE SELECTION
# =========================================================
st.subheader("Step 1: Choose Source")
input_method = st.radio(
    "Source",
    ["🚀 From Approved MRF", "📂 Upload Job Description", "✍️ Manual Entry"],
    horizontal=True,
    label_visibility="collapsed"
)

st.divider()

if input_method == "🚀 From Approved MRF":
    try:
        mrfs = supabase.table("requisitions").select("*").eq("status", "Approved").order("created_at", desc=True).execute().data
        if not mrfs:
            st.warning("No Approved MRFs found.")
        else:
            mrf_map = {f"{m['job_title']} (Req by: {m['requisitor_name']})": m for m in mrfs}
            selected_mrf_label = st.selectbox("Select Requisition", list(mrf_map.keys()))
            
            if st.button("⬇️ Load Data from MRF"):
                m_data = mrf_map[selected_mrf_label]
                st.session_state.job_title = m_data['job_title']
                st.session_state.job_dept = m_data['requisitor_dept']
                st.session_state.job_desc = m_data.get('responsibilities', '')
                st.session_state.job_reqs = f"- Education: {m_data.get('education_req')}\n- Skills: {m_data.get('skills_req')}\n- Experience: {m_data.get('experience_req')}"
                st.session_state.req_id_link = m_data['id']
                st.session_state.job_id = "" 
                st.session_state.job_status = "Draft"
                st.session_state.job_location = "Headquarters"
                st.toast("Data Loaded from MRF!", icon="✅")
    except Exception as e:
        st.error(f"Error: {e}")

elif input_method == "📂 Upload Job Description":
    uploaded_file = st.file_uploader("Upload JD", type=["pdf", "docx"])
    if uploaded_file:
        if st.button("⬇️ Parse & Load"):
            try:
                raw_text = read_pdf(uploaded_file) if uploaded_file.name.endswith(".pdf") else read_docx(uploaded_file)
                p_title, p_desc, p_reqs = parse_job_text(raw_text)
                
                st.session_state.job_title = p_title
                st.session_state.job_desc = p_desc
                st.session_state.job_reqs = p_reqs
                st.session_state.req_id_link = "" 
                st.session_state.job_id = "" 
                st.session_state.job_status = "Draft"
                st.session_state.job_location = "Headquarters"
                st.toast("Parsed!", icon="✅")
            except Exception as e:
                st.error(f"Error parsing: {e}")

elif input_method == "✍️ Manual Entry":
    if st.button("🔄 Reset / Clear Form"):
        clear_form()

# =========================================================
# 2. THE EDITOR
# =========================================================
st.subheader("Step 2: Review & Publish")

with st.form("job_editor_form"):
    c1, c2 = st.columns(2)
    
    title = c1.text_input("Job Title", value=st.session_state.job_title)
    
    depts = ["Engineering", "Marketing", "Sales", "HR", "Operations", "Finance", "Legal"]
    curr_dept = st.session_state.job_dept if st.session_state.job_dept in depts else depts[0]
    department = c1.selectbox("Department", depts, index=depts.index(curr_dept))
    
    # FIX: Status now respects the Edit button
    status_opts = ["Draft", "Active", "Closed"]
    curr_status = st.session_state.job_status if st.session_state.job_status in status_opts else "Draft"
    status = c2.selectbox("Status", status_opts, index=status_opts.index(curr_status))
    
    # FIX: Location now respects the Edit button
    loc_val = st.session_state.job_location if st.session_state.job_location else "Headquarters"
    location = c2.text_input("Location", value=loc_val)

    st.markdown("### 🤖 AI Requirements")
    requirements = st.text_area("Strict Requirements", value=st.session_state.job_reqs, height=150)

    st.markdown("### 📄 Job Description")
    description = st.text_area("Full Description", value=st.session_state.job_desc, height=250)

    job_id_tracker = st.session_state.job_id 

    submitted = st.form_submit_button("💾 Save Job Posting", type="primary")

    if submitted:
        if not title or not requirements:
            st.warning("Job Title and Requirements are required.")
        else:
            job_data = {
                "title": title, "department": department, "status": status,
                "location": location, "requirements": requirements,
                "description": description,
                "requisition_id": st.session_state.req_id_link if st.session_state.req_id_link else None
            }
            try:
                if job_id_tracker:
                    supabase.table("jobs").update(job_data).eq("id", job_id_tracker).execute()
                    st.success(f"Job '{title}' Updated!")
                else:
                    supabase.table("jobs").insert(job_data).execute()
                    st.success(f"Job '{title}' Created!")
                clear_form()
                st.rerun()
            except Exception as e:
                st.error(f"Database Error: {e}")

# =========================================================
# 3. MANAGE EXISTING JOBS
# =========================================================
st.divider()
st.subheader("📂 Job History & Management")

try:
    jobs_response = supabase.table("jobs").select("*").order("created_at", desc=True).execute()
    
    if jobs_response.data:
        for job in jobs_response.data:
            # Color coding
            color = "green" if job['status'] == "Active" else "orange" if job['status'] == "Draft" else "red"
            
            with st.expander(f":{color}[{job['status']}] {job['title']} ({job.get('department', 'General')})"):
                
                # DETAILS ROW
                c_det1, c_det2 = st.columns(2)
                c_det1.caption(f"📍 {job.get('location', '-')}")
                c_det2.caption(f"📅 {job['created_at'][:10]}")

                # ACTION ROW
                st.markdown("---")
                c_act1, c_act2, c_act3, c_act4 = st.columns(4)
                
                # 1. EDIT BUTTON
                if c_act1.button("✏️ Edit Full", key=f"edit_{job['id']}"):
                    st.session_state.job_title = job['title']
                    st.session_state.job_dept = job.get('department', '')
                    st.session_state.job_desc = job.get('description', '')
                    st.session_state.job_reqs = job.get('requirements', '')
                    st.session_state.job_id = job['id']
                    st.session_state.req_id_link = job.get('requisition_id')
                    
                    # FIX: Save Status and Location to session state so they appear in the form
                    st.session_state.job_status = job.get('status', 'Draft')
                    st.session_state.job_location = job.get('location', 'Headquarters')
                    
                    st.toast("Job Loaded into Form!", icon="⬆️")
                    st.rerun()

                # 2. QUICK ACTIVATE
                if job['status'] != "Active":
                    if c_act2.button("🚀 Go Active", key=f"act_{job['id']}"):
                        supabase.table("jobs").update({"status": "Active"}).eq("id", job['id']).execute()
                        st.rerun()
                else:
                    if c_act2.button("⏸️ Set Draft", key=f"dft_{job['id']}"):
                        supabase.table("jobs").update({"status": "Draft"}).eq("id", job['id']).execute()
                        st.rerun()

                # 3. CLOSE JOB
                if job['status'] != "Closed":
                    if c_act3.button("🚫 Close Job", key=f"cls_{job['id']}"):
                         supabase.table("jobs").update({"status": "Closed"}).eq("id", job['id']).execute()
                         st.rerun()

                # 4. DELETE
                if c_act4.button("🗑️ Delete", key=f"del_{job['id']}"):
                    supabase.table("jobs").delete().eq("id", job['id']).execute()
                    st.rerun()
    else:
        st.info("No jobs found.")
except:
    pass