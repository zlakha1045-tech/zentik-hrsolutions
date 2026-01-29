import streamlit as st
from supabase import create_client
from styles import load_css, hero_section
import time
import mimetypes
from fpdf import FPDF
import base64
import streamlit.components.v1 as components # Native HTML renderer

st.set_page_config(page_title="Placement Manager", layout="wide")
load_css()

# --- SETUP SUPABASE ---
try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    st.error("Missing Supabase Secrets.")
    st.stop()

# ==========================================
# HELPER 1: GENERATE PDF (For Download)
# ==========================================
class OfferPDF(FPDF):
    def header(self):
        self.set_fill_color(255, 255, 255)
        self.rect(0, 0, 210, 297, 'F')
        self.set_font('Arial', 'B', 20)
        self.cell(0, 10, 'ZENTIK LABS', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, 'Excellence in Technology Solutions', 0, 1, 'C')
        self.line(10, 30, 200, 30)
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_offer_pdf(data):
    pdf = OfferPDF()
    pdf.add_page()
    pdf.set_text_color(0, 0, 0)
    
    pdf.set_font('Arial', '', 10); pdf.cell(0, 10, f"Date: {data['date']}", 0, 1, 'R'); pdf.ln(5)
    pdf.set_font('Arial', 'B', 10); pdf.cell(0, 5, f"To: {data['candidate_name']}", 0, 1)
    pdf.set_font('Arial', '', 10); pdf.cell(0, 5, f"Email: {data['candidate_email']}", 0, 1); pdf.ln(10)
    pdf.set_font('Arial', 'B', 12); pdf.cell(0, 10, 'SUBJECT: OFFER OF EMPLOYMENT', 0, 1, 'C'); pdf.ln(5)
    
    pdf.set_font('Arial', '', 11)
    body_text = (
        f"Dear {data['candidate_name'].split()[0]},\n\n"
        f"We are pleased to offer you the position of {data['job_title']} at Zentik Labs. "
        f"We were impressed with your skills and believe you will be a valuable asset to our {data['department']} team.\n\n"
        "Terms of Employment:"
    )
    pdf.multi_cell(0, 6, body_text)
    pdf.ln(2)
    bullets = [f"Start Date: {data['start_date']}", f"Annual Salary: {data['salary']}", f"Reporting To: {data['manager']}", f"Probation Period: {data['probation']} Months"]
    for b in bullets:
        pdf.cell(10); pdf.cell(0, 6, f"- {b}", 0, 1)
    
    pdf.ln(5); pdf.multi_cell(0, 6, "\nPlease sign and return the duplicate copy of this letter as a token of your acceptance.")
    pdf.ln(20); y_pos = pdf.get_y()
    pdf.set_xy(10, y_pos); pdf.cell(90, 5, "Sincerely,", 0, 1); pdf.ln(15); pdf.cell(90, 5, "HR Manager", 0, 1); pdf.cell(90, 5, "Zentik Labs", 0, 1)
    pdf.set_xy(110, y_pos); pdf.cell(90, 5, "Accepted By:", 0, 1); pdf.ln(15); pdf.cell(90, 5, data['candidate_name'], 0, 1)
    
    return bytes(pdf.output())

# ==========================================
# HELPER 2: GENERATE HTML (For Preview)
# ==========================================
def generate_offer_html(data):
    # This HTML mimics the PDF look perfectly
    return f"""
    <div style="font-family: Arial, sans-serif; padding: 40px; background: white; color: black; max-width: 800px; margin: auto; border: 1px solid #ccc; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        <div style="text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px;">
            <h1 style="margin: 0; color: #000;">ZENTIK LABS</h1>
            <p style="margin: 5px 0 0; color: #666; font-style: italic;">Excellence in Technology Solutions</p>
        </div>
        
        <p style="text-align: right;"><strong>Date:</strong> {data['date']}</p>
        
        <p><strong>To,</strong><br>{data['candidate_name']}<br>{data['candidate_email']}</p>
        
        <h3 style="text-align: center; margin-top: 30px; text-decoration: underline;">SUBJECT: OFFER OF EMPLOYMENT</h3>
        
        <p>Dear {data['candidate_name'].split()[0]},</p>
        
        <p>We are pleased to offer you the position of <strong>{data['job_title']}</strong> at Zentik Labs. 
        We were impressed with your skills and believe you will be a valuable asset to our {data['department']} team.</p>
        
        <h4>Terms of Employment:</h4>
        <ul style="line-height: 1.6;">
            <li><strong>Start Date:</strong> {data['start_date']}</li>
            <li><strong>Annual Salary:</strong> {data['salary']}</li>
            <li><strong>Reporting To:</strong> {data['manager']}</li>
            <li><strong>Probation Period:</strong> {data['probation']} Months</li>
        </ul>
        
        <p>Please sign and return the duplicate copy of this letter as a token of your acceptance.</p>
        
        <div style="display: flex; justify-content: space-between; margin-top: 60px;">
            <div>
                <p>Sincerely,</p><br>
                <strong>HR Manager</strong><br>Zentik Labs
            </div>
            <div>
                <p>Accepted By:</p><br>
                <strong>{data['candidate_name']}</strong>
            </div>
        </div>
    </div>
    """

# --- UI START ---
hero_section("assets/login_hero.jpg", "Placement & Offers", "Generate Offer Letters and Finalize Hires.")
tab_draft, tab_final = st.tabs(["📝 Draft & Send Offer", "🏁 Finalize Hire (Upload Signed)"])

# ==========================================
# TAB 1: DRAFT & SEND
# ==========================================
with tab_draft:
    st.subheader("1. Generate Offer Letter")
    
    try:
        response = supabase.table("placements").select("*, candidates(name, email), jobs(title, department)").eq("status", "Ready for Offer").execute()
        pending_list = response.data
    except:
        pending_list = []

    if not pending_list:
        st.info("✅ No new offers to generate.")
    else:
        if 'offer_generated' not in st.session_state:
            st.session_state.offer_generated = False
        
        pmap = {f"{p['candidates']['name']} - {p['jobs']['title']}": p for p in pending_list}
        selected_label = st.selectbox("Select Candidate", list(pmap.keys()))
        p_data = pmap[selected_label]

        st.divider()
        
        with st.form("offer_draft_form"):
            c1, c2 = st.columns(2)
            with c1:
                salary = st.text_input("Final Agreed Salary", placeholder="e.g. $95,000 / year")
                manager = st.text_input("Reporting Manager")
            with c2:
                start_date = st.date_input("Joining Date")
                probation = st.number_input("Probation Period (Months)", value=3)

            generate_btn = st.form_submit_button("👀 Preview Offer")

        if generate_btn or st.session_state.offer_generated:
            st.session_state.offer_generated = True
            
            offer_data = {
                "date": str(time.strftime("%Y-%m-%d")),
                "candidate_name": p_data['candidates']['name'],
                "candidate_email": p_data['candidates']['email'],
                "job_title": p_data['jobs']['title'],
                "department": p_data['jobs'].get('department', 'General'),
                "salary": salary if salary else "TBD",
                "start_date": str(start_date),
                "manager": manager if manager else "Hiring Manager",
                "probation": probation
            }
            
            # 1. SHOW HTML PREVIEW (Safe & Fast)
            st.markdown("### 📄 Offer Letter Preview")
            html_content = generate_offer_html(offer_data)
            components.html(html_content, height=600, scrolling=True)
            
            # 2. GENERATE PDF FOR DOWNLOAD
            pdf_bytes = create_offer_pdf(offer_data)

            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.download_button(
                    label="📥 Download PDF Offer",
                    data=pdf_bytes,
                    file_name=f"Offer_{p_data['candidates']['name'].replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )
            
            with col_d2:
                if st.button("✉️ Mark as Sent (Wait for Signature)", type="primary"):
                    supabase.table("placements").update({
                        "status": "Offer Sent",
                        "salary_offered": offer_data['salary'],
                        "start_date": offer_data['start_date']
                    }).eq("id", p_data['id']).execute()
                    
                    st.session_state.offer_generated = False
                    st.success("Status Updated! Moving candidate to 'Finalize Hire' tab.")
                    time.sleep(1.5)
                    st.rerun()

# ==========================================
# TAB 2: FINALIZE HIRE
# ==========================================
with tab_final:
    st.subheader("2. Confirm Hire (Upload Signed Copy)")
    
    try:
        response_sent = supabase.table("placements").select("*, candidates(name, email), jobs(title)").eq("status", "Offer Sent").execute()
        sent_list = response_sent.data
    except:
        sent_list = []

    if not sent_list:
        st.info("📭 No pending offers waiting for signature.")
    else:
        sent_map = {f"{p['candidates']['name']} - {p['jobs']['title']}": p for p in sent_list}
        selected_sent_label = st.selectbox("Select Candidate", list(sent_map.keys()), key="sel_final")
        sent_data = sent_map[selected_sent_label]

        st.info(f"Waiting for **{sent_data['candidates']['name']}** to return the signed letter.")
        
        with st.form("finalize_form"):
            st.markdown("### Upload Signed Document")
            signed_offer = st.file_uploader("Upload PDF/Image", type=["pdf", "jpg", "png"])
            confirm_btn = st.form_submit_button("🎉 Confirm & Hired", type="primary")
            
            if confirm_btn and signed_offer:
                try:
                    ext = signed_offer.name.split('.')[-1]
                    path = f"offers/{int(time.time())}_{sent_data['id']}.{ext}"
                    mime = mimetypes.guess_type(signed_offer.name)[0]
                    
                    supabase.storage.from_("resumes").upload(path, signed_offer.getvalue(), {"content-type": mime})
                    url = supabase.storage.from_("resumes").get_public_url(path)
                    
                    supabase.table("placements").update({"status": "Offer Accepted", "signed_mrf_url": url}).eq("id", sent_data['id']).execute()
                    supabase.table("candidates").update({"status": "Hired"}).eq("id", sent_data['candidate_id']).execute()
                    
                    st.balloons()
                    st.success(f"🎊 {sent_data['candidates']['name']} is officially HIRED!")
                    time.sleep(3)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")