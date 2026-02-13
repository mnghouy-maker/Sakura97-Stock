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
# Connects to your Sakura97-Stock sheet using the ID in Secrets
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(worksheet_name):
    try:
        # ttl="0s" ensures we always see the latest data from the office
        return conn.read(worksheet=worksheet_name, ttl="0s")
    except Exception:
        return pd.DataFrame()

# ==============================
# 2. UI & STYLING (ZK7 Office)
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
            [data-testid="stSidebar"] {{ background-color: rgba(0, 0, 0, 0.7) !important; backdrop-filter: blur(10px); }}
            .styled-header {{ 
                background-color: #262730; 
                padding: 30px; border-radius: 20px; text-align: center; margin-bottom: 30px; 
            }}
            .styled-header h1, .styled-header p {{ color: white !important; margin: 0; }}
            .st-emotion-cache-12w0qpk {{ background-color: rgba(255, 255, 255, 0.95) !important; border-radius: 15px !important; padding: 25px !important; }}
            </style>
        """, unsafe_allow_html=True)

# Load the background image
set_ui_design('BackImage.jpg')

# Ensure image folder exists for local caching
if not os.path.exists("images"): os.makedirs("images")

# ==============================
# 3. AUTHENTICATION
# ==============================
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'username': ""})

if not st.session_state['logged_in']:
    st.markdown('<div class="styled-header"><h1>🌸 Sakura97 Secure Access</h1><p>ZK7 Office</p></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Login", "Create Account"])
    
    with tab1:
        with st.form("login"):
            u_input = st.text_input("Username").strip()
            p_input = st.text_input("Password", type="password").strip()
            if st.form_submit_button("Login"):
                df = get_data("users")
                if not df.empty:
                    # Clean data to match text exactly
                    df['username'] = df['username'].astype(str).str.strip()
                    df['password'] = df['password'].astype(str).str.strip()
                    
                    match = df[(df['username'] == u_input) & (df['password'] == p_input)]
                    if not match.empty:
                        st.session_state.update({'logged_in': True, 'username': u_input})
                        st.rerun()
                st.error("Access Denied: Please check username/password or ensure Google Sheet tab is 'users'.")
    
    with tab2:
        with st.form("signup"):
            nu = st.text_input("New Username").strip()
            np = st.text_input("New Password", type="password").strip()
            if st.form_submit_button("Sign Up"):
                df = get_data("users")
                if nu and np:
                    new_row = pd.DataFrame([{"username": nu, "password": np}])
                    updated_df = pd.concat([df, new_row], ignore_index=True) if not df.empty else new_row
                    conn.update(worksheet="users", data=updated_df)
                    st.success("Account created successfully! Please go to the Login tab.")
    st.stop()

# ==============================
# 4. MAIN APPLICATION
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
        else: st.info("No stock items found for your account.")
    else: st.warning("Stock database is currently empty.")

# --- STOCK IN ---
elif menu == "Stock In":
    st.subheader("📥 Add Stock to Cloud")
    with st.form("stock_in"):
        name = st.text_input("Product Name").strip()
        qty = st.number_input("Quantity", min_value=1)
        img_file = st.file_uploader("Upload Product Image", type=["jpg", "png"])
        if st.form_submit_button("Save to Google Sheets"):
            if name:
                stock_df = get_data("stock")
                # Update existing or add new
                idx = stock_df[(stock_df['user_id'] == curr_user) & (stock_df['product_name'] == name)].index
                if not idx.empty:
                    stock_df.at[idx[0], 'quantity'] += qty
                else:
                    new_item = pd.DataFrame([{"product_name": name, "quantity": qty, "user_id": curr_user}])
                    stock_df = pd.concat([stock_df, new_item], ignore_index=True)
                
                if img_file: Image.open(img_file).save(f"images/{curr_user}_{name}.png")
                conn.update(worksheet="stock", data=stock_df)
                
                # Log transaction
                trans_df = get_data("transactions")
                new_t = pd.DataFrame([{"date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "product_name": name, "type": "IN", "qty": qty, "user_id": curr_user}])
                conn.update(worksheet="transactions", data=pd.concat([trans_df, new_t], ignore_index=True))
                st.success("Cloud Updated successfully!")
            else: st.error("Product name cannot be empty.")

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
                    
                    trans_df = get_data("transactions")
                    new_t = pd.DataFrame([{"date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "product_name": sel, "type": "OUT", "qty": q_out, "user_id": curr_user}])
                    conn.update(worksheet="transactions", data=pd.concat([trans_df, new_t], ignore_index=True))
                    st.success("Stock removed and logged!")
                    st.rerun()
                else: st.error("Error: Not enough stock in inventory.")
        else: st.info("You have no items in stock to remove.")

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
        
        # Filter for the current user and selected time
        report = trans_df[(trans_df['user_id'] == curr_user) & 
                          (trans_df['date_dt'].dt.year == y) & 
                          (trans_df['date_dt'].dt.month == m_idx)]
        
        if not report.empty:
            st.dataframe(report[['date', 'product_name', 'type', 'qty']], use_container_width=True)
        else: st.info("No transaction history found for this month.")
    else: st.info("No transactions recorded yet.")
