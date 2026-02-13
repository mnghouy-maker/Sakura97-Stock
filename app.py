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

c.execute('''CREATE TABLE IF NOT EXISTS users 
             (username TEXT PRIMARY KEY, password TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS stock 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
             product_name TEXT UNIQUE, 
             quantity INTEGER, 
             image_path TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS transactions 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
             product_name TEXT, type TEXT, qty INTEGER, date TEXT)''')
conn.commit()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def create_user(username, password):
    try:
        c.execute('INSERT INTO users(username,password) VALUES (?,?)', (username, make_hashes(password)))
        conn.commit()
        return True
    except:
        return False

def login_user(username, password):
    c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, make_hashes(password)))
    return c.fetchone()

if not os.path.exists("images"):
    os.makedirs("images")

# ==============================
# 2. PREMIUM UI & GLASSMORPHISM
# ==============================
def set_ui_design(image_file):
    if os.path.exists(image_file):
        with open(image_file, "rb") as f:
            data = f.read()
        encoded_string = base64.b64encode(data).decode()
        st.markdown(f"""
            <style>
            /* Global Background */
            .stApp {{
                background-image: url("data:image/png;base64,{encoded_string}");
                background-attachment: fixed;
                background-size: cover;
                background-position: center;
            }}

            /* Frosted Glass Sidebar */
            [data-testid="stSidebar"] {{ 
                background: rgba(255, 255, 255, 0.05) !important; 
                backdrop-filter: blur(20px); 
                border-right: 1px solid rgba(255, 255, 255, 0.1);
            }}

            /* Main Header Design */
            .styled-header {{ 
                background: rgba(30, 30, 35, 0.8); 
                padding: 40px; 
                border-radius: 25px; 
                text-align: center; 
                color: white; 
                margin-bottom: 35px;
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
            
            .styled-header h1 {{ font-size: 2.5rem; margin-bottom: 5px; color: #FFFFFF; }}
            .styled-header p {{ font-size: 1.1rem; color: #d1d1d1; }}

            /* Fixed Bottom Left Footer */
            .sino-footer {{
                position: fixed;
                left: 20px;
                bottom: 20px;
                background: rgba(0, 0, 0, 0.7);
                color: #ffffff;
                padding: 12px 25px;
                border-radius: 12px;
                z-index: 9999;
                font-size: 14px;
                font-weight: 500;
                border: 1px solid rgba(255, 255, 255, 0.2);
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            }}

            /* White Content Cards for Data Visibility */
            .content-card {{
                background: rgba(255, 255, 255, 0.95);
                padding: 25px;
                border-radius: 20px;
                color: #1a1a1a;
                margin-bottom: 20px;
                box-shadow: 0 8px 20px rgba(0,0,0,0.1);
            }}

            /* Input Form Styling */
            .stForm {{
                background: rgba(255, 255, 255, 0.9) !important;
                border-radius: 20px !important;
                padding: 30px !important;
                border: none !important;
            }}

            .black-text {{ color: #000000 !important; font-weight: 600; }}
            </style>
            
            <div class="sino-footer">Created by: Sino Menghuy</div>
        """, unsafe_allow_html=True)
    else:
        st.error("Error: 'BackImage.jpg' not found in root folder.")

set_ui_design('BackImage.jpg')

# ==============================
# 3. AUTHENTICATION LOGIC
# ==============================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

st.sidebar.markdown("### 🔐 Secure Access")
auth_mode = st.sidebar.radio("Navigation", ["Login", "Sign Up"])

if not st.session_state['logged_in']:
    st.markdown('<div class="styled-header"><h1>🌸 Sakura97 Stock Management</h1><p>Luxury Estate Inventory Portal</p></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("auth_box"):
            if auth_mode == "Sign Up":
                st.markdown('<h2 class="black-text">Create New Account</h2>', unsafe_allow_html=True)
                new_user = st.text_input("Username")
                new_pass = st.text_input("Password", type='password')
                if st.form_submit_button("Register Account"):
                    if create_user(new_user, new_pass):
                        st.success("Success! Please switch to Login in the sidebar.")
                    else: st.error("Username taken.")
            else:
                st.markdown('<h2 class="black-text">System Login</h2>', unsafe_allow_html=True)
                user = st.text_input("Username")
                password = st.text_input("Password", type='password')
                if st.form_submit_button("Sign In"):
                    if login_user(user, password):
                        st.session_state['logged_in'] = True
                        st.session_state['user'] = user
                        st.rerun()
                    else: st.error("Access Denied: Invalid Credentials")

# ==============================
# 4. PROTECTED SYSTEM CONTENT
# ==============================
else:
    st.sidebar.success(f"Connected: {st.session_state['user']}")
    if st.sidebar.button("Logout of System"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.markdown('<div class="styled-header"><h1>🌸 Sakura97 Stock Management</h1><p>Managed by: ZK7 Office</p></div>', unsafe_allow_html=True)
    
    menu = st.sidebar.selectbox("Dashboard Menu", ["View Stock", "Stock In", "Stock Out", "Daily Reports"])

    if menu == "View Stock":
        st.markdown('<h3 style="color:white; text-shadow: 2px 2px 4px #000;">📦 Real-Time Inventory</h3>', unsafe_allow_html=True)
        df = pd.read_sql_query("SELECT product_name, quantity FROM stock", conn)
        
        if not df.empty:
            for index, row in df.iterrows():
                st.markdown(f"""
                <div class="content-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h2 style="margin:0;">{row['product_name']}</h2>
                        <h3 style="margin:0; color:#2e7d32;">{row['quantity']} Units</h3>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("No items found in the current inventory.")

    elif menu == "Stock In":
        st.markdown('<h3 style="color:white; text-shadow: 2px 2px 4px #000;">📥 Inventory Intake</h3>', unsafe_allow_html=True)
        with st.form("intake_form"):
            st.markdown('<p class="black-text">Product Name</p>', unsafe_allow_html=True)
            name = st.text_input("").strip()
            st.markdown('<p class="black-text">Quantity to Add</p>', unsafe_allow_html=True)
            qty = st.number_input("", min_value=1)
            
            if st.form_submit_button("Confirm Stock In"):
                if name:
                    try:
                        c.execute("INSERT INTO stock (product_name, quantity) VALUES (?, ?)", (name, qty))
                    except:
                        c.execute("UPDATE stock SET quantity = quantity + ? WHERE product_name = ?", (qty, name))
                    
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    c.execute("INSERT INTO transactions (product_name, type, qty, date) VALUES (?, 'IN', ?, ?)", (name, qty, now))
                    conn.commit()
                    st.success(f"Added {qty} units of {name}")
                else: st.error("Product name is required.")

    elif menu == "Stock Out":
        st.markdown('<h3 style="color:white; text-shadow: 2px 2px 4px #000;">📤 Stock Removal</h3>', unsafe_allow_html=True)
        c.execute("SELECT product_name FROM stock")
        products = [row[0] for row in c.fetchall()]
        
        if products:
            with st.form("removal_form"):
                target = st.selectbox("Select Product", products)
                amt = st.number_input("Amount to Remove", min_value=1)
                if st.form_submit_button("Confirm Removal"):
                    c.execute("SELECT quantity FROM stock WHERE product_name = ?", (target,))
                    curr = c.fetchone()[0]
                    if amt <= curr:
                        new_qty = curr - amt
                        if new_qty == 0: c.execute("DELETE FROM stock WHERE product_name = ?", (target,))
                        else: c.execute("UPDATE stock SET quantity = ? WHERE product_name = ?", (new_qty, target))
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        c.execute("INSERT INTO transactions (product_name, type, qty, date) VALUES (?, 'OUT', ?, ?)", (target, amt, now))
                        conn.commit()
                        st.success("Removal successful.")
                        st.rerun()
                    else: st.error("Error: Not enough stock.")
        else: st.warning("Inventory is empty.")

    elif menu == "Daily Reports":
        st.markdown('<h3 style="color:white; text-shadow: 2px 2px 4px #000;">🗓 Transaction Logs</h3>', unsafe_allow_html=True)
        st.markdown('<div class="content-card">Logs are only accessible to administrative users. Contact ZK7 Office for full CSV export.</div>', unsafe_allow_html=True)
