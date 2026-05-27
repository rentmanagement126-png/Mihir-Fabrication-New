import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- 1. SETTINGS & DATABASE ---
st.set_page_config(layout="wide", page_title="Bills Management")

if 'db' not in st.session_state or st.session_state.db is None:
    st.error("Pehle Main Page par jaakar Database connect karein.")
    st.stop()

db = st.session_state.db
b_sheet = db.worksheet("Bills")
try:
    set_sheet = db.worksheet("Settings")
except:
    st.error("Sheet mein 'Settings' tab banayein aur A1 mein 'Keywords' likhein.")
    st.stop()

st.title("🧾 Resource & Bill Management")

tab1, tab2, tab3 = st.tabs(["➕ Add New Bill", "📂 View & Edit Bills", "⚙️ Manage Keywords"])

# --- TAB 1: ADD NEW BILL ---
with tab1:
    kw_data = set_sheet.get_all_records()
    kw_list = [row['Keywords'] for row in kw_data] if kw_data else ["Gas Bottle"]
    
    with st.form("new_bill_form_final", clear_on_submit=True):
        st.subheader("New Entry")
        c1, c2 = st.columns(2)
        with c1:
            b_date = st.date_input("Bill Date", datetime.now())
            b_no = st.text_input("Bill Number *")
            s_name = st.text_input("Shop Name *")
        with c2:
            res_type = st.selectbox("Resource Type", kw_list)
            amount = st.number_input("Amount (₹) *", min_value=0.0)
            status = st.selectbox("Status", ["Unpaid", "Paid"])
            # Status ke basis par mode disable karne ka logic (Form level)
            mode = st.selectbox("Mode", ["-", "Cash", "Online", "Cheque", "Credit"])
            
        if st.form_submit_button("💾 Save Bill"):
            if b_no and s_name and amount > 0:
                final_mode = "-" if status == "Unpaid" else mode
                b_sheet.append_row([str(b_date), b_no, s_name, res_type, amount, status, final_mode])
                st.success("Bill Saved!")
                if 'bills_cache' in st.session_state: del st.session_state.bills_cache
                time.sleep(1)
                st.rerun()

# --- TAB 2: VIEW & EDIT (Fixed Filters & Totals) ---
# --- TAB 2: VIEW & EDIT BILLS (Master Filters Version) ---
with tab2:
    st.subheader("🔍 Advanced Search & Filters")
    
    if st.button("🔄 Refresh Data List", use_container_width=True):
        with st.spinner("Fetching data..."):
            st.session_state.bills_cache = pd.DataFrame(b_sheet.get_all_records())

    if 'bills_cache' in st.session_state:
        df = st.session_state.bills_cache
        # Date column ko datetime format mein convert karna
        df['Bill Date'] = pd.to_datetime(df['Bill Date'], errors='coerce')
        
        # --- FILTERS SECTION ---
        row1_col1, row1_col2, row1_col3 = st.columns(3)
        
        # 1. Year Filter
        # --- 1. Year Filter (Lifetime Fix) ---
        current_year = datetime.now().year
        years_list = ["All"] + sorted(list(range(current_year - 2, current_year + 11)), reverse=True)
        
        sel_year = row1_col1.selectbox("Saal (Year)", years_list)
        
        # 2. Status Filter
        status_f = row1_col2.selectbox("Status", ["All", "Paid", "Unpaid"])
        
        # 3. Shop Dropdown Filter
        all_shops = sorted(df['Shop Name'].astype(str).unique().tolist())
        shop_f = row1_col3.selectbox("Company/Shop Name", ["All"] + all_shops)

        # 4. Date Range Filter (Date-wise)
        st.write("📅 **Specific Date Range chunein:**")
        min_date = df['Bill Date'].min().date() if not df['Bill Date'].empty else datetime.now().date()
        max_date = df['Bill Date'].max().date() if not df['Bill Date'].empty else datetime.now().date()
        
        date_range = st.date_input("Select Date Range", [min_date, max_date])

        # --- FILTER LOGIC ---
        df_display = df.copy()
        df_display['Status'] = df_display['Status'].astype(str).str.strip()

        # Year Filter Apply
        if sel_year != "All":
            df_display = df_display[df_display['Bill Date'].dt.year == int(sel_year)]
        
        # Status Filter Apply
        if status_f == "Paid":
            df_display = df_display[df_display['Status'] == "Paid"]
        elif status_f == "Unpaid":
            df_display = df_display[df_display['Status'].str.contains("Unpaid", case=False, na=False)]

        # Shop Filter Apply
        if shop_f != "All":
            df_display = df_display[df_display['Shop Name'] == shop_f]

        # Date Range Filter Apply
        if len(date_range) == 2:
            start_date, end_date = date_range
            df_display = df_display[(df_display['Bill Date'].dt.date >= start_date) & 
                                    (df_display['Bill Date'].dt.date <= end_date)]

        # --- DYNAMIC TOTALS ---
        st.write("---")
        total_val = df_display['Amount'].sum()
        m1, m2 = st.columns(2)
        m1.metric(f"Filtered Total Amount", f"₹{total_val:,.2f}")
        m2.metric("Bills Count", f"{len(df_display)} Bills")
        st.write("---")

        # Table Display (Date format sundar dikhane ke liye)
        df_final = df_display.copy()
        df_final['Bill Date'] = df_final['Bill Date'].dt.strftime('%d-%m-%Y')
        st.dataframe(df_final, use_container_width=True)
        
        # --- ADVANCED EDIT SECTION ---
        st.subheader("📝 Update Payment Details")
        with st.form("advanced_edit_final_v11"):
            col_e1, col_e2, col_e3 = st.columns(3)
            bill_ids = df_display['Bill No'].astype(str).tolist()
            sel_bill = col_e1.selectbox("Select Bill No", ["--"] + bill_ids)
            upd_status = col_e2.selectbox("Change Status", ["Paid", "Unpaid"])
            
            if upd_status == "Paid":
                upd_mode = col_e3.selectbox("Change Mode", ["Cash", "Online", "Cheque", "Credit"])
            else:
                upd_mode = "-"
                col_e3.write("⌛ Pending...")

            if st.form_submit_button("✅ Update Now"):
                if sel_bill != "--":
                    try:
                        mask = df['Bill No'].astype(str) == str(sel_bill)
                        row_idx = df[mask].index[0] + 2
                        b_sheet.update_cell(int(row_idx), 6, upd_status)
                        b_sheet.update_cell(int(row_idx), 7, upd_mode)
                        st.success(f"Bill {sel_bill} updated!")
                        if 'bills_cache' in st.session_state: del st.session_state.bills_cache
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
# --- TAB 3: KEYWORDS ---
with tab3:
    st.subheader("⚙️ Manage Keywords")
    new_kw = st.text_input("Naya Resource Name (e.g. Grinding Wheel)")
    if st.button("➕ Add to Database"):
        if new_kw:
            set_sheet.append_row([new_kw])
            st.success("Successfully Added!")
            time.sleep(1)
            st.rerun()