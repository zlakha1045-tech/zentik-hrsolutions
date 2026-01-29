import streamlit as st
from supabase import create_client
import pandas as pd
from styles import load_css

st.set_page_config(page_title="Hiring History", layout="wide")
load_css()

try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    st.error("Missing Secrets.")
    st.stop()

st.title("📂 Hiring History")
st.markdown("A complete archive of all candidates who have been **Offered** or **Hired**.")

# --- FILTERS ---
col1, col2 = st.columns(2)
with col1:
    view_mode = st.selectbox("Filter Status", ["All", "Offer Accepted", "Hired", "Offer Sent"])

# --- FETCH DATA ---
query = supabase.table("placements").select(
    "created_at, status, salary_offered, start_date, signed_mrf_url, candidates(name, email, resume_url), jobs(title, department, requisitions(signed_mrf_url))"
).order("created_at", desc=True)

if view_mode != "All":
    query = query.eq("status", view_mode)

# Execute
data = query.execute().data

if not data:
    st.info("No records found.")
else:
    # --- TABLE VIEW ---
    for row in data:
        cand = row['candidates']
        job = row['jobs']
        req = job.get('requisitions') or {}
        
        with st.expander(f"{cand['name']} - {job['title']} ({row['status']})"):
            c1, c2, c3, c4 = st.columns(4)
            c1.write(f"**Department:** {job.get('department', '-')}")
            c2.write(f"**Salary:** {row.get('salary_offered', '-')}")
            c3.write(f"**Start Date:** {row.get('start_date', '-')}")
            c4.write(f"**Hired On:** {row['created_at'][:10]}")
            
            st.divider()
            
            # LINKS SECTION
            l1, l2, l3 = st.columns(3)
            with l1:
                if cand.get('resume_url'):
                    st.link_button("📄 Candidate Resume", cand['resume_url'], use_container_width=True)
            with l2:
                if req.get('signed_mrf_url'):
                    st.link_button("📝 Original MRF", req['signed_mrf_url'], use_container_width=True)
            with l3:
                # In Placement_Manager, we saved the signed offer to 'signed_mrf_url' column of placement table
                # You might want to rename that column to 'signed_offer_url' in the future for clarity
                if row.get('signed_mrf_url'): 
                    st.link_button("🤝 Signed Offer Letter", row['signed_mrf_url'], use_container_width=True)