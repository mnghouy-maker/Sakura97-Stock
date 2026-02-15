import streamlit as st
import sqlite3
import os
import base64
import pandas as pd
import hashlib
from datetime import datetime
from PIL import Image
from io import BytesIO

# ==============================
# 1. DATABASE & DIRECTORY SETUP
# ==============================
def get_db_connection():
    conn = sqlite3.connect('stock.db', check_same_thread=False)
    return conn

conn = get_db_connection()
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS stock 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              product_name TEXT UNIQUE, 
              quantity INTEGER, 
              image_path TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS transactions 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              product_name TEXT, 
              type TEXT, 
              qty INTEGER, 
              date TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS users 
             (username TEXT PRIMARY KEY, password TEXT)''')

if not os.path.exists("images"):
    os.makedirs("images")
conn.commit()

# ==============================
# 2. SECURITY FUNCTIONS
# ==============================
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

# ==============================
# 3. UI DESIGN (GRAY BOXES & SUBMIT BUTTONS)
# ==============================
@st.cache_data
def get_base64_bin(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def set_ui_design(image_file):
    encoded_string = get_base64_bin(image_file)
    bg_style = ""
    if encoded_string:
        bg_style = f'background-image: url("data:image/png;base64,{encoded_string}");'

    st.markdown(f"""
        <style>
        .stApp {{
            {bg_style}
            background-attachment: fixed;
            background-size: cover;
            background-position: center;
        }}
        
        /* FORCE ALL TEXT TO WHITE */
        h1, h2, h3, h4, h5, h6, p, li, label, .stMarkdown, .stText, .stMetric, [data-testid="stHeader"] {{
            color: white !important;
        }}

        [data-testid="stSidebar"] {{
            background-color: rgba(0, 0, 0, 0.6) !important;
            backdrop-filter: blur(15px);
        }}
        
        [data-testid="stSidebar"] * {{
            color: white !important;
        }}

        /* --- SELECT MENU GRAY BOXES --- */
        div[data-baseweb="select"] > div {{
            background-color: #4F4F4F !important;
            border-color: #707070 !important;
        }}
        
        /* --- ALL BUTTONS (LOGIN, LOGOUT, & SUBMIT) GRAY --- */
        div.stButton > button, div.stFormSubmitButton > button {{
            background-color: #616161 !important;
            color: white !important;
            border: 1px solid #888888 !important;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            transition: 0.3s;
            width: 100%; /* Makes buttons full width for a cleaner look */
        }}
        
        div.stButton > button:hover, div.stFormSubmitButton > button:hover {{
            background-color: #808080 !important;
            border-color: white !important;
            color: white !important;
        }}

        .styled-header {{
            background-color: rgba(38, 39, 48, 0.8);
            padding: 40px 20px;
            border-radius: 20px;
            text-align: center;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            margin: 0 auto 40px auto;
            max-width: 700px;
        }}

        .corner-footer {{
            position: fixed;
            right: 20px; bottom: 20px;
            background-color: #262730;
            color: white !important;
            padding: 10px 25px;
            border-radius: 50px;
            font-size: 14px;
            z-index: 9999;
        }}

        /* Container for forms */
        [data-testid="stVerticalBlock"] > div:has(div.stForm) {{
            background-color: rgba(0, 0, 0, 0.5);
            padding: 20px;
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        header {{background: rgba(0,0,0,0) !important;}}
        </style>
        <div class="corner-footer">Created by: Sino Menghuy</div>
    """, unsafe_allow_html=True)

set_ui_design('BackImage.jpg')

# ==============================
# 4. SESSION STATE
# ==============================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user'] = None

# ==============================
# 5. AUTHENTICATION
# ==============================
if not st.session_state['logged_in']:
    st.markdown('<div class="styled-header"><h1>🔐 System Access</h1></div>', unsafe_allow_html=True)
    auth_mode = st.sidebar.selectbox("Access Mode", ["Login", "Sign Up"])
    
    if auth_mode == "Sign Up":
        st.subheader("Create New Account")
        new_user = st.text_input("New Username").strip()
        new_pass = st.text_input("New Password", type='password').strip()
        if st.button("Register"):
            if new_user and new_pass:
                try:
                    c.execute('INSERT INTO users(username, password) VALUES (?,?)', (new_user, make_hashes(new_pass)))
                    conn.commit()
                    st.success("Account created!")
                except: st.error("Username already exists.")
    
    elif auth_mode == "Login":
        st.subheader("Login to SK97")
        user = st.text_input("Username").strip()
        pswd = st.text_input("Password", type='password').strip()
        if st.button("Login"):
            c.execute('SELECT password FROM users WHERE username = ?', (user,))
            result = c.fetchone()
            if result and check_hashes(pswd, result[0]):
                st.session_state['logged_in'] = True
                st.session_state['user'] = user
                st.rerun()
            else: st.error("Invalid Credentials.")

# ==============================
# 6. MAIN APP
# ==============================
else:
    st.sidebar.success(f"Welcome, {st.session_state['user']}")
    if st.sidebar.button("Log Out"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.markdown("""
    <div class="styled-header">
        <h1 style='margin: 0; color: white !important;'>🌸 SK97 Stock Management</h1>
        <p style='margin: 10px 0 0 0; color: white !important; opacity: 0.8;'>Managed by: ZK7 Office</p>
    </div>""", unsafe_allow_html=True)

    menu = st.sidebar.selectbox("Select Menu", ["View Stock", "Stock In", "Stock Out", "Daily Reports"])

    if menu == "View Stock":
        st.subheader("📦 Current Inventory")
        df = pd.read_sql_query("SELECT product_name as 'Product', quantity as 'In Stock' FROM stock", conn)
        if not df.empty:
            for index, row in df.iterrows():
                col1, col2 = st.columns([1,4])
                img_p = f"images/{row['Product']}.png"
                with col1:
                    if os.path.exists(img_p): st.image(img_p, use_container_width=True)
                    else: st.caption("No Image")
                with col2:
                    st.markdown(f"### {row['Product']}")
                    st.write(f"**Quantity:** {row['In Stock']} units")
                    st.markdown("---")
        else: st.info("No items in stock.")

    elif menu == "Stock In":
        st.subheader("📥 Add/Update Stock")
        with st.form("stock_in_form", clear_on_submit=True):
            name = st.text_input("Product Name").strip()
            qty = st.number_input("Quantity", min_value=1)
            img_file = st.file_uploader("Image", type=["jpg", "png"])
            # THIS IS THE SUBMIT BOX
            if st.form_submit_button("Submit"):
                if name:
                    img_path = f"images/{name}.png"
                    if img_file: Image.open(img_file).save(img_path)
                    c.execute("INSERT OR REPLACE INTO stock (product_name, quantity, image_path) VALUES (?, COALESCE((SELECT quantity FROM stock WHERE product_name=?),0) + ?, ?)", (name, name, qty, img_path))
                    c.execute("INSERT INTO transactions (product_name, type, qty, date) VALUES (?, ?, ?, ?)", (name, "IN", qty, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit()
                    st.success(f"Added {qty} units.")

    elif menu == "Stock Out":
        st.subheader("📤 Remove Stock")
        c.execute("SELECT product_name FROM stock")
        products = [row[0] for row in c.fetchall()]
        if products:
            with st.form("stock_out_form"):
                selected_prod = st.selectbox("Product", products)
                qty_out = st.number_input("Remove Qty", min_value=1)
                # THIS IS THE SUBMIT BOX
                if st.form_submit_button("Confirm"):
                    c.execute("SELECT quantity FROM stock WHERE product_name = ?", (selected_prod,))
                    curr = c.fetchone()[0]
                    if qty_out <= curr:
                        new_q = curr - qty_out
                        if new_q == 0: c.execute("DELETE FROM stock WHERE product_name = ?", (selected_prod,))
                        else: c.execute("UPDATE stock SET quantity = ? WHERE product_name = ?", (new_q, selected_prod))
                        c.execute("INSERT INTO transactions (product_name, type, qty, date) VALUES (?, ?, ?, ?)", (selected_prod, "OUT", qty_out, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        conn.commit()
                        st.success("Updated!")
                        st.rerun()
                    else: st.error("Low stock.")
        else: st.warning("Inventory Empty")

    elif menu == "Daily Reports":
        st.subheader("🗓 Reports")
        col_s, col_e = st.columns(2)
        start_date = col_s.date_input("Start", datetime.now().replace(day=1))
        end_date = col_e.date_input("End", datetime.now())
        
        report_df = pd.read_sql_query("SELECT date, product_name, type, qty FROM transactions WHERE date(date) BETWEEN ? AND ?", conn, params=(str(start_date), str(end_date)))
        
        if not report_df.empty:
            st.dataframe(report_df, use_container_width=True)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                report_df.to_excel(writer, index=False)
            st.download_button("🟢 Download Excel", output.getvalue(), f"SK97_Report.xlsx")
            
            st.markdown("---")
            m1, m2 = st.columns(2)
            m1.metric("Total IN", report_df[report_df['type']=='IN']['qty'].sum())
            m2.metric("Total OUT", report_df[report_df['type']=='OUT']['qty'].sum())
        else: st.warning("No data.")
