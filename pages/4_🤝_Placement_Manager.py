import streamlit as st
from supabase import create_client
from styles import load_css, hero_section
import time
import mimetypes

st.set_page_config(page_title="Placement Manager", layout="wide")
load_css()

try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    st.error("Missing Supabase Secrets.")
    st.stop()

# --- HELPER: GENERATE PRINTABLE HTML ---
def generate_mrf_html(data):
    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 40px; border: 1px solid #ccc; background: white; color: black; max-width: 800px; margin: auto;">
        <div style="text-align: center; margin-bottom: 20px;">
            <h1 style="margin: 0; color: #000;">ZentikLabs</h1>
            <h3 style="margin: 5px 0; text-transform: uppercase;">Manpower Requisition Form</h3>
        </div>
        
        <table style="width: 100%; border-collapse: collapse; border: 1px solid black;">
            <tr>
                <td style="padding: 10px; border: 1px solid black; width: 50%;">
                    <strong>Requisitor:</strong> {data.get('requisitor_name', '')}<br>
                    <strong>Dept:</strong> {data.get('requisitor_dept', '')} | <strong>Ext:</strong> {data.get('requisitor_ext', '')}
                </td>
                <td style="padding: 10px; border: 1px solid black;">
                    <strong>Date Required:</strong> {data.get('date_required', '')}<br>
                    <strong>No. Required:</strong> {data.get('number_required', '1')}
                </td>
            </tr>
            <tr>
                <td colspan="2" style="padding: 10px; border: 1px solid black;">
                    <strong>Job Title:</strong> {data.get('job_title', '')}<br>
                    <strong>Shift:</strong> {data.get('shift', 'General')}
                </td>
            </tr>
        </table>
        
        <div style="margin-top: 20px; border: 1px solid black; padding: 10px;">
            <strong>(A) Recruitment Type:</strong> {data.get('recruitment_type', '')} 
            {f"(Reason: {data.get('replacement_reason', '')})" if data.get('recruitment_type') == 'Replacement' else ''}<br>
            <strong>(B) Employment:</strong> {data.get('employment_nature', '')}<br>
            <strong>(C) Source:</strong> {data.get('hiring_source', '')}
        </div>
        
        <div style="margin-top: 20px;">
            <h4 style="border-bottom: 1px solid black;">QUALIFICATIONS REQUIRED</h4>
            <p><strong>Education:</strong> {data.get('education_req', '')}</p>
            <p><strong>Skills:</strong> {data.get('skills_req', '')}</p>
            <p><strong>Experience:</strong> {data.get('experience_req', '')}</p>
        </div>

        <div style="margin-top: 20px;">
            <h4 style="border-bottom: 1px solid black;">RESPONSIBILITIES</h4>
            <p>{data.get('responsibilities', '').replace('\n', '<br>')}</p>
        </div>

        <div style="margin-top: 40px; border-top: 1px solid black; padding-top: 10px; display: flex; justify-content: space-between;">
            <div>____________________<br>Requisitor Sign</div>
            <div>____________________<br>General Manager</div>
            <div>____________________<br>Managing Director</div>
        </div>
    </div>
    """
    return html

hero_section("assets/login_hero.jpg", "Placement & MRF Center", "Digital Requisition & Approval Workflow")

# --- STEP 1: SELECT CANDIDATE ---
st.subheader("1. Select Candidate")
try:
    # Filter for 'Pending Hire' OR 'Drafting MRF' (so you can save work later)
    response = supabase.table("placements").select(
        "*, candidates(name), jobs(title, department)"
    ).in_("status", ["Pending Hire", "Drafting MRF"]).execute()
    pending_list = response.data
except:
    pending_list = []

if not pending_list:
    st.info("✅ No pending placements.")
    st.stop()

placement_map = {f"{p['candidates']['name']} - {p['jobs']['title']}": p for p in pending_list}
selected_label = st.selectbox("Select Placement", list(placement_map.keys()))
p_data = placement_map[selected_label]
p_id = p_data['id']

# --- STEP 2: THE "ZENTIK" DIGITAL FORM ---
st.divider()
st.subheader("2. Manpower Requisition Details")

# Autofill existing data if available, else defaults
with st.form("zentik_mrf_form"):
    st.markdown("### 🏢 Requisitor Info")
    c1, c2, c3 = st.columns(3)
    req_name = c1.text_input("Requisitor Name", value=p_data.get('requisitor_name', ''))
    req_dept = c2.text_input("Department", value=p_data.get('requisitor_dept', p_data['jobs'].get('department', '')))
    req_ext  = c3.text_input("Tel / Ext", value=p_data.get('requisitor_ext', ''))

    st.markdown("### 👷 Manpower Required")
    r1, r2, r3, r4 = st.columns(4)
    job_title = r1.text_input("Job Title", value=p_data['jobs']['title'])
    shift     = r2.text_input("Shift", value=p_data.get('shift', 'Day'))
    num_req   = r3.text_input("No. Required", value=p_data.get('number_required', '1'))
    date_req  = r4.date_input("Date Required")

    st.markdown("### ✅ Classification")
    cl1, cl2 = st.columns(2)
    with cl1:
        rec_type = st.radio("Recruitment Type", ["Additional Position", "Replacement for..."])
        if rec_type == "Replacement for...":
            rep_reason = st.selectbox("Reason", ["Resignation", "Termination", "Promotion", "Transfer"])
        else:
            rep_reason = None
            
    with cl2:
        emp_nature = st.radio("Employment Nature", ["Full-time", "Part-time", "Temporary", "Contract"])
        source     = st.radio("Source", ["Within", "Outside"])

    st.markdown("### 🎓 Qualifications & Duties")
    edu_req  = st.text_area("Education", value=p_data.get('education_req', ''))
    skills_req = st.text_area("Skills", value=p_data.get('skills_req', ''))
    exp_req  = st.text_area("Experience", value=p_data.get('experience_req', ''))
    resp     = st.text_area("Areas of Responsibility", value=p_data.get('responsibilities', ''), height=150)
    remarks  = st.text_input("Remarks / Justification", value=p_data.get('remarks', ''))

    # ACTION BUTTONS
    f1, f2 = st.columns([1, 1])
    save_draft = f1.form_submit_button("💾 Save Draft")
    
    if save_draft:
        update_data = {
            "requisitor_name": req_name, "requisitor_dept": req_dept, "requisitor_ext": req_ext,
            "shift": shift, "number_required": num_req, "date_required": str(date_req),
            "recruitment_type": rec_type, "replacement_reason": rep_reason,
            "employment_nature": emp_nature, "hiring_source": source,
            "education_req": edu_req, "skills_req": skills_req, "experience_req": exp_req,
            "responsibilities": resp, "remarks": remarks,
            "status": "Drafting MRF"
        }
        supabase.table("placements").update(update_data).eq("id", p_id).execute()
        st.success("Draft Saved!")
        st.rerun()

# --- STEP 3: PREVIEW & SIGN & UPLOAD ---
st.divider()
st.subheader("3. Finalize & Sign")
c_preview, c_upload = st.columns([1, 1])

with c_preview:
    st.info("👇 **Step A:** Download or Print this form to get signatures.")
    # Prepare data dict for rendering
    render_data = {
        'requisitor_name': req_name, 'requisitor_dept': req_dept, 'requisitor_ext': req_ext,
        'job_title': job_title, 'shift': shift, 'number_required': num_req, 'date_required': date_req,
        'recruitment_type': rec_type, 'replacement_reason': rep_reason, 'employment_nature': emp_nature,
        'hiring_source': source, 'education_req': edu_req, 'skills_req': skills_req,
        'experience_req': exp_req, 'responsibilities': resp
    }
    
    # We use an expander to show the "Paper View"
    with st.expander("📄 View Printable ZentikLabs Form", expanded=True):
        html_content = generate_mrf_html(render_data)
        st.components.v1.html(html_content, height=600, scrolling=True)
        st.caption("💡 Right-click inside the white box > 'Print' > 'Save as PDF'")

with c_upload:
    st.info("👇 **Step B:** Upload the SIGNED form here to send for approval.")
    uploaded_signed = st.file_uploader("Upload Signed MRF (PDF/Image)", type=['pdf', 'jpg', 'png'])
    
    if st.button("🚀 Submit for Approval", type="primary"):
        if uploaded_signed:
            try:
                # Upload File
                file_ext = uploaded_signed.name.split('.')[-1]
                path = f"signed_mrf/{int(time.time())}_{p_id}.{file_ext}"
                mime = mimetypes.guess_type(uploaded_signed.name)[0]
                
                supabase.storage.from_("resumes").upload(
                    path, uploaded_signed.getvalue(), {"content-type": mime}
                )
                url = supabase.storage.from_("resumes").get_public_url(path)
                
                # Update Status
                supabase.table("placements").update({
                    "signed_mrf_url": url,
                    "status": "Pending Approval"
                }).eq("id", p_id).execute()
                
                st.balloons()
                st.success("Signed MRF Submitted! Sent to Management.")
                time.sleep(2)
                st.rerun()
            except Exception as e:
                st.error(f"Upload failed: {e}")
        else:
            st.warning("Please upload the signed document first.")