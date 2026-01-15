import streamlit as st
import pandas as pd
import random
import time
from datetime import date
import io

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Retirement Planner Pro - Final Edition", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .main { background-color: #0E1116; color: #E5E7EB; }
    .stApp { background-color: #0E1116; }
    .input-card { background-color: #1A2233; padding: 25px; border-radius: 10px; border: 1px solid #374151; }
    .result-text { color: #22C55E; font-family: 'Courier New', monospace; font-weight: bold; }
    .quote-text { color: #22C55E; font-style: italic; font-weight: bold; text-align: center; display: block; margin-top: 20px; }
    .stButton>button { background-color: #22C55E; color: white; width: 100%; border: none; font-weight: bold; height: 3.5em; border-radius: 8px; }
    .stButton>button:hover { background-color: #16a34a; }
    </style>
    """, unsafe_allow_html=True)

# --- MOTIVATION QUOTES ---
all_quotes = [
    "“Investment is not a one-time decision, it is a lifetime habit.”",
    "“Wealth is not created overnight; it grows with consistency.”",
    "“The day you start a SIP, your future begins.”",
    "“SIP to build wealth, SWP to live life.”",
    "“Start today, for the sake of tomorrow.”"
]

# --- CORE LOGIC ---
def calculate_retirement_final(c_age, r_age, l_exp, c_exp, inf_rate, c_sav, e_corp, pre_ret_r, post_ret_r, legacy_amount):
    years_to_retire = r_age - c_age
    ret_years = l_exp - r_age
    m_to_retire = years_to_retire * 12
    ret_months = ret_years * 12

    future_monthly_exp_unrounded = c_exp * ((1 + inf_rate/100) ** years_to_retire)
    future_monthly_exp = round(future_monthly_exp_unrounded)
    base_annual_withdrawal = future_monthly_exp_unrounded * 12

    annual_real_rate = ((1 + post_ret_r/100) / (1 + inf_rate/100)) - 1
    monthly_real_rate = (1 + annual_real_rate)**(1/12) - 1

    if monthly_real_rate != 0:
        corp_req_annuity = future_monthly_exp_unrounded * (1 - (1 + monthly_real_rate) ** (-ret_months)) / monthly_real_rate
        corp_req_legacy = legacy_amount / ((1 + monthly_real_rate) ** ret_months) if legacy_amount > 0 else 0
        corp_req = corp_req_annuity + corp_req_legacy
    else:
        corp_req = future_monthly_exp_unrounded * ret_months + legacy_amount

    pre_r_monthly = (1 + pre_ret_r/100)**(1/12) - 1
    existing_future = e_corp * ((1 + pre_r_monthly) ** m_to_retire)
    
    if pre_r_monthly > 0:
        sip_future = c_sav * (((1 + pre_r_monthly) ** m_to_retire - 1) / pre_r_monthly) * (1 + pre_r_monthly)
    else:
        sip_future = c_sav * m_to_retire
        
    total_savings = max(0, round(existing_future + sip_future))
    shortfall = max(0.0, corp_req - total_savings)
    
    req_sip = 0
    req_lumpsum = 0
    if shortfall > 0 and m_to_retire > 0:
        if pre_r_monthly > 0:
            req_sip = (shortfall * pre_r_monthly) / (((1 + pre_r_monthly) ** m_to_retire - 1) * (1 + pre_r_monthly))
            req_lumpsum = shortfall / ((1 + pre_r_monthly) ** m_to_retire)
        else:
            req_sip = shortfall / m_to_retire
            req_lumpsum = shortfall

    annual_withdrawals = []
    for year in range(ret_years):
        age = r_age + year
        withdrawal = round(base_annual_rounded := (future_monthly_exp_unrounded * 12) * ((1 + inf_rate/100) ** year))
        annual_withdrawals.append({
            "Age": int(age),
            "Year": year + 1,
            "Annual Withdrawal": withdrawal,
            "Monthly Amount": round(withdrawal / 12)
        })

    return {
        "future_exp": future_monthly_exp,
        "corp_req": round(corp_req),
        "total_sav": total_savings,
        "shortfall": round(shortfall),
        "req_sip": round(req_sip),
        "req_lumpsum": round(req_lumpsum),
        "legacy_amount": legacy_amount,
        "annual_withdrawals": annual_withdrawals,
        "ret_years": ret_years
    }

# --- MAIN APP ---
st.markdown("<h1 style='text-align: center;'>RETIREMENT PLANNER PRO</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #9CA3AF;'>Developed by SHAMSUDEEN ABDULLA</p>", unsafe_allow_html=True)

st.markdown('<div class="input-card">', unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 👤 Personal Information")
    current_age = st.number_input("Current Age", value=30, min_value=0, max_value=100, step=1)
    retire_age = st.number_input("Retirement Age", value=60, min_value=current_age+1, max_value=110, step=1)
    life_exp = st.number_input("Expected Life Expectancy", value=85, min_value=retire_age+1, max_value=120, step=1)
    current_expense = st.number_input("Monthly Expense (₹)", value=30000, min_value=1, step=500)

with col2:
    st.markdown("### 💰 Investment Details")
    inf_rate = st.number_input("Inflation Rate (%)", value=6.0, step=0.1, format="%.1f")
    existing_corp = st.number_input("Existing Savings (₹)", value=0, min_value=0, step=5000)
    current_sip = st.number_input("Monthly SIP (₹)", value=0, min_value=0, step=100)
    pre_ret_rate = st.number_input("Pre-retirement Returns (%)", value=12.0, min_value=0.1, step=0.1, format="%.1f")
    post_ret_rate = st.number_input("Post-retirement Returns (%)", value=8.0, min_value=0.1, step=0.1, format="%.1f")
    legacy_amount = st.number_input("Legacy Amount (₹)", value=0, min_value=0, step=100000)

st.markdown('</div>', unsafe_allow_html=True)

if st.button("Calculate"):
    res = calculate_retirement_final(current_age, retire_age, life_exp, current_expense, inf_rate, current_sip, existing_corp, pre_ret_rate, post_ret_rate, legacy_amount)
    st.session_state.res = res
    
    st.divider()
    r1, r2 = st.columns(2)
    with r1:
        st.write(f"Monthly Expense at Retirement:")
        st.markdown(f'<h2 class="result-text">₹ {res["future_exp"]:,}</h2>', unsafe_allow_html=True)
        st.write(f"Required Retirement Corpus:")
        st.markdown(f'<h2 class="result-text">₹ {res["corp_req"]:,}</h2>', unsafe_allow_html=True)

    with r2:
        st.write(f"Projected Savings:")
        st.markdown(f'<h2 style="color: white;">₹ {res["total_sav"]:,}</h2>', unsafe_allow_html=True)
        sh_color = "#22C55E" if res["shortfall"] <= 0 else "#ef4444"
        st.write(f"Shortfall:")
        st.markdown(f'<h2 style="color: {sh_color};">₹ {res["shortfall"]:,}</h2>', unsafe_allow_html=True)

    if res["shortfall"] > 0:
        st.warning(f"Additional Monthly SIP Required: ₹ {res['req_sip']:,}")
    
    st.dataframe(pd.DataFrame(res["annual_withdrawals"]), use_container_width=True, hide_index=True)
    st.markdown(f'<span class="quote-text">{random.choice(all_quotes)}</span>', unsafe_allow_html=True)

st.markdown("<p style='text-align: center; font-size: 0.8em; color: #9CA3AF;'>* Based on assumptions. Market risks apply.</p>", unsafe_allow_html=True)

# ✅ PROFESSIONAL EXCEL DOWNLOAD WITH DESIGN
if 'res' in st.session_state and st.session_state.res is not None:
    res = st.session_state.res
    
    # Create an in-memory buffer for Excel
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet('Retirement Plan')
        
        # --- STYLES ---
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#16A34A', 'font_color': 'white', 'border': 1, 'align': 'center'})
        sub_header_fmt = workbook.add_format({'bold': True, 'bg_color': '#F3F4F6', 'border': 1})
        currency_fmt = workbook.add_format({'num_format': '₹ #,##0', 'border': 1})
        percent_fmt = workbook.add_format({'num_format': '0.0"%"', 'border': 1})
        border_fmt = workbook.add_format({'border': 1})
        title_fmt = workbook.add_format({'bold': True, 'font_size': 16, 'font_color': '#16A34A'})
        disclaimer_fmt = workbook.add_format({'font_size': 9, 'italic': True, 'font_color': '#4B5563', 'text_wrap': True})

        # --- CONTENT ---
        # Title
        worksheet.write('A1', 'RETIREMENT PLAN REPORT', title_fmt)
        worksheet.write('A2', f'Generated on: {date.today().strftime("%d %b %Y")}')
        worksheet.write('A3', f'Planner: SHAMSUDEEN ABDULLA')

        # Section 1: Inputs
        worksheet.write('A5', '1. INPUT PARAMETERS', sub_header_fmt)
        input_data = [
            ["Current Age", current_age], ["Retirement Age", retire_age], 
            ["Life Expectancy", life_exp], ["Current Monthly Expense", current_expense],
            ["Inflation Rate", inf_rate/100], ["Expected Pre-Retirement Return", pre_ret_rate/100],
            ["Expected Post-Retirement Return", post_ret_rate/100], ["Legacy Goal", legacy_amount]
        ]
        for i, (label, val) in enumerate(input_data):
            worksheet.write(i+5, 0, label, border_fmt)
            if "Rate" in label or "Return" in label:
                worksheet.write(i+5, 1, val, percent_fmt)
            else:
                worksheet.write(i+5, 1, val, currency_fmt)

        # Section 2: Results Summary
        worksheet.write('D5', '2. PLAN SUMMARY', sub_header_fmt)
        res_data = [
            ["Monthly Expense at Retirement", res['future_exp']],
            ["Total Corpus Needed", res['corp_req']],
            ["Projected Savings", res['total_sav']],
            ["Shortfall", res['shortfall']],
            ["Required Extra SIP", res['req_sip']]
        ]
        for i, (label, val) in enumerate(res_data):
            worksheet.write(i+5, 3, label, border_fmt)
            worksheet.write(i+5, 4, val, currency_fmt)

        # Section 3: Yearly Schedule
        worksheet.write('A15', '3. YEARLY WITHDRAWAL SCHEDULE', sub_header_fmt)
        headers = ["Age", "Year", "Annual Withdrawal (₹)", "Monthly Amount (₹)"]
        for col_num, header in enumerate(headers):
            worksheet.write(15, col_num, header, header_fmt)

        for row_num, row_data in enumerate(res['annual_withdrawals']):
            worksheet.write(row_num + 16, 0, row_data["Age"], border_fmt)
            worksheet.write(row_num + 16, 1, row_data["Year"], border_fmt)
            worksheet.write(row_num + 16, 2, row_data["Annual Withdrawal"], currency_fmt)
            worksheet.write(row_num + 16, 3, row_data["Monthly Amount"], currency_fmt)

        # Section 4: Disclaimer
        disclaimer_text = ("DISCLAIMER: This report is for educational purposes only. The calculations are based on "
                           "the assumptions provided. Market returns are subject to volatility and not guaranteed. "
                           "Please consult a certified financial planner before making investment decisions.")
        worksheet.merge_range('A100:E103', disclaimer_text, disclaimer_fmt)

        # Set Column Widths
        worksheet.set_column('A:A', 30)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 5)
        worksheet.set_column('D:D', 30)
        worksheet.set_column('E:E', 20)

    # Download Button
    st.download_button(
        label="📥 Download Detailed Excel Report",
        data=buffer.getvalue(),
        file_name=f"Retirement_Plan_{date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
