import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- 1. SETTINGS & DB ---
st.set_page_config(layout="wide", page_title="Mihir Fabrication - Advance Manager")

if 'db' not in st.session_state or st.session_state.db is None:
    st.error("Pehle Main Page par jaakar Database connect karein.")
    st.stop()

db = st.session_state.db
c_sheet = db.worksheet("Clients")
adv_sheet = db.worksheet("Advances")

st.title("💰 Advance Payment & Bill Linking")

# --- 2. NEW ADVANCE ENTRY FORM ---
with st.expander("➕ Add New Advance Entry", expanded=True):
    col1, col2 = st.columns(2)
    clients_df = pd.DataFrame(c_sheet.get_all_records())
    client_list = sorted(clients_df['Company Name'].tolist()) if 'Company Name' in clients_df.columns else []
    
    selected_client = col1.selectbox("Select Company", client_list)
    adv_date = col1.date_input("Date of Payment", datetime.now())
    adv_amount = col2.number_input("Advance Amount (₹)", min_value=0.0, step=1000.0)
    remarks = col2.text_input("Remarks (Project Name)")

    if st.button("💾 Save Advance", use_container_width=True):
        if selected_client and adv_amount > 0:
            # Column Order: Date, Company Name, Advance Amount, Remarks, Bill No
            new_row = [adv_date.strftime("%d/%m/%Y"), selected_client, adv_amount, remarks, "PENDING"]
            adv_sheet.append_row(new_row)
            st.success("Advance Save Ho Gaya!")
            time.sleep(1)
            st.rerun()

st.write("---")

# --- 3. ADVANCE TABLE WITH BILL LINKING OPTION ---
st.subheader("📜 Advance Records & Bill Assignment")

try:
    all_adv = pd.DataFrame(adv_sheet.get_all_records())
    
    if not all_adv.empty:
        # Display Table
        st.dataframe(all_adv, use_container_width=True)
        
        # --- 4. BILL LINKING SECTION (Baad mein Bill No daalne ke liye) ---
    # --- 4. BILL LINKING SECTION ---
        st.write("---")
        st.subheader("🔗 Link Bill No to Advance")
        
        # Ab ye check karega ki agar Bill No khali hai ya "PENDING" hai, dono chalenge
        pending_adv = all_adv[(all_adv['Bill No'] == "PENDING") | (all_adv['Bill No'] == "") | (all_adv['Bill No'].isna())]
        
        if not pending_adv.empty:
            l1, l2, l3 = st.columns([2, 1, 1])
            
            # Dropdown menu ke liye options
            options = pending_adv.apply(lambda x: f"{x['Company Name']} - ₹{x['Advance Amount']} ({x['Date']})", axis=1).tolist()
            sel_entry = l1.selectbox("Kiska Bill No add karna hai?", options)
            
            bill_to_add = l2.text_input("Enter Bill No (e.g. 101)")
            
            if l3.button("✅ Link Bill Now", use_container_width=True):
                if bill_to_add:
                    # Sahi row dhoondna (+2 header aur 0-index ke liye)
                    row_idx = pending_adv.index[options.index(sel_entry)] + 2
                    
                    # Google Sheet update (Column E = 5)
                    adv_sheet.update_cell(row_idx, 5, bill_to_add)
                    
                    st.success(f"Bill No {bill_to_add} successfully add ho gaya!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("Pehle Bill No toh likhiye!")
        else:
            st.info("Sare Bills link ho chuke hain! ✅")
            
    else:
        st.info("Abhi koi data nahi hai. Pehli entry karein.")
except Exception as e:
    st.warning("Make sure 'Advances' sheet has headers: Date, Company Name, Advance Amount, Remarks, Bill No")