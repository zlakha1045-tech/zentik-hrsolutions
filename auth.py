import streamlit as st
import extra_streamlit_components as stx
import time

# 1. Cookie Manager Setup
def get_manager():
    return stx.CookieManager()

# 2. Draw Login Form
def login_form():
    """Draws the Login UI and handles authentication."""
    cookie_manager = get_manager()
    
    # Check if already logged in via cookie
    if "token" in cookie_manager.get_all():
        if cookie_manager.get("token") == "valid_session":
            st.session_state.password_correct = True
            return True

    # Check session state (for the current run)
    if st.session_state.get("password_correct", False):
        return True

    # --- DRAW THE LOGIN UI ---
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        # The Glassmorphism Login Card
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # LOGO
        try:
            st.image("assets/logo.png", width=120) 
        except:
            st.header("Zentik Labs")
            
        st.markdown("### Welcome Back")
        st.caption("Sign in to your AI Recruitment Portal")
        
        password = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Log In", type="primary", use_container_width=True):
            if password == "zentik2026": 
                st.session_state.password_correct = True
                # Set a cookie that expires in 1 day
                cookie_manager.set("token", "valid_session", expires_at=None)
                st.rerun()
            else:
                st.error("❌ Invalid Access Key")
        
        st.markdown('</div>', unsafe_allow_html=True)

    return False

# 3. The Gatekeeper Function (This was missing!)
def require_auth():
    """
    Put this at the top of every page. 
    If not logged in, it stops execution and shows the login form.
    """
    if not login_form():
        st.stop()  # Stop the page from loading anything else