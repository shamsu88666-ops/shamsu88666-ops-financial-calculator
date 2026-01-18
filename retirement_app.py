import streamlit as st
import pandas as pd
import random
import time
from datetime import date
import io

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Retirement Planner Pro - Expert Edition", layout="wide")

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
            "User Age": r_age + year,
            "Year of Retirement": f"Year {year + 1}",
            "Yearly Requirement": round(monthly_expense_this_year * 12),
            "Monthly Pension": round(monthly_expense_this_year),
            "Wealth Status": round(current_balance)
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
    st.markdown("### 👤 Basic Details")
    current_age = st.number_input("Current Age", value=30)
    retire_age = st.number_input("Retirement Age", value=60)
    life_exp = st.number_input("Planning Until Age", value=85)
    current_expense = st.number_input("Monthly Expense Needed Today (₹)", value=30000)

with col2:
    st.markdown("### 💰 Financial Data")
    inf_rate = st.number_input("Inflation Rate (%)", value=6.0)
    existing_corp = st.number_input("Existing Fund (₹)", value=0)
    current_sip = st.number_input("Monthly Investment (₹)", value=0)
    pre_ret_rate = st.number_input("Expected Returns (%)", value=12.0)
    post_ret_rate = st.number_input("Post-retirement Returns (%)", value=8.0)
    legacy_amount = st.number_input("Legacy Amount (Today's Value) (₹)", value=0)
st.markdown('</div>', unsafe_allow_html=True)

if st.button("Generate Detailed Plan"):
    res = calculate_retirement_final(current_age, retire_age, life_exp, current_expense, inf_rate, current_sip, existing_corp, pre_ret_rate, post_ret_rate, legacy_amount)
    st.session_state.res = res
    st.session_state.user_name = user_name
    
    st.success(f"Plan Generated for {user_name}!")
    st.dataframe(pd.DataFrame(res["annual_withdrawals"]), use_container_width=True, hide_index=True)

# --- EXCEL DOWNLOAD (OPTIMIZED) ---
if 'res' in st.session_state:
    res = st.session_state.res
    u_name = st.session_state.user_name
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet('Financial Plan')
        
        # Formats
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#22C55E', 'font_color': 'white', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        cell_fmt = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
        curr_fmt = workbook.add_format({'num_format': '₹ #,##0', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        title_fmt = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter'})
        info_fmt = workbook.add_format({'italic': True, 'font_color': '#555555', 'text_wrap': True, 'font_size': 11})

        # 1. Report Title & Info
        worksheet.merge_range('A1:E2', f'COMPLETE RETIREMENT STRATEGY FOR {u_name.upper()}', title_fmt)
        worksheet.write('A3', 'Plan Prepared On:', workbook.add_format({'bold': True}))
        worksheet.write('B3', str(date.today()), cell_fmt)

        # 2. Key Highlights (Results)
        worksheet.merge_range('A5:E5', 'FINANCIAL GOALS & SHORTFALL ANALYSIS', header_fmt)
        summary = [
            ["Monthly Expense Needed at Age " + str(retire_age), res['future_exp']],
            ["Total Wealth Fund Required (Corpus)", res['corp_req']],
            ["Projected Fund from Current Savings", res['total_sav']],
            ["Fund Shortfall (Extra Needed)", res['shortfall']],
            ["Recommended Additional Monthly SIP", res['req_sip']],
            ["OR Lumpsum Investment Needed Today", res['req_lumpsum']]
        ]
        for i, (label, val) in enumerate(summary):
            worksheet.merge_range(i+6, 0, i+6, 2, label, cell_fmt)
            worksheet.merge_range(i+6, 3, i+6, 4, val, curr_fmt)

        # 3. Yearly Wealth Chart
        start_row = 14
        worksheet.merge_range(f'A{start_row}:E{start_row}', 'YEAR-BY-YEAR WEALTH & WITHDRAWAL PLAN', header_fmt)
        headers = ["Your Age", "Year of Retirement", "Yearly Cash Requirement", "Monthly Pension", "Wealth Status (Balance)"]
        for c, h in enumerate(headers):
            worksheet.write(start_row, c, h, header_fmt)
        
        for r, row in enumerate(res['annual_withdrawals']):
            curr_r = start_row + 1 + r
            worksheet.write(curr_r, 0, row["User Age"], cell_fmt)
            worksheet.write(curr_r, 1, row["Year of Retirement"], cell_fmt)
            worksheet.write(curr_r, 2, row["Yearly Requirement"], curr_fmt)
            worksheet.write(curr_r, 3, row["Monthly Pension"], curr_fmt)
            worksheet.write(curr_r, 4, row["Wealth Status"], curr_fmt)

        # 4. Adding Explanatory Notes at the bottom
        last_row = start_row + len(res['annual_withdrawals']) + 2
        notes = [
            "* Yearly Cash Requirement: ഓരോ വർഷവും നിങ്ങളുടെ ജീവിതച്ചെലവിനായി ആവശ്യമായ തുക (പണപ്പെരുപ്പം ഉൾപ്പെടെ).",
            "* Monthly Pension: ഓരോ മാസവും നിങ്ങളുടെ അക്കൗണ്ടിലേക്ക് വിഭാവനം ചെയ്യുന്ന തുക.",
            "* Wealth Status (Balance): എല്ലാ ചെലവുകൾക്കും ശേഷം നിങ്ങളുടെ പക്കൽ അവശേഷിക്കുന്ന നിക്ഷേപ മൂല്യം."
        ]
        for i, note in enumerate(notes):
            worksheet.merge_range(last_row + i, 0, last_row + i, 4, note, info_fmt)

        # Set Column Widths
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('C:C', 30)
        worksheet.set_column('D:D', 30)
        worksheet.set_column('E:E', 35)

    st.download_button(label="📥 Download This Detailed Professional Report", data=buffer.getvalue(), file_name=f"Retirement_Expert_Plan_{u_name}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
