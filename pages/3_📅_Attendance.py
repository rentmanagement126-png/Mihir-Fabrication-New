import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
import time

# --- 1. SETTINGS & DATABASE ---
st.set_page_config(layout="wide", page_title="Mihir Fabrication System")

if 'db' not in st.session_state or st.session_state.db is None:
    st.error("Pehle Main Page par jaakar Database connect karein.")
    st.stop()

db = st.session_state.db
w_sheet = db.worksheet("Workers")
a_sheet = db.worksheet("Attendance")
s_sheet = db.worksheet("Salaries")

st.title("📅 Attendance & Salary System v5.2 (Bulk Entry Enabled)")

# --- 2. GLOBAL CACHE LOGIC (Quota Protection) ---
def get_data_from_google():
    try:
        workers = pd.DataFrame(w_sheet.get_all_records())
        attendance = pd.DataFrame(a_sheet.get_all_records())
        return workers, attendance
    except Exception as e:
        st.error(f"Google API Busy: 30 seconds wait karein.")
        return None, None

def is_worker_active_in_month(row, sel_month, sel_year):
    if row['Status'] == 'Active': return True
    if row['Status'] == 'Inactive' and row.get('Exit Date'):
        try:
            exit_dt = pd.to_datetime(row['Exit Date'])
            if (sel_year < exit_dt.year) or (sel_year == exit_dt.year and sel_month <= exit_dt.month):
                return True
        except: return False
    return False

# --- 3. TABS DEFINITION ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "👤 Add Worker", "📝 Daily Attendance", "📊 Salary & Print", "📅 Attendance Sheet", "⚙️ Manage Workers"
])

# --- TAB 1: ADD NEW WORKER ---
with tab1:
    with st.expander("➕ Register New Worker", expanded=True):
        with st.form("w_form_v5", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Full Name *")
                phone = st.text_input("Phone Number")
                role = st.selectbox("Role", ["Welder", "Fitter", "Helper", "Grinder", "Supervisor"])
                rate = st.number_input("Day Rate (8 Hrs) *", min_value=0)
                join_d = st.date_input("Joining Date", datetime.now())
            with c2:
                aadhaar = st.text_input("Aadhaar Number")
                bank = st.text_input("Bank Name")
                acc = st.text_input("Account Number")
                ifsc = st.text_input("IFSC Code")
            if st.form_submit_button("Save Worker"):
                if name and rate > 0:
                    w_sheet.append_row([len(w_sheet.get_all_records())+1, name, phone, role, rate, "Auto", bank, acc, ifsc, aadhaar, "Active", str(join_d), ""])
                    st.success(f"{name} Successfully Registered!")
                    time.sleep(1)
                    st.rerun()

# --- TAB 2: DAILY & BULK ATTENDANCE ---
# --- TAB 2: DAILY & BULK ATTENDANCE (Updated for Total OT) ---
with tab2:
    if 'daily_att_cache' not in st.session_state:
        st.session_state.daily_att_cache = pd.DataFrame()
    if 'active_w_list' not in st.session_state:
        st.session_state.active_w_list = pd.DataFrame()

    # --- UPDATED OPTION: BULK ENTRY (With Single Total OT Value) ---
    with st.expander("📝 Bulk Attendance Entry (Manual Card)"):
        st.info("💡 Worker select karein. OT Hours sirf aakhri selected date par add honge taaki total sahi rahe.")
        
        df_w_bulk, _ = get_data_from_google()
        if df_w_bulk is not None:
            w_names = df_w_bulk['Name'].tolist()
            sel_worker = st.selectbox("Select Worker", w_names, key="bulk_w")
            
            c_b1, c_b2 = st.columns(2)
            start_d = c_b1.date_input("Start Date", date.today() - timedelta(days=30))
            end_d = c_b2.date_input("End Date", date.today())
            
            c_b3, c_b4 = st.columns(2)
            bulk_status = c_b3.selectbox("Status for all days", ["Present", "Absent", "Half Day"])
            # Naya: Single value for Total OT
            total_ot_to_add = c_b4.number_input("Total OT Hours (Month Total)", min_value=0.0, step=0.5)
            
            if st.button("🚀 Apply Bulk Entry", use_container_width=True):
                w_id = df_w_bulk[df_w_bulk['Name'] == sel_worker]['Worker ID'].values[0]
                current_d = start_d
                bulk_updates = []
                
                while current_d <= end_d:
                    # Logic: Sirf aakhri selected date (End Date) par Total OT Hours daalna
                    # Baaki saari dates par OT 0.0 rahega taaki duplication na ho
                    if current_d == end_d:
                        ot_value = total_ot_to_add
                    else:
                        ot_value = 0.0
                        
                    bulk_updates.append([current_d.strftime("%Y-%m-%d"), int(w_id), bulk_status, ot_value])
                    current_d += timedelta(days=1)
                
                # Update logic (Avoid duplicates)
                all_v = a_sheet.get_all_values()
                header = all_v[0]
                existing_data = all_v[1:]
                
                dates_to_update = [b[0] for b in bulk_updates]
                cleaned_data = [r for r in existing_data if not (r[0] in dates_to_update and int(r[1]) == int(w_id))]
                
                final_v = [header] + cleaned_data + bulk_updates
                a_sheet.update('A1', final_v)
                st.success(f"Success! {sel_worker} ki attendance mark ho gayi aur Total OT ({total_ot_to_add}) add ho gaya.")
                time.sleep(1)
                st.rerun()

    st.write("---")
    # ... (Baaki Daily Attendance ka code same rahega)
    st.subheader("📝 Daily Attendance Entry")
    sel_date_dt = st.date_input("Select Date", datetime.now(), key="att_date")
    sel_date_str = sel_date_dt.strftime("%Y-%m-%d")

    if st.button("🔄 Load Worker List", use_container_width=True):
        df_w, df_a = get_data_from_google()
        if df_w is not None:
            st.session_state.active_w_list = df_w[df_w.apply(lambda r: is_worker_active_in_month(r, sel_date_dt.month, sel_date_dt.year), axis=1)]
            st.session_state.daily_att_cache = df_a[df_a['Date'] == sel_date_str] if not df_a.empty else pd.DataFrame()
            st.rerun()

    if not st.session_state.active_w_list.empty:
        updates = []
        st.write("---")
        h1, h2, h3, h4 = st.columns([0.5, 3, 1, 1])
        h2.write("**Worker Name**")
        h3.write("**Status**")
        h4.write("**OT Hrs**")

        for _, row in st.session_state.active_w_list.iterrows():
            wid, wname = row['Worker ID'], row['Name']
            prev = st.session_state.daily_att_cache[st.session_state.daily_att_cache['Worker ID'] == wid] if not st.session_state.daily_att_cache.empty else pd.DataFrame()
            
            c1, c2, c3, c4 = st.columns([0.5, 3, 1, 1])
            is_p = c1.checkbox("", value=(not prev.empty and prev['Status'].values[0] != "Absent"), key=f"t_{wid}")
            c2.write(f"**{wname}**")
            
            if is_p:
                s_val = prev['Status'].values[0] if not prev.empty else "Present"
                s = c3.selectbox("S", ["Present", "Half Day"], key=f"s_{wid}", label_visibility="collapsed", index=0 if s_val == "Present" else 1)
                o_val = prev['OT_Hours'].values[0] if not prev.empty else 0.0
                o = c4.number_input("OT", min_value=0.0, step=0.5, value=float(o_val), key=f"o_{wid}", label_visibility="collapsed")
                updates.append([sel_date_str, wid, s, o])
            else:
                updates.append([sel_date_str, wid, "Absent", 0.0])

        if st.button("💾 Save Attendance", use_container_width=True):
            all_v = a_sheet.get_all_values()
            new_rows = [all_v[0]] + [r for r in all_v[1:] if r[0] != sel_date_str] + updates
            a_sheet.update('A1', new_rows)
            st.success("Attendance Saved!")
            del st.session_state.daily_att_cache
            time.sleep(1)
            st.rerun()

# --- TAB 3: SALARY REPORT ---
with tab3:
    st.subheader("📊 Monthly Salary Calculation & Print Center")
    c1, c2 = st.columns(2)
    
    current_year = datetime.now().year
    years_list = list(range(current_year - 2, current_year + 11))
    
    s_y = c1.selectbox("Select Year", years_list, index=2, key="sal_y")
    s_m = c2.selectbox("Select Month", list(calendar.month_name)[1:], index=datetime.now().month-1, key="sal_m")
    m_idx = list(calendar.month_name).index(s_m)

    if st.button("🚀 Generate Salary Report", use_container_width=True):
        df_w, df_a = get_data_from_google()
        
        try:
            df_adv_all = pd.DataFrame(db.worksheet("Workers_Advance").get_all_records())
        except:
            st.error("Sheet 'Workers_Advance' nahi mili! Please check karein.")
            st.stop()

        if df_w is not None and df_a is not None:
            df_a['Date'] = pd.to_datetime(df_a['Date'], errors='coerce')
            mon_att = df_a[(df_a['Date'].dt.month == m_idx) & (df_a['Date'].dt.year == s_y)]
            rel_w = df_w[df_w.apply(lambda r: is_worker_active_in_month(r, m_idx, s_y), axis=1)]
            
            sal_list = []
            for _, w in rel_w.iterrows():
                w_id = str(w['Worker ID']).strip()
                w_a = mon_att[mon_att['Worker ID'] == int(w_id)]
                
                total_adv = 0.0
                if not df_adv_all.empty:
                    df_adv_all['Date'] = pd.to_datetime(df_adv_all['Date'], errors='coerce')
                    temp_adv = df_adv_all[
                        (df_adv_all['Worker ID'].astype(str).str.strip() == w_id) & 
                        (df_adv_all['Date'].dt.month == m_idx) & 
                        (df_adv_all['Date'].dt.year == s_y)
                    ]
                    total_adv = pd.to_numeric(temp_adv['Amount'], errors='coerce').sum()

                days = len(w_a[w_a['Status']=='Present']) + (len(w_a[w_a['Status']=='Half Day'])*0.5)
                ot = pd.to_numeric(w_a['OT_Hours'], errors='coerce').sum()
                day_rate = float(w['Per Day Rate'])
                gross = (days * day_rate) + (ot * (day_rate/8))
                
                sal_list.append({
                    "Worker ID": w_id, 
                    "Name": w['Name'], 
                    "Days": days, 
                    "OT": ot, 
                    "Gross": round(gross, 2), 
                    "Total Advance": round(total_adv, 2), 
                    "Net Payable": round(gross - total_adv, 2), 
                    "Method": "Cash",
                    "Status": "Unpaid"
                })
            
            st.session_state.sal_df_cache = pd.DataFrame(sal_list)

    if 'sal_df_cache' in st.session_state:
        final_df = st.data_editor(
            st.session_state.sal_df_cache, 
            use_container_width=True, 
            key="sal_editor_final_v10",
            column_config={
                "Method": st.column_config.SelectboxColumn(
                    "Method",
                    options=["Cash", "Bank Transfer", "UPI", "Cheque"],
                    required=True,
                ),
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["Paid", "Unpaid", "Pending"],
                    required=True,
                ),
                "Worker ID": st.column_config.Column(disabled=True),
                "Name": st.column_config.Column(disabled=True),
                "Gross": st.column_config.Column(disabled=True),
            }
        )
        
        final_df["Net Payable"] = final_df["Gross"] - final_df["Total Advance"]
        st.session_state.sal_df_cache = final_df

        if st.button("💾 Save Salary Database", use_container_width=True):
            m_y = f"{s_m}-{s_y}"
            all_s = s_sheet.get_all_values()
            rows_to_save = final_df.drop(columns=["Name"]).values.tolist()
            final_rows = [[m_y] + r for r in rows_to_save]
            
            updated_sheet = [all_s[0]] + [r for r in all_s[1:] if r[0] != m_y] + final_rows
            s_sheet.update('A1', updated_sheet)
            st.success(f"✅ {m_y} data saved successfully!")

        st.write("---")
        if st.checkbox("🔍 Preview A4 Salary Sheet"):
            rows_html = "".join([
                f"<tr><td>{r['Name']}</td><td>{r['Days']}</td><td>{r['OT']}</td><td>₹{r['Gross']:,}</td>"
                f"<td style='color:red;'>-₹{r['Total Advance']:,}</td><td style='font-weight:bold;'>₹{r['Net Payable']:,}</td>"
                f"<td>{r['Method']}</td><td style='width:100px;'></td></tr>" 
                for _, r in final_df.iterrows()
            ])
            
            salary_html = f"""
            <div id='print-area' style='width:210mm; min-height:280mm; background:white; color:black; font-family:Arial; padding:15mm; margin:auto; border:1px solid #ddd;'>
                <style>
                    @media print {{ @page {{ size: A4 portrait; margin: 10mm; }} .no-print {{ display: none !important; }} }}
                    table{{width:100%; border-collapse:collapse; margin-top:20px;}}
                    th,td{{border:1px solid black; padding:8px; font-size:12px; text-align:center;}}
                    th{{background:#f2f2f2;}}
                </style>
                <div style='text-align:center;'>
                    <h2 style='margin:0;'>MIHIR FABRICATION</h2>
                    <p style='margin:5px;'>Ankleshwar, Gujarat</p>
                    <hr>
                    <h4>SALARY REPORT: {s_m} {s_y}</h4>
                </div>
                <table>
                    <thead>
                        <tr><th>Worker Name</th><th>Days</th><th>OT</th><th>Gross</th><th>Adv.</th><th>Net Pay</th><th>Mode</th><th>Signature</th></tr>
                    </thead>
                    <tbody>{rows_html}</tbody>
                </table>
                <div style='margin-top:50px; display:flex; justify-content:space-between; padding:0 30px;'>
                    <div><br>_________________<br>Prepared By</div>
                    <div><br>_________________<br>Manager Sign</div>
                    <div><br>_________________<br>Authorized Sign</div>
                </div>
                <div class='no-print' style='text-align:center; margin-top:30px;'>
                    <button onclick='window.print()' style='width:100%; padding:12px; background:#0d47a1; color:white; border:none; border-radius:5px; cursor:pointer; font-weight:bold;'>🖨️ PRINT NOW</button>
                </div>
            </div>"""
            st.components.v1.html(salary_html, height=900, scrolling=True)

# --- TAB 4: ATTENDANCE SHEET ---
with tab4:
    st.subheader("📅 Monthly Matrix Grid")
    c1, c2 = st.columns(2)
    current_year = datetime.now().year
    years_list = list(range(current_year - 2, current_year + 11))
    
    v_y = c1.selectbox("Year", years_list, index=2, key="vy_matrix")
    v_m = c2.selectbox("Month", list(calendar.month_name)[1:], index=datetime.now().month-1, key="vm_matrix")
    m_idx = list(calendar.month_name).index(v_m)
    num_days = calendar.monthrange(v_y, m_idx)[1]

    if st.button("🔍 Generate Matrix Grid", use_container_width=True):
        df_w, df_a = get_data_from_google()
        if df_w is not None:
            df_a['Date'] = pd.to_datetime(df_a['Date'])
            mon_data = df_a[(df_a['Date'].dt.month == m_idx) & (df_a['Date'].dt.year == v_y)]
            visible_ids = df_w[df_w.apply(lambda r: is_worker_active_in_month(r, m_idx, v_y), axis=1)]['Worker ID'].tolist()
            if not mon_data.empty:
                mon_data = mon_data[mon_data['Worker ID'].isin(visible_ids)].merge(df_w[['Worker ID', 'Name']], on='Worker ID')
                mon_data['Day'] = mon_data['Date'].dt.day
                mon_data['Disp'] = mon_data.apply(lambda r: f"{'P' if r['Status']=='Present' else 'H' if r['Status']=='Half Day' else 'A'}{'('+str(r['OT_Hours'])+')' if r['OT_Hours']>0 else ''}", axis=1)
                grid = mon_data.pivot(index='Name', columns='Day', values='Disp')
                now = datetime.now()
                for d in range(1, num_days + 1):
                    if d not in grid.columns:
                        if (v_y > now.year) or (v_y == now.year and m_idx > now.month) or (v_y == now.year and m_idx == now.month and d > now.day):
                            grid[d] = ""
                        else: grid[d] = "A"
                st.session_state.matrix_cache = grid[sorted(grid.columns)].fillna("")

    if 'matrix_cache' in st.session_state:
        st.dataframe(st.session_state.matrix_cache, use_container_width=True)
        if st.checkbox("🔍 Preview Landscape Sheet"):
            g = st.session_state.matrix_cache
            thr = "".join([f"<th style='font-size:9px;'>{d}</th>" for d in g.columns])
            trows = "".join([f"<tr><td style='font-weight:bold; font-size:10px;'>{n}</td>" + "".join([f"<td style='font-size:9px;'>{r[d]}</td>" for d in g.columns]) + "</tr>" for n, r in g.iterrows()])
            
            matrix_html = f"""
            <div style='width:280mm; background:white; color:black; font-family:Arial; padding:5mm; margin:auto;'>
                <style> @media print {{ @page {{ size: A4 landscape; margin: 5mm; }} .no-print {{ display: none !important; }} }} table{{width:100%; border-collapse:collapse; table-layout:fixed;}} th,td{{border:1px solid black; text-align:center; padding:2px; font-size:9px;}} </style>
                <div style='text-align:center;'><h3>MIHIR FABRICATION - {v_m} {v_y}</h3></div>
                <table><thead><tr style='background:#eee;'><th style='width:120px;'>Worker Name</th>{thr}</tr></thead><tbody>{trows}</tbody></table>
                <div class='no-print' style='margin-top:20px;'><button onclick='window.print()' style='width:100%; padding:10px; background:green; color:white; border:none; cursor:pointer;'>PRINT LANDSCAPE SHEET</button></div>
            </div>"""
            st.components.v1.html(matrix_html, height=600, scrolling=True)

# --- TAB 5: MANAGE WORKERS ---
with tab5:
    st.subheader("⚙️ Manage & Edit Workers")
    if st.button("🔄 Refresh Worker List", use_container_width=True, key="ref_w"):
        df_w_raw, _ = get_data_from_google()
        if df_w_raw is not None:
            st.session_state.manage_cache = df_w_raw

    if 'manage_cache' in st.session_state:
        df_manage = st.session_state.manage_cache
        with st.expander("📝 Edit Worker Details", expanded=True):
            sel_worker_name = st.selectbox("Select Worker to Update", ["-- Select Worker --"] + df_manage['Name'].tolist())
            if sel_worker_name != "-- Select Worker --":
                worker_row = df_manage[df_manage['Name'] == sel_worker_name].iloc[0]
                sheet_idx = df_manage[df_manage['Name'] == sel_worker_name].index[0] + 2
                with st.form("edit_worker_form"):
                    c1, c2 = st.columns(2)
                    with c1:
                        new_name = st.text_input("Name", value=worker_row['Name'])
                        new_status = st.selectbox("Status", ["Active", "Inactive"], index=0 if worker_row['Status'] == "Active" else 1)
                        new_rate = st.number_input("Day Rate", value=float(worker_row['Per Day Rate']))
                        new_join_date = st.date_input("Joining Date", value=pd.to_datetime(worker_row['Joining Date']).date() if worker_row['Joining Date'] else datetime.now().date())
                    with c2:
                        new_bank = st.text_input("Bank Name", value=worker_row['Bank Name'])
                        new_acc = st.text_input("A/C No", value=worker_row['A/C No'])
                        new_exit = st.date_input("Exit Date", value=pd.to_datetime(worker_row['Exit Date']).date() if worker_row['Exit Date'] else datetime.now().date())
                    
                    if st.form_submit_button("✅ Update Worker"):
                        updated_row = [int(worker_row['Worker ID']), new_name, worker_row['Phone'], worker_row['Role'], new_rate, "Auto", new_bank, new_acc, worker_row['IFSC'], worker_row['Aadhaar'], new_status, str(new_join_date), str(new_exit) if new_status == "Inactive" else ""]
                        w_sheet.update(f'A{sheet_idx}:M{sheet_idx}', [updated_row])
                        st.success(f"{new_name} updated!")
                        del st.session_state.manage_cache
                        time.sleep(1)
                        st.rerun()