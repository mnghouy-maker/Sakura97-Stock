import streamlit as st
import sqlite3
import os
import base64
import pandas as pd
import hashlib
from datetime import datetime
from PIL import Image

# ==============================
# 1. DATABASE & DIRECTORY SETUP
# ==============================
conn = sqlite3.connect('stock.db', check_same_thread=False)
c = conn.cursor()

# Ensure all tables exist
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

# Fix for older databases missing columns
try:
    c.execute("ALTER TABLE stock ADD COLUMN image_path TEXT")
except sqlite3.OperationalError:
    pass 

conn.commit()

if not os.path.exists("images"):
    os.makedirs("images")

# ==============================
# 2. SECURITY FUNCTIONS
# ==============================
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

# ==============================
# 3. UI, STYLING & FULL BACKGROUND
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
            header {{background: rgba(0,0,0,0) !important;}}
            [data-testid="stSidebar"] {{
                background-color: rgba(0, 0, 0, 0.4) !important;
                backdrop-filter: blur(15px);
            }}
            .styled-header {{
                background-color: #262730;
                color: #ffffff !important;
                padding: 40px 20px;
                border-radius: 20px;
                text-align: center;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                margin: 0 auto 40px auto;
                max-width: 700px;
            }}
            .corner-footer {{
                position: fixed;
                right: 20px;
                bottom: 20px;
                background-color: #262730;
                color: #ffffff !important;
                padding: 10px 25px;
                border-radius: 50px;
                font-size: 14px;
                font-weight: bold;
                z-index: 9999;
            }}
            /* Container styling */
            [data-testid="stVerticalBlock"] > div:has(div.stForm) {{
                background-color: rgba(255, 255, 255, 0.9);
                padding: 20px;
                border-radius: 15px;
            }}
            h1, h2, h3, p {{ color: #1E1E1E; }}
            </style>
            <div class="corner-footer">Created by: Sino Menghuy</div>
        """, unsafe_allow_html=True)
    else:
        st.sidebar.warning("Background 'BackImage.jpg' not found.")

set_ui_design('BackImage.jpg')

# ==============================
# 4. AUTHENTICATION LOGIC
# ==============================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# Sidebar for Login/Signup
if not st.session_state['logged_in']:
    st.markdown('<div class="styled-header"><h1 style="color:white !important;">🔐 System Access</h1></div>', unsafe_allow_html=True)
    
    auth_mode = st.sidebar.selectbox("Access Mode", ["Login", "Sign Up"])
    
    if auth_mode == "Sign Up":
        st.subheader("Create New Account")
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password", type='password')
        if st.button("Register"):
            if new_user and new_pass:
                try:
                    c.execute('INSERT INTO users(username, password) VALUES (?,?)', (new_user, make_hashes(new_pass)))
                    conn.commit()
                    st.success("Account created! Please switch to Login mode.")
                except sqlite3.IntegrityError:
                    st.error("Username already exists.")
            else:
                st.warning("Please fill all fields.")
                
    elif auth_mode == "Login":
        st.subheader("Login to Sakura97")
        user = st.text_input("Username")
        pswd = st.text_input("Password", type='password')
        if st.button("Login"):
            c.execute('SELECT password FROM users WHERE username = ?', (user,))
            result = c.fetchone()
            if result and check_hashes(pswd, result[0]):
                st.session_state['logged_in'] = True
                st.session_state['user'] = user
                st.rerun()
            else:
                st.error("Invalid Username or Password")

# ==============================
# 5. MAIN APP (ONLY IF LOGGED IN)
# ==============================
else:
    st.sidebar.success(f"Welcome, {st.session_state['user']}")
    if st.sidebar.button("Log Out"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.markdown("""
    <div class="styled-header">
        <h1 style='margin: 0; color: #FFFFFF !important; font-size: 38px; font-weight: 800;'>🌸 Sakura97 Stock Management</h1>
        <p style='margin: 15px 0 0 0; color: #FFFFFF !important; font-size: 14px; font-weight: 400; opacity: 0.9;'>Managed by: ZK7 Office</p>
    </div>""", unsafe_allow_html=True)

    menu = st.sidebar.selectbox("Select Menu", ["View Stock", "Stock In", "Stock Out", "Daily Reports"])

    if menu == "View Stock":
        st.subheader("📦 Current Inventory")
        df = pd.read_sql_query("SELECT product_name as 'Product', quantity as 'In Stock' FROM stock", conn)
        
        if not df.empty:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📊 Download CSV", data=csv, file_name="Inventory.csv", mime='text/csv')
            
            for index, row in df.iterrows():
                with st.container():
                    col1, col2 = st.columns([1,4])
                    img_p = f"images/{row['Product']}.png"
                    with col1:
                        if os.path.exists(img_p): st.image(img_p, use_container_width=True)
                        else: st.caption("No Image")
                    with col2:
                        st.markdown(f"### {row['Product']}")
                        st.write(f"**Quantity Available:** {row['In Stock']} units")
                        st.markdown("---")
        else:
            st.info("No items in stock.")

    elif menu == "Stock In":
        st.subheader("📥 Add/Update Stock")
        with st.form("stock_in_form"):
            name = st.text_input("Product Name").strip()
            qty = st.number_input("Quantity to Add", min_value=1)
            img_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])
            submitted = st.form_submit_button("Submit Stock In")
            
            if submitted:
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
                    st.success(f"✅ Added {qty} units of {name}.")
                else:
                    st.error("Product name is required.")

    elif menu == "Stock Out":
        st.subheader("📤 Remove Stock")
        c.execute("SELECT product_name FROM stock")
        products = [row[0] for row in c.fetchall()]
        
        if products:
            selected_prod = st.selectbox("Search Product", products)
            qty_out = st.number_input("Quantity to Remove", min_value=1)
            
            if st.button("Confirm Removal"):
                c.execute("SELECT quantity FROM stock WHERE product_name = ?", (selected_prod,))
                current_inv = c.fetchone()[0]
                
                if qty_out <= current_inv:
                    new_inv = current_inv - qty_out
                    if new_inv == 0:
                        c.execute("DELETE FROM stock WHERE product_name = ?", (selected_prod,))
                    else:
                        c.execute("UPDATE stock SET quantity = ? WHERE product_name = ?", (new_inv, selected_prod))
                    
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    c.execute("INSERT INTO transactions (product_name, type, qty, date) VALUES (?, ?, ?, ?)", (selected_prod, "OUT", qty_out, now))
                    conn.commit()
                    st.success(f"✅ Removed {qty_out} units.")
                    st.rerun()
                else:
                    st.error(f"Not enough stock! Current balance: {current_inv}")
        else:
            st.warning("No products available.")

    elif menu == "Daily Reports":
        st.subheader("🗓 Transaction Archive")
        col_y, col_m = st.columns(2)
        with col_y:
            sel_year = st.selectbox("Year", list(range(2025, 2101)), index=1) # 2026 default
        with col_m:
            months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            sel_month = st.selectbox("Month", months, index=datetime.now().month - 1)

        month_idx = f"{months.index(sel_month) + 1:02d}"
        search_str = f"{sel_year}-{month_idx}%"
        report_df = pd.read_sql_query("SELECT date, product_name as 'Product', type as 'Action', qty as 'Quantity' FROM transactions WHERE date LIKE ? ORDER BY date DESC", conn, params=(search_str,))
        
        if not report_df.empty:
            st.dataframe(report_df, use_container_width=True)
        else:
            st.write(f"No activity for {sel_month} {sel_year}.")
