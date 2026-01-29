import streamlit as st
import base64
import os

def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

def load_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
            
            html, body, [class*="css"] {
                font-family: 'Inter', sans-serif;
            }

            /* --- 1. GLASSMORPHISM METRIC CARDS --- */
            .metric-card {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
                padding: 20px;
                text-align: center;
                backdrop-filter: blur(10px);
                transition: transform 0.2s;
            }
            .metric-card:hover {
                transform: translateY(-5px);
                border-color: rgba(255, 255, 255, 0.3);
            }
            .metric-value {
                font-size: 2.5rem;
                font-weight: 700;
                background: -webkit-linear-gradient(eee, #94a3b8);
                -webkit-background-clip: text;
                color: white; 
                margin-bottom: 5px;
            }
            .metric-label {
                font-size: 0.9rem;
                color: #94a3b8;
                letter-spacing: 1px;
                text-transform: uppercase;
                font-weight: 600;
            }

            /* --- 2. HERO SECTION --- */
            .hero-container {
                padding: 4rem 2rem;
                border-radius: 20px;
                color: white;
                text-align: center;
                background-size: cover;
                background-position: center;
                margin-bottom: 2rem;
                box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            .hero-title {
                font-size: 3.5rem;
                font-weight: 800;
                text-shadow: 0 0 20px rgba(0,0,0,0.8);
            }
            .hero-subtitle {
                font-size: 1.2rem;
                font-weight: 500;
                opacity: 0.9;
                text-shadow: 0 2px 4px rgba(0,0,0,0.8);
            }

            /* --- 3. MODERN BUTTONS --- */
            div[data-testid="stLinkButton"] > a {
                background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
                color: white !important;
                border: none;
                padding: 0.5rem 1.5rem;
                border-radius: 50px;
                font-weight: 600;
                text-decoration: none;
                box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
                transition: all 0.3s ease;
                display: block;
                text-align: center;
            }
            div[data-testid="stLinkButton"] > a:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(99, 102, 241, 0.6);
            }

            /* --- 4. SCORE BADGES --- */
            .score-badge {
                font-size: 20px;
                font-weight: 800;
                padding: 8px 16px;
                border-radius: 12px;
                text-align: center;
                width: fit-content;
                box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            }
            .score-green { background: linear-gradient(135deg, #10B981 0%, #059669 100%); color: white; }
            .score-orange { background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); color: white; }
            .score-red { background: linear-gradient(135deg, #EF4444 0%, #B91C1C 100%); color: white; }
        </style>
    """, unsafe_allow_html=True)

def hero_section(image_path, title, subtitle):
    if os.path.exists(image_path):
        img_b64 = get_base64_of_bin_file(image_path)
        st.markdown(
            f"""
            <div class="hero-container" style="
                background-image: linear-gradient(to bottom, rgba(0,0,0,0.3), rgba(0,0,0,0.8)), url('data:image/jpg;base64,{img_b64}');">
                <div class="hero-title">{title}</div>
                <div class="hero-subtitle">{subtitle}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.title(title)
        st.write(subtitle)