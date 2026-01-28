import streamlit as st
from supabase import create_client
from styles import load_css, hero_section
import time
import mimetypes

st.set_page_config(page_title="Create Requisition", layout="wide")
load_css()

try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    st.error("Missing Supabase Secrets.")
    st.stop()

# --- HELPER: GENERATE PRINTABLE HTML (Same as before) ---
def generate_mrf_html(data):
    # (Reuse the HTML generation code I gave you in the previous response)
    # For brevity, imagine the HTML string generator is here
    # ...
    return f"""<div style="font-family: Arial; padding: 20px; border: 1px solid black;">
    <h1>ZentikLabs MRF</h1>
    <p><strong>Role:</strong> {data.get('job_title')}</p>
    <p><strong>Dept:</strong> {data.get('requisitor_dept')}</p>
    <p><strong>Reason:</strong> {data.get('recruitment_type')}</p>
    <hr>
    <p><em>Signatures Required Below</em></p>
    <br><br><br>
    </div>""" 

hero_section("assets/login_hero.jpg", "MRF Creator", "Start the hiring process by creating a Manpower Requisition.")

st.subheader("📝 New Manpower Requisition")
st.caption("Fill out the details to request a new hire. Once approved, this will become a Job Posting.")

# --- THE FORM ---
with st.form("new_mrf_form"):
    st.markdown("### 🏢 Requisitor Info")
    c1, c2, c3 = st.columns(3)
    req_name = c1.text_input("Requisitor Name")
    req_dept = c2.text_input("Department")
    req_ext  = c3.text_input("Tel / Ext")

    st.markdown("### 👷 Position Details")
    r1, r2, r3, r4 = st.columns(4)
    job_title = r1.text_input("Job Title")
    shift     = r2.text_input("Shift", value="Day")
    num_req   = r3.number_input("No. Required", min_value=1, value=1)
    date_req  = r4.date_input("Date Required")

    st.markdown("### ✅ Classification")
    cl1, cl2 = st.columns(2)
    with cl1:
        rec_type = st.radio("Recruitment Type", ["Additional Position", "Replacement"])
        rep_reason = st.text_input("If Replacement, Reason:") if rec_type == "Replacement" else None
    with cl2:
        emp_nature = st.radio("Employment Nature", ["Full-time", "Part-time", "Contract"])
        source     = st.radio("Source", ["Within", "Outside", "Both"])

    st.markdown("### 🎓 Requirements")
    edu_req    = st.text_area("Education Required")
    skills_req = st.text_area("Skills Required")
    exp_req    = st.text_area("Experience Required")
    resp       = st.text_area("Key Responsibilities")
    
    # Hidden draft state for the preview
    submitted_draft = st.form_submit_button("👀 Preview & Generate PDF")

# --- PREVIEW SECTION ---
if submitted_draft:
    st.divider()
    st.subheader("📄 Preview & Download")
    
    mrf_data = {
        "job_title": job_title, "requisitor_dept": req_dept, 
        "recruitment_type": rec_type, "requisitor_name": req_name,
        # ... pass all fields ...
    }
    
    c_view, c_upload = st.columns(2)
    
    with c_view:
        # Show the "Paper"
        st.info("Step 1: Print this, Sign it, Scan it.")
        st.components.v1.html(generate_mrf_html(mrf_data), height=400, scrolling=True)
    
    with c_upload:
        st.info("Step 2: Upload the Signed PDF")
        signed_file = st.file_uploader("Upload Signed MRF", type=["pdf", "jpg", "png"])
        
        if st.button("🚀 Submit Requisition", type="primary"):
            if signed_file:
                try:
                    # 1. Upload File
                    file_ext = signed_file.name.split('.')[-1]
                    path = f"requisitions/{int(time.time())}_{job_title}.{file_ext}"
                    mime = mimetypes.guess_type(signed_file.name)[0]
                    
                    supabase.storage.from_("resumes").upload(
                        path, signed_file.getvalue(), {"content-type": mime}
                    )
                    url = supabase.storage.from_("resumes").get_public_url(path)
                    
                    # 2. Save to DB
                    mrf_record = {
                        "job_title": job_title,
                        "requisitor_name": req_name,
                        "requisitor_dept": req_dept,
                        "requisitor_ext": req_ext,
                        "shift": shift,
                        "number_required": num_req,
                        "date_required": str(date_req),
                        "recruitment_type": rec_type,
                        "replacement_reason": rep_reason,
                        "employment_nature": emp_nature,
                        "hiring_source": source,
                        "education_req": edu_req,
                        "skills_req": skills_req,
                        "experience_req": exp_req,
                        "responsibilities": resp,
                        "signed_mrf_url": url,
                        "status": "Pending Approval"
                    }
                    
                    supabase.table("requisitions").insert(mrf_record).execute()
                    
                    st.balloons()
                    st.success("Requisition Submitted! It is now pending Management Approval.")
                    time.sleep(2)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Please upload the signed document.")