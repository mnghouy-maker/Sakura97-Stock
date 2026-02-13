import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import os
import base64
from datetime import datetime
from PIL import Image

# ==================================================
# GOOGLE SHEETS CONNECTION (LOCAL JSON)
# ==================================================
conn = st.connection(
    "gsheets",
    type=GSheetsConnection,
    service_account="service_account.json"
)

SPREADSHEET_ID = "1bMPsjGBFMIJ01TtKY-pfEguJYCuSY_rSm4wcFFutTcQ"

# ==================================================
# DATA FUNCTIONS
# ==================================================
def get_data(sheet_name):
    try:
        df = conn.read(
            spreadsheet=SPREADSHEET_ID,
            worksheet=sheet_name
        )
        if df is None:
            return pd.DataFrame()
        return df
    except Exception as e:
        st.error(f"Google Sheets Error ({sheet_name}): {e}")
        return pd.DataFrame()

def update_data(sheet_name, df):
    try:
        conn.update(
            spreadsheet=SPREADSHEET_ID,
            worksheet=sheet_name,
            data=df
        )
    except Exception as e:
        st.error(f"Update Failed ({sheet_name}): {e}")

# ==================================================
# BACKGROUND DESIGN
# ==================================================
def set_background(image_file):
    if os.path.exists(image_file):
        with open(image_file, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        </style>
        """, unsafe_allow_html=True)

set_background("BackImage.jpg")

if not os.path.exists("images"):
    os.makedirs("images")

# ==================================================
# SESSION STATE
# ==================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# ==================================================
# LOGIN PAGE
# ==================================================
if not st.session_state.logged_in:

    st.markdown("""
    <div style="background:#262730;padding:30px;border-radius:20px;text-align:center;margin-bottom:30px;">
        <h1 style="color:white;">🌸 Sakura97 Secure Access</h1>
        <p style="color:white;">ZK7 Office Cloud</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("Username").strip()
        password = st.text_input("Password", type="password").strip()
        submit = st.form_submit_button("Login")

        if submit:
            users_df = get_data("users")

            if users_df.empty:
                st.error("❌ 'users' sheet missing or empty.")
            else:
                users_df["username"] = users_df["username"].astype(str).str.strip()
                users_df["password"] = users_df["password"].astype(str).str.strip()

                match = users_df[
                    (users_df["username"] == username) &
                    (users_df["password"] == password)
                ]

                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

    st.stop()

# ==================================================
# MAIN SYSTEM
# ==================================================
current_user = st.session_state.username

st.sidebar.title(f"👤 {current_user}")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()

st.markdown(f"""
<div style="background:#262730;padding:30px;border-radius:20px;text-align:center;margin-bottom:30px;">
    <h1 style="color:white;">🌸 Sakura97 Stock Management</h1>
    <p style="color:white;">ZK7 Office | {current_user}</p>
</div>
""", unsafe_allow_html=True)

menu = st.sidebar.selectbox("Menu", ["View Stock", "Stock In", "Stock Out", "Daily Reports"])

# ==================================================
# VIEW STOCK
# ==================================================
if menu == "View Stock":
    stock_df = get_data("stock")

    if stock_df.empty:
        st.warning("Stock sheet empty or missing.")
    else:
        my_stock = stock_df[stock_df["user_id"] == current_user]

        if my_stock.empty:
            st.info("No stock available.")
        else:
            for _, row in my_stock.iterrows():
                col1, col2 = st.columns([1, 3])

                with col1:
                    img_path = f"images/{current_user}_{row['product_name']}.png"
                    if os.path.exists(img_path):
                        st.image(img_path, use_container_width=True)
                    else:
                        st.caption("No Image")

                with col2:
                    st.subheader(row["product_name"])
                    st.write(f"Quantity: {row['quantity']}")
                    st.markdown("---")

# ==================================================
# STOCK IN
# ==================================================
elif menu == "Stock In":
    st.subheader("📥 Add Stock")

    with st.form("stock_in"):
        product = st.text_input("Product Name").strip()
        quantity = st.number_input("Quantity", min_value=1)
        image_file = st.file_uploader("Upload Image", type=["png", "jpg"])
        submit = st.form_submit_button("Save")

        if submit:
            if product:
                stock_df = get_data("stock")

                if stock_df.empty:
                    stock_df = pd.DataFrame(columns=["product_name","quantity","user_id"])

                existing = stock_df[
                    (stock_df["product_name"] == product) &
                    (stock_df["user_id"] == current_user)
                ]

                if not existing.empty:
                    idx = existing.index[0]
                    stock_df.at[idx, "quantity"] += quantity
                else:
                    new_row = pd.DataFrame([{
                        "product_name": product,
                        "quantity": quantity,
                        "user_id": current_user
                    }])
                    stock_df = pd.concat([stock_df, new_row], ignore_index=True)

                update_data("stock", stock_df)

                # Save image locally
                if image_file:
                    img = Image.open(image_file)
                    img.save(f"images/{current_user}_{product}.png")

                # Save transaction
                trans_df = get_data("transactions")
                if trans_df.empty:
                    trans_df = pd.DataFrame(columns=["date","product_name","type","qty","user_id"])

                new_trans = pd.DataFrame([{
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "product_name": product,
                    "type": "IN",
                    "qty": quantity,
                    "user_id": current_user
                }])

                trans_df = pd.concat([trans_df, new_trans], ignore_index=True)
                update_data("transactions", trans_df)

                st.success("Stock Added Successfully!")
                st.rerun()
            else:
                st.error("Product name required.")

# ==================================================
# STOCK OUT
# ==================================================
elif menu == "Stock Out":
    st.subheader("📤 Remove Stock")

    stock_df = get_data("stock")

    if stock_df.empty:
        st.warning("Stock sheet missing.")
    else:
        my_items = stock_df[stock_df["user_id"] == current_user]["product_name"].tolist()

        if not my_items:
            st.info("No items available.")
        else:
            selected = st.selectbox("Select Product", my_items)
            qty_out = st.number_input("Quantity Out", min_value=1)

            if st.button("Confirm"):
                idx = stock_df[
                    (stock_df["product_name"] == selected) &
                    (stock_df["user_id"] == current_user)
                ].index[0]

                if qty_out <= stock_df.at[idx, "quantity"]:
                    stock_df.at[idx, "quantity"] -= qty_out
                    update_data("stock", stock_df)

                    trans_df = get_data("transactions")
                    new_trans = pd.DataFrame([{
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "product_name": selected,
                        "type": "OUT",
                        "qty": qty_out,
                        "user_id": current_user
                    }])

                    trans_df = pd.concat([trans_df, new_trans], ignore_index=True)
                    update_data("transactions", trans_df)

                    st.success("Stock Updated!")
                    st.rerun()
                else:
                    st.error("Not enough stock.")

# ==================================================
# DAILY REPORTS
# ==================================================
elif menu == "Daily Reports":
    st.subheader("🗓 Transaction Records")

    trans_df = get_data("transactions")

    if trans_df.empty:
        st.info("No transaction data.")
    else:
        my_trans = trans_df[trans_df["user_id"] == current_user]
        st.dataframe(my_trans, use_container_width=True)
