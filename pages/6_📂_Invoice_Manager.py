import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- 1. SETTINGS ---
st.set_page_config(layout="wide", page_title="Mihir Fabrication - Invoice Manager")

if 'db' not in st.session_state or st.session_state.db is None:
    st.error("Pehle Main Page par jaakar Database connect karein.")
    st.stop()

db = st.session_state.db
i_sheet = db.worksheet("Invoices")

st.title("📂 Advanced Invoice & Payment Manager")

# --- 2. DATA REFRESH FUNCTION ---
def refresh_data():
    data = i_sheet.get_all_records()
    st.session_state.inv_manager_cache = pd.DataFrame(data)

if st.button("🔄 Refresh Data List", use_container_width=True):
    refresh_data()
    st.rerun()

if 'inv_manager_cache' not in st.session_state:
    refresh_data()

df = st.session_state.inv_manager_cache

if not df.empty:
    df = df.loc[:, ~df.columns.duplicated()]

    # --- 3. FILTERS ---
    st.subheader("🔍 Search Invoices")
    c1, c2, c3 = st.columns(3)
    status_f = c1.selectbox("Filter by Status", ["All", "Paid", "Partially Paid", "Unpaid"])
    client_f = c2.selectbox("Filter by Client", ["All"] + sorted(df['Client Name'].unique().tolist()))
    search_f = c3.text_input("Search Bill No")

    df_display = df.copy()
    if status_f != "All": df_display = df_display[df_display['Status'] == status_f]
    if client_f != "All": df_display = df_display[df_display['Client Name'] == client_f]
    if search_f: df_display = df_display[df_display['Bill No'].astype(str).str.contains(search_f)]

    st.dataframe(df_display, use_container_width=True)

    # --- 4. PAYMENT LOGIC (ADD OR EDIT) ---
    st.write("---")
    st.subheader("💰 Collection Manager")
    
    # Bill Selection
    sel_bill = st.selectbox("Select Bill No to Manage", ["None"] + df_display['Bill No'].tolist())
    
    if sel_bill != "None":
        cell = i_sheet.find(str(sel_bill))
        row_values = i_sheet.row_values(cell.row)
        
        try:
            already_received = float(row_values[12]) if len(row_values) >= 13 and row_values[12] != "" else 0.0
        except:
            already_received = 0.0
            
        total_bill = float(df[df['Bill No'] == sel_bill]['Total'].iloc[0])

        st.info(f"📊 **Current Status for Bill {sel_bill}:** Total Received: ₹{already_received:,.2f} | Total Bill: ₹{total_bill:,.2f}")

        # --- TWO MODES: ADD OR OVERWRITE ---
        tab1, tab2 = st.tabs(["➕ Add New Collection", "✏️ Edit/Correct Total Received"])

        with tab1:
            u2, u3, u4 = st.columns([1.5, 1.5, 1])
            pay_now = u2.number_input("Aaj kitna mila?", min_value=0.0, step=100.0, key="add_mode")
            pay_method = u3.selectbox("Method", ["Cash", "Online", "Cheque", "-"], key="add_meth")
            
            if u4.button("✅ Update Balance", use_container_width=True):
                if pay_now > 0:
                    new_received = already_received + pay_now
                    update_val = True
                else:
                    st.warning("Amount enter karein.")
                    update_val = False

        with tab2:
            st.warning("⚠️ Is option se purana balance delete hokar naya set ho jayega. (Mistake theek karne ke liye)")
            e2, e3, e4 = st.columns([1.5, 1.5, 1])
            correct_total = e2.number_input("Sahi Total Received amount kya hai?", min_value=0.0, value=already_received, step=100.0, key="edit_mode_val")
            edit_method = e3.selectbox("Method", ["Cash", "Online", "Cheque", "-"], key="edit_meth")
            
            if e4.button("🛠️ Fix Total", use_container_width=True):
                new_received = correct_total
                pay_method = edit_method
                update_val = True
                st.info(f"Correcting value to {new_received}...")

        # COMMON UPDATE LOGIC
        if 'update_val' in locals() and update_val:
            new_balance = total_bill - new_received
            
            # Status Logic
            if new_received >= total_bill: stat = "Paid"
            elif new_received > 0: stat = "Partially Paid"
            else: stat = "Unpaid"

            # Update Google Sheets (K=11, L=12, M=13, N=14)
            i_sheet.update_cell(cell.row, 11, stat)
            i_sheet.update_cell(cell.row, 12, pay_method)
            i_sheet.update_cell(cell.row, 13, new_received)
            i_sheet.update_cell(cell.row, 14, new_balance)
            
            st.success(f"Success! Bill No {sel_bill} updated. New Total Received: ₹{new_received}")
            refresh_data()
            time.sleep(1)
            st.rerun()

else:
    st.info("No data found.")