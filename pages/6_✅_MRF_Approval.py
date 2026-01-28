import streamlit as st
from supabase import create_client
import pandas as pd

st.set_page_config(page_title="Management Approval", layout="wide")

# --- CUSTOM STYLE ---
st.markdown("""
<style>
    .approval-card {
        background-color: #1a1c24;
        border-left: 5px solid #f1c40f; /* Yellow for Pending */
        padding: 20px;
        margin-bottom: 20px;
        border-radius: 5px;
    }
    .data-label { color: #a0a0a0; font-size: 0.9em; }
    .data-value { color: #ffffff; font-weight: bold; font-size: 1.1em; }
</style>
""", unsafe_allow_html=True)

try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    st.error("Missing Supabase Secrets.")
    st.stop()

st.title("🛡️ Management Approval Board")
st.markdown("Review and authorize pending Manpower Requisitions.")

tab_pending, tab_history = st.tabs(["📥 Pending Inbox", "✅ Approval History"])

# --- TAB 1: PENDING APPROVALS ---
with tab_pending:
    # Fetch placements waiting for approval
    try:
        response = supabase.table("placements").select(
            "*, candidates(name), jobs(title, department)"
        ).eq("status", "Pending Approval").order("created_at", desc=True).execute()
        
        pending_items = response.data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        st.stop()

    if not pending_items:
        st.success("🎉 All caught up! No pending approvals.")
    else:
        for p in pending_items:
            # Layout: Card for each request
            with st.container():
                st.markdown(f"""
                <div class="approval-card">
                    <h3>{p['candidates']['name']} <span style="font-size:0.7em; color:#888;">for</span> {p['jobs']['title']}</h3>
                    <p style="color:#4da6ff;">{p['jobs'].get('department', 'General Dept')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Digital MRF Details Grid
                c1, c2, c3, c4 = st.columns(4)
                c1.markdown(f"**💰 Salary:**\n\n{p.get('proposed_salary', 'N/A')}")
                c2.markdown(f"**📅 Start Date:**\n\n{p.get('start_date', 'N/A')}")
                c3.markdown(f"**👤 Manager:**\n\n{p.get('hiring_manager', 'N/A')}")
                c4.markdown(f"**📋 Type:**\n\n{p.get('employment_type', 'N/A')}")
                
                st.markdown(f"**📝 Justification:**")
                st.info(p.get('justification', 'No justification provided.'))
                
                # Action Buttons
                col_approve, col_reject = st.columns([1, 6])
                
                with col_approve:
                    if st.button("✅ APPROVE", key=f"app_{p['id']}", type="primary"):
                        # Update status to 'Approved'
                        supabase.table("placements").update({"status": "Approved"}).eq("id", p['id']).execute()
                        # Also update Candidate status to 'Hired' officially
                        supabase.table("candidates").update({"status": "Hired"}).eq("id", p['candidate_id']).execute()
                        st.success("Approved!")
                        st.rerun()
                        
                with col_reject:
                    if st.button("🚫 REJECT", key=f"rej_{p['id']}"):
                        supabase.table("placements").update({"status": "Rejected by Mgmt"}).eq("id", p['id']).execute()
                        st.error("Request Rejected.")
                        st.rerun()
                
                st.divider()

# --- TAB 2: HISTORY ---
with tab_history:
    try:
        history = supabase.table("placements").select(
            "*, candidates(name), jobs(title)"
        ).in_("status", ["Approved", "Rejected by Mgmt"]).order("created_at", desc=True).execute().data
        
        if history:
            st.dataframe(
                pd.DataFrame(history)[['created_at', 'status', 'candidates', 'jobs', 'hiring_manager']],
                use_container_width=True
            )
        else:
            st.info("No history yet.")
    except:
        pass