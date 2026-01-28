import streamlit as st
from supabase import create_client
from styles import load_css
import base64
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
st.markdown("Step 2: Upload the signed PDF to send it for management approval.")

# --- 1. FETCH DRAFTS ---
try:
    # Only get drafts
    drafts = supabase.table("requisitions").select("*").eq("status", "Draft").execute().data
except Exception as e:
    st.error(f"Connection Error: {e}")
    st.stop()

if not drafts:
    st.info("✅ No pending drafts found. Go to 'Create Requisition' to start one.")
    st.stop()

# --- 2. SELECT DRAFT ---
draft_map = {f"{d['job_title']} (Req: {d['requisitor_name']})": d for d in drafts}
selected_label = st.selectbox("Select Draft to Submit", list(draft_map.keys()))
selected_draft = draft_map[selected_label]

st.divider()

# --- 3. UPLOAD & PREVIEW ---
c1, c2 = st.columns([1, 1])

with c1:
    st.subheader("📤 Upload Signed Document")
    uploaded_file = st.file_uploader("Upload PDF/Image", type=["pdf", "png", "jpg"])

    if uploaded_file:
        # PREVIEW LOGIC
        st.markdown("### 👁️ Document Preview")
        if uploaded_file.type == "application/pdf":
            # PDF Preview using base64 embedding
            base64_pdf = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
        else:
            # Image Preview
            st.image(uploaded_file, use_container_width=True)

with c2:
    st.subheader("🚀 Finalize")
    st.info(f"You are submitting **{selected_draft['job_title']}** for approval.")
    
    if st.button("Submit for Approval", type="primary", disabled=(not uploaded_file)):
        if uploaded_file:
            try:
                with st.spinner("Uploading file..."):
                    # 1. Upload File
                    file_ext = uploaded_file.name.split('.')[-1]
                    path = f"requisitions/{selected_draft['id']}_signed.{file_ext}"
                    mime = mimetypes.guess_type(uploaded_file.name)[0]
                    
                    supabase.storage.from_("resumes").upload(path, uploaded_file.getvalue(), {"content-type": mime})
                    url = supabase.storage.from_("resumes").get_public_url(path)

                    # 2. Update DB (Status -> Pending Approval)
                    supabase.table("requisitions").update({
                        "status": "Pending Approval",
                        "signed_mrf_url": url
                    }).eq("id", selected_draft['id']).execute()

                    st.balloons()
                    st.success("Submitted! Sent to Management Inbox.")
                    time.sleep(2)
                    st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")