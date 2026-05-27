import streamlit as st
import pandas as pd
from datetime import datetime
from num2words import num2words 

# --- 1. DATABASE CONNECTION ---
if 'db' not in st.session_state or st.session_state.db is None:
    st.error("Pehle Main Page par jaakar Database connect karein.")
    st.stop()

db = st.session_state.db
st.set_page_config(page_title="Mihir Fabrication - Fetch Bills", layout="wide")

i_sheet = db.worksheet("Invoices")
c_sheet = db.worksheet("Clients")

st.title("🔍 Search & View Previous Bills")

# --- 2. SEARCH INTERFACE ---
f_col1, f_col2, f_col3 = st.columns([1, 1, 1])
curr_yr = datetime.now().year
years = sorted(list(range(curr_yr - 2, curr_yr + 5)), reverse=True)
search_year = f_col1.selectbox("Select Bill Year", years, index=years.index(curr_yr) if curr_yr in years else 0)
search_no = f_col2.number_input("Enter Bill No", min_value=1, step=1)

if f_col3.button("🔍 Search Bill", use_container_width=True):
    # Fetch fresh data from sheet
    all_invoices = pd.DataFrame(i_sheet.get_all_records())
    all_invoices['temp_date'] = pd.to_datetime(all_invoices['Date'], dayfirst=True, errors='coerce')
    
    match = all_invoices[(all_invoices['Bill No'].astype(str) == str(search_no)) & (all_invoices['temp_date'].dt.year == search_year)]
    
    if not match.empty:
        row = match.iloc[0]
        # FIX: Parsing Original Bill Date
        original_date_str = str(row['Date']) # "22/03/2026"
        company = row['Client Name']
        
        # Load Client Details
        clients_df = pd.DataFrame(c_sheet.get_all_records())
        c_row = clients_df[clients_df["Company Name"] == company].iloc[0] if not clients_df[clients_df["Company Name"] == company].empty else {"Address": "", "GSTIN": ""}

        # Parse Bill Items
        descs = str(row['Description']).split(" | ")
        hsns = str(row.get('HSN Codes', "9987")).split(" | ")
        qtys = str(row.get('Qty', "-")).split(" | ")
        rates = str(row.get('Rate', "0")).split(" | ")
        amts = str(row.get('Amount', "0")).split(" | ")

        bill_items = []
        for i in range(len(descs)):
            try: v = float(str(amts[i]).replace(',', ''))
            except: v = 0.0
            bill_items.append({
                "SR.No": i + 1, "HSN": hsns[i] if i < len(hsns) else "9987", 
                "DISCRIPTION": descs[i], "QTY": qtys[i] if i < len(qtys) else "-", 
                "RATE": rates[i] if i < len(rates) else "0", "AMOUNT": v
            })

        # Calculations
        sub = sum(item['AMOUNT'] for item in bill_items)
        tax = round(sub * 0.09, 2)
        grand = round(sub + (tax * 2), 2)
        def to_w(n): return "Rupees " + num2words(int(n), lang='en_IN').title() + " Only"

        # --- 3. PRINT PREVIEW (BLACK & WHITE) ---
        limit = 16 
        pages = [bill_items[i:i+limit] for i in range(0, len(bill_items), limit)]
        all_pages_html = ""
        c_sr, c_desc, c_hsn, c_qty, c_rate, c_amt = "6%", "46%", "12%", "10%", "12%", "14%"

        for idx, p_items in enumerate(pages):
            is_last = (idx == len(pages) - 1)
            rows_html = "".join([f"<tr><td style='width:{c_sr}; text-align:center; height:32px; border: 1px solid #000;'>{it['SR.No']}</td><td style='width:{c_desc}; padding:8px; font-size:11.5px; border: 1px solid #000;'>{it['DISCRIPTION']}</td><td style='width:{c_hsn}; text-align:center; border: 1px solid #000;'>{it['HSN']}</td><td style='width:{c_qty}; text-align:center; border: 1px solid #000;'>{it['QTY']}</td><td style='width:{c_rate}; text-align:center; border: 1px solid #000;'>{it['RATE']}</td><td style='width:{c_amt}; text-align:right; border: 1px solid #000;'>{float(it['AMOUNT']):,.2f}</td></tr>" for it in p_items])
            filler_rows = limit - len(p_items)
            filler_html = "".join([f"<tr style='height:32px;'><td style='border: 1px solid #000;'></td><td style='border: 1px solid #000;'></td><td style='border: 1px solid #000;'></td><td style='border: 1px solid #000;'></td><td style='border: 1px solid #000;'></td><td style='border: 1px solid #000;'></td></tr>" for _ in range(filler_rows)])
            
            footer_sec = f"""
            <table style="width:100%; border-collapse:collapse; border:1.5px solid #000; border-top:none; table-layout:fixed; margin-top:-1px;">
                <tr>
                    <td rowspan="4" style="width:60%; border:1px solid #000; padding:15px; vertical-align:top;"><strong>In Words:</strong><br><span style="font-size:13px; font-weight:bold;">{to_w(grand)}</span></td>
                    <td style="width:25%; border:1px solid #000; padding:5px; text-align:right; font-size:12.2px;">Total Rs...</td>
                    <td style="width:15%; border:1px solid #000; text-align:right; padding:5px; font-size:12.2px;">₹{sub:,.2f}</td>
                </tr>
                <tr><td style="border:1px solid #000; padding:5px; text-align:right; font-size:12.2px;">CGST 9%...</td><td style="border:1px solid #000; text-align:right; padding:5px; font-size:12.2px;">₹{tax:,.2f}</td></tr>
                <tr><td style="border:1px solid #000; padding:5px; text-align:right; font-size:12.2px;">SGST 9%...</td><td style="border:1px solid #000; text-align:right; padding:5px; font-size:12.2px;">₹{tax:,.2f}</td></tr>
                <tr style="background:#fff; border-top: 1.5px solid #000;"><td style="border:1px solid #000; padding:5px; text-align:right; font-weight:bold; font-size:13px;">GRAND TOTAL Rs</td><td style="border:1px solid #000; text-align:right; padding:5px; font-weight:bold; font-size:13px;">₹{grand:,.2f}</td></tr>
                <tr>
                    <td style="border:1px solid #000; padding:15px; font-size:11.5px; line-height:1.6; vertical-align:top;">
                        <strong>Bank Details:</strong><br>Mihir Fabrication <br> IFSC: RATN0000227<br>AC: 409001864077 | Branch: Ankleshwar
                    </td>
                    <td colspan="2" style="border:1px solid #000; text-align:center; font-size:12px; vertical-align:top; padding:10px;">
                        <div style="height:100px; display:flex; flex-direction:column; justify-content:space-between;">
                            FOR MIHIR FABRICATION<br><br><br><strong>PROPRIETOR</strong>
                        </div>
                    </td>
                </tr>
            </table>""" if is_last else f"<table style='width:100%; border-collapse:collapse; border:1.5px solid #000; border-top:none; margin-top:-1px;'><tr><td style='text-align:center; padding:15px; font-weight:bold; color:#000; font-size:14px; border:1px solid #000;'>CONTINUED ON PAGE {idx+2}...</td></tr></table>"

            all_pages_html += f"""
            <div class="page" style="{'page-break-after: always;' if not is_last else ''}">
                <div style="text-align: right; font-weight: bold; font-size: 11px;">MOB. NO. 8460597856, 9427583687</div>
                <div style="text-align:center; padding-bottom:5px;">
                    <h1 style="color:#000; margin:0; font-size:28px;">MIHIR FABRICATION</h1>
                    <p style="font-size:10px; font-weight:bold; margin:2px 0; color:#000;">ALL KIND OF FABRICATION, UNLOADING, SHIFTING & ERECTION</p>
                    <p style="font-size:9px; margin:0; color:#555;">Jobs: Structural, Pipeline, Tank Chimney, Labour Supply</p>
                    <p style="font-size:9px; margin:0;">01, LAXMAN NAGAR, Sarangpore, Ankleshwar, Bharuch, Gujarat |<b> GSTIN: 24AHYPB0673P1ZS</b></p>
                </div>
                <div style="background:#fff; color:#000; text-align:center; font-weight:bold; padding:6px; margin-top:5px; border:1.5px solid #000;">TAX INVOICE</div>
                <div style="display:flex; border:1.5px solid #000; border-top:none;">
                    <div style="flex:2.5; border-right:1.5px solid #000; padding:10px; font-size:12px;"><strong>To,</strong><br><b style="font-size:14px;">{company}</b><br>{c_row['Address']}<br><strong>GSTIN:</strong> {c_row['GSTIN']}</div>
                    <div style="flex:1; font-size:12px; font-weight:bold;">
                        <div style="border-bottom:1.5px solid #000; padding:8px 10px; display:flex; justify-content:space-between;"><span>BILL NO:</span> <span>{search_no}</span></div>
                        <div style="padding:8px 10px; display:flex; justify-content:space-between;"><span>DATE:</span> <span>{original_date_str}</span></div>
                    </div>
                </div>
                <table style="width:100%; border-collapse:collapse; table-layout:fixed; border:2.5px solid #000; border-top:none;">
                    <thead style="background:#eee; color:#000; font-size:11px;">
                        <tr><th style="width:{c_sr}; border:1px solid #000; padding:10px;">SR</th><th style="width:{c_desc}; border:1px solid #000;">DESCRIPTION</th><th style="width:{c_hsn}; border:1px solid #000;">HSN/SAC</th><th style="width:{c_qty}; border:1px solid #000;">QTY</th><th style="width:{c_rate}; border:1px solid #000;">RATE</th><th style="width:{c_amt}; border:1px solid #000;">AMOUNT</th></tr>
                    </thead>
                    <tbody style="font-size:11.5px;">{rows_html}{filler_html}</tbody>
                </table>
                {footer_sec}
                <div style="text-align:right; font-size:9px; margin-top:5px; color:#666;">Page {idx+1} of {len(pages)}</div>
            </div>"""

        st.components.v1.html(f"""
            <style>
                @media print {{ @page {{ size: A4; margin: 0; }} .no-print {{ display:none !important; }} .page {{ border:none !important; box-shadow:none !important; margin:0 !important; }} }}
                .page {{ width:210mm; height:297mm; padding:10mm 15mm; margin:15px auto; background:white; border:1px solid #eee; display:flex; flex-direction:column; font-family:Arial, sans-serif; box-sizing: border-box; }}
                table {{ border-collapse: collapse !important; table-layout: fixed !important; width: 100% !important; }}
                table td {{ border: 1px solid #000 !important; word-wrap: break-word; vertical-align: middle; }}
            </style>
            <div class="no-print" style="text-align:center; margin-bottom:20px;"><button onclick="window.print()" style="padding:12px 50px; background:#000; color:white; border:none; border-radius:8px; cursor:pointer; font-weight:bold; font-size:16px;">⎙ PRINT FETCHED BILL</button></div>
            {all_pages_html}
        """, height=1200, scrolling=True)
    else:
        st.error(f"Bill No {search_no} for year {search_year} not found in database!")