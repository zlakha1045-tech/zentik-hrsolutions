import streamlit as st
from supabase import create_client
import pandas as pd

st.set_page_config(page_title="Approve MRF", layout="wide")

try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    st.stop()

st.title("🛡️ Requisition Approval & Archive")

tab_inbox, tab_archive = st.tabs(["📥 Approval Inbox", "🗄️ MRF Archive"])

# --- TAB 1: INBOX ---
with tab_inbox:
    # Fetch Pending
    pending = supabase.table("requisitions").select("*").eq("status", "Pending Approval").execute().data
    
    if not pending:
        st.success("All caught up! No pending requests.")
    else:
        for r in pending:
            with st.expander(f"ACTION REQUIRED: {r['job_title']} ({r['requisitor_name']})", expanded=True):
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.write(f"**Justification:** {r.get('skills_req', 'N/A')}")
                    st.metric("Headcount", r['number_required'])
                with c2:
                    if r.get('signed_mrf_url'):
                        st.link_button("📄 View Signed PDF", r['signed_mrf_url'])
                    
                    # Approve/Reject
                    col_a, col_b = st.columns(2)
                    if col_a.button("✅ APPROVE", key=f"ok_{r['id']}"):
                        supabase.table("requisitions").update({"status": "Approved"}).eq("id", r['id']).execute()
                        st.rerun()
                    if col_b.button("🚫 REJECT", key=f"no_{r['id']}"):
                        supabase.table("requisitions").update({"status": "Rejected"}).eq("id", r['id']).execute()
                        st.rerun()

# --- TAB 2: ARCHIVE (Your Requirement) ---
with tab_archive:
    st.markdown("### 📜 Master Requisition Database")
    # Fetch EVERYTHING except Drafts
    history = supabase.table("requisitions").select("*").neq("status", "Draft").order("created_at", desc=True).execute().data
    
    if history:
        # Create a nice dataframe
        df = pd.DataFrame(history)
        # Select clean columns
        display_df = df[['created_at', 'job_title', 'requisitor_name', 'status', 'signed_mrf_url']]
        
        # Display as a searchable table
        st.dataframe(
            display_df,
            column_config={
                "signed_mrf_url": st.column_config.LinkColumn("Signed Doc"),
                "created_at": st.column_config.DatetimeColumn("Date", format="D MMM YYYY"),
            },
            use_container_width=True
        )
    else:
        st.info("No history yet.")