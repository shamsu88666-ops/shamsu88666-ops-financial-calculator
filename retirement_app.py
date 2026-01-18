import streamlit as st
import pandas as pd
import random
import time
from datetime import date
import io

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Retirement Planner Pro - Full Edition", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1116 !important; color: #E5E7EB !important; }
    .input-card {
        background-color: #1A2233 !important; padding: 25px; border-radius: 10px;
        border: 1px solid #374151; color: #E5E7EB !important;
    }
    .stButton>button {
        background-color: #22C55E !important; color: white !important; width: 100%;
        border: none; font-weight: bold; height: 3.5em; border-radius: 8px;
    }
    .dev-container { text-align: center; margin-bottom: 25px; }
    .dev-btn { display: inline-block; padding: 8px 16px; margin: 5px; border-radius: 5px; text-decoration: none !important; font-weight: bold; color: white !important; font-size: 13px; }
    .wa-btn { background-color: #25D366; }
    .fb-btn { background-color: #1877F2; }
    </style>
    """, unsafe_allow_html=True)

# --- CORE LOGIC ---
def calculate_retirement_final(c_age, r_age, l_exp, c_exp, inf_rate, c_sav, e_corp, pre_ret_r, post_ret_r, legacy_amount_real):
    months_to_retire = (r_age - c_age) * 12
    retirement_months = (l_exp - r_age) * 12
    total_months = (l_exp - c_age) * 12
    
    monthly_inf = (1 + inf_rate/100) ** (1/12) - 1
    monthly_pre_ret = (1 + pre_ret_r/100) ** (1/12) - 1
    monthly_post_ret = (1 + post_ret_r/100) ** (1/12) - 1
    
    legacy_nominal = legacy_amount_real * (1 + monthly_inf) ** total_months
    expense_at_retirement = c_exp * (1 + monthly_inf) ** months_to_retire
    
    if abs(monthly_post_ret - monthly_inf) > 0.0001:
        pv_expenses = expense_at_retirement * (1 - ((1 + monthly_inf) / (1 + monthly_post_ret)) ** retirement_months) / (monthly_post_ret - monthly_inf)
    else:
        pv_expenses = expense_at_retirement * retirement_months
    
    pv_legacy = legacy_nominal / (1 + monthly_post_ret) ** retirement_months if legacy_nominal > 0 else 0
    corp_req = pv_expenses + pv_legacy
    future_existing = e_corp * (1 + monthly_pre_ret) ** months_to_retire
    
    if monthly_pre_ret > 0:
        future_sip = c_sav * (((1 + monthly_pre_ret) ** months_to_retire - 1) / monthly_pre_ret) * (1 + monthly_pre_ret)
    else:
        future_sip = c_sav * months_to_retire
        
    total_savings = future_existing + future_sip
    shortfall = max(0, corp_req - total_savings)
    
    req_sip = 0
    req_lumpsum = 0
    if shortfall > 0 and months_to_retire > 0:
        if monthly_pre_ret > 0:
            req_sip = (shortfall * monthly_pre_ret) / (((1 + monthly_pre_ret) ** months_to_retire - 1) * (1 + monthly_pre_ret))
            req_lumpsum = shortfall / ((1 + monthly_pre_ret) ** months_to_retire)
        else:
            req_sip = shortfall / months_to_retire
            req_lumpsum = shortfall
    
    annual_withdrawals = []
    current_balance = corp_req
    
    for year in range(retirement_months // 12):
        monthly_expense_this_year = expense_at_retirement * (1 + monthly_inf) ** (year * 12)
        for month in range(12):
            current_balance = (current_balance * (1 + monthly_post_ret)) - monthly_expense_this_year
        
        annual_withdrawals.append({
            "Age": r_age + year,
            "Year of Retirement": f"Year {year + 1}",
            "Yearly Withdrawal": round(monthly_expense_this_year * 12),
            "Monthly Pension": round(monthly_expense_this_year),
            "Remaining Wealth": round(current_balance)
        })
    
    return {
        "future_exp": round(expense_at_retirement),
        "corp_req": round(corp_req),
        "total_sav": round(total_savings),
        "shortfall": round(shortfall),
        "req_sip": round(req_sip),
        "req_lumpsum": round(req_lumpsum),
        "legacy_real": round(legacy_amount_real),
        "legacy_nominal": round(legacy_nominal),
        "annual_withdrawals": annual_withdrawals
    }

# --- MAIN APP ---
st.markdown("<h1 style='text-align: center;'>RETIREMENT PLANNER PRO</h1>", unsafe_allow_html=True)

st.markdown(f"""
    <div class="dev-container">
        <p style='margin-bottom: 5px; font-size: 0.9em; color: #6B7280;'>Developed by Shamsudeen abdulla</p>
        <a href="https://wa.me/qr/IOBUQDQMM2X3D1" target="_blank" class="dev-btn wa-btn">WhatsApp Developer</a>
        <a href="https://www.facebook.com/shamsudeen.abdulla.2025/" target="_blank" class="dev-btn fb-btn">Facebook Profile</a>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="input-card">', unsafe_allow_html=True)
user_name = st.text_input("Name of the User", value="Valued User")
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 👤 Personal Details")
    current_age = st.number_input("Current Age", value=30, step=1)
    retire_age = st.number_input("Retirement Age", value=60, step=1)
    life_exp = st.number_input("Life Expectancy (Plan Until Age)", value=85, step=1)
    current_expense = st.number_input("Current Monthly Expense (₹)", value=30000, step=500)

with col2:
    st.markdown("### 💰 Financial Inputs")
    inf_rate = st.number_input("Inflation Rate (%)", value=6.0, step=0.1)
    existing_corp = st.number_input("Existing Savings (₹)", value=0, step=5000)
    current_sip = st.number_input("Current Monthly SIP (₹)", value=0, step=100)
    pre_ret_rate = st.number_input("Pre-retirement Returns (%)", value=12.0, step=0.1)
    post_ret_rate = st.number_input("Post-retirement Returns (%)", value=8.0, step=0.1)
    legacy_amount = st.number_input("Legacy (Future Gift for Family) - Today's Value (₹)", value=0, step=100000)
st.markdown('</div>', unsafe_allow_html=True)

if st.button("Calculate Plan"):
    res = calculate_retirement_final(current_age, retire_age, life_exp, current_expense, inf_rate, current_sip, existing_corp, pre_ret_rate, post_ret_rate, legacy_amount)
    st.session_state.res = res
    st.session_state.user_name = user_name
    
    st.divider()
    r1, r2 = st.columns(2)
    with r1:
        st.metric("Expense at Retirement (Monthly)", f"₹ {res['future_exp']:,}")
        st.metric("Total Fund Needed (Corpus)", f"₹ {res['corp_req']:,}")
        st.metric("Legacy Today", f"₹ {res['legacy_real']:,}")
    with r2:
        st.metric("Total Projected Savings", f"₹ {res['total_sav']:,}")
        st.metric("Shortfall (Gap)", f"₹ {res['shortfall']:,}", delta_color="inverse")
        st.metric(f"Nominal Legacy at {life_exp}", f"₹ {res['legacy_nominal']:,}")

    if res["shortfall"] > 0:
        st.error("📉 SHORTFALL DETECTED")
        st.markdown(f"**Additional Monthly SIP Needed:** ₹ {res['req_sip']:,}")
        st.markdown(f"**OR Lumpsum Today:** ₹ {res['req_lumpsum']:,}")

    st.write("### Retirement Cashflow Breakdown")
    st.dataframe(pd.DataFrame(res["annual_withdrawals"]), use_container_width=True, hide_index=True)

# --- EXCEL DOWNLOAD (RESTORED ALL RESULTS) ---
if 'res' in st.session_state:
    res = st.session_state.res
    u_name = st.session_state.user_name
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet('Retirement Plan')
        
        # Styles
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#22C55E', 'font_color': 'white', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        cell_fmt = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
        curr_fmt = workbook.add_format({'num_format': '₹ #,##0', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        title_fmt = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter'})

        # Title
        worksheet.merge_range('A1:E1', f'RETIREMENT STRATEGY REPORT FOR {u_name.upper()}', title_fmt)
        worksheet.write('A2', 'Date:', workbook.add_format({'bold': True}))
        worksheet.write('B2', str(date.today()), cell_fmt)

        # 1. Inputs Section
        worksheet.merge_range('A4:B4', 'YOUR SETTINGS', header_fmt)
        inputs = [
            ["Current Age", current_age], ["Retirement Age", retire_age], ["Plan Duration (Until Age)", life_exp],
            ["Current Monthly Cost", current_expense], ["Assumed Inflation (%)", inf_rate],
            ["Existing Savings", existing_corp], ["Existing SIP", current_sip],
            ["Return Before Retirement (%)", pre_ret_rate], ["Return After Retirement (%)", post_ret_rate],
            ["Legacy (Current Value)", res['legacy_real']]
        ]
        for i, (k, v) in enumerate(inputs):
            worksheet.write(i+5, 0, k, cell_fmt)
            worksheet.write(i+5, 1, v, cell_fmt)

        # 2. Results Section (ALL RESULTS RESTORED)
        worksheet.merge_range('D4:E4', 'PLAN CALCULATION SUMMARY', header_fmt)
        summary = [
            ["Monthly Expense at Retirement", res['future_exp']],
            ["Total Required Wealth Fund", res['corp_req']],
            ["Projected Savings Fund", res['total_sav']],
            ["Fund Shortfall (Gap)", res['shortfall']],
            ["Extra Monthly SIP Required", res['req_sip']],
            ["Extra Lumpsum Required Today", res['req_lumpsum']],
            ["Legacy (Current Buying Power)", res['legacy_real']],
            ["Legacy (Actual Amount at End)", res['legacy_nominal']]
        ]
        for i, (k, v) in enumerate(summary):
            worksheet.write(i+5, 3, k, cell_fmt)
            worksheet.write(i+5, 4, v, curr_fmt)

        # 3. Yearly Breakdown
        worksheet.merge_range('A17:E17', 'RETIREMENT INCOME & WEALTH TRACKER', header_fmt)
        headers = ["Your Age", "Retirement Year", "Yearly Income Taken", "Monthly Income Taken", "Remaining Fund Balance"]
        for c, h in enumerate(headers):
            worksheet.write(18, c, h, header_fmt)
        
        for r, row in enumerate(res['annual_withdrawals']):
            curr_r = 19 + r
            worksheet.write(curr_r, 0, row["Age"], cell_fmt)
            worksheet.write(curr_r, 1, row["Year of Retirement"], cell_fmt)
            worksheet.write(curr_r, 2, row["Yearly Withdrawal"], curr_fmt)
            worksheet.write(curr_r, 3, row["Monthly Pension"], curr_fmt)
            worksheet.write(curr_r, 4, row["Remaining Wealth"], curr_fmt)

        # Fix Column Widths to prevent '#####'
        worksheet.set_column('A:A', 30)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('C:C', 30)
        worksheet.set_column('D:D', 30)
        worksheet.set_column('E:E', 35)

    st.download_button(label="📥 Download Full Report", data=buffer.getvalue(), file_name=f"Retirement_Plan_{u_name}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
