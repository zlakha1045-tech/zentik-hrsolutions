import streamlit as st
from supabase import create_client
from styles import load_css, hero_section
import json
import time
import mimetypes

st.set_page_config(page_title="Interview Room", layout="wide")
load_css()

# --- CONNECT DB ---
try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    st.error("Missing Secrets.")
    st.stop()

# --- HERO SECTION ---
hero_section("assets/dashboard_hero.jpg", "Interview & Assessment", "Conduct interviews, upload evidence, and grade candidates.")

# --- 1. SELECT CANDIDATE (Only Shortlisted) ---
st.sidebar.title("🎤 Waiting Room")
try:
    # Fetch only SHORTLISTED candidates
    cands = supabase.table("candidates").select("*, jobs(title)").eq("status", "Shortlisted").execute().data
    
    if not cands:
        st.info("No candidates are currently shortlisted. Go to 'Analysis' to shortlist someone.")
        st.stop()
        
    cand_map = {f"{c['name']} ({c['jobs']['title']})": c for c in cands}
    selected_label = st.sidebar.radio("Select Candidate", list(cand_map.keys()))
    candidate = cand_map[selected_label]

except Exception as e:
    st.error(f"Error fetching candidates: {e}")
    st.stop()

# --- 2. INTERVIEW DASHBOARD ---
st.title(f"Interviewing: {candidate['name']}")
st.caption(f"Role: {candidate['jobs']['title']} | Current Match Score: {candidate['match_score']}%")

# SPLIT LAYOUT: Guide vs. Evidence
col_guide, col_evidence = st.columns([1, 1.5])

# --- LEFT COLUMN: AI GUIDE ---
with col_guide:
    st.container(border=True)
    st.subheader("🤖 AI Interview Guide")
    st.markdown("_Ask these questions to verify resume claims:_")
    
    questions = candidate.get('suggested_questions')
    if questions:
        # Handle string vs list format
        if isinstance(questions, str):
            try: questions = json.loads(questions)
            except: questions = [questions]
            
        for i, q in enumerate(questions):
            st.info(f"**Q{i+1}:** {q}")
            st.text_area(f"Notes on Q{i+1}", height=60, key=f"note_{i}")
    else:
        st.write("No AI questions generated.")
        
    st.divider()
    st.subheader("🚩 Red Flag Check")
    red_flags = candidate.get('red_flags', 'None')
    if red_flags != 'None':
        st.warning(f"Verify this: {red_flags}")
    else:
        st.success("No resume red flags detected.")

# --- RIGHT COLUMN: EVIDENCE UPLOAD ---
with col_evidence:
    st.container(border=True)
    st.subheader("📂 Assessment Evidence")
    st.markdown("Upload test results, recordings, or take-home assignments.")

    # A. UPLOAD NEW ASSETS
    uploaded_files = st.file_uploader("Attach Evidence", accept_multiple_files=True)
    
    if uploaded_files and st.button("⬆️ Upload Files"):
        current_assets = candidate.get('interview_assets', []) or []
        # Ensure it's a list (Supabase sometimes returns None)
        if not isinstance(current_assets, list): current_assets = []

        for file in uploaded_files:
            try:
                # 1. Upload to Supabase Storage
                file_ext = file.name.split('.')[-1]
                file_path = f"evidence/{candidate['id']}/{int(time.time())}_{file.name}"
                mime = mimetypes.guess_type(file.name)[0]
                
                supabase.storage.from_("resumes").upload(file_path, file.getvalue(), {"content-type": mime})
                public_url = supabase.storage.from_("resumes").get_public_url(file_path)
                
                # 2. Add to Local List
                current_assets.append({
                    "name": file.name,
                    "url": public_url,
                    "type": file_ext
                })
                
            except Exception as e:
                st.error(f"Upload failed for {file.name}: {e}")

        # 3. Save to DB
        supabase.table("candidates").update({"interview_assets": current_assets}).eq("id", candidate['id']).execute()
        st.success("Evidence Attached!")
        time.sleep(1)
        st.rerun()

    # B. VIEW EXISTING ASSETS
    st.divider()
    st.subheader("🗂️ Attached Files")
    existing_assets = candidate.get('interview_assets', [])
    if existing_assets and isinstance(existing_assets, list):
        for asset in existing_assets:
            c1, c2 = st.columns([4, 1])
            c1.write(f"📄 **{asset['name']}**")
            c1.caption(asset['url'])
            c2.link_button("View", asset['url'])
    else:
        st.info("No evidence uploaded yet.")

# --- 3. FINAL DECISION ---
st.divider()
st.subheader("👨‍⚖️ Interview Decision")

with st.form("decision_form"):
    final_notes = st.text_area("Final Interview Assessment / Executive Summary", height=150, placeholder="E.g., Candidate showed strong technical skills but lacked clarity on project X...")
    
    c1, c2 = st.columns(2)
    pass_interview = c1.form_submit_button("✅ Pass to Final Approval", type="primary", use_container_width=True)
    fail_interview = c2.form_submit_button("❌ Reject Candidate", type="secondary", use_container_width=True)

    if pass_interview:
        if not final_notes:
            st.warning("Please add assessment notes before passing.")
        else:
            # Update status AND save the notes
            # We append the interview notes to the existing notes or overwrite
            supabase.table("candidates").update({
                "status": "Pending Final Approval",
                "interview_notes": final_notes
            }).eq("id", candidate['id']).execute()
            
            # Create Placement Record (Buffer for Approval Page)
            placement_data = {
                "candidate_id": candidate['id'],
                "job_id": candidate['job_id'],
                "status": "Pending Final Approval",
                "justification": final_notes
            }
            supabase.table("placements").insert(placement_data).execute()

            st.balloons()
            st.success("Candidate moved to Authorization Queue!")
            time.sleep(2)
            st.rerun()

    if fail_interview:
        supabase.table("candidates").update({
            "status": "Rejected",
            "interview_notes": f"REJECTED IN INTERVIEW: {final_notes}"
        }).eq("id", candidate['id']).execute()
        st.error("Candidate Rejected.")
        time.sleep(2)
        st.rerun()