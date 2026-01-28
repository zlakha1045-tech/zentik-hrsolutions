import streamlit as st
from supabase import create_client
from styles import load_css
import time
import mimetypes

st.set_page_config(page_title="Submit Signed MRF", layout="wide")
load_css()

try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except:
    st.error("Missing Secrets.")
    st.stop()

st.title("📂 Submit Signed Requisition")
st.markdown("Upload your signed MRF here. You can link it to a previous draft or create a new submission.")

# --- 1. SELECTION LOGIC ---
c_sel, c_or = st.columns([3, 1])

# Fetch Drafts for the dropdown
try:
    drafts = supabase.table("requisitions").select("*").eq("status", "Draft").execute().data
except:
    drafts = []

draft_options = {f"{d['job_title']} (Req: {d['requisitor_name']})": d for d in drafts}
# Add option for Manual Upload
draft_options["-- Create New / No Draft --"] = None

selected_label = st.selectbox("Link to Draft (Optional)", list(draft_options.keys()))
selected_draft = draft_options[selected_label]

# --- 2. DETAILS INPUT ---
# If a draft is selected, we autofill. If not, user types it in.
st.divider()

if selected_draft:
    st.info(f"🔗 Linking to Draft ID: {selected_draft['id']}")
    job_title_input = st.text_input("Job Title", value=selected_draft['job_title'], disabled=True)
    req_id = selected_draft['id']
else:
    st.warning("📝 Creating a fresh submission (No draft linked).")
    job_title_input = st.text_input("Job Title", placeholder="e.g. Senior Accountant")
    req_id = None

# --- 3. UPLOAD & SUBMIT ---
c1, c2 = st.columns([1, 1])

with c1:
    st.subheader("📤 Upload Document")
    uploaded_file = st.file_uploader("Upload Signed PDF/Image", type=["pdf", "png", "jpg"])

    if uploaded_file:
        st.markdown("### 👁️ Preview")
        
        # FIX: "Blocked by Chrome" Issue
        if uploaded_file.type == "application/pdf":
            # Instead of iframe, we provide a button to view it
            st.info("📄 PDF detected.")
            st.download_button(
                "⬇️ Download to View/Verify", 
                uploaded_file, 
                file_name="preview.pdf",
                mime="application/pdf"
            )
        else:
            # Images are safe to preview directly
            st.image(uploaded_file, use_container_width=True)

with c2:
    st.subheader("🚀 Finalize Submission")
    
    if st.button("Submit for Approval", type="primary"):
        if not uploaded_file:
            st.error("Please upload a file.")
        elif not job_title_input:
            st.error("Job Title is required.")
        else:
            try:
                with st.spinner("Uploading & Submitting..."):
                    # 1. Upload File
                    file_ext = uploaded_file.name.split('.')[-1]
                    # Use timestamp if no ID to prevent overwriting
                    unique_id = req_id if req_id else int(time.time())
                    path = f"requisitions/{unique_id}_signed.{file_ext}"
                    mime = mimetypes.guess_type(uploaded_file.name)[0]
                    
                    supabase.storage.from_("resumes").upload(path, uploaded_file.getvalue(), {"content-type": mime})
                    url = supabase.storage.from_("resumes").get_public_url(path)

                    if req_id:
                        # UPDATE EXISTING DRAFT
                        supabase.table("requisitions").update({
                            "status": "Pending Approval",
                            "signed_mrf_url": url
                        }).eq("id", req_id).execute()
                    else:
                        # INSERT NEW ENTRY (Since no draft existed)
                        supabase.table("requisitions").insert({
                            "job_title": job_title_input,
                            "requisitor_name": "Uploaded Manually",
                            "status": "Pending Approval",
                            "signed_mrf_url": url,
                            "number_required": 1 # Default
                        }).execute()

                    st.balloons()
                    st.success("Submitted! Sent to Management Inbox.")
                    time.sleep(2)
                    st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")