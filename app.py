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
# 2. UI & FULL BACKGROUND STYLING
# ==============================
def set_ui_design(image_file):
    if os.path.exists(image_file):
        with open(image_file, "rb") as f:
            data = f.read()
        encoded_string = base64.b64encode(data).decode()
        st.markdown(f"""
            <style>
            /* Full Background Image */
            .stApp {{
                background-image: url("data:image/png;base64,{encoded_string}");
                background-attachment: fixed;
                background-size: cover;
                background-position: center;
            }}

            /* Glass effect for Sidebar */
            [data-testid="stSidebar"] {{ 
                background-color: rgba(0, 0, 0, 0.6) !important; 
                backdrop-filter: blur(15px); 
            }}
            
            /* Sidebar text colors */
            [data-testid="stSidebar"] * {{
                color: white !important;
            }}

            /* Header Box Styling */
            .styled-header {{ 
                background-color: rgba(38, 39, 48, 0.85); 
                padding: 30px; 
                border-radius: 20px; 
                text-align: center; 
                color: white; 
                margin-bottom: 30px;
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
                backdrop-filter: blur(4px);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}

            .corner-footer {{
                position: fixed;
                left: 20px;
                bottom: 20px;
                background-color: #262730;
                color: white;
                padding: 10px 20px;
                border-radius: 50px;
                z-index: 9999;
                font-weight: bold;
            }}

            /* Text Visibility Classes */
            .black-text {{ color: black !important; font-weight: bold; }}
            .white-text {{ color: white !important; }}

            /* Form / Card Styling */
            .stForm {{
                background-color: rgba(255, 255, 255, 0.9) !important;
                padding: 25px !important;
                border-radius: 15px !important;
            }}
            </style>
            <div class="corner-footer">Created by: Sino Menghuy</div>
        """, unsafe_allow_html=True)
    else:
        st.error(f"Error: '{image_file}' not found. Please upload your building image and rename it to 'BackImage.jpg'.")

set_ui_design('BackImage.jpg')

# ==============================
# 3. AUTHENTICATION LOGIC
# ==============================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

st.sidebar.title("🔐 Access Control")
auth_mode = st.sidebar.selectbox("Action", ["Login", "Sign Up"])

if not st.session_state['logged_in']:
    st.markdown('<div class="styled-header"><h1>🌸 Sakura97 Stock System</h1><p>Welcome to SK97 Smart Management</p></div>', unsafe_allow_html=True)
    
    # Login Box Styling
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("auth_form"):
            if auth_mode == "Sign Up":
                st.markdown('<h2 class="black-text">Create Account</h2>', unsafe_allow_html=True)
                new_user = st.text_input("Username")
                new_pass = st.text_input("Password", type='password')
                if st.form_submit_button("Register"):
                    if create_user(new_user, new_pass):
                        st.success("Account created! Now select Login in the sidebar.")
                    else: st.error("Username already exists.")
            else:
                st.markdown('<h2 class="black-text">User Login</h2>', unsafe_allow_html=True)
                user = st.text_input("Username")
                password = st.text_input("Password", type='password')
                if st.form_submit_button("Login"):
                    if login_user(user, password):
                        st.session_state['logged_in'] = True
                        st.session_state['user'] = user
                        st.rerun()
                    else: st.error("Invalid Username or Password")

# ==============================
# 4. MAIN APP CONTENT
# ==============================
else:
    st.sidebar.success(f"User: {st.session_state['user']}")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.markdown('<div class="styled-header"><h1>🌸 Sakura97 Stock Management</h1><p>Managed by: ZK7 Office</p></div>', unsafe_allow_html=True)
    
    menu = st.sidebar.selectbox("Select Menu", ["View Stock", "Stock In", "Stock Out", "Daily Reports"])

    if menu == "View Stock":
        st.markdown('<h3 class="black-text" style="background:white; padding:10px; border-radius:10px;">📦 Current Inventory</h3>', unsafe_allow_html=True)
        df = pd.read_sql_query("SELECT product_name as 'Product', quantity as 'In Stock' FROM stock", conn)
        if not df.empty:
            for index, row in df.iterrows():
                with st.container():
                    # Content inside white card for visibility
                    st.markdown(f"""
                    <div style="background:white; padding:20px; border-radius:10px; margin-bottom:10px; color:black;">
                        <h4>{row['Product']}</h4>
                        <p>Quantity: {row['In Stock']} units</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No items in stock.")

    elif menu == "Stock In":
        st.markdown('<h3 class="black-text" style="background:white; padding:10px; border-radius:10px;">📥 Stock Entry</h3>', unsafe_allow_html=True)
        with st.form("stock_in"):
            name = st.text_input("Product Name").strip()
            qty = st.number_input("Quantity", min_value=1)
            img_file = st.file_uploader("Upload Product Image", type=["jpg", "png"])
            if st.form_submit_button("Submit Stock"):
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
                    st.success(f"Recorded: {qty} units of {name}")
                else: st.error("Name is required.")

    elif menu == "Stock Out":
        st.markdown('<h3 class="black-text" style="background:white; padding:10px; border-radius:10px;">📤 Remove Stock</h3>', unsafe_allow_html=True)
        c.execute("SELECT product_name FROM stock")
        products = [row[0] for row in c.fetchall()]
        if products:
            with st.form("stock_out"):
                selected_prod = st.selectbox("Select Product", products)
                qty_out = st.number_input("Quantity to Remove", min_value=1)
                if st.form_submit_button("Confirm Removal"):
                    c.execute("SELECT quantity FROM stock WHERE product_name = ?", (selected_prod,))
                    current = c.fetchone()[0]
                    if qty_out <= current:
                        new_qty = current - qty_out
                        if new_qty == 0: c.execute("DELETE FROM stock WHERE product_name = ?", (selected_prod,))
                        else: c.execute("UPDATE stock SET quantity = ? WHERE product_name = ?", (new_qty, selected_prod))
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        c.execute("INSERT INTO transactions (product_name, type, qty, date) VALUES (?, ?, ?, ?)", (selected_prod, "OUT", qty_out, now))
                        conn.commit()
                        st.success("Stock updated successfully.")
                        st.rerun()
                    else: st.error("Insufficient stock!")
        else: st.warning("Inventory is empty.")

    elif menu == "Daily Reports":
        st.markdown('<h3 class="black-text" style="background:white; padding:10px; border-radius:10px;">🗓 Transaction History</h3>', unsafe_allow_html=True)
        st.info("Authorized area: Transaction logs are secured.")
        # Filter logic can go here...
