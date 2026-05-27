import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import time

# --- 1. PAGE CONFIG & THEME ---
st.set_page_config(
    layout="wide", 
    page_title="Mihir Fabrication | ERP", 
    page_icon="🏗️"
)

# Custom CSS for Professional Dark UI
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: bold; color: #00d4ff; }
    .stButton>button {
        width: 100%; border-radius: 12px; height: 3.5em;
        background-color: #1f2937; color: white; border: 1px solid #374151;
        transition: 0.3s; font-weight: bold;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        border-color: #3b82f6; transform: translateY(-3px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.4);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ADMIN LOGIN SECURITY ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Mihir Fabrication ERP Login")
    admin_password = st.text_input("Enter Admin Security Key", type="password")
    if st.button("Login"):
        if admin_password == "Mihir@2026":
            st.session_state.authenticated = True
            st.success("Access Granted!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Invalid Security Key!")
    st.stop()

# --- 3. SECURE DATABASE CONNECTION (Cloud Optimized) ---
if 'db' not in st.session_state:
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        # Streamlit Cloud Advanced Secrets se direct data check karega
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        
        client = gspread.authorize(creds)
        st.session_state.db = client.open("Mihir_Fabrication_DB") 
        st.session_state.conn_status = True
    except Exception as e:
        st.error(f"❌ Database Connection Error: {e}")
        st.stop()

db = st.session_state.db

# --- 4. HEADER SECTION ---
col_title, col_info = st.columns([2, 1])
with col_title:
    st.title("🏗️ Mihir Fabrication ERP")
    st.write(f"👋 **Welcome, Mihir!** | 📅 {datetime.now().strftime('%A, %d %B %Y')}")

with col_info:
    st.markdown(f"""
        <div style='text-align: right; padding-top: 10px; color: #94a3b8;'>
            <b>Location:</b> Ankleshwar Plant<br>
            <b>System Status:</b> Secured v6.0 Enterprise
        </div>
    """, unsafe_allow_html=True)

st.write("---")

# --- 5. LIVE METRICS ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("DB Status", "🟢 Secured Connection")
m2.metric("Plant Unit", "Unit-1 (GJ)")

# Live Expense Fetching
try:
    b_sheet = db.worksheet("Bills")
    bills_data = b_sheet.get_all_records()
    total_exp = sum(float(row['Amount']) for row in bills_data if row['Amount'])
    m3.metric("Shop Expenses", f"₹{total_exp:,.0f}")
except:
    m3.metric("Shop Expenses", "₹0")

m4.metric("Last Backup", datetime.now().strftime("%H:%M"))

st.write("---")

# --- 6. NAVIGATION CENTER ---
st.subheader("🚀 Operational Control Center")

r1c1, r1c2, r1c3 = st.columns(3)
with r1c1:
    if st.button("📄 Generate New Invoice"):
        st.switch_page("pages/1_📄_Bill_Generation.py")
with r1c2:
    if st.button("🔍 Fetch & Print Bill"):
        st.switch_page("pages/2_🔍_Fetch_Bill.py")
with r1c3:
    if st.button("📂 Invoice History"):
        st.switch_page("pages/6_📂_Invoice_Manager.py")

r2c1, r2c2, r2c3 = st.columns(3)
with r2c1:
    if st.button("📅 Attendance & Salary"):
        st.switch_page("pages/3_📅_Attendance.py")
with r2c2:
    if st.button("💸 Workers Advance"):
        st.switch_page("pages/8_💰_Workers_Advance.py")
with r2c3:
    if st.button("💰 Client Payments"):
        st.switch_page("pages/7_💰_Advance_Payment.py")

r3c1, r3c2, r3c3 = st.columns(3)
with r3c1:
    if st.button("🧾 Shop Bills"):
        st.switch_page("pages/4_🧾_Bills.py")
with r3c2:
    if st.button("👥 Client Database"):
        st.switch_page("pages/2_👥_Clients.py")
with r3c3:
    if st.button("📊 Dashboard"):
        st.switch_page("pages/5_Dashboard.py")

st.write("---")

# --- 7. FOOTER ---
st.markdown("<div style='text-align: center; color: #4b5563; font-size: 12px;'>Mihir Fabrication ERP System | 🔒 Encrypted Session </div>", unsafe_allow_html=True)
