import streamlit as st
from supabase import create_client
from styles import load_css, hero_section
import time
import mimetypes

st.set_page_config(page_title="Placement & MRF", layout="wide")
load_css()

try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    st.error("Missing Supabase Secrets.")
    st.stop()

hero_section(
    "assets/login_hero.jpg",
    "Placement Manager",
    "Finalize hires and attach Manpower Requisition Forms"
)

# --- STEP 1: FETCH PENDING HIRES ---
st.subheader("1. Pending Placements")
st.caption("Select a candidate who has been marked as 'Pending Hire' to finalize their paperwork.")

# Fetch only placements that are waiting for MRF (status = 'Pending Hire')
# We join with candidates and jobs to get names and titles
try:
    response = supabase.table("placements").select(
        "id, candidate_id, job_id, status, candidates(name, email), jobs(title)"
    ).eq("status", "Pending Hire").execute()
    
    pending_list = response.data
except Exception as e:
    st.error(f"Error fetching placements: {e}")
    st.stop()

if not pending_list:
    st.info("✅ No pending hires found. Go to 'Candidate Analysis' to hire someone!")
    st.stop()

# Create a mapping for the dropdown
# Format: "John Doe - Sales Manager"
placement_map = {
    f"{p['candidates']['name']} - {p['jobs']['title']}": p 
    for p in pending_list
}

selected_label = st.selectbox("Select Candidate", list(placement_map.keys()))
selected_placement = placement_map[selected_label]

candidate_name = selected_placement['candidates']['name']
job_title = selected_placement['jobs']['title']
placement_id = selected_placement['id']

st.success(f"Selected: **{candidate_name}** for **{job_title}**")

# --- STEP 2: UPLOAD MRF ---
st.divider()
st.subheader("2. Upload MRF (Manpower Requisition Form)")
st.caption(f"Upload the signed approval for {candidate_name}.")

uploaded_mrf = st.file_uploader("Upload Document", type=["pdf", "docx", "png", "jpg", "jpeg"])

if st.button("💾 Finalize & Place", type="primary"):
    if uploaded_mrf:
        try:
            # 1. Upload File to Supabase Storage
            file_ext = uploaded_mrf.name.split('.')[-1]
            # Unique filename: time_placementID.ext
            file_path = f"mrf/{int(time.time())}_{placement_id}.{file_ext}"
            content_type = mimetypes.guess_type(uploaded_mrf.name)[0] or "application/octet-stream"
            
            # Use 'resumes' bucket (or create a 'documents' bucket if you prefer)
            supabase.storage.from_("resumes").upload(
                path=file_path, 
                file=uploaded_mrf.getvalue(), 
                file_options={"content-type": content_type, "upsert": "true"}
            )
            
            # Get Public URL
            mrf_url = supabase.storage.from_("resumes").get_public_url(file_path)

            # 2. Update Placement Record
            # Change status to 'Placed' and save the URL
            supabase.table("placements").update({
                "status": "Placed",
                "mrf_url": mrf_url,
                "placed_at": "now()"
            }).eq("id", placement_id).execute()
            
            # 3. Update Candidate Status (Optional, keeps them synced)
            supabase.table("candidates").update({
                "status": "Placed"
            }).eq("id", selected_placement['candidate_id']).execute()

            st.balloons()
            st.success(f"🎉 {candidate_name} has been successfully placed!")
            time.sleep(2)
            st.rerun()
            
        except Exception as e:
            st.error(f"Error finalizing placement: {e}")
    else:
        st.warning("⚠️ Please upload the MRF document first.")

# --- STEP 3: HISTORY ---
st.divider()
st.subheader("📂 Placement History")

# Fetch completed placements
try:
    history = supabase.table("placements").select(
        "placed_at, mrf_url, candidates(name), jobs(title)"
    ).eq("status", "Placed").order("placed_at", desc=True).execute().data

    if history:
        for p in history:
            with st.container():
                c1, c2, c3 = st.columns([2, 2, 1])
                c1.write(f"**{p['candidates']['name']}**")
                c2.write(f"Role: {p['jobs']['title']}")
                
                if p.get('mrf_url'):
                    c3.link_button("📄 View MRF", p['mrf_url'])
                else:
                    c3.write("No Doc")
                st.divider()
    else:
        st.caption("No finalized placements yet.")

except:
    pass