import streamlit as st
import sqlite3
import os
import base64
import pandas as pd
from datetime import datetime
from PIL import Image

# ==============================
# 1. DATABASE SETUP
# ==============================
conn = sqlite3.connect('stock.db', check_same_thread=False)
c = conn.cursor()

c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)')
c.execute('''CREATE TABLE IF NOT EXISTS stock 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              user_id INTEGER,
              product_name TEXT, 
              quantity INTEGER, 
              image_path TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS transactions 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              user_id INTEGER,
              product_name TEXT, 
              type TEXT, 
              qty INTEGER, 
              date TEXT)''')
conn.commit()

if not os.path.exists("images"):
    os.makedirs("images")

# ==============================
# 2. UI & STYLING
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
            [data-testid="stSidebar"] {{ background-color: rgba(0, 0, 0, 0.4) !important; backdrop-filter: blur(10px); }}
            .styled-header {{ 
                background-color: #262730; 
                padding: 30px; 
                border-radius: 20px; 
                text-align: center; 
                margin-bottom: 30px; 
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            }}
            .styled-header h1, .styled-header p {{ color: #FFFFFF !important; margin: 0; font-weight: bold; }}
            /* White content cards */
            .st-emotion-cache-12w0qpk {{ background-color: rgba(255, 255, 255, 0.95) !important; border-radius: 15px !important; padding: 25px !important; }}
            h2, h3, p {{ color: #1E1E1E !important; }}
            </style>
        """, unsafe_allow_html=True)

set_ui_design('BackImage.jpg')

# ==============================
# 3. AUTHENTICATION LOGIC
# ==============================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_id'] = None
    st.session_state['username'] = ""

if not st.session_state['logged_in']:
    st.markdown('<div class="styled-header"><h1>🌸 Sakura97 Secure Access</h1><p>Managed by: ZK7 Office</p></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Login", "Create Account"])
    
    with tab1:
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                c.execute('SELECT id FROM users WHERE username = ? AND password = ?', (u, p))
                res = c.fetchone()
                if res:
                    st.session_state.update({'logged_in': True, 'user_id': res[0], 'username': u})
                    st.rerun()
                else: st.error("Invalid credentials")
    with tab2:
        with st.form("signup"):
            nu = st.text_input("New Username")
            np = st.text_input("New Password", type="password")
            if st.form_submit_button("Sign Up"):
                try:
                    c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (nu, np))
                    conn.commit()
                    st.success("Account created! Go to Login tab.")
                except: st.error("Username already exists")
    st.stop()

# ==============================
# 4. MAIN APPLICATION
# ==============================
uid = st.session_state['user_id']
st.sidebar.write(f"Logged in as: **{st.session_state['username']}**")
if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False
    st.rerun()

st.markdown(f"""
<div class="styled-header">
    <h1>🌸 Sakura97 Stock Management</h1>
    <p>User: {st.session_state['username']} | Managed by: ZK7 Office</p>
</div>""", unsafe_allow_html=True)

menu = st.sidebar.selectbox("Select Menu", ["View Stock", "Stock In", "Stock Out", "Daily Reports"])

# --- VIEW STOCK ---
if menu == "View Stock":
    st.subheader("📦 My Inventory")
    df = pd.read_sql_query("SELECT product_name as 'Product', quantity as 'In Stock' FROM stock WHERE user_id = ?", conn, params=(uid,))
    if not df.empty:
        for i, row in df.iterrows():
            with st.container():
                col1, col2 = st.columns([1,4])
                img_p = f"images/{uid}_{row['Product']}.png"
                with col1:
                    if os.path.exists(img_p): st.image(img_p, use_container_width=True)
                    else: st.caption("No Image")
                with col2:
                    st.markdown(f"### {row['Product']}")
                    st.write(f"**Stock Level:** {row['In Stock']} units")
                    st.markdown("---")
    else: st.info("No stock recorded.")

# --- STOCK IN ---
elif menu == "Stock In":
    st.subheader("📥 Add Stock")
    with st.form("in"):
        name = st.text_input("Product Name").strip()
        qty = st.number_input("Quantity", min_value=1)
        img = st.file_uploader("Upload Image", type=["jpg", "png"])
        if st.form_submit_button("Submit"):
            if name:
                path = f"images/{uid}_{name}.png"
                if img: Image.open(img).save(path)
                c.execute("SELECT id FROM stock WHERE user_id = ? AND product_name = ?", (uid, name))
                if c.fetchone(): c.execute("UPDATE stock SET quantity = quantity + ? WHERE user_id = ? AND product_name = ?", (qty, uid, name))
                else: c.execute("INSERT INTO stock (user_id, product_name, quantity, image_path) VALUES (?, ?, ?, ?)", (uid, name, qty, path))
                c.execute("INSERT INTO transactions (user_id, product_name, type, qty, date) VALUES (?, ?, 'IN', ?, ?)", (uid, name, qty, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.success("Stock added!")
            else: st.error("Enter product name")

# --- STOCK OUT ---
elif menu == "Stock Out":
    st.subheader("📤 Remove Stock")
    c.execute("SELECT product_name FROM stock WHERE user_id = ?", (uid,))
    items = [r[0] for r in c.fetchall()]
    if items:
        sel = st.selectbox("Select Product", items)
        q_out = st.number_input("Quantity to Remove", min_value=1)
        if st.button("Confirm Removal"):
            c.execute("SELECT quantity FROM stock WHERE user_id = ? AND product_name = ?", (uid, sel))
            curr = c.fetchone()[0]
            if q_out <= curr:
                c.execute("UPDATE stock SET quantity = ? WHERE user_id = ? AND product_name = ?", (curr - q_out, uid, sel))
                c.execute("INSERT INTO transactions (user_id, product_name, type, qty, date) VALUES (?, ?, 'OUT', ?, ?)", (uid, sel, q_out, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.success("Updated!"); st.rerun()
            else: st.error("Insufficient stock!")
    else: st.warning("Inventory empty.")

# --- DAILY REPORTS (WITH DAY-BY-DAY FILTER) ---
elif menu == "Daily Reports":
    st.subheader("🗓 My Archive (2026-2100)")
    col1, col2 = st.columns(2)
    with col1: y = st.selectbox("Year", list(range(2026, 2101)))
    with col2:
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        m = st.selectbox("Month", months, index=datetime.now().month-1)
    
    st.write("🔍 **Select Day Range:**")
    d_col1, d_col2 = st.columns(2)
    with d_col1: s_day = st.number_input("From Day", 1, 31, 1)
    with d_col2: e_day = st.number_input("To Day", 1, 31, 31)

    m_idx = f"{months.index(m) + 1:02d}"
    search = f"{y}-{m_idx}%"
    df_rep = pd.read_sql_query("SELECT date, product_name as 'Product', type as 'Action', qty as 'Quantity' FROM transactions WHERE user_id = ? AND date LIKE ? ORDER BY date DESC", conn, params=(uid, search))
    
    if not df_rep.empty:
        df_rep['Date/Time'] = pd.to_datetime(df_rep['date'])
        df_rep['Day'] = df_rep['Date/Time'].dt.day
        filtered = df_rep[(df_rep['Day'] >= s_day) & (df_rep['Day'] <= e_day)]
        
        if not filtered.empty:
            st.dataframe(filtered[['Date/Time', 'Day', 'Product', 'Action', 'Quantity']], use_container_width=True)
            tin = filtered[filtered['Action'] == 'IN']['Quantity'].sum()
            tout = filtered[filtered['Action'] == 'OUT']['Quantity'].sum()
            st.info(f"📊 **Summary (Day {s_day}-{e_day})**: {tin} IN | {tout} OUT")
        else: st.warning("No records for this day range.")
    else: st.write("No activity this month.")
