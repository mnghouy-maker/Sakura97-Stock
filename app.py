import streamlit as st
import sqlite3
import os
import base64
import pandas as pd
import hashlib
from datetime import datetime
from PIL import Image
from io import BytesIO
from fpdf import FPDF

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
# 2. SECURITY & UTILS
# ==============================
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

def create_pdf(df, start, end):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=f"SK97 Stock Report ({start} to {end})", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(45, 10, "Date", 1)
    pdf.cell(85, 10, "Product", 1)
    pdf.cell(30, 10, "Type", 1)
    pdf.cell(30, 10, "Qty", 1)
    pdf.ln()
    pdf.set_font("Arial", size=10)
    for index, row in df.iterrows():
        # Encode to latin-1 and replace unknown chars with '?' to avoid UnicodeEncodeError
        name_safe = str(row['product_name']).encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(45, 10, str(row['date'])[:10], 1)
        pdf.cell(85, 10, name_safe, 1)
        pdf.cell(30, 10, str(row['type']), 1)
        pdf.cell(30, 10, str(row['qty']), 1)
        pdf.ln()
    return pdf.output(dest='S')

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
        h1, h2, h3, h4, h5, h6, p, li, label, .stMarkdown, .stText, .stMetric, [data-testid="stHeader"] {{ color: white !important; }}
        [data-testid="stSidebar"] {{ background-color: rgba(0, 0, 0, 0.7) !important; backdrop-filter: blur(15px); }}
        div[data-baseweb="select"] > div {{ background-color: #4F4F4F !important; border: 1px solid #707070 !important; color: white !important; }}
        div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input {{ background-color: #4F4F4F !important; color: white !important; border: 1px solid #707070 !important; }}
        div.stButton > button, div.stFormSubmitButton > button, div.stDownloadButton > button {{ background-color: #616161 !important; color: white !important; border: 1px solid #888888 !important; border-radius: 8px; width: 100%; }}
        div.stButton > button:hover, div.stFormSubmitButton > button:hover {{ background-color: #808080 !important; border-color: white !important; }}
        [data-testid="stVerticalBlock"] > div:has(div.stForm), .stDataFrame, .stTable, .element-container:has(.stMetric) {{ background-color: rgba(70, 70, 70, 0.6) !important; padding: 15px; border-radius: 12px; border: 1px solid #555; }}
        .styled-header {{ background-color: rgba(50, 50, 50, 0.8); padding: 40px 20px; border-radius: 20px; text-align: center; margin-bottom: 40px; }}
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
            except: st.error("User exists")
else:
    # ==============================
    # 5. MAIN APP LOGIC
    # ==============================
    if st.sidebar.button("Log Out"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.markdown('<div class="styled-header"><h1>🌸 SK97 Stock Management</h1></div>', unsafe_allow_html=True)
    menu = st.sidebar.selectbox("Select Menu", ["View Stock", "Stock In", "Stock Out", "Delete Stock", "Daily Reports"])

    # --- VIEW STOCK ---
    if menu == "View Stock":
        st.subheader("📦 Current Inventory")
        df = pd.read_sql_query("SELECT product_name, quantity FROM stock", conn)
        if not df.empty:
            for _, row in df.iterrows():
                col1, col2 = st.columns([1,4])
                img_p = f"images/{row['product_name']}.png"
                with col1:
                    if os.path.exists(img_p): st.image(img_p)
                with col2:
                    st.write(f"### {row['product_name']}")
                    st.write(f"Stock: {row['quantity']} units")
                st.divider()
        else: st.info("No stock found.")

    # --- STOCK IN ---
    elif menu == "Stock In":
        st.subheader("📥 Stock In")
        with st.form("in"):
            name = st.text_input("Product Name")
            qty = st.number_input("Qty", min_value=1)
            img = st.file_uploader("Image", type=['png', 'jpg'])
            if st.form_submit_button("Submit"):
                img_path = f"images/{name}.png"
                if img: Image.open(img).save(img_path)
                c.execute("INSERT OR REPLACE INTO stock (product_name, quantity, image_path) VALUES (?, COALESCE((SELECT quantity FROM stock WHERE product_name=?),0) + ?, ?)", (name, name, qty, img_path))
                c.execute("INSERT INTO transactions (product_name, type, qty, date) VALUES (?, 'IN', ?, ?)", (name, qty, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.success(f"Added {qty} to {name}")

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
                    curr = c.fetchone()[0]
                    if q_out <= curr:
                        c.execute("UPDATE stock SET quantity = quantity - ? WHERE product_name = ?", (q_out, sel))
                        c.execute("INSERT INTO transactions (product_name, type, qty, date) VALUES (?, 'OUT', ?, ?)", (sel, q_out, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        conn.commit()
                        st.success("Updated!")
                        st.rerun()
                    else: st.error("Not enough stock!")
        else: st.warning("Inventory is empty.")

    # --- DELETE STOCK (NEW OPTION) ---
    elif menu == "Delete Stock":
        st.subheader("🗑 Delete Product")
        st.warning("Warning: This will permanently remove the product and its image from the database.")
        c.execute("SELECT product_name FROM stock")
        prods = [r[0] for r in c.fetchall()]
        if prods:
            with st.form("delete_form"):
                to_delete = st.selectbox("Select product to remove", prods)
                confirm = st.checkbox("I confirm I want to delete this product")
                if st.form_submit_button("Delete Permanently"):
                    if confirm:
                        # Remove image file if it exists
                        img_path = f"images/{to_delete}.png"
                        if os.path.exists(img_path):
                            os.remove(img_path)
                        # Remove from DB
                        c.execute("DELETE FROM stock WHERE product_name = ?", (to_delete,))
                        conn.commit()
                        st.success(f"Deleted {to_delete}")
                        st.rerun()
                    else:
                        st.error("Please check the confirmation box first.")
        else:
            st.info("No products to delete.")

    # --- DAILY REPORTS ---
    elif menu == "Daily Reports":
        st.subheader("🗓 Reports")
        c1, c2 = st.columns(2)
        start = c1.date_input("Start")
        end = c2.date_input("End")
        report_df = pd.read_sql_query("SELECT date, product_name, type, qty FROM transactions WHERE date(date) BETWEEN ? AND ?", conn, params=(str(start), str(end)))
        if not report_df.empty:
            for _, row in report_df.iterrows():
                with st.container():
                    r1, r2 = st.columns([1, 5])
                    img_p = f"images/{row['product_name']}.png"
                    with r1:
                        if os.path.exists(img_p): st.image(img_p, width=60)
                    with r2:
                        color = "green" if row['type'] == 'IN' else "red"
                        st.markdown(f"**{row['date']}** | {row['product_name']} | <span style='color:{color}'>{row['type']}</span> | **{row['qty']}**", unsafe_allow_html=True)
                st.divider()
            
            st.write("### Export")
            pdf_bytes = create_pdf(report_df, start, end)
            st.download_button("🔴 Download PDF", pdf_bytes, "Report.pdf", "application/pdf")
            buffer = BytesIO()
            report_df.to_excel(buffer, index=False)
            st.download_button("🟢 Download Excel", buffer.getvalue(), "Report.xlsx")
        else:
            st.warning("No data found.")
