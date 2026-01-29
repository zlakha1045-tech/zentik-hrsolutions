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

# --- HELPER: GENERATE OFFER LETTER HTML ---
def generate_offer_html(data):
    return f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Georgia', serif; color: black; }}
            .container {{ padding: 50px; max-width: 800px; margin: auto; border: 1px solid #ddd; }}
            .header {{ text-align: center; border-bottom: 2px solid #000; padding-bottom: 20px; margin-bottom: 30px; }}
            .footer {{ display: flex; justify-content: space-between; margin-top: 50px; }}
        </style>
    </head>
    <body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0; letter-spacing: 2px;">ZentikLabs</h1>
            <p style="font-size: 0.9em; color: #555;">Excellence in Technology Solutions</p>
        </div>
        
        <p style="text-align: right;"><strong>Date:</strong> {data['date']}</p>
        
        <p><strong>To,</strong><br>
        {data['candidate_name']}<br>
        {data['candidate_email']}</p>
        
        <h3 style="text-align: center; margin-top: 40px; text-decoration: underline;">SUBJECT: OFFER OF EMPLOYMENT</h3>
        
        <p>Dear {data['candidate_name'].split()[0]},</p>
        
        <p>We are pleased to offer you the position of <strong>{data['job_title']}</strong> at ZentikLabs. 
        We were impressed with your skills and believe you will be a valuable asset to our {data['department']} team.</p>
        
        <h4 style="margin-top: 20px;">Terms of Employment:</h4>
        <ul>
            <li><strong>Start Date:</strong> {data['start_date']}</li>
            <li><strong>Annual CTC:</strong> {data['salary']}</li>
            <li><strong>Reporting To:</strong> {data['manager']}</li>
            <li><strong>Probation Period:</strong> {data['probation']} Months</li>
        </ul>
        
        <p>Please sign and return the duplicate copy of this letter as a token of your acceptance.</p>
        
        <br><br>
        <div class="footer">
            <div>
                <p>Sincerely,</p>
                <br>
                <strong>HR Manager</strong><br>
                ZentikLabs
            </div>
            <div>
                <p>Accepted By:</p>
                <br>
                <strong>{data['candidate_name']}</strong>
            </div>
        </div>
    </div>
    </body>
    </html>
    """

hero_section("assets/login_hero.jpg", "Placement & Offers", "Generate Offer Letters and Finalize Hires.")

# --- TABS FOR WORKFLOW ---
tab_draft, tab_final = st.tabs(["📝 Draft & Send Offer", "🏁 Finalize Hire (Upload Signed)"])

# ==========================================
# TAB 1: DRAFT & SEND (The "Waiting Room")
# ==========================================
with tab_draft:
    st.subheader("1. Generate Offer Letter")
    
    # Fetch candidates ready for offer
    try:
        response = supabase.table("placements").select(
            "*, candidates(name, email), jobs(title, department)"
        ).eq("status", "Ready for Offer").execute()
        pending_list = response.data
    except:
        pending_list = []

    if not pending_list:
        st.info("✅ No new offers to generate.")
    else:
        # Selection Map
        pmap = {f"{p['candidates']['name']} - {p['jobs']['title']}": p for p in pending_list}
        selected_label = st.selectbox("Select Candidate", list(pmap.keys()), key="sel_draft")
        p_data = pmap[selected_label]

        st.divider()
        
        # Input Details
        with st.form("offer_draft_form"):
            c1, c2 = st.columns(2)
            with c1:
                salary = st.text_input("Final Agreed Salary", placeholder="e.g. $95,000 / year")
                manager = st.text_input("Reporting Manager")
            with c2:
                start_date = st.date_input("Joining Date")
                probation = st.number_input("Probation Period (Months)", value=3)

            generate_btn = st.form_submit_button("👀 Preview & Generate")

        if generate_btn:
            offer_data = {
                "date": str(time.strftime("%Y-%m-%d")),
                "candidate_name": p_data['candidates']['name'],
                "candidate_email": p_data['candidates']['email'],
                "job_title": p_data['jobs']['title'],
                "department": p_data['jobs'].get('department', 'General'),
                "salary": salary,
                "start_date": str(start_date),
                "manager": manager,
                "probation": probation
            }
            html_content = generate_offer_html(offer_data)
            
            # Show Preview
            st.components.v1.html(html_content, height=600, scrolling=True)
            
            # ACTION BUTTONS
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                # 1. DOWNLOAD BUTTON
                st.download_button(
                    label="📥 Download HTML Offer Letter",
                    data=html_content,
                    file_name=f"Offer_Letter_{p_data['candidates']['name'].replace(' ', '_')}.html",
                    mime="text/html",
                    help="Download this file, open it in your browser, and Print to PDF (Ctrl+P)."
                )
            
            with col_d2:
                # 2. MARK AS SENT
                if st.button("✉️ Mark as Sent (Wait for Signature)", type="primary"):
                    # Update status to move them to Tab 2
                    supabase.table("placements").update({
                        "status": "Offer Sent", # <--- MOVES THEM TO TAB 2
                        "salary_offered": salary,
                        "start_date": str(start_date)
                    }).eq("id", p_data['id']).execute()
                    
                    st.success("Status Updated! When they reply, go to the 'Finalize Hire' tab.")
                    time.sleep(2)
                    st.rerun()


# ==========================================
# TAB 2: FINALIZE HIRE (The "Closing Room")
# ==========================================
with tab_final:
    st.subheader("2. Confirm Hire (Upload Signed Copy)")
    
    # Fetch candidates who have been sent an offer
    try:
        response_sent = supabase.table("placements").select(
            "*, candidates(name, email), jobs(title)"
        ).eq("status", "Offer Sent").execute()
        sent_list = response_sent.data
    except:
        sent_list = []

    if not sent_list:
        st.info("📭 No pending offers waiting for signature.")
    else:
        # Selection Map
        sent_map = {f"{p['candidates']['name']} - {p['jobs']['title']}": p for p in sent_list}
        selected_sent_label = st.selectbox("Select Candidate", list(sent_map.keys()), key="sel_final")
        sent_data = sent_map[selected_sent_label]

        st.info(f"Waiting for **{sent_data['candidates']['name']}** to return the signed letter.")
        
        with st.form("finalize_form"):
            st.markdown("### Upload Signed Document")
            signed_offer = st.file_uploader("Upload PDF/Image", type=["pdf", "jpg", "png"])
            
            confirm_btn = st.form_submit_button("🎉 Confirm & Hired", type="primary")
            
            if confirm_btn:
                if signed_offer:
                    try:
                        # Upload File
                        ext = signed_offer.name.split('.')[-1]
                        path = f"offers/{int(time.time())}_{sent_data['id']}.{ext}"
                        mime = mimetypes.guess_type(signed_offer.name)[0]
                        
                        supabase.storage.from_("resumes").upload(path, signed_offer.getvalue(), {"content-type": mime})
                        url = supabase.storage.from_("resumes").get_public_url(path)
                        
                        # UPDATE DB -> HIRED
                        supabase.table("placements").update({
                            "status": "Offer Accepted",
                            "signed_mrf_url": url
                        }).eq("id", sent_data['id']).execute()
                        
                        supabase.table("candidates").update({
                            "status": "Hired"
                        }).eq("id", sent_data['candidate_id']).execute()
                        
                        st.balloons()
                        st.success(f"🎊 {sent_data['candidates']['name']} is officially HIRED!")
                        time.sleep(3)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("⚠️ You must upload the signed document to confirm.")