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
    <div style="font-family: 'Georgia', serif; padding: 50px; background: white; color: black; max-width: 800px; margin: auto; border: 1px solid #ddd;">
        <div style="text-align: center; border-bottom: 2px solid #000; padding-bottom: 20px; margin-bottom: 30px;">
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
        <div style="display: flex; justify-content: space-between; margin-top: 50px;">
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
    """

hero_section("assets/login_hero.jpg", "Placement & Offers", "Generate Offer Letters and Finalize Hires.")

# --- STEP 1: SELECT PENDING HIRE ---
st.subheader("1. Select Candidate for Offer")

try:
    # CHANGED: Filter for 'Ready for Offer' instead of 'Pending Hire'
    response = supabase.table("placements").select(
        "*, candidates(name, email), jobs(title, department)"
    ).eq("status", "Ready for Offer").execute()
    
    pending_list = response.data
except Exception as e:
    st.error(f"Error: {e}")
    st.stop()

if not pending_list:
    st.info("✅ No authorized offers pending. Wait for Management Approval.")
    st.stop()

# Map selection
pmap = {f"{p['candidates']['name']} - {p['jobs']['title']}": p for p in pending_list}
selected_label = st.selectbox("Select Candidate", list(pmap.keys()))
p_data = pmap[selected_label]

# --- STEP 2: OFFER DETAILS ---
st.divider()
st.subheader("2. Draft Offer Details")

with st.form("offer_form"):
    c1, c2 = st.columns(2)
    with c1:
        salary = st.text_input("Final Agreed Salary", placeholder="e.g. $95,000 / year")
        manager = st.text_input("Reporting Manager")
    with c2:
        start_date = st.date_input("Joining Date")
        probation = st.number_input("Probation Period (Months)", value=3)

    submitted = st.form_submit_button("👀 Preview Offer Letter")

# --- STEP 3: PREVIEW & FINALIZE ---
if submitted or st.session_state.get('offer_generated'):
    st.session_state.offer_generated = True
    
    st.divider()
    c_view, c_action = st.columns([3, 2])
    
    with c_view:
        st.markdown("### 📄 Letter Preview")
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
        html = generate_offer_html(offer_data)
        st.components.v1.html(html, height=600, scrolling=True)
    
    with c_action:
        st.markdown("### 🚀 Finalize Hire")
        st.info("1. Download/Print the letter.\n2. Get it signed.\n3. Upload to close the loop.")
        
        signed_offer = st.file_uploader("Upload Signed Acceptance", type=["pdf", "jpg", "png"])
        
        if st.button("🎉 Confirm Hiring", type="primary"):
            if signed_offer:
                try:
                    # Upload File
                    ext = signed_offer.name.split('.')[-1]
                    path = f"offers/{int(time.time())}_{p_data['id']}.{ext}"
                    mime = mimetypes.guess_type(signed_offer.name)[0]
                    
                    supabase.storage.from_("resumes").upload(path, signed_offer.getvalue(), {"content-type": mime})
                    url = supabase.storage.from_("resumes").get_public_url(path)
                    
                    # UPDATE PLACEMENT -> 'Offer Accepted'
                    supabase.table("placements").update({
                        "status": "Offer Accepted",
                        "salary_offered": salary,
                        "start_date": str(start_date),
                        "signed_mrf_url": url # Using this column for Signed Offer URL for now
                    }).eq("id", p_data['id']).execute()
                    
                    # UPDATE CANDIDATE -> 'Hired'
                    supabase.table("candidates").update({
                        "status": "Hired"
                    }).eq("id", p_data['candidate_id']).execute()
                    
                    # UPDATE REQUISITION (If linked) -> Mark filled?
                    # (Optional logic: You could decrement the 'number_required' in requisitions table here)
                    
                    st.balloons()
                    st.success(f"🎊 {p_data['candidates']['name']} is officially HIRED!")
                    time.sleep(3)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Please upload the signed acceptance letter.")