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
        withdrawal = (future_monthly_exp_unrounded * 12) * ((1 + inf_rate/100) ** year)
        annual_withdrawals.append({
            "Age": int(age),
            "Year": year + 1,
            "Annual Withdrawal": round(withdrawal),
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
        st.markdown(f"🔹 **Additional Monthly SIP:** <span style='font-size:1.5em; color:#22C55E;'>₹ {res['req_sip']:,}</span>", unsafe_allow_html=True)
        st.markdown(f"🔹 **OR One-time Lumpsum Today:** <span style='font-size:1.5em; color:#22C55E;'>₹ {res['req_lumpsum']:,}</span>", unsafe_allow_html=True)
    else:
        st.success("✅ Your current savings plan is on track!")

    st.dataframe(pd.DataFrame(res["annual_withdrawals"]), use_container_width=True, hide_index=True)
    st.markdown(f'<span class="quote-text">{random.choice(all_quotes)}</span>', unsafe_allow_html=True)

# ✅ PROFESSIONAL EXCEL DOWNLOAD
if 'res' in st.session_state and st.session_state.res is not None:
    res = st.session_state.res
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet('Retirement Plan')
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#16A34A', 'font_color': 'white', 'border': 1})
        currency_fmt = workbook.add_format({'num_format': '₹ #,##0', 'border': 1})
        percent_fmt = workbook.add_format({'num_format': '0.0"%"', 'border': 1})
        
        worksheet.write('A1', 'RETIREMENT PLAN REPORT', workbook.add_format({'bold': True, 'font_size': 16}))
        worksheet.write('A3', f'Planner: SHAMSUDEEN ABDULLA')

        # Summary Table
        summary_labels = ["Required Corpus", "Projected Savings", "Shortfall", "Extra Monthly SIP", "One-time Lumpsum"]
        summary_vals = [res['corp_req'], res['total_sav'], res['shortfall'], res['req_sip'], res['req_lumpsum']]
        for i, (l, v) in enumerate(zip(summary_labels, summary_vals)):
            worksheet.write(i+5, 0, l)
            worksheet.write(i+5, 1, v, currency_fmt)

        # Schedule
        headers = ["Age", "Year", "Annual Withdrawal", "Monthly Amount"]
        for c, h in enumerate(headers): worksheet.write(12, c, h, header_fmt)
        for r, row in enumerate(res['annual_withdrawals']):
            worksheet.write(r+13, 0, row["Age"])
            worksheet.write(r+13, 1, row["Year"])
            worksheet.write(r+13, 2, row["Annual Withdrawal"], currency_fmt)
            worksheet.write(r+13, 3, row["Monthly Amount"], currency_fmt)

        worksheet.set_column('A:D', 20)

    st.download_button(label="📥 Download Excel Report", data=buffer.getvalue(), file_name=f"Retirement_Plan_{date.today()}.xlsx", mime="application/vnd.ms-excel")
