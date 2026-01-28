import streamlit as st
from supabase import create_client
from styles import load_css, hero_section
import time
import mimetypes

st.set_page_config(page_title="Placement & MRF", layout="wide")
load_css()
supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

hero_section(
    "assets/login_hero.jpg", # Reusing an image, you can add 'placement_hero.jpg' later
    "Placement Manager",
    "Finalize hires and attach Manpower Requisition Forms"
)

# --- STEP 1: SELECT JOB ---
st.subheader("1. Select Position")
try:
    jobs = supabase.table("jobs").select("id, title, department").eq("status", "active").execute()
    job_map = {f"{j['title']} ({j['department']})": j['id'] for j in jobs.data}
except:
    st.error("Error loading jobs.")
    st.stop()

if not job_map:
    st.warning("No active jobs.")
    st.stop()

selected_job_label = st.selectbox("Choose Job Opening", list(job_map.keys()))
selected_job_id = job_map[selected_job_label]

# --- STEP 2: SELECT CANDIDATE ---
st.subheader("2. Select Candidate")
# Get candidates who applied for this job, sorted by score
try:
    # Join applications with candidates table
    apps = supabase.table("applications").select(
        "candidate_id, match_score, candidates(id, name, email)"
    ).eq("job_id", selected_job_id).order("match_score", desc=True).execute()
    
    cand_map = {}
    if apps.data:
        for app in apps.data:
            c = app['candidates']
            if c:
                label = f"{c['name']} (Score: {app['match_score']}%)"
                cand_map[label] = c['id']
    
except Exception as e:
    st.error(f"Error loading candidates: {e}")
    cand_map = {}

if not cand_map:
    st.info("No candidates have applied for this job yet.")
    st.stop()

selected_cand_label = st.selectbox("Choose Candidate to Hire", list(cand_map.keys()))
selected_cand_id = cand_map[selected_cand_label]

# --- STEP 3: UPLOAD MRF ---
st.subheader("3. Upload MRF (Manpower Requisition Form)")
st.caption("Upload the approved signed form (PDF/Word/Image) to finalize this placement.")

uploaded_mrf = st.file_uploader("Upload MRF", type=["pdf", "docx", "png", "jpg", "jpeg"])

if st.button("💾 Finalize Placement", type="primary"):
    if uploaded_mrf:
        try:
            # 1. Upload File
            file_ext = uploaded_mrf.name.split('.')[-1]
            file_path = f"mrf/{int(time.time())}_{selected_cand_id}.{file_ext}"
            content_type = mimetypes.guess_type(uploaded_mrf.name)[0]
            
            supabase.storage.from_("resumes").upload(
                path=file_path, 
                file=uploaded_mrf.getvalue(), 
                file_options={"content-type": content_type, "upsert": "true"}
            )
            mrf_url = supabase.storage.from_("resumes").get_public_url(file_path)

            # 2. Create Placement Record
            placement_data = {
                "job_id": selected_job_id,
                "candidate_id": selected_cand_id,
                "mrf_url": mrf_url,
                "status": "pending_approval"
            }
            supabase.table("placements").insert(placement_data).execute()
            
            st.success("🎉 Placement Created Successfully!")
            st.balloons()
            
        except Exception as e:
            st.error(f"Error saving placement: {e}")
    else:
        st.warning("Please upload the MRF document first.")

# --- VIEW EXISTING PLACEMENTS ---
st.divider()
st.subheader("Recent Placements")
places = supabase.table("placements").select(
    "created_at, status, mrf_url, jobs(title), candidates(name)"
).order("created_at", desc=True).execute()

if places.data:
    for p in places.data:
        with st.container():
            c1, c2, c3 = st.columns([2, 2, 1])
            c1.write(f"**{p['candidates']['name']}**")
            c1.caption(f"Role: {p['jobs']['title']}")
            c2.write(f"Status: `{p['status']}`")
            c3.link_button("View MRF", p['mrf_url'])
            st.divider()