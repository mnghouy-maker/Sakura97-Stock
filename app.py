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
conn = sqlite3.connect('stock.db', check_same_thread=False)
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
# 3. UI DESIGN (UPDATED FOR WHITE TEXT)
# ==============================
def set_ui_design(image_file):
    if os.path.exists(image_file):
        with open(image_file, "rb") as f:
            data = f.read()
        encoded_string = base64.b64encode(data).decode()
        st.markdown(f"""
            <style>
            /* Main App Background */
            .stApp {{
                background-image: url("data:image/png;base64,{encoded_string}");
                background-attachment: fixed;
                background-size: cover;
                background-position: center;
            }}

            /* GLOBAL TEXT COLOR: WHITE */
            h1, h2, h3, h4, h5, h6, p, li, label, .stMarkdown, .stText, .stMetric, [data-testid="stHeader"] {{
                color: white !important;
            }}

            /* Sidebar text and background */
            [data-testid="stSidebar"] {{
                background-color: rgba(0, 0, 0, 0.5) !important;
                backdrop-filter: blur(15px);
            }}
            [data-testid="stSidebar"] * {{
                color: white !important;
            }}

            /* Header Box */
            .styled-header {{
                background-color: rgba(38, 39, 48, 0.8);
                color: #ffffff !important;
                padding: 40px 20px;
                border-radius: 20px;
                text-align: center;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                margin: 0 auto 40px auto;
                max-width: 700px;
            }}

            /* Footer */
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

            /* Form Containers (Changed to dark/transparent for white text contrast) */
            [data-testid="stVerticalBlock"] > div:has(div.stForm) {{
                background-color: rgba(0, 0, 0, 0.4);
                padding: 20px;
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}

            /* Metric styling */
            [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {{
                color: white !important;
            }}

            header {{background: rgba(0,0,0,0) !important;}}
            
            /* Input Box Fixes */
            .stTextInput input, .stNumberInput input {{
                color: white !important;
                background-color: rgba(255,255,255,0.1) !important;
            }}
            </style>
            <div class="corner-footer">Created by: Sino Menghuy</div>
        """, unsafe_allow_html=True)
    else:
        st.sidebar.warning(f"Background '{image_file}' not found.")

set_ui_design('BackImage.jpg')

# ==============================
# 4. SESSION STATE INIT
# ==============================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user'] = None

# ==============================
# 5. AUTHENTICATION LOGIC
# ==============================
if not st.session_state['logged_in']:
    st.markdown('<div class="styled-header"><h1 style="color:white !important;">🔐 System Access</h1></div>', unsafe_allow_html=True)
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
                    st.success("Account created! You can now Login.")
                except sqlite3.IntegrityError:
                    st.error("Username already exists.")
            else:
                st.warning("Please fill all fields.")
    
    elif auth_mode == "Login":
        st.subheader("Login to Sakura97")
        user = st.text_input("Username").strip()
        pswd = st.text_input("Password", type='password').strip()
        if st.button("Login"):
            c.execute('SELECT password FROM users WHERE username = ?', (user,))
            result = c.fetchone()
            if result and check_hashes(pswd, result[0]):
                st.session_state['logged_in'] = True
                st.session_state['user'] = user
                st.rerun()
            else:
                st.error("Invalid Username or Password.")

# ==============================
# 6. MAIN APP (LOGGED IN)
# ==============================
else:
    st.sidebar.success(f"Welcome, {st.session_state['user']}")
    if st.sidebar.button("Log Out"):
        st.session_state['logged_in'] = False
        st.session_state['user'] = None
        st.rerun()

    st.markdown("""
    <div class="styled-header">
        <h1 style='margin: 0; color: #FFFFFF !important; font-size: 38px; font-weight: 800;'>🌸 Sakura97 Stock Management</h1>
        <p style='margin: 15px 0 0 0; color: #FFFFFF !important; font-size: 14px; font-weight: 400; opacity: 0.9;'>Managed by: ZK7 Office</p>
    </div>""", unsafe_allow_html=True)

    menu = st.sidebar.selectbox("Select Menu", ["View Stock", "Stock In", "Stock Out", "Daily Reports"])

    # -------- VIEW STOCK --------
    if menu == "View Stock":
        st.subheader("📦 Current Inventory")
        df = pd.read_sql_query("SELECT product_name as 'Product', quantity as 'In Stock' FROM stock", conn)
        if not df.empty:
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

    # -------- STOCK IN --------
    elif menu == "Stock In":
        st.subheader("📥 Add/Update Stock")
        with st.form("stock_in_form"):
            name = st.text_input("Product Name").strip()
            qty = st.number_input("Quantity to Add", min_value=1)
            img_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])
            submitted = st.form_submit_button("Submit Stock In")
            if submitted and name:
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

    # -------- STOCK OUT --------
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
                    if new_inv == 0: c.execute("DELETE FROM stock WHERE product_name = ?", (selected_prod,))
                    else: c.execute("UPDATE stock SET quantity = ? WHERE product_name = ?", (new_inv, selected_prod))
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    c.execute("INSERT INTO transactions (product_name, type, qty, date) VALUES (?, ?, ?, ?)", (selected_prod, "OUT", qty_out, now))
                    conn.commit()
                    st.success(f"✅ Removed {qty_out} units.")
                    st.rerun()
                else: st.error(f"Not enough stock! Balance: {current_inv}")

    # -------- DAILY REPORTS --------
    elif menu == "Daily Reports":
        st.subheader("🗓 Transaction Archive & Custom Reports")
        
        col_start, col_end = st.columns(2)
        with col_start:
            start_date = st.date_input("Start Date", datetime.now().replace(day=1))
        with col_end:
            end_date = st.date_input("End Date", datetime.now())

        if start_date > end_date:
            st.error("Error: Start Date must be before End Date.")
        else:
            query = """
                SELECT date, product_name as 'Product', type as 'Action', qty as 'Quantity' 
                FROM transactions 
                WHERE date(date) BETWEEN date(?) AND date(?)
                ORDER BY date DESC
            """
            report_df = pd.read_sql_query(query, conn, params=(str(start_date), str(end_date)))

            if not report_df.empty:
                st.info(f"Report for: {start_date} to {end_date}")
                st.dataframe(report_df, use_container_width=True)
                
                st.markdown("### 📥 Download Reports")
                col_ex1, col_ex2 = st.columns(2)

                output_excel = BytesIO()
                with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                    report_df.to_excel(writer, index=False, sheet_name='Summary')
                col_ex1.download_button(
                    label="🟢 Download Excel",
                    data=output_excel.getvalue(),
                    file_name=f"Report_{start_date}_to_{end_date}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(190, 10, f"Stock Report: {start_date} to {end_date}", ln=True, align='C')
                pdf.ln(10)
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(45, 10, "Date", 1); pdf.cell(65, 10, "Product", 1); pdf.cell(40, 10, "Action", 1); pdf.cell(30, 10, "Qty", 1); pdf.ln()
                pdf.set_font("Arial", '', 10)
                for _, r in report_df.iterrows():
                    pdf.cell(45, 10, str(r['date'])[:10], 1)
                    pdf.cell(65, 10, str(r['Product']), 1)
                    pdf.cell(40, 10, str(r['Action']), 1)
                    pdf.cell(30, 10, str(r['Quantity']), 1); pdf.ln()
                
                col_ex2.download_button(
                    label="🔴 Download PDF",
                    data=pdf.output(dest='S').encode('latin-1'),
                    file_name=f"Report_{start_date}_to_{end_date}.pdf",
                    mime="application/pdf"
                )

                st.markdown("---")
                st.subheader("📊 Period Totals")
                m_col1, m_col2 = st.columns(2)
                total_in = report_df[report_df['Action'] == 'IN']['Quantity'].sum()
                total_out = report_df[report_df['Action'] == 'OUT']['Quantity'].sum()
                m_col1.metric("Total Stock In", f"{total_in} units")
                m_col2.metric("Total Stock Out", f"{total_out} units")
            else:
                st.warning(f"No transactions found between {start_date} and {end_date}.")
