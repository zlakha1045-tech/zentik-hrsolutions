import streamlit as st
from supabase import create_client
from styles import load_css, hero_section
import time
from fpdf import FPDF
import streamlit.components.v1 as components

st.set_page_config(page_title="Create Requisition", layout="wide")
load_css()

# --- SETUP SUPABASE ---
try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    st.error("Missing Supabase Secrets.")
    st.stop()

# ==========================================
# 1. PDF GENERATOR (The Fix)
# ==========================================
class MRF_PDF(FPDF):
    def header(self):
        self.set_fill_color(255, 255, 255)
        self.rect(0, 0, 210, 297, 'F') # Force White Background
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'MANPOWER REQUISITION FORM (MRF)', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_mrf_pdf(data):
    pdf = MRF_PDF()
    pdf.add_page()
    pdf.set_text_color(0, 0, 0)
    
    # Section: Job Details
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '1. JOB DETAILS', 0, 1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    
    pdf.set_font('Arial', '', 10)
    details = [
        f"Job Title: {data['title']}",
        f"Department: {data['department']}",
        f"Hiring Manager: {data['manager']}",
        f"Number of Positions: {data['count']}",
        f"Employment Type: {data['type']}"
    ]
    for d in details:
        pdf.cell(0, 8, f"- {d}", 0, 1)
    
    pdf.ln(5)
    
    # Section: Budget & Compensation
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '2. BUDGET & COMPENSATION', 0, 1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 8, f"Salary Range: {data['salary']}", 0, 1)
    
    pdf.ln(5)
    
    # Section: Justification
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '3. JUSTIFICATION', 0, 1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 6, data['justification'])
    
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, 10, "Requested By: __________________________   Date: ____________", 0, 1)

    # --- THE FIX ---
    # Return raw bytes directly (Compatible with fpdf2)
    return bytes(pdf.output())

# ==========================================
# 2. HTML PREVIEW GENERATOR
# ==========================================
def generate_mrf_html(data):
    return f"""
    <div style="font-family: Arial, sans-serif; padding: 40px; background: white; border: 1px solid #ccc; max-width: 800px; margin: auto;">
        <h2 style="text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px;">MANPOWER REQUISITION FORM</h2>
        
        <h3 style="background: #eee; padding: 5px;">1. JOB DETAILS</h3>
        <p><strong>Job Title:</strong> {data['title']}</p>
        <p><strong>Department:</strong> {data['department']}</p>
        <p><strong>Manager:</strong> {data['manager']}</p>
        <p><strong>Positions:</strong> {data['count']} | <strong>Type:</strong> {data['type']}</p>
        
        <h3 style="background: #eee; padding: 5px;">2. BUDGET</h3>
        <p><strong>Salary Range:</strong> {data['salary']}</p>
        
        <h3 style="background: #eee; padding: 5px;">3. JUSTIFICATION</h3>
        <p>{data['justification']}</p>
        
        <br><br>
        <div style="border-top: 1px solid #000; padding-top: 10px; margin-top: 30px;">
            <p><strong>Requested By:</strong> {data['manager']} &nbsp;&nbsp;&nbsp; <strong>Date:</strong> {time.strftime('%Y-%m-%d')}</p>
        </div>
    </div>
    """

# --- UI START ---
hero_section("assets/login_hero.jpg", "Create Requisition", "Draft new roles for management approval.")

st.subheader("📝 New Role Request")

# SESSION STATE FOR FORM
if 'mrf_generated' not in st.session_state:
    st.session_state.mrf_generated = False

with st.form("mrf_form"):
    c1, c2 = st.columns(2)
    with c1:
        title = st.text_input("Job Title", "Technical Sales Manager")
        department = st.selectbox("Department", ["Sales", "Engineering", "Marketing", "HR"])
        manager = st.text_input("Hiring Manager", "Alex Mercer")
    with c2:
        count = st.number_input("Number of Positions", min_value=1, value=1)
        emp_type = st.selectbox("Type", ["Full-Time", "Part-Time", "Contract"])
        salary = st.text_input("Budgeted Salary Range", "$80,000 - $100,000")
        
    justification = st.text_area("Justification for Hire", "We need to expand our sales team to handle incoming enterprise leads.")
    
    # REQUIREMENTS (HIDDEN FOR PDF, USED FOR DB)
    reqs = st.text_area("Key Requirements / Skills", "Salesforce, B2B Sales, Leadership")
    
    generate_btn = st.form_submit_button("👀 Preview & Generate MRF")

# --- LOGIC ---
if generate_btn or st.session_state.mrf_generated:
    st.session_state.mrf_generated = True
    
    mrf_data = {
        "title": title, "department": department, "manager": manager,
        "count": count, "type": emp_type, "salary": salary,
        "justification": justification
    }
    
    # 1. SHOW HTML PREVIEW
    st.markdown("### 📄 Document Preview")
    html_view = generate_mrf_html(mrf_data)
    components.html(html_view, height=600, scrolling=True)
    
    # 2. GENERATE PDF
    pdf_bytes = create_mrf_pdf(mrf_data)
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.download_button(
            "📥 Download MRF (PDF)", 
            data=pdf_bytes,
            file_name=f"MRF_{title.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
    
    with col_b:
        if st.button("🚀 Submit for Approval", type="primary"):
            try:
                # 1. Upload PDF
                timestamp = int(time.time())
                path = f"requisitions/{timestamp}_{title.replace(' ', '_')}.pdf"
                supabase.storage.from_("resumes").upload(path, pdf_bytes, {"content-type": "application/pdf"})
                public_url = supabase.storage.from_("resumes").get_public_url(path)
                
                # 2. Insert to DB
                # Note: We are saving the raw text description for the Job Board later
                job_data = {
                    "title": title,
                    "department": department,
                    "status": "Pending", # Needs approval
                    "description": f"{justification}\n\nRequirements:\n{reqs}",
                    "mrf_url": public_url
                }
                
                supabase.table("requisitions").insert(job_data).execute()
                
                st.session_state.mrf_generated = False
                st.success("Requisition Submitted! Waiting for Management Approval.")
                time.sleep(2)
                st.switch_page("pages/3_✅_Approve_Requisition.py")
                
            except Exception as e:
                st.error(f"Error submitting: {e}")