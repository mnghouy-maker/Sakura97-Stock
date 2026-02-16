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
if not os.path.exists("images"):
    os.makedirs("images")

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

conn.commit()

# ==============================
# 2. SECURITY FUNCTIONS
# ==============================
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

# ==============================
# 3. UI DESIGN (GRAY THEME)
# ==============================
@st.cache_data
def get_base64_bin(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def set_ui_design(image_file):
    encoded_string = get_base64_bin(image_file)
    bg_style = f'background-image: url("data:image/png;base64,{encoded_string}");' if encoded_string else ""
    st.markdown(f"""
        <style>
        .stApp {{ {bg_style} background-attachment: fixed; background-size: cover; background-position: center; }}
        
        h1, h2, h3, h4, h5, h6, p, li, label, .stMarkdown, .stText, .stMetric, [data-testid="stHeader"] {{ 
            color: white !important; 
        }}

        [data-testid="stSidebar"] {{ 
            background-color: rgba(0, 0, 0, 0.7) !important; 
            backdrop-filter: blur(15px); 
        }}
        
        div[data-baseweb="select"] > div {{ background-color: #4F4F4F !important; border: 1px solid #707070 !important; color: white !important; }}
        div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input {{ 
            background-color: #4F4F4F !important; 
            color: white !important; 
            border: 1px solid #707070 !important; 
        }}

        div.stButton > button {{ 
            background-color: #616161 !important; 
            color: white !important; 
            border: 1px solid #888888 !important; 
            border-radius: 8px; 
            width: 100%; 
        }}
        
        .stButton > button[key^="del_"] {{
            background-color: #8B0000 !important;
            border-color: #FF4B4B !important;
        }}

        div.stButton > button:hover {{ 
            background-color: #808080 !important; 
            border-color: white !important; 
        }}

        [data-testid="stVerticalBlock"] > div:has(div.stForm), .stDataFrame, .stTable, .element-container:has(.stMetric) {{ 
            background-color: rgba(70, 70, 70, 0.6) !important; 
            padding: 15px; 
            border-radius: 12px; 
            border: 1px solid #555; 
        }}

        .styled-header {{ 
            background-color: rgba(50, 50, 50, 0.8); 
            padding: 40px 20px; 
            border-radius: 20px; 
            text-align: center; 
            margin-bottom: 40px; 
        }}
        header {{background: rgba(0,0,0,0) !important;}}
        </style>
    """, unsafe_allow_html=True)

set_ui_design('BackImage.jpg')

# ==============================
# 4. AUTHENTICATION
# ==============================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.markdown('<div class="styled-header"><h1>🔐 System Access</h1></div>', unsafe_allow_html=True)
    auth_mode = st.sidebar.selectbox("Access Mode", ["Login", "Sign Up"])
    user = st.text_input("Username").strip()
    pswd = st.text_input("Password", type='password').strip()
    
    if st.button("Submit"):
        if auth_mode == "Login":
            c.execute('SELECT password FROM users WHERE username = ?', (user,))
            res = c.fetchone()
            if res and check_hashes(pswd, res[0]):
                st.session_state['logged_in'] = True
                st.session_state['user'] = user
                st.rerun()
            else: st.error("Invalid credentials")
        else:
            try:
                c.execute('INSERT INTO users(username, password) VALUES (?,?)', (user, make_hashes(pswd)))
                conn.commit()
                st.success("Account created!")
            except: st.error("User already exists.")
else:
    # ==============================
    # 5. MAIN APP LOGIC
    # ==============================
    if st.sidebar.button("Log Out"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.markdown('<div class="styled-header"><h1>🌸 SK97 Stock Management</h1></div>', unsafe_allow_html=True)
    menu = st.sidebar.selectbox("Select Menu", ["View Stock", "Stock In", "Stock Out", "Daily Reports"])

    # --- VIEW STOCK ---
    if menu == "View Stock":
        df = pd.read_sql_query("SELECT product_name, quantity FROM stock", conn)
        st.subheader(f"📦 Current Inventory ({len(df)} Types)")
        
        if not df.empty:
            for i, row in enumerate(df.iloc, 1):
                col0, col1, col2, col3 = st.columns([0.5, 1.5, 4, 1])
                img_p = os.path.join("images", f"{row['product_name']}.png")
                
                with col0:
                    st.write(f"### {i}.") 
                
                with col1:
                    if os.path.exists(img_p): st.image(img_p)
                    else: st.write("🖼️")
                
                with col2:
                    st.write(f"### {row['product_name']}")
                    st.write(f"Stock: **{row['quantity']}** units")
                
                with col3:
                    st.write("") 
                    if st.button("Delete", key=f"del_{row['product_name']}"):
                        if os.path.exists(img_p): os.remove(img_p)
                        c.execute("DELETE FROM stock WHERE product_name = ?", (row['product_name'],))
                        conn.commit()
                        st.success(f"Deleted {row['product_name']}")
                        st.rerun()
                st.divider()
        else: 
            st.info("No stock found.")

    # --- STOCK IN ---
    elif menu == "Stock In":
        st.subheader("📥 Stock In / Add New Type")
        
        c.execute("SELECT product_name FROM stock")
        existing_prods = [r[0] for r in c.fetchall()]
        
        tab1, tab2 = st.tabs(["Add to Existing", "Create New Type"])
        
        with tab1:
            if existing_prods:
                with st.form("add_existing"):
                    sel_name = st.selectbox("Select Product", existing_prods)
                    add_qty = st.number_input("Quantity to Add", min_value=1)
                    if st.form_submit_button("Add Stock"):
                        c.execute("UPDATE stock SET quantity = quantity + ? WHERE product_name = ?", (add_qty, sel_name))
                        c.execute("INSERT INTO transactions (product_name, type, qty, date) VALUES (?, 'IN', ?, ?)", 
                                  (sel_name, add_qty, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        conn.commit()
                        st.success(f"Added {add_qty} to {sel_name}")
                        st.rerun()
            else:
                st.info("No products registered yet. Go to 'Create New Type'.")

        with tab2:
            with st.form("create_new"):
                new_name = st.text_input("New Product Name")
                initial_qty = st.number_input("Initial Quantity", min_value=0, value=0)
                new_img = st.file_uploader("Upload Any Photo", type=['png', 'jpg', 'jpeg'])
                
                if st.form_submit_button("Register Product"):
                    if new_name:
                        # Ensures folder exists
                        if not os.path.exists("images"): os.makedirs("images")
                        
                        # Use Product Name as the file name, regardless of what the user uploaded
                        img_path = os.path.join("images", f"{new_name}.png")
                        
                        try:
                            if new_img: 
                                # Convert and save as PNG using the Product Name
                                Image.open(new_img).convert("RGB").save(img_path, "PNG")
                            
                            c.execute("INSERT INTO stock (product_name, quantity, image_path) VALUES (?, ?, ?)", 
                                      (new_name, initial_qty, img_path))
                            
                            if initial_qty > 0:
                                c.execute("INSERT INTO transactions (product_name, type, qty, date) VALUES (?, 'IN', ?, ?)", 
                                          (new_name, initial_qty, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                            
                            conn.commit()
                            st.success(f"Registered {new_name} successfully!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("This product name already exists!")
                        except Exception as e:
                            st.error(f"Error: {e}")
                    else:
                        st.error("Please enter a product name.")

    # --- STOCK OUT ---
    elif menu == "Stock Out":
        st.subheader("📤 Stock Out")
        c.execute("SELECT product_name FROM stock")
        prods = [r[0] for r in c.fetchall()]
        if prods:
            with st.form("out"):
                sel = st.selectbox("Product", prods)
                q_out = st.number_input("Qty", min_value=1)
                if st.form_submit_button("Confirm"):
                    c.execute("SELECT quantity FROM stock WHERE product_name = ?", (sel,))
                    res = c.fetchone()
                    if res and q_out <= res[0]:
                        c.execute("UPDATE stock SET quantity = quantity - ? WHERE product_name = ?", (q_out, sel))
                        c.execute("INSERT INTO transactions (product_name, type, qty, date) VALUES (?, 'OUT', ?, ?)", (sel, q_out, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        conn.commit()
                        st.success("Updated successfully!")
                        st.rerun()
                    else: st.error("Insufficient stock!")
        else: st.warning("Inventory is empty.")

    # --- DAILY REPORTS ---
    elif menu == "Daily Reports":
        st.subheader("🗓 Reports")
        c1, c2 = st.columns(2)
        start = c1.date_input("Start")
        end = c2.date_input("End")
        
        report_df = pd.read_sql_query("SELECT date, product_name, type, qty FROM transactions WHERE date(date) BETWEEN ? AND ?", conn, params=(str(start), str(end)))
        
        if not report_df.empty:
            st.write(f"#### Total Transactions: {len(report_df)}")
            for i, row in enumerate(report_df.iloc, 1):
                with st.container():
                    r0, r1, r2 = st.columns([0.5, 1, 5])
                    img_p = os.path.join("images", f"{row['product_name']}.png")
                    with r0:
                        st.write(f"**{i}.**")
                    with r1:
                        if os.path.exists(img_p): st.image(img_p, width=60)
                    with r2:
                        color = "green" if row['type'] == 'IN' else "red"
                        st.markdown(f"**{row['date']}** | {row['product_name']} | <span style='color:{color}'>{row['type']}</span> | **{row['qty']}**", unsafe_allow_html=True)
                st.divider()
            
            st.write("### Export")
            buffer = BytesIO()
            report_df.to_excel(buffer, index=False)
            st.download_button("🟢 Download Excel", buffer.getvalue(), "Report.xlsx")
        else:
            st.warning("No data found for these dates.")
