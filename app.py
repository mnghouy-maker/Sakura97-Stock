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

# Create Tables
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

# New Table for Users
c.execute('''CREATE TABLE IF NOT EXISTS users 
             (username TEXT PRIMARY KEY, password TEXT)''')

try:
    c.execute("ALTER TABLE stock ADD COLUMN image_path TEXT")
except sqlite3.OperationalError:
    pass 

conn.commit()

if not os.path.exists("images"):
    os.makedirs("images")

# ==============================
# HELPER FUNCTIONS (Auth)
# ==============================
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

def create_user(username, password):
    c.execute('INSERT INTO users(username,password) VALUES (?,?)', (username, password))
    conn.commit()

def login_user(username, password):
    c.execute('SELECT * FROM users WHERE username =? AND password =?', (username, password))
    data = c.fetchall()
    return data

# ==============================
# 2. UI, STYLING & FULL BACKGROUND
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
                background-color: rgba(0, 0, 0, 0.3) !important;
                backdrop-filter: blur(10px);
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
                box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            }}
            .st-emotion-cache-12w0qpk {{
                background-color: rgba(255, 255, 255, 0.95) !important;
                padding: 30px !important;
                border-radius: 15px !important;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
            }}
            h2, h3, p {{ color: #1E1E1E !important; }}
            </style>
            <div class="corner-footer">Created by: Sino Menghuy</div>
        """, unsafe_allow_html=True)
    else:
        st.sidebar.warning(f"Background image '{image_file}' not found.")

set_ui_design('BackImage.jpg')

# ==============================
# 3. LOGIN / SIGNUP LOGIC
# ==============================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.markdown("""<div class="styled-header">
        <h1 style='margin: 0; color: #FFFFFF !important;'>🔐 System Access</h1>
    </div>""", unsafe_allow_html=True)
    
    auth_menu = st.sidebar.selectbox("Access Mode", ["Login", "Sign Up"])
    
    if auth_menu == "Login":
        st.subheader("Login to your Account")
        username = st.text_input("User Name")
        password = st.text_input("Password", type='password')
        if st.button("Login"):
            hashed_pswd = make_hashes(password)
            result = login_user(username, check_hashes(password, hashed_pswd))
            if result:
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.success(f"Welcome {username}")
                st.rerun()
            else:
                st.error("Incorrect Username/Password")

    elif auth_menu == "Sign Up":
        st.subheader("Create New Account")
        new_user = st.text_input("Username")
        new_password = st.text_input("Password", type='password')
        if st.button("Signup"):
            create_user(new_user, make_hashes(new_password))
            st.success("You have successfully created a valid Account")
            st.info("Go to Login Menu to login")

else:
    # ==============================
    # 4. MAIN APPLICATION (AUTHENTICATED)
    # ==============================
    st.sidebar.write(f"Logged in as: **{st.session_state['username']}**")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.markdown("""
    <div class="styled-header">
        <h1 style='margin: 0; color: #FFFFFF !important; font-size: 38px; font-weight: 800;'>🌸 SK97 Stock Management</h1>
        <p style='margin: 15px 0 0 0; color: #FFFFFF !important; font-size: 14px; font-weight: 400; opacity: 0.9;'>Managed by: ZK7 Office</p>
    </div>""", unsafe_allow_html=True)

    menu = st.sidebar.selectbox("Select Menu", ["View Stock", "Stock In", "Stock Out", "Daily Reports"])

    # --- REST OF YOUR ORIGINAL CODE ---
    if menu == "View Stock":
        st.subheader("📦 Current Inventory")
        df = pd.read_sql_query("SELECT product_name as 'Product', quantity as 'In Stock' FROM stock", conn)
        
        if not df.empty:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📊 Download Inventory", data=csv, file_name="Sakura97_Inventory.csv", mime='text/csv')
            
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
                    st.success(f"✅ Recorded: {qty} units of {name} added.")
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
                    st.success(f"✅ Removed {qty_out} units of {selected_prod}")
                    st.rerun()
                else:
                    st.error(f"Not enough stock! Current balance: {current_inv}")
        else:
            st.warning("No products available to remove.")

    elif menu == "Daily Reports":
        st.subheader("🗓 Transaction Archive (2026-2100)")
        
        col_y, col_m = st.columns(2)
        with col_y:
            sel_year = st.selectbox("Year", list(range(2026, 2101)), index=0)
        with col_m:
            months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            sel_month = st.selectbox("Month", months, index=datetime.now().month - 1)

        st.write("🔍 Filter by Day Range:")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            start_day = st.number_input("From Day", min_value=1, max_value=31, value=1)
        with col_d2:
            end_day = st.number_input("To Day", min_value=1, max_value=31, value=31)

        month_idx = f"{months.index(sel_month) + 1:02d}"
        search_str = f"{sel_year}-{month_idx}%"
        report_df = pd.read_sql_query("SELECT date, product_name as 'Product', type as 'Action', qty as 'Quantity' FROM transactions WHERE date LIKE ? ORDER BY date DESC", conn, params=(search_str,))
        
        if not report_df.empty:
            report_df['Date/Time'] = pd.to_datetime(report_df['date'])
            report_df['Day'] = report_df['Date/Time'].dt.day
            filtered_df = report_df[(report_df['Day'] >= start_day) & (report_df['Day'] <= end_day)]
            display_df = filtered_df[['Date/Time', 'Day', 'Product', 'Action', 'Quantity']]
            
            if not display_df.empty:
                st.dataframe(display_df, use_container_width=True)
                total_in = display_df[display_df['Action'] == 'IN']['Quantity'].sum()
                total_out = display_df[display_df['Action'] == 'OUT']['Quantity'].sum()
                st.info(f"📊 Summary: {total_in} units In | {total_out} units Out")
                
                csv_report = display_df.to_csv(index=False).encode('utf-8')
                st.download_button(f"📥 Download Report", data=csv_report, file_name=f"Sakura97_{sel_month}_{sel_year}.csv")
            else:
                st.warning(f"No records for Day {start_day}-{end_day}.")
        else:
            st.write(f"No activity for {sel_month} {sel_year}.")

