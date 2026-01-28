import streamlit as st
from supabase import create_client
import pandas as pd

st.set_page_config(page_title="Management Approval", layout="wide")

# --- CUSTOM STYLE ---
st.markdown("""
<style>
    .approval-card {
        background-color: #1a1c24;
        border-left: 5px solid #f1c40f; 
        padding: 20px;
        margin-bottom: 20px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    st.error("Missing Supabase Secrets.")
    st.stop()

st.title("🛡️ Management Approval Board")
st.markdown("Review Manpower Requisitions. **Approving** an MRF automatically creates a **Draft Job** for HR.")

tab_pending, tab_history = st.tabs(["📥 Pending Inbox", "📜 History"])

# --- TAB 1: PENDING APPROVALS ---
with tab_pending:
    # Fetch Pending Requisitions
    try:
        response = supabase.table("requisitions").select("*").eq("status", "Pending Approval").order("created_at", desc=True).execute()
        pending_items = response.data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        st.stop()

    if not pending_items:
        st.success("🎉 All caught up! No pending approvals.")
    else:
        for r in pending_items:
            # Layout: Card for each request
            with st.container():
                st.markdown(f"""
                <div class="approval-card">
                    <h3>{r['job_title']} <span style="font-size:0.7em; color:#888;">requested by</span> {r['requisitor_name']}</h3>
                    <p style="color:#4da6ff;">{r['requisitor_dept']} | {r['recruitment_type']} | {r['number_required']} Position(s)</p>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2 = st.columns([3, 1])
                
                with c1:
                    st.markdown("**🎓 Justification & Requirements:**")
                    st.info(f"**Reason:** {r.get('replacement_reason', 'New Position')}\n\n**Skills:** {r.get('skills_req')}\n\n**Responsibilities:** {r.get('responsibilities')}")
                
                with c2:
                    if r.get('signed_mrf_url'):
                        st.link_button("📄 View Signed PDF", r['signed_mrf_url'], use_container_width=True)
                    else:
                        st.warning("No PDF Attached")

                # ACTIONS
                col_approve, col_reject = st.columns([1, 4])
                
                with col_approve:
                    if st.button("✅ APPROVE", key=f"app_{r['id']}", type="primary"):
                        try:
                            # 1. Update MRF Status
                            supabase.table("requisitions").update({"status": "Approved"}).eq("id", r['id']).execute()
                            
                            # 2. AUTO-CREATE DRAFT JOB
                            # We merge specific requirements into one block for the AI
                            ai_requirements = f"- Education: {r.get('education_req')}\n- Skills: {r.get('skills_req')}\n- Experience: {r.get('experience_req')}"
                            
                            new_job = {
                                "title": r['job_title'],
                                "department": r['requisitor_dept'],
                                "status": "Draft",  # HR must review before publishing
                                "requisition_id": r['id'],
                                "requirements": ai_requirements, # Pre-fill for AI
                                "description": r.get('responsibilities'),
                                "location": "On-Site" # Default
                            }
                            supabase.table("jobs").insert(new_job).execute()
                            
                            st.balloons()
                            st.success("Approved! Draft Job created in Job Manager.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

                with col_reject:
                    if st.button("🚫 REJECT", key=f"rej_{r['id']}"):
                        supabase.table("requisitions").update({"status": "Rejected"}).eq("id", r['id']).execute()
                        st.warning("Requisition Rejected.")
                        st.rerun()
                
                st.divider()

# --- TAB 2: HISTORY ---
with tab_history:
    # (Simple table view)
    try:
        hist = supabase.table("requisitions").select("created_at, job_title, status, requisitor_name").neq("status", "Pending Approval").order("created_at", desc=True).execute().data
        if hist:
            st.dataframe(pd.DataFrame(hist), use_container_width=True)
    except:
        pass