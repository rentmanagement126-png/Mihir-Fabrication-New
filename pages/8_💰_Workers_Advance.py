import streamlit as st
import pandas as pd
from datetime import datetime
import time

st.set_page_config(layout="wide", page_title="Mihir Fabrication - Workers Advance")

if 'db' not in st.session_state:
    st.error("Pehle Main Page par jaakar Database connect karein.")
    st.stop()

db = st.session_state.db
w_sheet = db.worksheet("Workers")
adv_sheet = db.worksheet("Workers_Advance") # Google Sheet mein ye naam ki sheet honi chahiye

st.title("💰 Workers Advance Manager")

# 1. Advance Entry Form
with st.form("worker_adv_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    # Active Workers ki list nikalna
    df_w = pd.DataFrame(w_sheet.get_all_records())
    active_w = df_w[df_w['Status'] == 'Active']
    w_list = active_w.apply(lambda x: f"{x['Worker ID']} - {x['Name']}", axis=1).tolist()
    
    selected_w = col1.selectbox("Worker Select Karein", w_list)
    amount = col2.number_input("Advance Amount (₹)", min_value=0, step=100)
    adv_date = col1.date_input("Date", datetime.now())
    note = col2.text_input("Remarks / Reason")
    
    if st.form_submit_button("💾 Save Advance Entry"):
        if amount > 0:
            wid = selected_w.split(" - ")[0]
            wname = selected_w.split(" - ")[1]
            # Google Sheet mein data bhej rahe hain
            adv_sheet.append_row([adv_date.strftime("%Y-%m-%d"), wid, wname, amount, note])
            st.success(f"Done! ₹{amount} ka advance {wname} ke naam save ho gaya.")
            time.sleep(1)
            st.rerun()

# 2. History Table
st.write("---")
st.subheader("📜 Recent Advance Records")
df_adv = pd.DataFrame(adv_sheet.get_all_records())
if not df_adv.empty:
    st.dataframe(df_adv.sort_values(by='Date', ascending=False), use_container_width=True)