import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import os
import base64
from datetime import datetime
from PIL import Image

# ==============================
# 1. GOOGLE SHEETS CONNECTION
# ==============================
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(worksheet_name):
    try:
        # We use ttl=0 to always get the freshest office data
        return conn.read(worksheet=worksheet_name, ttl="0s")
    except Exception:
        return pd.DataFrame()

# ==============================
# 2. UI & STYLING (ZK7 Office)
# ==============================
def set_ui_design(image_file):
    if os.path.exists(image_file):
        with open(image_file, "rb") as f:
            data = f.read()
        encoded_string = base64.b64encode(data).decode()
        st.markdown(f"""
            <style>
            .stApp {{
                background-image: url("data:image/png;base64,{encoded_string}");
                background-attachment: fixed;
                background-size: cover;
                background-position: center;
            }}
            [data-testid="stSidebar"] {{ background-color: rgba(0, 0, 0, 0.7) !important; backdrop-filter: blur(10px); }}
            .styled-header {{ 
                background-color: #262730; 
                padding: 30px; border-radius: 20px; text-align: center; margin-bottom: 30px; 
            }}
            .styled-header h1, .styled-header p {{ color: white !important; margin: 0; }}
            .st-emotion-cache-12w0qpk {{ background-color: rgba(255, 255, 255, 0.9) !important; border-radius: 15px !important; padding: 25px !important; }}
            </style>
        """, unsafe_allow_html=True)

set_ui_design('BackImage.jpg')
if not os.path.exists("images"): os.makedirs("images")

# ==============================
# 3. AUTHENTICATION
# ==============================
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'username': ""})

if not st.session_state['logged_in']:
    st.markdown('<div class="styled-header"><h1>🌸 Sakura97 Secure Access</h1><p>ZK7 Office</p></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Login", "Create Account"])
    
    with tab1:
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                df = get_data("users")
                if not df.empty and u in df['username'].values:
                    match = df[(df['username'] == u) & (df['password'].astype(str) == p)]
                    if not match.empty:
                        st.session_state.update({'logged_in': True, 'username': u})
                        st.rerun()
                st.error("Access Denied: Check username/password or tab headers.")

    with tab2:
        with st.form("signup"):
            nu = st.text_input("New Username")
            np = st.text_input("New Password", type="password")
            if st.form_submit_button("Sign Up"):
                df = get_data("users")
                if nu and np:
                    new_row = pd.DataFrame([{"username": nu, "password": np}])
                    updated_df = pd.concat([df, new_row], ignore_index=True) if not df.empty else new_row
                    conn.update(worksheet="users", data=updated_df)
                    st.success("Account created! You can login now.")
    st.stop()

# ==============================
# 4. MAIN SYSTEM
# ==============================
curr_user = st.session_state['username']
st.sidebar.title(f"👤 {curr_user}")
if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False
    st.rerun()

st.markdown(f'<div class="styled-header"><h1>🌸 Sakura97 Stock Management</h1><p>ZK7 Office | {curr_user}</p></div>', unsafe_allow_html=True)

menu = st.sidebar.selectbox("Menu", ["View Stock", "Stock In", "Stock Out", "Daily Reports"])

# All functional logic for Stock In/Out and Reports follows here...
# (Data is pulled from 'stock' and 'transactions' tabs)
