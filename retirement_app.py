import streamlit as st
import pandas as pd
import random
import time
from datetime import date
import io

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Retirement Planner Pro - Final Edition", layout="wide")

# --- CUSTOM CSS (Optimized for both Light & Dark Mode) ---
st.markdown("""
    <style>
    /* Force Dark Theme Background for all modes */
    .stApp {
        background-color: #0E1116 !important;
        color: #E5E7EB !important;
    }
    .main {
        background-color: #0E1116 !important;
    }
    /* Input Card Styling */
    .input-card {
        background-color: #1A2233 !important;
        padding: 25px;
        border-radius: 10px;
        border: 1px solid #374151;
        color: #E5E7EB !important;
    }
    /* Results Styling */
    .result-text {
        color: #22C55E !important;
        font-family: 'Courier New', monospace;
        font-weight: bold;
    }
    /* Quote Styling */
    .quote-text {
        color: #22C55E !important;
        font-style: italic;
        font-weight: bold;
        text-align: center;
        display: block;
        margin-top: 20px;
    }
    /* Buttons */
    .stButton>button {
        background-color: #22C55E !important;
        color: white !important;
        width: 100%;
        border: none;
        font-weight: bold;
        height: 3.5em;
        border-radius: 8px;
    }
    .stButton>button:hover {
        background-color: #16a34a !important;
        color: white !important;
    }
    /* Text Input Labels & Color Fix */
    label, p, span, h1, h2, h3 {
        color: #E5E7EB !important;
    }
    /* Metric label color fix */
    [data-testid="stMetricLabel"] {
        color: #9CA3AF !important;
    }
    /* Metric value color fix */
    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
    }
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
    current_balance = total_savings if total_savings > corp_req else corp_req
    monthly_post_ret_r = (1 + post_ret_r/100)**(1/12) - 1
    
    for year in range(ret_years):
        age = r_age + year
        withdrawal_monthly = future_monthly_exp_unrounded * ((1 + inf_rate/100) ** year)
        
        # Balance calculation for the year
        for _ in range(12):
            current_balance = (current_balance * (1 + monthly_post_ret_r)) - withdrawal_monthly
        
        annual_withdrawals.append({
            "Age": int(age),
            "Year": year + 1,
            "Annual Withdrawal": round(withdrawal_monthly * 12),
            "Monthly Amount": round(withdrawal_monthly),
            "Remaining Corpus (Legacy)": round(max(0, current_balance))
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
st.markdown("<p style='text-align: center; color: #9CA3AF;'>Designed for Your Future Wealth</p>", unsafe_allow_html=True)

st.markdown('<div class="input-card">', unsafe_allow_html=True)
user_name = st.text_input("Name of the User", value="Valued User")
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 👤 Personal Information")
    current_age = st.number_input("Current Age", value=30, min_value=0, max_value=100, step=1)
    retire_age = st.number_input("Retirement Age", value=60, min_value=current_age+1, max_value=110, step=1)
    life_exp = st.number_input("Expected Life Expectancy", value=85, min_value=retire_age+1, max_value=120, step=1)
    current_expense = st.number_input("Current Monthly Expense (₹)", value=30000, min_value=1, step=500)

with col2:
    st.markdown("### 💰 Investment Details")
    inf_rate = st.number_input("Inflation Rate (%)", value=6.0, step=0.1, format="%.1f")
    existing_corp = st.number_input("Existing Savings (₹)", value=0, min_value=0, step=5000)
    current_sip = st.number_input("Current Monthly SIP (₹)", value=0, min_value=0, step=100)
    pre_ret_rate = st.number_input("Pre-retirement Returns (%)", value=12.0, min_value=0.1, step=0.1, format="%.1f")
    post_ret_rate = st.number_input("Post-retirement Returns (%)", value=8.0, min_value=0.1, step=0.1, format="%.1f")
    legacy_amount = st.number_input("Legacy Amount (₹)", value=0, min_value=0, step=100000)
st.markdown('</div>', unsafe_allow_html=True)

if st.button("Calculate"):
    res = calculate_retirement_final(current_age, retire_age, life_exp, current_expense, inf_rate, current_sip, existing_corp, pre_ret_rate, post_ret_rate, legacy_amount)
    st.session_state.res = res
    st.session_state.user_name = user_name
    
    st.divider()
    r1, r2 = st.columns(2)
    with r1:
        st.metric("Expense at Retirement (Monthly)", f"₹ {res['future_exp']:,}")
        st.metric("Required Retirement Corpus", f"₹ {res['corp_req']:,}")
    with r2:
        st.metric("Projected Savings", f"₹ {res['total_sav']:,}")
        st.metric("Shortfall", f"₹ {res['shortfall']:,}", delta_color="inverse")

    if res["shortfall"] > 0:
        st.error("📉 SHORTFALL ANALYSIS")
        st.markdown(f"To cover the shortfall of **₹ {res['shortfall']:,}**, you need to invest:")
        st.markdown(f"🔹 **Additional Monthly SIP:** <span style='font-size:1.2em; color:#22C55E;'>₹ {res['req_sip']:,}</span>", unsafe_allow_html=True)
        st.markdown(f"🔹 **OR One-time Lumpsum Today:** <span style='font-size:1.2em; color:#22C55E;'>₹ {res['req_lumpsum']:,}</span>", unsafe_allow_html=True)
    else:
        st.success("✅ Your current savings plan is on track!")

    st.write("### Post-Retirement Yearly Cashflow & Legacy Corpus")
    st.dataframe(pd.DataFrame(res["annual_withdrawals"]), use_container_width=True, hide_index=True)
    st.markdown(f'<span class="quote-text">{random.choice(all_quotes)}</span>', unsafe_allow_html=True)

st.markdown("<p style='text-align: center; font-size: 0.8em; color: #9CA3AF;'>* Based on assumptions. Market risks apply.</p>", unsafe_allow_html=True)

# ✅ EXCEL DOWNLOAD WITH DISCLAIMER AT TOP
if 'res' in st.session_state and st.session_state.res is not None:
    res = st.session_state.res
    u_name = st.session_state.user_name
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet('Retirement Plan')
        
        # Styles
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#16A34A', 'font_color': 'white', 'border': 1})
        title_fmt = workbook.add_format({'bold': True, 'font_size': 14})
        currency_fmt = workbook.add_format({'num_format': '₹ #,##0', 'border': 1})
        disclaimer_fmt = workbook.add_format({'italic': True, 'font_color': 'red', 'text_wrap': True, 'border': 1, 'valign': 'top'})
        normal_fmt = workbook.add_format({'border': 1})

        # --- SECTION: DISCLAIMER (AT TOP) ---
        disclaimer_text = (
            "DISCLAIMER: This report is generated based on basic mathematics and the inputs provided by you. "
            "Practical results may vary significantly. Your financial planning should not be based solely on this report. "
            "The app developer shall not be held responsible for any financial liabilities, losses, or other damages "
            "incurred based on the information provided in this report."
        )
        worksheet.merge_range('A1:F4', disclaimer_text, disclaimer_fmt)

        # --- SECTION: REPORT INFO ---
        worksheet.write('A6', 'RETIREMENT PLAN REPORT', title_fmt)
        worksheet.write('A7', f'User Name: {u_name}')
        worksheet.write('A8', f'Generated on: {date.today()}')

        # --- SECTION: INPUTS ---
        worksheet.write('A10', '1. INPUT PARAMETERS', header_fmt)
        inputs = [
            ["Current Age", current_age], ["Retirement Age", retire_age], ["Life Expectancy", life_exp],
            ["Current Monthly Expense", current_expense], ["Inflation Rate (%)", inf_rate],
            ["Existing Savings", existing_corp], ["Current Monthly SIP", current_sip],
            ["Pre-retirement Return (%)", pre_ret_rate], ["Post-retirement Return (%)", post_ret_rate],
            ["Legacy Amount", legacy_amount]
        ]
        for i, (l, v) in enumerate(inputs):
            worksheet.write(i+11, 0, l, normal_fmt)
            worksheet.write(i+11, 1, v, normal_fmt)

        # --- SECTION: RESULTS ---
        worksheet.write('D10', '2. RESULTS SUMMARY', header_fmt)
        summary = [
            ["Expense at Retirement", res['future_exp']], ["Required Corpus", res['corp_req']],
            ["Projected Savings", res['total_sav']], ["Shortfall", res['shortfall']],
            ["Extra Monthly SIP Needed", res['req_sip']], ["One-time Lumpsum Needed", res['req_lumpsum']]
        ]
        for i, (l, v) in enumerate(summary):
            worksheet.write(i+11, 3, l, normal_fmt)
            worksheet.write(i+11, 4, v, currency_fmt)

        # --- SECTION: WITHDRAWAL SCHEDULE ---
        worksheet.write('A23', '3. YEARLY WITHDRAWAL & REMAINING CORPUS', header_fmt)
        table_headers = ["Age", "Year", "Annual Withdrawal", "Monthly Amount", "Remaining Corpus (Legacy)"]
        for c, h in enumerate(table_headers):
            worksheet.write(24, c, h, header_fmt)
        
        for r, row in enumerate(res['annual_withdrawals']):
            worksheet.write(r+25, 0, row["Age"], normal_fmt)
            worksheet.write(r+25, 1, row["Year"], normal_fmt)
            worksheet.write(r+25, 2, row["Annual Withdrawal"], currency_fmt)
            worksheet.write(r+25, 3, row["Monthly Amount"], currency_fmt)
            worksheet.write(r+25, 4, row["Remaining Corpus (Legacy)"], currency_fmt)

        worksheet.set_column('A:F', 22)

    st.download_button(
        label="📥 Download Excel Report", 
        data=buffer.getvalue(), 
        file_name=f"Retirement_Plan_{u_name}_{date.today()}.xlsx", 
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
