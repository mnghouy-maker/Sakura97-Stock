import streamlit as st
import sqlite3
import os
import base64
import pandas as pd
from datetime import datetime
from PIL import Image

# ==============================
# DATABASE SETUP
# ==============================
conn = sqlite3.connect('stock.db', check_same_thread=False)
c = conn.cursor()

# Users Table
c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
            )''')

# Stock Table (linked to user)
c.execute('''CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            product_name TEXT,
            quantity INTEGER,
            image_path TEXT
            )''')

# Transactions Table
c.execute('''CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            product_name TEXT,
            type TEXT,
            qty INTEGER,
            date TEXT
            )''')

conn.commit()

if not os.path.exists("images"):
    os.makedirs("images")

# ==============================
# LOGIN SYSTEM
# ==============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

def login():
    st.title("🔐 Login to Sakura97 Stock System")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Login"):
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            user = c.fetchone()
            if user:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password")

    with col2:
        if st.button("Register"):
            try:
                c.execute("INSERT INTO users (username, password) VALUES (?,?)", (username, password))
                conn.commit()
                st.success("Account created! Now login.")
            except:
                st.error("Username already exists.")

if not st.session_state.logged_in:
    login()
    st.stop()

# ==============================
# FORCE BLACK TEXT CSS
# ==============================
st.markdown("""
<style>
h2, h3, label, .stSubheader, .stSelectbox label,
.stNumberInput label, .stTextInput label,
.stFileUploader label {
    color: black !important;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# HEADER
# ==============================
st.markdown("""
<div style='background-color:#262730;padding:40px;border-radius:20px;text-align:center;margin-bottom:40px;'>
<h1 style='color:white;'>🌸 Sakura97 Stock Management</h1>
<p style='color:white;'>Managed by: ZK7 Office</p>
</div>
""", unsafe_allow_html=True)

st.write(f"👤 Logged in as: {st.session_state.username}")

if st.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

menu = st.sidebar.selectbox("Select Menu", ["View Stock", "Stock In", "Stock Out", "Daily Reports"])

# ==============================
# VIEW STOCK
# ==============================
if menu == "View Stock":
    st.subheader("Current Inventory")

    df = pd.read_sql_query(
        "SELECT product_name as 'Product', quantity as 'In Stock' FROM stock WHERE username=?",
        conn,
        params=(st.session_state.username,)
    )

    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No items in stock.")

# ==============================
# STOCK IN
# ==============================
elif menu == "Stock In":
    st.subheader("Add/Update Stock")

    name = st.text_input("Product Name")
    qty = st.number_input("Quantity to Add", min_value=1)
    img_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])

    if st.button("Submit"):
        img_path = f"images/{st.session_state.username}_{name}.png"

        if img_file:
            Image.open(img_file).save(img_path)

        c.execute("SELECT * FROM stock WHERE username=? AND product_name=?",
                  (st.session_state.username, name))
        existing = c.fetchone()

        if existing:
            c.execute("UPDATE stock SET quantity = quantity + ? WHERE username=? AND product_name=?",
                      (qty, st.session_state.username, name))
        else:
            c.execute("INSERT INTO stock (username, product_name, quantity, image_path) VALUES (?,?,?,?)",
                      (st.session_state.username, name, qty, img_path))

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO transactions (username, product_name, type, qty, date) VALUES (?,?,?,?,?)",
                  (st.session_state.username, name, "IN", qty, now))

        conn.commit()
        st.success("Stock updated successfully!")

# ==============================
# STOCK OUT
# ==============================
elif menu == "Stock Out":
    st.subheader("Remove Stock")

    c.execute("SELECT product_name FROM stock WHERE username=?", (st.session_state.username,))
    products = [row[0] for row in c.fetchall()]

    if products:
        selected = st.selectbox("Select Product", products)
        qty_out = st.number_input("Quantity to Remove", min_value=1)

        if st.button("Confirm"):
            c.execute("SELECT quantity FROM stock WHERE username=? AND product_name=?",
                      (st.session_state.username, selected))
            current = c.fetchone()[0]

            if qty_out <= current:
                new_qty = current - qty_out

                if new_qty == 0:
                    c.execute("DELETE FROM stock WHERE username=? AND product_name=?",
                              (st.session_state.username, selected))
                else:
                    c.execute("UPDATE stock SET quantity=? WHERE username=? AND product_name=?",
                              (new_qty, st.session_state.username, selected))

                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("INSERT INTO transactions (username, product_name, type, qty, date) VALUES (?,?,?,?,?)",
                          (st.session_state.username, selected, "OUT", qty_out, now))

                conn.commit()
                st.success("Stock removed successfully!")
                st.rerun()
            else:
                st.error("Not enough stock.")
    else:
        st.warning("No products available.")

# ==============================
# DAILY REPORTS
# ==============================
elif menu == "Daily Reports":
    st.subheader("🗓 Transaction Archive (2026-2100)")

    sel_year = st.selectbox("Year", list(range(2026, 2101)))
    months = ["January","February","March","April","May","June",
              "July","August","September","October","November","December"]
    sel_month = st.selectbox("Month", months)

    st.write("Filter by Day Range:")

    start_day = st.number_input("From Day", min_value=1, max_value=31, value=1)
    end_day = st.number_input("To Day", min_value=1, max_value=31, value=31)

    month_idx = f"{months.index(sel_month)+1:02d}"
    search_str = f"{sel_year}-{month_idx}%"

    report_df = pd.read_sql_query(
        "SELECT date, product_name, type, qty FROM transactions WHERE username=? AND date LIKE ? ORDER BY date DESC",
        conn,
        params=(st.session_state.username, search_str)
    )

    if not report_df.empty:
        st.dataframe(report_df, use_container_width=True)
    else:
        st.write(f"No activity for {sel_month} {sel_year}.")
