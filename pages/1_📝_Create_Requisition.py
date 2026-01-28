import streamlit as st
from supabase import create_client
from styles import load_css, hero_section
from fpdf import FPDF
import time
import mimetypes
import io

st.set_page_config(page_title="Create Requisition", layout="wide")
load_css()

try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    st.error("Missing Supabase Secrets.")
    st.stop()

# --- HELPER: CLEAN TEXT FOR PDF ---
def clean_text(text):
    if not text:
        return ""
    # 1. Replace common "smart" characters with standard ones
    replacements = {
        '\u2018': "'", '\u2019': "'",  # Smart single quotes
        '\u201c': '"', '\u201d': '"',  # Smart double quotes
        '\u2013': '-', '\u2014': '-',  # Dashes
        '\u2022': '*',                 # Bullet points
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # 2. Force encoding to Latin-1 (removes emojis/weird symbols)
    return text.encode('latin-1', 'replace').decode('latin-1')

# --- PDF GENERATOR CLASS ---
class MRF_PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'ZentikLabs', 0, 1, 'C')
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Manpower Requisition Form', 0, 1, 'C')
        self.ln(5)

    def section_title(self, title):
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(240, 240, 240)
        self.cell(0, 8, title, 1, 1, 'L', fill=True)

    def draw_form(self, data):
        self.add_page()
        self.set_font('Arial', '', 10)

        # 1. OFFICIAL USE BOX
        self.set_font('Arial', 'I', 8)
        self.multi_cell(0, 5, "Note: This MRF is to be used for Non-exempt and Exempt positions only. Please complete thoroughly.\nAll MRFs must be approved by General Manager/Managing Director before submission to HR.", 1)
        self.ln(2)

        # 2. REQUISITOR
        self.section_title("REQUISITOR")
        self.set_font('Arial', '', 10)
        
        # Row 1
        self.cell(40, 10, "Name:", border='LBT')
        self.cell(150, 10, clean_text(data.get('requisitor_name', '')), border='RBT', ln=1)
        # Row 2
        self.cell(40, 10, "Department:", border='LBT')
        self.cell(80, 10, clean_text(data.get('requisitor_dept', '')), border='BT')
        self.cell(30, 10, "Tel/Ext:", border='BT')
        self.cell(40, 10, clean_text(data.get('requisitor_ext', '')), border='RBT', ln=1)
        self.ln(2)

        # 3. MANPOWER REQUIRED
        self.section_title("MANPOWER REQUIRED")
        # Row 1
        self.cell(40, 10, "Job Title:", border='LBT')
        self.cell(80, 10, clean_text(data.get('job_title', '')), border='BT')
        self.cell(20, 10, "Shift:", border='BT')
        self.cell(50, 10, clean_text(data.get('shift', '')), border='RBT', ln=1)
        # Row 2
        self.cell(40, 10, "Number Required:", border='LBT')
        self.cell(80, 10, str(data.get('number_required', '')), border='BT')
        self.cell(30, 10, "Date Required:", border='BT')
        self.cell(40, 10, str(data.get('date_required', '')), border='RBT', ln=1)
        self.ln(2)

        # 4. CLASSIFICATION
        self.section_title("CLASSIFICATION")
        
        # A. Recruitment Type
        rtype = clean_text(data.get('recruitment_type', ''))
        self.cell(10, 8, "(A)", 0, 0)
        self.cell(50, 8, f"[{'X' if 'Additional' in rtype else ' '}] Additional Position", 0, 0)
        self.cell(60, 8, f"[{'X' if 'Replacement' in rtype else ' '}] Replacement", 0, 0)
        self.cell(0, 8, f"Reason: {clean_text(data.get('replacement_reason', 'N/A'))}", 0, 1)

        # B. Employment
        enature = clean_text(data.get('employment_nature', ''))
        self.cell(10, 8, "(B)", 0, 0)
        self.cell(50, 8, f"[{'X' if 'Full-time' in enature else ' '}] Full-time", 0, 0)
        self.cell(50, 8, f"[{'X' if 'Part-time' in enature else ' '}] Part-time", 0, 0)
        self.cell(50, 8, f"[{'X' if 'Contract' in enature else ' '}] Contract", 0, 1)

        # C. Source
        src = clean_text(data.get('hiring_source', ''))
        self.cell(10, 8, "(C)", 0, 0)
        self.cell(50, 8, f"[{'X' if 'Within' in src else ' '}] Within Company", 0, 0)
        self.cell(50, 8, f"[{'X' if 'Outside' in src else ' '}] Outside", 0, 1)
        self.ln(2)

        # 5. QUALIFICATIONS (Used Multi-cell here, this is where it crashed before)
        self.section_title("QUALIFICATIONS REQUIRED")
        
        self.set_font('Arial', 'B', 9)
        self.cell(0, 6, "Education:", 0, 1)
        self.set_font('Arial', '', 9)
        self.multi_cell(0, 6, clean_text(data.get('education_req', '')), 1)
        
        self.set_font('Arial', 'B', 9)
        self.cell(0, 6, "Skills:", 0, 1)
        self.set_font('Arial', '', 9)
        self.multi_cell(0, 6, clean_text(data.get('skills_req', '')), 1)
        
        self.set_font('Arial', 'B', 9)
        self.cell(0, 6, "Experience:", 0, 1)
        self.set_font('Arial', '', 9)
        self.multi_cell(0, 6, clean_text(data.get('experience_req', '')), 1)
        self.ln(2)

        # 6. RESPONSIBILITIES
        self.section_title("AREAS OF RESPONSIBILITY")
        self.set_font('Arial', '', 9)
        self.multi_cell(0, 6, clean_text(data.get('responsibilities', '')), 1)
        self.ln(5)

        # 7. APPROVALS
        self.section_title("APPROVALS")
        self.ln(15) 
        
        y = self.get_y()
        self.line(10, y, 70, y)
        self.line(80, y, 140, y)
        self.line(150, y, 200, y)
        
        self.cell(60, 5, "Requisitor Signature", 0, 0, 'C')
        self.cell(10, 5, "", 0, 0)
        self.cell(60, 5, "General Manager", 0, 0, 'C')
        self.cell(10, 5, "", 0, 0)
        self.cell(50, 5, "Managing Director", 0, 1, 'C')


# --- MAIN APP LOGIC ---
hero_section("assets/login_hero.jpg", "MRF Creator", "Start the hiring process by creating a Manpower Requisition.")

st.subheader("📝 New Manpower Requisition")
st.caption("Fill out the details to request a new hire. Once approved, this will become a Job Posting.")

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
    resp       = st.text_area("Key Responsibilities", height=150)
    
    submitted_draft = st.form_submit_button("💾 Generate PDF Form")

# --- PDF GENERATION & UPLOAD SECTION ---
if submitted_draft:
    mrf_data = {
        "requisitor_name": req_name, "requisitor_dept": req_dept, "requisitor_ext": req_ext,
        "job_title": job_title, "shift": shift, "number_required": num_req, "date_required": date_req,
        "recruitment_type": rec_type, "replacement_reason": rep_reason,
        "employment_nature": emp_nature, "hiring_source": source,
        "education_req": edu_req, "skills_req": skills_req, "experience_req": exp_req,
        "responsibilities": resp
    }
    
    try:
        pdf = MRF_PDF()
        pdf.draw_form(mrf_data)
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        
        st.divider()
        col_dl, col_ul = st.columns(2)
        
        with col_dl:
            st.success("✅ Form Generated!")
            st.info("Step 1: Download the PDF, Print & Sign it.")
            st.download_button(
                label="⬇️ Download ZentikLabs MRF (PDF)",
                data=pdf_bytes,
                file_name=f"MRF_{job_title.replace(' ', '_')}.pdf",
                mime="application/pdf",
                type="primary"
            )
        
        with col_ul:
            st.info("Step 2: Upload the SIGNED PDF to submit.")
            signed_file = st.file_uploader("Upload Signed MRF", type=["pdf", "jpg", "png"])
            
            if st.button("🚀 Submit Requisition Final"):
                if signed_file:
                    try:
                        file_ext = signed_file.name.split('.')[-1]
                        path = f"requisitions/{int(time.time())}_{job_title.replace(' ', '_')}.{file_ext}"
                        mime = mimetypes.guess_type(signed_file.name)[0]
                        
                        supabase.storage.from_("resumes").upload(path, signed_file.getvalue(), {"content-type": mime})
                        url = supabase.storage.from_("resumes").get_public_url(path)
                        
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
                        st.success("Requisition Submitted Successfully!")
                        time.sleep(2)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("⚠️ You must upload the signed file to proceed.")
    except Exception as e:
        st.error(f"PDF Generation Error: {e}")