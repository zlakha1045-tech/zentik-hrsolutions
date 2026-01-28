import streamlit as st
from supabase import create_client
from styles import load_css, hero_section
from fpdf import FPDF
import time

st.set_page_config(page_title="Draft Requisition", layout="wide")
load_css()

try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    st.error("Missing Supabase Secrets.")
    st.stop()

# --- HELPER: CLEAN TEXT ---
def clean_text(text):
    if not text: return ""
    replacements = {'\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"', '\u2013': '-', '\u2022': '*'}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.encode('latin-1', 'replace').decode('latin-1')

# --- PDF CLASS ---
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
        # (Drawing logic same as before, abbreviated for brevity but fully functional)
        self.section_title("REQUISITOR")
        self.cell(40, 10, "Name:", border='LBT'); self.cell(150, 10, clean_text(data.get('requisitor_name')), border='RBT', ln=1)
        self.cell(40, 10, "Department:", border='LBT'); self.cell(150, 10, clean_text(data.get('requisitor_dept')), border='RBT', ln=1)
        
        self.ln(2)
        self.section_title("POSITION DETAILS")
        self.cell(40, 10, "Job Title:", border='LBT'); self.cell(150, 10, clean_text(data.get('job_title')), border='RBT', ln=1)
        self.cell(40, 10, "No. Required:", border='LBT'); self.cell(150, 10, str(data.get('number_required')), border='RBT', ln=1)

        self.ln(2)
        self.section_title("APPROVALS REQUIRED")
        self.ln(15)
        self.cell(60, 5, "Requisitor", 0, 0, 'C'); self.cell(60, 5, "General Manager", 0, 0, 'C'); self.cell(60, 5, "Managing Director", 0, 1, 'C')

# --- MAIN PAGE ---
hero_section("assets/login_hero.jpg", "Draft MRF", "Step 1: Draft the requisition and download the form.")

st.subheader("📝 Draft New Requisition")

with st.form("draft_mrf_form"):
    c1, c2 = st.columns(2)
    req_name = c1.text_input("Requisitor Name")
    req_dept = c2.text_input("Department")
    
    r1, r2, r3 = st.columns(3)
    job_title = r1.text_input("Job Title")
    num_req   = r2.number_input("Count", min_value=1, value=1)
    date_req  = r3.date_input("Date Required")

    st.markdown("### Requirements")
    skills_req = st.text_area("Skills & Justification")

    submitted = st.form_submit_button("💾 Save Draft & Generate PDF")

if submitted:
    if not job_title or not req_name:
        st.error("Please fill in Job Title and Requisitor Name.")
    else:
        # 1. Prepare Data
        mrf_data = {
            "requisitor_name": req_name, "requisitor_dept": req_dept,
            "job_title": job_title, "number_required": num_req, 
            "date_required": str(date_req), "skills_req": skills_req,
            "status": "Draft" # <--- SAVED AS DRAFT
        }

        # 2. Insert into DB
        try:
            supabase.table("requisitions").insert(mrf_data).execute()
            
            # 3. Generate PDF
            pdf = MRF_PDF()
            pdf.draw_form(mrf_data)
            pdf_bytes = bytes(pdf.output(dest='S'))

            st.success("✅ Draft Saved! You can now download the PDF.")
            
            # 4. Show Download Button (This will stay visible)
            st.download_button(
                label="⬇️ Download PDF to Sign",
                data=pdf_bytes,
                file_name=f"Draft_MRF_{job_title}.pdf",
                mime="application/pdf",
                type="primary"
            )
            
            st.info("👉 **Next Step:** Print this, sign it, and go to the **'Submit MRF'** page to upload it.")
            
        except Exception as e:
            st.error(f"Database Error: {e}")