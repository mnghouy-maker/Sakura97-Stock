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

# Create tables if they don't exist
c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
c.execute('''CREATE TABLE IF NOT EXISTS stock 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT UNIQUE, quantity INTEGER, image_path TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS transactions 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT, type TEXT, qty INTEGER, date TEXT)''')
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
# 2. ADVANCED UI & SIDEBAR STYLING
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
            
            /* High-End Sidebar Styling */
            [data-testid="stSidebar"] {{
                background-color: rgba(0, 0, 0, 0.7) !important;
                backdrop-filter: blur(15px);
                border-right: 1px solid rgba(255, 255, 255, 0.1);
            }}
            
            /* Glass-morphism Cards */
            .glass-card {{
                background: rgba(255, 255, 255, 0.95);
                padding: 25px;
                border-radius: 15px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                color: #1E1E1E !important;
                margin-bottom: 20px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}

            .styled-header {{
                background: rgba(38, 39, 48, 0.9);
                padding: 40px;
                border-radius: 20px;
                text-align: center;
                color: white !important;
                margin-bottom: 30px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.5);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}

            /* Bottom Left Footer */
            .custom-footer {{
                position: fixed;
                left: 20px;
                bottom: 20px;
                background: rgba(0, 0, 0, 0.8);
                color: #00ffcc !important;
                padding: 10px 20px;
                border-radius: 8px;
                font-family: 'Courier New', monospace;
                font-size: 13px;
                border: 1px solid #00ffcc;
                z-index: 1000;
            }}

            h1, h2, h3, p {{ color: white !important; }}
            .black-text {{ color: #000000 !important; }}
            </style>
            <div class="custom-footer">CREATED BY: SINO MENGHUY</div>
        """, unsafe_allow_html=True)

set_ui_design('BackImage.jpg')

# ==============================
# 3. SESSION & AUTH
# ==============================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.markdown('<div class="styled-header"><h1>🌸 Sakura97 Stock System</h1><p>Secure Portal for ZK7 Office</p></div>', unsafe_allow_html=True)
    auth_mode = st.sidebar.radio("Access Control", ["Login", "Sign Up"])
    
    with st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        if auth_mode == "Sign Up":
            user_new = st.text_input("New Username")
            pass_new = st.text_input("New Password", type='password')
            if st.button("Register Account"):
                if create_user(user_new, pass_new): st.success("Success! Please Login.")
                else: st.error("User already exists.")
        else:
            user_log = st.text_input("Username")
            pass_log = st.text_input("Password", type='password')
            if st.button("Sign In"):
                if login_user(user_log, pass_log):
                    st.session_state['logged_in'] = True
                    st.session_state['user'] = user_log
                    st.rerun()
                else: st.error("Access Denied.")
        st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# 4. MAIN SYSTEM
# ==============================
else:
    st.sidebar.markdown(f"### 👤 {st.session_state['user']}")
    if st.sidebar.button("🔓 Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    menu = st.sidebar.selectbox("Navigation", ["View Stock", "Stock In", "Stock Out", "Daily Reports"])
    st.markdown('<div class="styled-header"><h1>🌸 Sakura97 Management</h1></div>', unsafe_allow_html=True)

    # --- DAILY REPORTS (2026 - 2100) ---
    if menu == "Daily Reports":
        st.markdown('### 🗓 Transaction Archive (2026-2100)')
        
        with st.expander("🔍 Filter Records", expanded=True):
            col_y, col_m = st.columns(2)
            with col_y:
                sel_year = st.selectbox("Select Year", list(range(2026, 2101)))
            with col_m:
                months = ["January", "February", "March", "April", "May", "June", 
                          "July", "August", "September", "October", "November", "December"]
                sel_month = st.selectbox("Select Month", months, index=datetime.now().month - 1)
            
            st.write("Filter by Day Range:")
            d_start, d_end = st.slider("Days of Month", 1, 31, (1, 31))

        # Query Database
        month_idx = f"{months.index(sel_month) + 1:02d}"
        search_pattern = f"{sel_year}-{month_idx}%"
        
        report_df = pd.read_sql_query(
            "SELECT date, product_name as 'Product', type as 'Action', qty as 'Quantity' FROM transactions WHERE date LIKE ? ORDER BY date DESC",
            conn, params=(search_pattern,)
        )

        if not report_df.empty:
            report_df['Date/Time'] = pd.to_datetime(report_df['date'])
            report_df['Day'] = report_df['Date/Time'].dt.day
            
            # Filter by specific days
            final_df = report_df[(report_df['Day'] >= d_start) & (report_df['Day'] <= d_end)]
            
            if not final_df.empty:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.dataframe(final_df[['Date/Time', 'Product', 'Action', 'Quantity']], use_container_width=True)
                
                # Totals
                tin = final_df[final_df['Action']=='IN']['Quantity'].sum()
                tout = final_df[final_df['Action']=='OUT']['Quantity'].sum()
                st.markdown(f"<p class='black-text'><b>Total In:</b> {tin} | <b>Total Out:</b> {tout}</p>", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.warning(f"No data for days {d_start} to {d_end}.")
        else:
            st.info(f"No transactions found for {sel_month} {sel_year}.")

    # --- STOCK MANAGEMENT ---
    elif menu == "View Stock":
        df = pd.read_sql_query("SELECT product_name as 'Product', quantity as 'Units' FROM stock", conn)
        if not df.empty:
            for _, row in df.iterrows():
                st.markdown(f"""<div class="glass-card">
                    <h3 class="black-text">{row['Product']}</h3>
                    <p class="black-text"><b>Current Stock:</b> {row['Units']} units</p>
                </div>""", unsafe_allow_html=True)
        else: st.info("Inventory is empty.")

    elif menu == "Stock In":
        with st.form("in_form"):
            st.markdown('<h3 class="black-text">Add Stock</h3>', unsafe_allow_html=True)
            p_name = st.text_input("Product Name")
            p_qty = st.number_input("Quantity", min_value=1)
            if st.form_submit_button("Submit"):
                try:
                    c.execute("INSERT INTO stock (product_name, quantity) VALUES (?, ?)", (p_name, p_qty))
                except:
                    c.execute("UPDATE stock SET quantity = quantity + ? WHERE product_name = ?", (p_qty, p_name))
                c.execute("INSERT INTO transactions (product_name, type, qty, date) VALUES (?, ?, ?, ?)", 
                          (p_name, "IN", p_qty, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.success("Stock Added")

    elif menu == "Stock Out":
        c.execute("SELECT product_name FROM stock")
        prods = [r[0] for r in c.fetchall()]
        if prods:
            with st.form("out_form"):
                p_sel = st.selectbox("Product", prods)
                p_out = st.number_input("Quantity to Remove", min_value=1)
                if st.form_submit_button("Confirm"):
                    c.execute("SELECT quantity FROM stock WHERE product_name=?", (p_sel,))
                    curr = c.fetchone()[0]
                    if p_out <= curr:
                        c.execute("UPDATE stock SET quantity = quantity - ? WHERE product_name = ?", (p_out, p_sel))
                        c.execute("INSERT INTO transactions (product_name, type, qty, date) VALUES (?, ?, ?, ?)", 
                                  (p_sel, "OUT", p_out, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        conn.commit()
                        st.success("Stock Removed")
                        st.rerun()
                    else: st.error("Insufficient Stock")
