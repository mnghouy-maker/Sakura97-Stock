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

# Create tables
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

# Helper Functions for Security
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

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

# Ensure image directory exists
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
            }}
            [data-testid="stSidebar"] {{ background-color: rgba(0, 0, 0, 0.4) !important; backdrop-filter: blur(10px); }}
            .styled-header {{ background-color: #262730; padding: 20px; border-radius: 20px; text-align: center; color: white; margin-bottom: 20px; }}
            .corner-footer {{ position: fixed; right: 20px; bottom: 20px; background-color: #262730; color: white; padding: 10px; border-radius: 50px; z-index: 9999; }}
            </style>
            <div class="corner-footer">Created by: Sino Menghuy</div>
        """, unsafe_allow_html=True)

set_ui_design('BackImage.jpg')

# ==============================
# 3. AUTHENTICATION LOGIC
# ==============================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

st.sidebar.title("🔐 Access Control")
auth_mode = st.sidebar.selectbox("Action", ["Login", "Sign Up"])

if not st.session_state['logged_in']:
    st.markdown('<div class="styled-header"><h1>🌸 Sakura97 Stock System</h1><p>Please Login to Continue</p></div>', unsafe_allow_html=True)
    
    with st.container():
        if auth_mode == "Sign Up":
            new_user = st.text_input("Create Username")
            new_pass = st.text_input("Create Password", type='password')
            if st.button("Register"):
                if create_user(new_user, new_pass):
                    st.success("Account created! Please switch to Login.")
                else:
                    st.error("Username already exists.")
        
        else:
            user = st.text_input("Username")
            password = st.text_input("Password", type='password')
            if st.button("Login"):
                result = login_user(user, password)
                if result:
                    st.session_state['logged_in'] = True
                    st.session_state['user'] = user
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")

# ==============================
# 4. MAIN APP (ONLY ACCESSIBLE IF LOGGED IN)
# ==============================
else:
    st.sidebar.success(f"Welcome, {st.session_state['user']}")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.markdown('<div class="styled-header"><h1>🌸 Sakura97 Stock Management</h1><p>Managed by: ZK7 Office</p></div>', unsafe_allow_html=True)
    
    menu = st.sidebar.selectbox("Select Menu", ["View Stock", "Stock In", "Stock Out", "Daily Reports"])

    if menu == "View Stock":
        st.subheader("📦 Current Inventory")
        df = pd.read_sql_query("SELECT product_name as 'Product', quantity as 'In Stock' FROM stock", conn)
        if not df.empty:
            for index, row in df.iterrows():
                with st.container():
                    col1, col2 = st.columns([1,4])
                    img_p = f"images/{row['Product']}.png"
                    with col1:
                        if os.path.exists(img_p): st.image(img_p)
                        else: st.caption("No Image")
                    with col2:
                        st.markdown(f"### {row['Product']}")
                        st.write(f"**Quantity:** {row['In Stock']} units")
                    st.markdown("---")
        else:
            st.info("No items in stock.")

    elif menu == "Stock In":
        st.subheader("📥 Add/Update Stock")
        with st.form("stock_in_form"):
            name = st.text_input("Product Name").strip()
            qty = st.number_input("Quantity to Add", min_value=1)
            img_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])
            if st.form_submit_button("Submit"):
                if name:
                    img_path = f"images/{name}.png"
                    if img_file: Image.open(img_file).save(img_path)
                    try:
                        c.execute("INSERT INTO stock (product_name, quantity, image_path) VALUES (?, ?, ?)", (name, qty, img_path))
                    except:
                        c.execute("UPDATE stock SET quantity = quantity + ? WHERE product_name = ?", (qty, name))
                    
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    c.execute("INSERT INTO transactions (product_name, type, qty, date) VALUES (?, ?, ?, ?)", (name, "IN", qty, now))
                    conn.commit()
                    st.success(f"Added {qty} units of {name}")
                else:
                    st.error("Name required.")

    elif menu == "Stock Out":
        st.subheader("📤 Remove Stock")
        c.execute("SELECT product_name FROM stock")
        products = [row[0] for row in c.fetchall()]
        if products:
            selected_prod = st.selectbox("Product", products)
            qty_out = st.number_input("Quantity", min_value=1)
            if st.button("Confirm"):
                c.execute("SELECT quantity FROM stock WHERE product_name = ?", (selected_prod,))
                current_inv = c.fetchone()[0]
                if qty_out <= current_inv:
                    new_inv = current_inv - qty_out
                    if new_inv == 0: c.execute("DELETE FROM stock WHERE product_name = ?", (selected_prod,))
                    else: c.execute("UPDATE stock SET quantity = ? WHERE product_name = ?", (new_inv, selected_prod))
                    
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    c.execute("INSERT INTO transactions (product_name, type, qty, date) VALUES (?, ?, ?, ?)", (selected_prod, "OUT", qty_out, now))
                    conn.commit()
                    st.success(f"Removed {qty_out} units")
                    st.rerun()
                else:
                    st.error("Insufficient stock!")

    elif menu == "Daily Reports":
        st.subheader("🗓 Transaction Archive")
        # (Keep your existing report logic here...)
        st.info("Report section is active for authorized users.")
