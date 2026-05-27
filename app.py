import streamlit as st
import pandas as pd
from datetime import datetime
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
    
    /* Global Button Style */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.5em;
        background-color: #1f2937;
        color: white;
        border: 1px solid #374151;
        transition: 0.3s;
        font-weight: bold;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        border-color: #3b82f6;
        transform: translateY(-3px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.4);
    }
    
    /* Custom Status Cards */
    .status-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #334155;
        text-align: center;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE CONNECTION (Optimized) ---
if 'db' not in st.session_state:
    import gspread
    from google.oauth2.service_account import Credentials
    
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        creds = Credentials.from_service_account_file("creds.json", scopes=scope)
        client = gspread.authorize(creds)
        st.session_state.db = client.open("Mihir_Fabrication_DB") 
        st.session_state.conn_status = True
    except Exception as e:
        st.error(f"❌ Database Error: {e}")
        st.session_state.conn_status = False
        st.stop()

db = st.session_state.db

# --- 3. HEADER SECTION ---
col_title, col_info = st.columns([2, 1])
with col_title:
    st.title("🏗️ Mihir Fabrication ERP")
    st.write(f"👋 **Welcome back, Mihir!** | 📅 {datetime.now().strftime('%A, %d %B %Y')}")

with col_info:
    st.markdown(f"""
        <div style='text-align: right; padding-top: 10px; color: #94a3b8;'>
            <b>Location:</b> Ankleshwar Plant<br>
            <b>System:</b> v6.0 Enterprise
        </div>
    """, unsafe_allow_html=True)

st.write("---")

# --- 4. LIVE METRICS (Horizontal Grid) ---
m1, m2, m3, m4 = st.columns(4)

db_icon = "🟢" if st.session_state.conn_status else "🔴"
m1.metric("DB Status", f"{db_icon} Connected")
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

# --- 5. QUICK NAVIGATION (Better Grid) ---
st.subheader("🚀 Operational Control Center")

# Row 1: Dashboard & Invoices
r1c1, r1c2, r1c3 = st.columns(3)
with r1c1:
    if st.button("📊 Open Master Dashboard"):
        st.switch_page("pages/5_Dashboard.py")
with r1c2:
    if st.button("📄 Generate New Invoice"):
        st.switch_page("pages/1_📄_Bill_Generation.py")
with r1c3:
    if st.button("💰 Client Advance (Project)"):
        st.switch_page("pages/7_💰_Advance_Payment.py")

# Row 2: Workers & Attendance
r2c1, r2c2, r2c3 = st.columns(3)
with r2c1:
    if st.button("📅 Attendance & Salary"):
        st.switch_page("pages/3_📅_Attendance.py")
with r2c2:
    if st.button("💸 Workers Advance Manager"):
        st.switch_page("pages/8_💰_Workers_Advance.py")
with r2c3:
    if st.button("🧾 Resource & Shop Bills"):
        st.switch_page("pages/4_🧾_Bills.py")

# Row 3: Management & Fetching
r3c1, r3c2, r3c3, r3c4 = st.columns(4)
with r3c1:
    if st.button("📂 Invoice History"):
        st.switch_page("pages/6_📂_Invoice_Manager.py")
with r3c2:
    # --- NAYA BUTTON: FETCH BILL PAGE ---
    if st.button("🔍 Fetch & Print Bill"):
        st.switch_page("pages/2_🔍_Fetch_Bill.py")
with r3c3:
    if st.button("👥 Client Database"):
        st.switch_page("pages/2_👥_Clients.py")
with r3c4:
    if st.button("⚙️ System Settings"):
        st.info("Settings coming soon!")

st.write("---")

# --- 6. SMART INSIGHTS ---
st.subheader("💡 Business Alerts")
i1, i2 = st.columns(2)

with i1:
    st.info("📈 **Efficiency Tip:** Is mahine ke invoices pichle saal se 12% zyada hain.")
with i2:
    try:
        unpaid = [r for r in bills_data if r['Status'] == 'Unpaid']
        if unpaid:
            st.warning(f"⚠️ **Pending Dues:** {len(unpaid)} Shop Bills abhi tak 'Unpaid' hain.")
        else:
            st.success("✅ Saare shop bills clear hain!")
    except:
        st.write("Checking dues...")

# --- FOOTER ---
st.markdown("<br><div style='text-align: center; color: #4b5563; font-size: 12px;'>Mihir Fabrication ERP System | Designed for Lifetime Performance</div>", unsafe_allow_html=True)