import streamlit as st
import pandas as pd

# --- DATABASE CONNECTION ---
if 'db' not in st.session_state or st.session_state.db is None:
    st.error("Pehle Main Page par jaakar Database connect karein.")
    st.stop()

db = st.session_state.db
st.title("👥 Client Management")

# Safe Sheet Connection
try:
    c_sheet = db.worksheet("Clients")
    raw_data = c_sheet.get_all_values()
    
    if len(raw_data) > 0:
        # Headers: Company Name, Address, GSTIN
        clients_df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
    else:
        clients_df = pd.DataFrame(columns=["Company Name", "Address", "GSTIN"])
except Exception as e:
    st.info("Clients sheet initialize ho rahi hai...")
    c_sheet = db.add_worksheet(title="Clients", rows="100", cols="5")
    c_sheet.append_row(["Company Name", "Address", "GSTIN"])
    clients_df = pd.DataFrame(columns=["Company Name", "Address", "GSTIN"])

# --- ADD NEW CLIENT ---
with st.expander("➕ Add New Client"):
    with st.form("client_form", clear_on_submit=True):
        c_name = st.text_input("Company Name")
        c_addr = st.text_area("Address")
        c_gst  = st.text_input("GSTIN Number")
        
        if st.form_submit_button("Save Client"):
            if c_name:
                # Sirf 3 details save hongi
                c_sheet.append_row([c_name, c_addr, c_gst])
                st.success(f"{c_name} saved successfully!")
                st.rerun()
            else:
                st.warning("Company name likhna zaroori hai.")

st.write("---")

# --- VIEW & EDIT CLIENTS ---
st.subheader("📋 Client List")
if not clients_df.empty:
    # Editable table without Contact column
    edited_clients = st.data_editor(
        clients_df[["Company Name", "Address", "GSTIN"]], 
        use_container_width=True, 
        num_rows="dynamic"
    )
    
    if st.button("💾 Save All Changes"):
        c_sheet.clear()
        c_sheet.append_row(["Company Name", "Address", "GSTIN"])
        if not edited_clients.empty:
            c_sheet.append_rows(edited_clients.values.tolist())
        st.success("Client list updated!")
else:
    st.info("Abhi koi client add nahi kiya gaya hai.")