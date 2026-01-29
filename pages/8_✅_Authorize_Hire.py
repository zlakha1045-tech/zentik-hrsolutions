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
st.markdown("Review candidates passed from the **Interview Room**. Check assessment evidence and recruiter notes before authorizing.")

# --- FETCH PENDING APPROVALS ---
try:
    # UPDATED QUERY: Fetch interview_assets and interview_notes from candidates table
    response = supabase.table("placements").select(
        "*, candidates(name, email, resume_url, interview_assets, interview_notes), jobs(title, department, requisitions(signed_mrf_url, number_required))"
    ).eq("status", "Pending Final Approval").execute()
    
    approvals = response.data
except Exception as e:
    st.error(f"Error fetching data: {e}")
    st.stop()

if not approvals:
    st.info("✅ No candidates waiting for final authorization.")
    st.stop()

# --- DISPLAY CARDS ---
for item in approvals:
    cand = item['candidates']
    job = item['jobs']
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

        c1, c2 = st.columns([1, 1])

        # Recruiter / Interview Notes
        with c1:
            st.subheader("💬 Interview Assessment")
            # We prefer the specific interview notes from the placement record justification
            notes = item.get('justification') or cand.get('interview_notes') or "No specific notes provided."
            st.info(notes)

        # Evidence Display
        with c2:
            st.subheader("📹 Assessment Evidence")
            assets = cand.get('interview_assets')
            
            if assets and isinstance(assets, list) and len(assets) > 0:
                for asset in assets:
                    # Renders a clickable button/link for each video or test result
                    st.markdown(f"📎 **[{asset['name']}]({asset['url']})**")
            else:
                st.markdown("_No files uploaded in Interview Room._")

        st.divider()

        # ACTION BUTTONS
        btn_col1, btn_col2 = st.columns([1, 5])
        
        with btn_col1:
            if st.button("✅ Authorize Offer", key=f"auth_{item['id']}", type="primary"):
                # Move to next stage: 'Ready for Offer'
                supabase.table("placements").update({"status": "Ready for Offer"}).eq("id", item['id']).execute()
                # Update Candidate status too
                supabase.table("candidates").update({"status": "Approved for Hire"}).eq("id", item['candidate_id']).execute()
                
                st.success("Authorized! Sent to Placement Manager for Offer Generation.")
                st.rerun()
                
        with btn_col2:
            if st.button("🚫 Reject Selection", key=f"rej_{item['id']}"):
                supabase.table("placements").update({"status": "Rejected by Mgmt"}).eq("id", item['id']).execute()
                supabase.table("candidates").update({"status": "Rejected"}).eq("id", item['candidate_id']).execute()
                st.error("Selection Rejected.")
                st.rerun()
        
        st.divider()