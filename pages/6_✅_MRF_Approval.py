import streamlit as st
from supabase import create_client
from styles import load_css, hero_section
import time
import mimetypes

st.set_page_config(page_title="MRF Approval", layout="wide")
load_css()
supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

hero_section(
    "assets/login_hero.jpg", 
    "Management Approval",
    "Review, Sign, and Approve Manpower Requisitions"
)

# Create Tabs for Workflow
tab_inbox, tab_history = st.tabs(["📥 Pending Inbox", "📜 Approval History"])

# ==========================================
# TAB 1: PENDING INBOX (Your To-Do List)
# ==========================================
with tab_inbox:
    try:
        # Get all placements waiting for approval
        response = supabase.table("placements").select(
            "*, jobs(title, department), candidates(name, email)"
        ).eq("status", "pending_approval").order("created_at", desc=True).execute()
        
        pending_items = response.data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        pending_items = []

    if not pending_items:
        st.info("✅ All caught up! No pending approvals.")
    else:
        st.markdown(f"### ⏳ Waiting for Signature ({len(pending_items)})")
        
        for item in pending_items:
            with st.container():
                # Header
                c1, c2, c3 = st.columns([2, 2, 2])
                c1.markdown(f"**{item['candidates']['name']}**")
                c2.markdown(f"Role: **{item['jobs']['title']}**")
                c3.caption(f"Drafted: {item['created_at'][:10]}")
                
                # Review Area
                with st.expander(f"Review Requisition", expanded=False):
                    col_left, col_right = st.columns(2)
                    
                    # LEFT: Review Draft
                    with col_left:
                        st.info("ℹ️ **Step 1: Review Draft**")
                        st.write(f"Department: **{item['jobs']['department']}**")
                        st.markdown(f"[📄 Download Draft MRF]({item['mrf_url']})")
                        
                        st.divider()
                        
                        # REJECT BUTTON
                        with st.form(key=f"reject_{item['id']}"):
                            reason = st.text_input("Reason for Rejection")
                            if st.form_submit_button("❌ Reject Request"):
                                if reason:
                                    supabase.table("placements").update({
                                        "status": "rejected",
                                        "rejection_reason": reason
                                    }).eq("id", item['id']).execute()
                                    st.rerun()
                                else:
                                    st.warning("Please provide a reason.")

                    # RIGHT: Approve & Sign
                    with col_right:
                        st.success("✅ **Step 2: Approve & Sign**")
                        st.caption("Upload the signed/stamped MRF to finalize.")
                        
                        signed_file = st.file_uploader("Upload Signed MRF", type=["pdf", "jpg", "png"], key=f"up_{item['id']}")
                        
                        if st.button("🚀 Approve & Hire", key=f"btn_{item['id']}", type="primary"):
                            if signed_file:
                                try:
                                    # Upload
                                    file_ext = signed_file.name.split('.')[-1]
                                    path = f"signed_mrf/{int(time.time())}_{item['id']}.{file_ext}"
                                    content_type = mimetypes.guess_type(signed_file.name)[0]
                                    
                                    supabase.storage.from_("resumes").upload(
                                        path=path, 
                                        file=signed_file.getvalue(), 
                                        file_options={"content-type": content_type, "upsert": "true"}
                                    )
                                    signed_url = supabase.storage.from_("resumes").get_public_url(path)

                                    # Update DB (Change status to approved)
                                    supabase.table("placements").update({
                                        "status": "approved",
                                        "signed_mrf_url": signed_url
                                    }).eq("id", item['id']).execute()
                                    
                                    st.balloons()
                                    time.sleep(1)
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"Upload failed: {e}")
                            else:
                                st.warning("Upload the signed doc first.")
            st.divider()

# ==========================================
# TAB 2: HISTORY (The Archive)
# ==========================================
with tab_history:
    st.markdown("### 🗄️ Placements Archive")
    st.caption("This is your permanent record for analysis.")
    
    try:
        # Fetch everything that is NOT pending
        history_response = supabase.table("placements").select(
            "*, jobs(title, department), candidates(name)"
        ).neq("status", "pending_approval").order("created_at", desc=True).execute()
        
        history_items = history_response.data
    except:
        history_items = []

    if history_items:
        for h in history_items:
            # Color Code the Status
            color = "🟢" if h['status'] == 'approved' else "🔴"
            
            with st.expander(f"{color} {h['candidates']['name']} - {h['jobs']['title']}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Status:** {h['status'].upper()}")
                    st.write(f"**Date:** {h['created_at'][:10]}")
                    st.write(f"**Department:** {h['jobs']['department']}")
                
                with c2:
                    if h['status'] == 'approved':
                        st.success("Candidate Hired")
                        st.link_button("📄 View Signed MRF", h['signed_mrf_url'])
                    else:
                        st.error("Candidate Rejected")
                        st.write(f"**Reason:** {h.get('rejection_reason', 'N/A')}")
                        st.link_button("📄 View Draft MRF", h['mrf_url'])
    else:
        st.info("No history found yet.")