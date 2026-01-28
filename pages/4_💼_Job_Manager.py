import streamlit as st
from supabase import create_client
from styles import load_css
import pdfplumber
import docx
import re 

st.set_page_config(page_title="Job Manager", layout="wide")
load_css()

# --- 1. CONNECT DB & INIT STATE ---
try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    st.error("Missing Supabase Secrets.")
    st.stop()

# Initialize Session State Keys if they don't exist
# We bind these keys directly to the widgets later
defaults = {
    "job_title": "",
    "job_dept": "Engineering", # Default valid option
    "job_desc": "",
    "job_reqs": "",
    "job_status": "Draft",
    "job_location": "Headquarters",
    "job_id": "",         # Hidden tracker
    "req_id_link": ""     # Hidden tracker
}

for key, default_val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default_val

# --- 2. CALLBACK FUNCTIONS (The Fix for Double Click) ---
# These run BEFORE the app reloads, ensuring instant UI updates

def load_job_into_form(job):
    """Callback: specific for the EDIT button"""
    st.session_state.job_title = job['title']
    # Ensure department is valid, else default
    valid_depts = ["Engineering", "Marketing", "Sales", "HR", "Operations", "Finance", "Legal"]
    dept = job.get('department', 'Engineering')
    st.session_state.job_dept = dept if dept in valid_depts else "Engineering"
    
    st.session_state.job_desc = job.get('description', '')
    st.session_state.job_reqs = job.get('requirements', '')
    st.session_state.job_id = job['id']
    st.session_state.req_id_link = job.get('requisition_id')
    st.session_state.job_status = job.get('status', 'Draft')
    st.session_state.job_location = job.get('location', 'Headquarters')
    # No st.toast here to avoid UI clutter on rerun, but you can add it if you want.

def update_status_callback(job_id, new_status):
    """Callback: Updates DB directly"""
    supabase.table("jobs").update({"status": new_status}).eq("id", job_id).execute()

def delete_job_callback(job_id):
    """Callback: Deletes from DB"""
    supabase.table("jobs").delete().eq("id", job_id).execute()

def clear_form_callback():
    """Callback: Resets form"""
    for k, v in defaults.items():
        st.session_state[k] = v


# --- 3. HELPER FUNCTIONS ---
def read_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def read_docx(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def parse_job_text(raw_text):
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
# STEP 1: CHOOSE SOURCE
# =========================================================
st.subheader("Step 1: Choose Source")
input_method = st.radio("Source", ["🚀 From Approved MRF", "📂 Upload Job Description", "✍️ Manual Entry"], horizontal=True, label_visibility="collapsed")
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
                st.toast("Data Loaded!", icon="✅")
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
                st.session_state.job_id = ""
                st.session_state.job_status = "Draft"
                st.toast("Parsed!", icon="✅")
            except Exception as e:
                st.error(f"Error parsing: {e}")

elif input_method == "✍️ Manual Entry":
    st.button("🔄 Reset / Clear Form", on_click=clear_form_callback)


# =========================================================
# STEP 2: THE EDITOR (Bound to Session State)
# =========================================================
st.subheader("Step 2: Review & Publish")

with st.form("job_editor_form"):
    c1, c2 = st.columns(2)
    
    # KEY CHANGE: using key=... binds the widget directly to session state
    title = c1.text_input("Job Title", key="job_title")
    
    depts = ["Engineering", "Marketing", "Sales", "HR", "Operations", "Finance", "Legal"]
    department = c1.selectbox("Department", depts, key="job_dept")
    
    status_opts = ["Draft", "Active", "Closed"]
    status = c2.selectbox("Status", status_opts, key="job_status")
    
    location = c2.text_input("Location", key="job_location")

    st.markdown("### 🤖 AI Requirements")
    requirements = st.text_area("Strict Requirements", key="job_reqs", height=150)

    st.markdown("### 📄 Job Description")
    description = st.text_area("Full Description", key="job_desc", height=250)

    submitted = st.form_submit_button("💾 Save Job Posting", type="primary")

    if submitted:
        if not st.session_state.job_title or not st.session_state.job_reqs:
            st.warning("Job Title and Requirements are required.")
        else:
            job_data = {
                "title": st.session_state.job_title,
                "department": st.session_state.job_dept,
                "status": st.session_state.job_status,
                "location": st.session_state.job_location,
                "requirements": st.session_state.job_reqs,
                "description": st.session_state.job_desc,
                "requisition_id": st.session_state.req_id_link if st.session_state.req_id_link else None
            }
            try:
                # Decide Insert vs Update based on hidden ID
                if st.session_state.job_id:
                    supabase.table("jobs").update(job_data).eq("id", st.session_state.job_id).execute()
                    st.success(f"Job Updated!")
                else:
                    supabase.table("jobs").insert(job_data).execute()
                    st.success(f"Job Created!")
                
                # Optional: Clear form after save
                # clear_form_callback() 
                # st.rerun() 
            except Exception as e:
                st.error(f"Database Error: {e}")

# =========================================================
# STEP 3: JOB HISTORY (Using Callbacks)
# =========================================================
st.divider()
st.subheader("📂 Job History & Management")

try:
    jobs_response = supabase.table("jobs").select("*").order("created_at", desc=True).execute()
    
    if jobs_response.data:
        for job in jobs_response.data:
            color = "green" if job['status'] == "Active" else "orange" if job['status'] == "Draft" else "red"
            
            with st.expander(f":{color}[{job['status']}] {job['title']} ({job.get('department', 'General')})"):
                
                c_det1, c_det2 = st.columns(2)
                c_det1.caption(f"📍 {job.get('location', '-')}")
                c_det2.caption(f"📅 {job['created_at'][:10]}")

                st.markdown("---")
                c_act1, c_act2, c_act3, c_act4 = st.columns(4)
                
                # 1. EDIT (Uses Callback) - Single Click!
                c_act1.button("✏️ Edit Full", key=f"edit_{job['id']}", 
                              on_click=load_job_into_form, args=(job,))

                # 2. QUICK ACTIVE (Uses Callback) - Single Click!
                if job['status'] != "Active":
                    c_act2.button("🚀 Go Active", key=f"act_{job['id']}",
                                  on_click=update_status_callback, args=(job['id'], "Active"))
                else:
                    c_act2.button("⏸️ Set Draft", key=f"dft_{job['id']}",
                                  on_click=update_status_callback, args=(job['id'], "Draft"))

                # 3. CLOSE (Uses Callback)
                if job['status'] != "Closed":
                    c_act3.button("🚫 Close Job", key=f"cls_{job['id']}",
                                  on_click=update_status_callback, args=(job['id'], "Closed"))

                # 4. DELETE (Uses Callback)
                c_act4.button("🗑️ Delete", key=f"del_{job['id']}",
                              on_click=delete_job_callback, args=(job['id'],))
    else:
        st.info("No jobs found.")
except Exception as e:
    st.error(f"Error loading jobs: {e}")