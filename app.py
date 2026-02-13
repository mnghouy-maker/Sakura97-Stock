import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import os
import base64
from datetime import datetime
from PIL import Image

# ==============================
# 1. GOOGLE SHEETS CONNECTION
# ==============================
# Connects to your Sheet ID: 1bMPsjGBFMIJ01TtKY-pfEguJYCuSY_rSm4wcFFutTcQ
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(worksheet_name):
    try:
        # ttl=0 is the "Zero-Cache" fix. It forces the app to read row 2 now.
        df = conn.read(worksheet=worksheet_name, ttl=0)
        if df is None or df.empty:
            if worksheet_name == "users": return pd.DataFrame(columns=["username", "password"])
            if worksheet_name == "stock": return pd.DataFrame(columns=["product_name", "quantity", "user_id"])
            if worksheet_name == "transactions": return pd.DataFrame(columns=["date", "product_name", "type", "qty", "user_id"])
        return df
    except Exception as e:
        st.error(f"Sheet Connection Error: {e}")
        return pd.DataFrame()

# ==============================
# 2. UI & STYLING (The 97 Casino / ZK7 Office)
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
            [data-testid="stSidebar"] {{ background-color: rgba(0, 0, 0, 0.8) !important; backdrop-filter: blur(10px); }}
            .styled-header {{ 
                background-color: #262730; 
                padding: 30px; border-radius: 20px; text-align: center; margin-bottom: 30px; 
            }}
            .styled-header h1, .styled-header p {{ color: white !important; margin: 0; }}
            .st-emotion-cache-12w0qpk {{ background-color: rgba(255, 255, 255, 0.95) !important; border-radius: 15px !important; padding: 25px !important; }}
            </style>
        """, unsafe_allow_html=True)

set_ui_design('BackImage.jpg')
if not os.path.exists("images"): os.makedirs("images")

# ==============================
# 3. LOGIN SYSTEM (CLEAN MATCHING)
# ==============================
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'username': ""})

if not st.session_state['logged_in']:
    st.markdown('<div class="styled-header"><h1>🌸 Sakura97 Secure Access</h1><p>ZK7 Office Cloud</p></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Login", "Create Account"])
    
    with tab1:
        with st.form("login"):
            u_input = st.text_input("Username").strip()
            p_input = st.text_input("Password", type="password").strip()
            
            if st.form_submit_button("Login"):
                df = get_data("users")
                if not df.empty:
                    # Clean the data from the sheet to prevent "Ghost" errors
                    df['username'] = df['username'].astype(str).str.strip()
                    df['password'] = df['password'].astype(str).str.strip()
                    
                    match = df[(df['username'] == u_input) & (df['password'] == p_input)]
                    
                    if not match.empty:
                        st.session_state.update({'logged_in': True, 'username': u_input})
                        st.rerun()
                    else:
                        st.error("Access Denied: Check Row 2 in your Google Sheet.")
                else:
                    st.error("Database Error: 'users' tab is empty or not found.")
    
    with tab2:
        with st.form("signup"):
            nu = st.text_input("New Username").strip()
            np = st.text_input("New Password", type="password").strip()
            if st.form_submit_button("Sign Up"):
                if nu and np:
                    df = get_data("users")
                    new_row = pd.DataFrame([{"username": nu, "password": np}])
                    updated_df = pd.concat([df, new_row], ignore_index=True)
                    conn.update(worksheet="users", data=updated_df)
                    st.success("User added to Cloud! Now try logging in.")
    st.stop()

# ==============================
# 4. INVENTORY MANAGEMENT
# ==============================
curr_user = st.session_state['username']
st.sidebar.title(f"👤 {curr_user}")
if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False
    st.rerun()

st.markdown(f'<div class="styled-header"><h1>🌸 Sakura97 Stock Management</h1><p>ZK7 Office | {curr_user}</p></div>', unsafe_allow_html=True)

menu = st.sidebar.selectbox("Menu", ["View Stock", "Stock In", "Stock Out", "Daily Reports"])

# --- VIEW STOCK ---
if menu == "View Stock":
    stock_df = get_data("stock")
    if not stock_df.empty:
        my_stock = stock_df[stock_df['user_id'] == curr_user]
        if not my_stock.empty:
            for _, row in my_stock.iterrows():
                with st.container():
                    col1, col2 = st.columns([1,4])
                    img_path = f"images/{curr_user}_{row['product_name']}.png"
                    with col1:
                        if os.path.exists(img_path): st.image(img_path, use_container_width=True)
                        else: st.caption("No Image")
                    with col2:
                        st.subheader(row['product_name'])
                        st.write(f"Quantity: {row['quantity']} units")
                        st.markdown("---")
        else: st.info("Inventory is empty.")
    else: st.warning("Stock tab is empty.")

# --- STOCK IN ---
elif menu == "Stock In":
    st.subheader("📥 Add Stock")
    with st.form("stock_in"):
        name = st.text_input("Product Name").strip()
        qty = st.number_input("Quantity", min_value=1)
        img_file = st.file_uploader("Upload Image", type=["jpg", "png"])
        if st.form_submit_button("Save to Cloud"):
            if name:
                stock_df = get_data("stock")
                idx = stock_df[(stock_df['user_id'] == curr_user) & (stock_df['product_name'] == name)].index
                if not idx.empty:
                    stock_df.at[idx[0], 'quantity'] += qty
                else:
                    new_item = pd.DataFrame([{"product_name": name, "quantity": qty, "user_id": curr_user}])
                    stock_df = pd.concat([stock_df, new_item], ignore_index=True)
                
                if img_file: Image.open(img_file).save(f"images/{curr_user}_{name}.png")
                conn.update(worksheet="stock", data=stock_df)
                
                # Transaction Log
                trans_df = get_data("transactions")
                new_t = pd.DataFrame([{"date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "product_name": name, "type": "IN", "qty": qty, "user_id": curr_user}])
                conn.update(worksheet="transactions", data=pd.concat([trans_df, new_t], ignore_index=True))
                st.success("Synced to Cloud!")
            else: st.error("Product name required.")

# --- STOCK OUT ---
elif menu == "Stock Out":
    st.subheader("📤 Remove Stock")
    stock_df = get_data("stock")
    if not stock_df.empty:
        my_items = stock_df[stock_df['user_id'] == curr_user]['product_name'].tolist()
        if my_items:
            sel = st.selectbox("Select Product", my_items)
            q_out = st.number_input("Quantity Out", min_value=1)
            if st.button("Confirm Removal"):
                idx = stock_df[(stock_df['user_id'] == curr_user) & (stock_df['product_name'] == sel)].index[0]
                if q_out <= stock_df.at[idx, 'quantity']:
                    stock_df.at[idx, 'quantity'] -= q_out
                    conn.update(worksheet="stock", data=stock_df)
                    
                    # Transaction Log
                    trans_df = get_data("transactions")
                    new_t = pd.DataFrame([{"date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "product_name": sel, "type": "OUT", "qty": q_out, "user_id": curr_user}])
                    conn.update(worksheet="transactions", data=pd.concat([trans_df, new_t], ignore_index=True))
                    st.success("Cloud Updated!"); st.rerun()
                else: st.error("Not enough stock available.")

# --- DAILY REPORTS ---
elif menu == "Daily Reports":
    st.subheader("🗓 Transaction Archive")
    trans_df = get_data("transactions")
    if not trans_df.empty:
        trans_df['date_dt'] = pd.to_datetime(trans_df['date'])
        y = st.selectbox("Year", [2026, 2025])
        m_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        m = st.selectbox("Month", m_names, index=datetime.now().month-1)
        m_idx = m_names.index(m) + 1
        
        report = trans_df[(trans_df['user_id'] == curr_user) & (trans_df['date_dt'].dt.year == y) & (trans_df['date_dt'].dt.month == m_idx)]
        if not report.empty:
            st.dataframe(report[['date', 'product_name', 'type', 'qty']], use_container_width=True)
        else: st.info("No records for this month.")
