import streamlit as st
import sqlite3
import os
import base64
import pandas as pd
from datetime import datetime
from PIL import Image

# ==============================
# 1. DATABASE SETUP (Multi-User)
# ==============================
conn = sqlite3.connect('stock.db', check_same_thread=False)
c = conn.cursor()

# Create tables if they don't exist
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
            .styled-header {{ background-color: #262730; padding: 30px; border-radius: 20px; text-align: center; margin-bottom: 30px; border: 1px solid #444; }}
            .styled-header h1, .styled-header p {{ color: white !important; margin: 0; }}
            .st-emotion-cache-12w0qpk {{ background-color: rgba(255, 255, 255, 0.95) !important; border-radius: 15px !important; padding: 25px !important; }}
            </style>
        """, unsafe_allow_html=True)

set_ui_design('BackImage.jpg')

# ==============================
# 3. LOGIN / SIGNUP LOGIC
# ==============================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_id'] = None
    st.session_state['username'] = ""

def login_user(username, password):
    c.execute('SELECT id FROM users WHERE username = ? AND password = ?', (username, password))
    return c.fetchone()

def signup_user(username, password):
    try:
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        return True
    except:
        return False

if not st.session_state['logged_in']:
    st.markdown('<div class="styled-header"><h1>🌸 Sakura97 Secure Access</h1><p>ZK7 Office Management System</p></div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Login", "Create Account"])
    
    with tab1:
        with st.form("login_form"):
            user = st.text_input("Username")
            pw = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                result = login_user(user, pw)
                if result:
                    st.session_state['logged_in'] = True
                    st.session_state['user_id'] = result[0]
                    st.session_state['username'] = user
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")

    with tab2:
        with st.form("signup_form"):
            new_user = st.text_input("New Username")
            new_pw = st.text_input("New Password", type="password")
            if st.form_submit_button("Sign Up"):
                if signup_user(new_user, new_pw):
                    st.success("Account created! You can now login.")
                else:
                    st.error("Username already exists.")
    st.stop()

# ==============================
# 4. MAIN APP (ONLY FOR LOGGED IN)
# ==============================
uid = st.session_state['user_id']

# Sidebar Header
st.sidebar.title(f"👤 {st.session_state['username']}")
if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False
    st.rerun()

st.markdown(f"""
<div class="styled-header">
    <h1>🌸 Sakura97 Stock Management</h1>
    <p>User: {st.session_state['username']} | ZK7 Office</p>
</div>""", unsafe_allow_html=True)

menu = st.sidebar.selectbox("Select Menu", ["View Stock", "Stock In", "Stock Out", "Daily Reports"])

# --- VIEW STOCK ---
if menu == "View Stock":
    st.subheader("📦 My Inventory")
    df = pd.read_sql_query("SELECT product_name as 'Product', quantity as 'In Stock' FROM stock WHERE user_id = ?", conn, params=(uid,))
    
    if not df.empty:
        for index, row in df.iterrows():
            with st.container():
                col1, col2 = st.columns([1,4])
                img_p = f"images/{uid}_{row['Product']}.png"
                with col1:
                    if os.path.exists(img_p): st.image(img_p, use_container_width=True)
                    else: st.caption("No Image")
                with col2:
                    st.markdown(f"### {row['Product']}")
                    st.write(f"**Quantity:** {row['In Stock']} units")
                    st.markdown("---")
    else:
        st.info("Your inventory is empty.")

# --- STOCK IN ---
elif menu == "Stock In":
    st.subheader("📥 Add Stock")
    with st.form("stock_in"):
        name = st.text_input("Product Name").strip()
        qty = st.number_input("Quantity", min_value=1)
        img_file = st.file_uploader("Image", type=["jpg", "png"])
        if st.form_submit_button("Submit"):
            if name:
                img_path = f"images/{uid}_{name}.png"
                if img_file: Image.open(img_file).save(img_path)
                
                # Check if user already has this product
                c.execute("SELECT id FROM stock WHERE user_id = ? AND product_name = ?", (uid, name))
                exists = c.fetchone()
                
                if exists:
                    c.execute("UPDATE stock SET quantity = quantity + ? WHERE id = ?", (qty, exists[0]))
                else:
                    c.execute("INSERT INTO stock (user_id, product_name, quantity, image_path) VALUES (?, ?, ?, ?)", (uid, name, qty, img_path))
                
                c.execute("INSERT INTO transactions (user_id, product_name, type, qty, date) VALUES (?, ?, 'IN', ?, ?)", 
                          (uid, name, qty, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.success(f"Added {qty} to {name}")
            else: st.error("Name required")

# --- STOCK OUT ---
elif menu == "Stock Out":
    st.subheader("📤 Remove Stock")
    c.execute("SELECT product_name FROM stock WHERE user_id = ?", (uid,))
    prods = [r[0] for r in c.fetchall()]
    if prods:
        sel = st.selectbox("Product", prods)
        q_out = st.number_input("Qty to Remove", min_value=1)
        if st.button("Confirm"):
            c.execute("SELECT quantity FROM stock WHERE user_id = ? AND product_name = ?", (uid, sel))
            curr = c.fetchone()[0]
            if q_out <= curr:
                c.execute("UPDATE stock SET quantity = ? WHERE user_id = ? AND product_name = ?", (curr - q_out, uid, sel))
                c.execute("INSERT INTO transactions (user_id, product_name, type, qty, date) VALUES (?, ?, 'OUT', ?, ?)", 
                          (uid, sel, q_out, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.success("Updated!")
                st.rerun()
            else: st.error("Not enough stock!")
    else: st.warning("No products found.")

# --- REPORTS ---
elif menu == "Daily Reports":
    st.subheader("🗓 My Archive (2026-2100)")
    y = st.selectbox("Year", list(range(2026, 2101)))
    m_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    m = st.selectbox("Month", m_names, index=datetime.now().month-1)
    
    m_idx = f"{m_names.index(m) + 1:02d}"
    search = f"{y}-{m_idx}%"
    
    df_rep = pd.read_sql_query("SELECT date, product_name, type, qty FROM transactions WHERE user_id = ? AND date LIKE ? ORDER BY date DESC", 
                               conn, params=(uid, search))
    if not df_rep.empty:
        st.dataframe(df_rep, use_container_width=True)
    else:
        st.write("No data for this month.")
