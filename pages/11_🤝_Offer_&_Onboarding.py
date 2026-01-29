import streamlit as st
from supabase import create_client
from styles import load_css, hero_section
import time
import mimetypes
from fpdf import FPDF
import base64

st.set_page_config(page_title="Placement Manager", layout="wide")
load_css()

# --- SETUP SUPABASE ---
try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    st.error("Missing Supabase Secrets.")
    st.stop()

# --- HELPER: GENERATE PDF OFFER ---
class OfferPDF(FPDF):
    def header(self):
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
    
    # Date
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 10, f"Date: {data['date']}", 0, 1, 'R')
    pdf.ln(5)

    # To Address
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 5, f"To: {data['candidate_name']}", 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 5, f"Email: {data['candidate_email']}", 0, 1)
    pdf.ln(10)

    # Subject
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'SUBJECT: OFFER OF EMPLOYMENT', 0, 1, 'C')
    pdf.ln(5)

    # Body
    pdf.set_font('Arial', '', 11)
    body_text = (
        f"Dear {data['candidate_name'].split()[0]},\n\n"
        f"We are pleased to offer you the position of {data['job_title']} at Zentik Labs. "
        f"We were impressed with your skills and believe you will be a valuable asset to our {data['department']} team.\n\n"
        "Terms of Employment:"
    )
    pdf.multi_cell(0, 6, body_text)
    
    # Bullets
    pdf.ln(2)
    bullets = [
        f"Start Date: {data['start_date']}",
        f"Annual Salary: {data['salary']}",
        f"Reporting To: {data['manager']}",
        f"Probation Period: {data['probation']} Months"
    ]
    for b in bullets:
        pdf.cell(10) # Indent
        pdf.cell(0, 6, f"- {b}", 0, 1)
    
    # Closing
    pdf.ln(5)
    pdf.multi_cell(0, 6, "\nPlease sign and return the duplicate copy of this letter as a token of your acceptance.")
    
    # Signatures
    pdf.ln(20)
    y_pos = pdf.get_y()
    
    # Left Signature
    pdf.set_xy(10, y_pos)
    pdf.cell(90, 5, "Sincerely,", 0, 1)
    pdf.ln(15)
    pdf.cell(90, 5, "HR Manager", 0, 1)
    pdf.cell(90, 5, "Zentik Labs", 0, 1)
    
    # Right Signature
    pdf.set_xy(110, y_pos)
    pdf.cell(90, 5, "Accepted By:", 0, 1)
    pdf.ln(15)
    pdf.cell(90, 5, data['candidate_name'], 0, 1)
    
    # Return PDF as bytes
    return pdf.output(dest='S').encode('latin-1')

# --- UI START ---
hero_section("assets/login_hero.jpg", "Placement & Offers", "Generate Offer Letters and Finalize Hires.")
tab_draft, tab_final = st.tabs(["📝 Draft & Send Offer", "🏁 Finalize Hire (Upload Signed)"])

# ==========================================
# TAB 1: DRAFT & SEND
# ==========================================
with tab_draft:
    st.subheader("1. Generate Offer Letter")
    
    # Fetch Data
    try:
        response = supabase.table("placements").select("*, candidates(name, email), jobs(title, department)").eq("status", "Ready for Offer").execute()
        pending_list = response.data
    except:
        pending_list = []

    if not pending_list:
        st.info("✅ No new offers to generate.")
    else:
        # Initialize Session State for this form
        if 'offer_generated' not in st.session_state:
            st.session_state.offer_generated = False
        
        pmap = {f"{p['candidates']['name']} - {p['jobs']['title']}": p for p in pending_list}
        selected_label = st.selectbox("Select Candidate", list(pmap.keys()))
        p_data = pmap[selected_label]

        st.divider()
        
        # FORM
        with st.form("offer_draft_form"):
            c1, c2 = st.columns(2)
            with c1:
                salary = st.text_input("Final Agreed Salary", placeholder="e.g. $95,000 / year")
                manager = st.text_input("Reporting Manager")
            with c2:
                start_date = st.date_input("Joining Date")
                probation = st.number_input("Probation Period (Months)", value=3)

            generate_btn = st.form_submit_button("👀 Create Offer PDF")

        # LOGIC: If button clicked OR state is already True
        if generate_btn or st.session_state.offer_generated:
            st.session_state.offer_generated = True # KEEP IT TRUE
            
            # Prepare Data
            offer_data = {
                "date": str(time.strftime("%Y-%m-%d")),
                "candidate_name": p_data['candidates']['name'],
                "candidate_email": p_data['candidates']['email'],
                "job_title": p_data['jobs']['title'],
                "department": p_data['jobs'].get('department', 'General'),
                "salary": salary if salary else "TBD", # Handle empty state on reload
                "start_date": str(start_date),
                "manager": manager if manager else "Hiring Manager",
                "probation": probation
            }
            
            # Generate PDF Bytes
            pdf_bytes = create_offer_pdf(offer_data)
            
            # Show PDF Preview (Embedded)
            base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
            
            # ACTION BUTTONS
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
                    # Update DB
                    supabase.table("placements").update({
                        "status": "Offer Sent",
                        "salary_offered": offer_data['salary'],
                        "start_date": offer_data['start_date']
                    }).eq("id", p_data['id']).execute()
                    
                    # Reset State and Rerun
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