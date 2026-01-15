import streamlit as st
import pandas as pd
import random
import time
from datetime import date
import io
from fpdf import FPDF

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
    "“നിക്ഷേപം ഒരു ഒറ്റ തീരുമാനം അല്ല, ജീവിതകാല ശീലമാണ്.”",
    "“സമ്പത്ത് പെട്ടെന്ന് ഉണ്ടാകുന്നില്ല; സ്ഥിരതയോടെ വളരുന്നു.”",
    "“SIP തുടങ്ങുന്ന ദിവസം നിങ്ങളുടെ ഭാവി ആരംഭിക്കുന്നു”",
    "“സമ്പത്ത് പണിയാൻ SIP, ജീവിക്കാൻ SWP”",
    "“ഇന്ന് തുടങ്ങൂ, നാളേയ്ക്ക് വേണ്ടി.”"
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
        else:
            req_sip = shortfall / m_to_retire
        req_lumpsum = shortfall / ((1 + pre_r_monthly) ** m_to_retire)

    annual_withdrawals = []
    base_annual_rounded = round(base_annual_withdrawal)
    for year in range(ret_years):
        age = r_age + year
        withdrawal = base_annual_rounded * ((1 + inf_rate/100) ** year)
        annual_withdrawals.append({
            "പ്രായം": int(age),
            "വർഷം": year + 1,
            "വർഷിക പിൻവലിക്കൽ": round(withdrawal),
            "മാസിക തുക": round(withdrawal / 12)
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
st.markdown("<p style='text-align: center; color: #9CA3AF;'>Designed by SHAMSUDEEN ABDULLA</p>", unsafe_allow_html=True)

st.markdown('<div class="input-card">', unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 👤 വ്യക്തിഗത വിവരങ്ങൾ")
    current_age = st.number_input("നിലവിലെ പ്രായം", value=30, min_value=0, max_value=100, step=1)
    retire_age = st.number_input("വിരമിക്കൽ പ്രായം", value=60, min_value=current_age+1, max_value=110, step=1)
    life_exp = st.number_input("പ്രതീക്ഷിക്കുന്ന ആയുസ്സ്", value=85, min_value=retire_age+1, max_value=120, step=1)
    current_expense = st.number_input("പ്രതിമാസ ചെലവ് (₹)", value=30000, min_value=1, step=500)

with col2:
    st.markdown("### 💰 നിക്ഷേപ വിവരങ്ങൾ")
    inf_rate = st.number_input("വിലക്കയറ്റം (%)", value=6.0, step=0.1, format="%.1f")
    existing_corp = st.number_input("നിലവിലെ സമ്പാദ്യം (₹)", value=0, min_value=0, step=5000)
    current_sip = st.number_input("മാസ നിക്ഷേപം - SIP (₹)", value=0, min_value=0, step=100)
    pre_ret_rate = st.number_input("വിരമിക്കൽ വരെയുള്ള returns (%)", value=12.0, min_value=0.1, step=0.1, format="%.1f")
    post_ret_rate = st.number_input("വിരമിച്ച ശേഷമുള്ള returns (%)", value=8.0, min_value=0.1, step=0.1, format="%.1f")
    legacy_amount = st.number_input("ബാക്കി തുക (₹)", value=0, min_value=0, step=100000)

st.markdown('</div>', unsafe_allow_html=True)

if st.button("കണക്കുകൂട്ടുക"):
    if current_age >= retire_age or retire_age >= life_exp:
        st.error("❌ പ്രായം പരിശോധിക്കുക")
    else:
        res = calculate_retirement_final(current_age, retire_age, life_exp, current_expense, inf_rate, current_sip, existing_corp, pre_ret_rate, post_ret_rate, legacy_amount)
        st.session_state.res = res
        
        # Display results
        r1, r2 = st.columns(2)
        with r1:
            st.metric("പ്രതിമാസ ചെലവ്", f"₹ {res['future_exp']:,}")
            st.metric("ആവശ്യമായ കോർപസ്", f"₹ {res['corp_req']:,}")
        with r2:
            st.metric("കണക്കാക്കിയ സമ്പാദ്യം", f"₹ {res['total_sav']:,}")
            st.metric("കുറവ്", f"₹ {res['shortfall']:,}")

        st.divider()
        st.dataframe(pd.DataFrame(res["annual_withdrawals"]), hide_index=True, use_container_width=True)

# PDF Generation
if 'res' in st.session_state:
    res = st.session_state.res
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Retirement Plan Report", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(0, 10, f"Future Monthly Expense: INR {res['future_exp']:,}", ln=True)
    pdf.cell(0, 10, f"Total Corpus Required: INR {res['corp_req']:,}", ln=True)
    pdf.cell(0, 10, f"Shortfall: INR {res['shortfall']:,}", ln=True)
    
    # PDF-നെ bytes ആക്കി മാറ്റുന്നു (എറർ ഒഴിവാക്കാൻ ഇത് അത്യാവശ്യമാണ്)
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    
    st.download_button(
        label="📥 ഫലങ്ങൾ PDF ആയി ഡൗൺലോഡ് ചെയ്യുക",
        data=pdf_bytes,
        file_name="retirement_plan.pdf",
        mime="application/pdf"
    )
