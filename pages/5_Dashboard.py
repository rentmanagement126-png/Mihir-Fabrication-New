import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- 1. SETTINGS & DATABASE ---
st.set_page_config(layout="wide", page_title="Mihir Fabrication - Command Center")

if 'db' not in st.session_state or st.session_state.db is None:
    st.error("Pehle Main Page par jaakar Database connect karein.")
    st.stop()

db = st.session_state.db

try:
    inv_df = pd.DataFrame(db.worksheet("Invoices").get_all_records())
    bill_df = pd.DataFrame(db.worksheet("Bills").get_all_records())
    sal_df = pd.DataFrame(db.worksheet("Salaries").get_all_records())
    
    # Cleaning Columns
    for df_temp in [inv_df, bill_df, sal_df]:
        df_temp.columns = [str(c).strip() for c in df_temp.columns]

    # Date Cleaning Function
    def clean_date(df):
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
        else:
            df['Date'] = pd.to_datetime(datetime.now().strftime("%d/%m/%Y"))
        return df

    inv_df = clean_date(inv_df)
    bill_df = clean_date(bill_df)

    # Numeric Cleaning
    num_cols = ['Total', 'Amount Received', 'Balance']
    for col in num_cols:
        if col in inv_df.columns:
            inv_df[col] = pd.to_numeric(inv_df[col], errors='coerce').fillna(0)
    
    if 'Amount' in bill_df.columns:
        bill_df['Amount'] = pd.to_numeric(bill_df['Amount'], errors='coerce').fillna(0)
    if 'Net Payable' in sal_df.columns:
        sal_df['Net Payable'] = pd.to_numeric(sal_df['Net Payable'], errors='coerce').fillna(0)

except Exception as e:
    st.error(f"⚠️ Data Loading Error: {e}")
    st.stop()

# --- 2. SIDEBAR FILTERS ---
st.sidebar.header("🗓️ Filter Data")
available_years = inv_df['Date'].dt.year.dropna().unique()
all_years = sorted([int(y) for y in available_years], reverse=True)
if not all_years: all_years = [datetime.now().year]

selected_year = st.sidebar.selectbox("Select Year", ["All Time"] + list(all_years))
selected_month = st.sidebar.selectbox("Select Month", ["All Year", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])

def apply_filter(df):
    if selected_year != "All Time":
        df = df[df['Date'].dt.year == selected_year]
        if selected_month != "All Year":
            month_idx = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"].index(selected_month) + 1
            df = df[df['Date'].dt.month == month_idx]
    return df

f_inv = apply_filter(inv_df)
f_bill = apply_filter(bill_df)

st.title("🛡️ Mihir Fabrication - Command Center")

# --- 3. TOP METRICS ---
st.subheader("💰 Client Payments (Inflow)")
c1, c2, c3, c4 = st.columns(4)
total_billed = f_inv['Total'].sum()
cash_received = f_inv['Amount Received'].sum()
client_pending = f_inv['Balance'].sum()
c1.metric("Total Invoices", len(f_inv))
c2.metric("Total Billed Value", f"₹{total_billed:,.0f}")
c3.metric("Cash Received", f"₹{cash_received:,.0f}", delta=f"{(cash_received/total_billed*100 if total_billed>0 else 0):.1f}%")
c4.metric("Pending Clients", f"₹{client_pending:,.0f}", delta_color="inverse")

st.subheader("📉 Factory Expenses & Liabilities")
e1, e2, e3, e4 = st.columns(4)
total_salaries = sal_df['Net Payable'].sum()
paid_bills = f_bill[f_bill['Status'] == 'Paid']['Amount'].sum()
unpaid_bills = f_bill[f_bill['Status'] != 'Paid']['Amount'].sum()
total_exp_paid = paid_bills + total_salaries
e1.metric("Paid Resource Bills", f"₹{paid_bills:,.0f}")
e2.metric("Salaries Paid", f"₹{total_salaries:,.0f}")
e3.metric("Total Paid Expense", f"₹{total_exp_paid:,.0f}")
e4.metric("Unpaid (Liability)", f"₹{unpaid_bills:,.0f}", delta_color="inverse")

# --- 4. REAL PROFIT ---
st.write("---")
actual_profit = cash_received - total_exp_paid
st.subheader(f"⚖️ Cash-in-Hand Profit: ₹{actual_profit:,.2f}")
if actual_profit > 0: st.success("✅ Factory is running on Positive Cash Flow!")
else: st.error("⚠️ Expenses are higher than received cash!")

# --- 5. NEW CHARTS SECTION (BOTTOM) ---
st.write("---")
st.subheader("📊 Business Analysis Charts")
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.write("📝 **Expense Composition** (Kahan kitna kharcha hua)")
    exp_pie = pd.DataFrame({
        'Category': ['Salaries', 'Paid Resource Bills', 'Pending Bills'],
        'Amount': [total_salaries, paid_bills, unpaid_bills]
    })
    fig1 = px.pie(exp_pie, values='Amount', names='Category', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig1, use_container_width=True)

with col_chart2:
    st.write("📈 **Income vs Expense Trend**")
    trend_data = pd.DataFrame({
        'Type': ['Cash Received', 'Total Expenses'],
        'Amount': [cash_received, total_exp_paid + unpaid_bills]
    })
    fig2 = px.bar(trend_data, x='Type', y='Amount', color='Type', color_discrete_map={'Cash Received':'#2E7D32', 'Total Expenses':'#C62828'})
    st.plotly_chart(fig2, use_container_width=True)

# --- 6. ACTION TABLES ---
st.write("---")
t1, t2 = st.columns(2)
with t1:
    st.subheader("🚩 Pending From Clients")
    st.table(f_inv[f_inv['Balance'] > 0][['Client Name', 'Balance']].sort_values('Balance', ascending=False).head(5))
with t2:
    st.subheader("🚧 Our Unpaid Bills")
    unpaid_list = f_bill[f_bill['Status'] != 'Paid']
    if not unpaid_list.empty:
        # Using index 0 if Description column missing
        desc = 'Description' if 'Description' in unpaid_list.columns else unpaid_list.columns[0]
        st.table(unpaid_list[[desc, 'Amount']].head(5))