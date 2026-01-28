import streamlit as st
from supabase import create_client
from styles import load_css

st.set_page_config(page_title="Hiring Approval", layout="wide")
load_css()

try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    st.error("Missing Secrets.")
    st.stop()

st.title("🛡️ Final Hiring Authorization")
st.markdown("Review candidates selected by recruiters. Check the **MRF** and **Resume** before authorizing an Offer Letter.")

# --- FETCH PENDING APPROVALS ---
# We look for status 'Pending Final Approval'
try:
    # We fetch Placement + Candidate + Job + Requisition (Linked to Job)
    # Note: This relies on your foreign keys being set up correctly in Supabase
    response = supabase.table("placements").select(
        "*, candidates(name, email, resume_url), jobs(title, department, requisitions(signed_mrf_url, number_required))"
    ).eq("status", "Pending Final Approval").execute()
    
    approvals = response.data
except Exception as e:
    st.error(f"Error fetching data: {e}")
    st.stop()

if not approvals:
    st.info("✅ No candidates waiting for authorization.")
    st.stop()

# --- DISPLAY CARDS ---
for item in approvals:
    cand = item['candidates']
    job = item['jobs']
    # Handle case where job might not have a linked requisition
    req = job['requisitions'] if job.get('requisitions') else {}
    
    with st.container():
        st.markdown(f"""
        <div style="background-color: #1a1c24; border: 1px solid #333; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h2 style="margin: 0; color: white;">{cand['name']}</h2>
                    <p style="color: #4da6ff; margin: 5px 0;">Role: <strong>{job['title']}</strong> ({job.get('department', 'General')})</p>
                </div>
                <div style="text-align: right;">
                     <span style="background-color: #f1c40f; color: black; padding: 5px 10px; border-radius: 5px; font-weight: bold;">Action Required</span>
                </div>
            </div>
            <hr style="border-color: #333;">
            <div style="display: flex; gap: 20px; margin-bottom: 15px;">
                 {'<a href="' + cand['resume_url'] + '" target="_blank" style="text-decoration: none; color: white; background: #333; padding: 8px 15px; border-radius: 5px;">📄 View Resume</a>' if cand.get('resume_url') else ''}
                 {'<a href="' + req['signed_mrf_url'] + '" target="_blank" style="text-decoration: none; color: white; background: #333; padding: 8px 15px; border-radius: 5px;">📝 View Approved MRF</a>' if req.get('signed_mrf_url') else '<span style="color: #666; padding: 8px;">No MRF Linked</span>'}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Recruiter Summary Section
        with st.expander("💬 Recruiter Notes / Justification", expanded=True):
            st.info(item.get('justification') or "No specific notes from the recruiter.")

        # ACTION BUTTONS
        c1, c2 = st.columns([1, 5])
        
        with c1:
            if st.button("✅ Authorize Offer", key=f"auth_{item['id']}", type="primary"):
                # Move to next stage: 'Ready for Offer'
                supabase.table("placements").update({"status": "Ready for Offer"}).eq("id", item['id']).execute()
                # Update Candidate status too
                supabase.table("candidates").update({"status": "Approved for Hire"}).eq("id", item['candidate_id']).execute()
                
                st.success("Authorized! Sent to Placement Manager for Offer Generation.")
                st.rerun()
                
        with c2:
            if st.button("🚫 Reject Selection", key=f"rej_{item['id']}"):
                supabase.table("placements").update({"status": "Rejected by Mgmt"}).eq("id", item['id']).execute()
                supabase.table("candidates").update({"status": "Rejected"}).eq("id", item['candidate_id']).execute()
                st.error("Selection Rejected.")
                st.rerun()
        
        st.divider()