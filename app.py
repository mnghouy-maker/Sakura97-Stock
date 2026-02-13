import streamlit as st
import sqlite3
import os
import base64
import pandas as pd
import hashlib
from datetime import datetime
from PIL import Image

# ==============================
# 1. DATABASE & AUTH SETUP
# ==============================
conn = sqlite3.connect('stock.db', check_same_thread=False)
c = conn.cursor()

c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
c.execute('''CREATE TABLE IF NOT EXISTS stock 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT UNIQUE, 
              quantity INTEGER, image_path TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS transactions 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT, 
              type TEXT, qty INTEGER, date TEXT)''')
conn.commit()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def create_user(username, password):
    try:
        c.execute('INSERT INTO users(username,password) VALUES (?,?)', (username, make_hashes(password)))
        conn.commit()
        return True
    except: return False

def login_user(username, password):
    c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, make_hashes(password)))
    return c.fetchone()

if not os.path.exists("images"):
    os.makedirs("images")

# ==============================
# 2. PREMIUM UI & FONT STYLING
# ==============================
def set_ui_design(image_file):
    if os.path.exists(image_file):
        with open(image_file, "rb") as f:
            data = f.read()
        encoded_string = base64.b64encode(data).decode()
        st.markdown(f"""
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

            /* Global Font Settings */
            html, body, [class*="st-"] {{
                font-family: 'Inter', sans-serif !important;
            }}

            /* Full Screen Background */
            .stApp {{
                background-image: url("data:image/png;base64,{encoded_string}");
                background-attachment: fixed;
                background-size: cover;
                background-position: center;
            }}

            /* Professional Sidebar (Glass) */
            [data-testid="stSidebar"] {{
                background-color: rgba(15, 15, 15, 0.7) !important;
                backdrop-filter: blur(15px);
                border-right: 1px solid rgba(255,255,255,0.1);
            }}

            /* Main Header Design */
            .main-header {{
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                padding: 40px;
                border-radius: 24px;
                text-align: center;
                border: 1px solid rgba(255, 255, 255, 0.2);
                margin-bottom: 30px;
                box-shadow: 0 15px 35px rgba(0,0,0,0.2);
            }}
            .main-header h1 {{ color: white !important; font-weight: 700; letter-spacing: -1px; }}
            .main-header p {{ color: rgba(255,255,255,0.8) !important; font-weight: 300; }}

            /* Content Cards */
            .content-card {{
                background: white;
                padding: 25px;
                border-radius: 16px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
                margin-bottom: 15px;
                border-left: 5px solid #1E1E1E;
            }}

            /* Footer Fixed Bottom Left */
            .footer-credit {{
                position: fixed;
                left: 20px;
                bottom: 20px;
                background: rgba(0, 0, 0, 0.8);
                color: #ffffff !important;
                padding: 12px 24px;
                border-radius: 12px;
                font-size: 13px;
                font-weight: 600;
                letter-spacing: 0.5px;
                z-index: 1000;
                border: 1px solid rgba(255,255,255,0.1);
            }}

            /* Button Styling */
            .stButton>button {{
                width: 100%;
                border-radius: 8px !important;
                font-weight: 600 !important;
                text-transform: uppercase;
                letter-spacing: 1px;
                padding: 10px !important;
            }}
            </style>
            <div class="footer-credit">Created by: Sino Menghuy</div>
        """, unsafe_allow_html=True)

set_ui_design('BackImage.jpg')

# ==============================
# 3. LOGIN & ACCESS CONTROL
# ==============================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.markdown('<div class="main-header"><h1>🌸 Sakura97</h1><p>Executive Stock Management System</p></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        tab1, tab2 = st.tabs(["Secure Login", "Register"])
        with tab1:
            u = st.text_input("Username", key="login_u")
            p = st.text_input("Password", type="password", key="login_p")
            if st.button("Access System"):
                if login_user(u, p):
                    st.session_state['logged_in'] = True
                    st.session_state['user'] = u
                    st.rerun()
                else: st.error("Invalid Credentials")
        with tab2:
            nu = st.text_input("New Username")
            np = st.text_input("New Password", type="password")
            if st.button("Create Account"):
                if create_user(nu, np): st.success("Account Ready. Please Login.")
                else: st.error("Username taken.")

# ==============================
# 4. PROTECTED APP CONTENT
# ==============================
else:
    st.sidebar.markdown(f"### 👤 {st.session_state['user']}")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    menu = st.sidebar.radio("NAVIGATION", ["Inventory Overview", "Stock In", "Stock Out", "Audit Reports"])
    
    st.markdown(f'<div class="main-header"><h1>{menu}</h1><p>Sakura97 Corporate Terminal</p></div>', unsafe_allow_html=True)

    if menu == "Inventory Overview":
        df = pd.read_sql_query("SELECT product_name, quantity FROM stock", conn)
        if not df.empty:
            for _, row in df.iterrows():
                st.markdown(f"""
                <div class="content-card">
                    <h3 style="margin:0; color:#1E1E1E;">{row['product_name']}</h3>
                    <p style="margin:5px 0 0 0; color:#666;">Current Balance: <b>{row['quantity']} Units</b></p>
                </div>
                """, unsafe_allow_html=True)
        else: st.info("Warehouse currently empty.")

    elif menu == "Stock In":
        with st.form("in_form"):
            name = st.text_input("Product Identifier")
            qty = st.number_input("Unit Quantity", min_value=1)
            if st.form_submit_button("Confirm Inbound"):
                if name:
                    try:
                        c.execute("INSERT INTO stock (product_name, quantity) VALUES (?, ?)", (name, qty))
                    except:
                        c.execute("UPDATE stock SET quantity = quantity + ? WHERE product_name = ?", (qty, name))
                    c.execute("INSERT INTO transactions (product_name, type, qty, date) VALUES (?, ?, ?, ?)", 
                              (name, "IN", qty, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit()
                    st.success(f"Log Updated: {name} units added.")
                else: st.error("Product name required.")

    elif menu == "Stock Out":
        c.execute("SELECT product_name FROM stock")
        prods = [r[0] for r in c.fetchall()]
        if prods:
            with st.form("out_form"):
                sel = st.selectbox("Select Product", prods)
                q = st.number_input("Units to Remove", min_value=1)
                if st.form_submit_button("Confirm Outbound"):
                    c.execute("SELECT quantity FROM stock WHERE product_name = ?", (sel,))
                    curr = c.fetchone()[0]
                    if q <= curr:
                        c.execute("UPDATE stock SET quantity = ? WHERE product_name = ?", (curr - q, sel))
                        c.execute("INSERT INTO transactions (product_name, type, qty, date) VALUES (?, ?, ?, ?)", 
                                  (sel, "OUT", q, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        conn.commit()
                        st.success("Outbound transaction finalized.")
                        st.rerun()
                    else: st.error("Inadequate stock levels.")

    elif menu == "Audit Reports":
        st.write("### Internal Audit Logs")
        report = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)
        st.dataframe(report, use_container_width=True)
