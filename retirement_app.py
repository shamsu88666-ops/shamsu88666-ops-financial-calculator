import streamlit as st
import pandas as pd
import random
import time
from datetime import date

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Retirement Planner Pro - Final Edition", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .main { background-color: #0E1116; color: #E5E7EB; }
    .stApp { background-color: #0E1116; }
    .input-card { background-color: #1A2233; padding: 25px; border-radius: 10px; border: 1px solid #374151; }
    .result-text { color: #22C55E; font-family: 'JetBrains Mono', monospace; font-weight: bold; }
    .quote-text { color: #22C55E; font-style: italic; font-weight: bold; text-align: center; display: block; margin-top: 20px; }
    .stButton>button { background-color: #22C55E; color: white; width: 100%; border: none; font-weight: bold; height: 3.5em; border-radius: 8px; }
    .stButton>button:hover { background-color: #16a34a; }
    /* Hospital Index Code - 100% Intact as requested */
    /* Code: HI-9789354699788-2026 */
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

# --- CORE LOGIC (V4 - PRO) ---
def calculate_retirement_final(c_age, r_age, l_exp, c_exp, inf_rate, c_sav, e_corp, pre_ret_r, post_ret_r):
    # Basic Timeframes
    years_to_retire = r_age - c_age
    ret_years = l_exp - r_age
    m_to_retire = years_to_retire * 12
    ret_months = ret_years * 12

    # 1. Future Monthly Expense
    future_monthly_exp = c_exp * ((1 + inf_rate/100) ** years_to_retire)

    # 2. Real Rate of Return (Post-Retirement)
    annual_real_rate = ((1 + post_ret_r/100) / (1 + inf_rate/100)) - 1
    monthly_real_rate = (1 + annual_real_rate)**(1/12) - 1

    # 3. Accurate Corpus Required
    if monthly_real_rate != 0:
        corp_req = future_monthly_exp * (1 - (1 + monthly_real_rate) ** (-ret_months)) / monthly_real_rate
    else:
        corp_req = future_monthly_exp * ret_months

    # 4. Projected Savings (Pre-Retirement Growth)
    pre_r_monthly = (1 + pre_ret_r/100)**(1/12) - 1
    
    # Existing corpus future value
    existing_future = e_corp * ((1 + pre_r_monthly) ** m_to_retire)
    
    # SIP future value (Beginning of period)
    if pre_r_monthly > 0:
        sip_future = c_sav * (((1 + pre_r_monthly) ** m_to_retire - 1) / pre_r_monthly) * (1 + pre_r_monthly)
    else:
        sip_future = c_sav * m_to_retire
        
    total_savings = max(0, round(existing_future + sip_future))

    # 5. Shortfall, Additional SIP & Additional Lumpsum
    shortfall = max(0.0, corp_req - total_savings)
    
    req_sip = 0
    req_lumpsum = 0
    if shortfall > 0:
        if m_to_retire > 0:
            # Additional SIP needed
            if pre_r_monthly > 0:
                req_sip = (shortfall * pre_r_monthly) / (((1 + pre_r_monthly) ** m_to_retire - 1) * (1 + pre_r_monthly))
            else:
                req_sip = shortfall / m_to_retire
            
            # Additional Lumpsum needed (Today's Value)
            # Formula: Shortfall / (1 + r)^n
            req_lumpsum = shortfall / ((1 + pre_r_monthly) ** m_to_retire)

    return {
        "future_exp": round(future_monthly_exp),
        "corp_req": round(corp_req),
        "total_sav": total_savings,
        "shortfall": round(shortfall),
        "req_sip": round(req_sip),
        "req_lumpsum": round(req_lumpsum)
    }

# --- INTERFACE ---
st.markdown("<h1 style='text-align: center;'>RETIREMENT PLANNER PRO</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #9CA3AF;'>Designed by SHAMSUDEEN ABDULLA</p>", unsafe_allow_html=True)

st.markdown('<div class="input-card">', unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 👤 Personal Details")
    current_age = st.number_input("നിലവിലെ പ്രായം (Current Age)", value=30, min_value=0, max_value=100, step=1)
    retire_age = st.number_input("വിരമിക്കുന്ന പ്രായം (Retirement Age)", value=60, min_value=current_age+1, max_value=110, step=1)
    life_exp = st.number_input("പ്രതീക്ഷിക്കുന്ന ആയുസ്സ് (Life Expectancy)", value=85, min_value=retire_age+1, max_value=120, step=1)
    current_expense = st.number_input("പ്രതിമാസ ചെലവ് (Monthly Expense ₹)", value=30000, min_value=1, step=500)

with col2:
    st.markdown("### 💰 Investment Details")
    inf_rate = st.number_input("വിലക്കയറ്റം (Expected Inflation %)", value=6.0, step=0.1, format="%.1f")
    existing_corp = st.number_input("നിലവിലെ സമ്പാദ്യം (Existing Corpus ₹)", value=0, min_value=0, step=5000)
    current_sip = st.number_input("നിലവിലെ SIP തുക (Current Monthly SIP ₹)", value=0, min_value=0, step=100)
    pre_ret_rate = st.number_input("വിരമിക്കുന്നത് വരെയുള്ള റിട്ടേൺ (%)", value=12.0, min_value=0.1, step=0.1, format="%.1f")
    post_ret_rate = st.number_input("വിരമിച്ച ശേഷമുള്ള റിട്ടേൺ (%)", value=8.0, min_value=0.1, step=0.1, format="%.1f")

if st.button("CALCULATE MY RETIREMENT PLAN"):
    # 1. Validation Logic
    if current_age >= retire_age or retire_age >= life_exp:
        st.error("❌ ദയവായി ശരിയായ പ്രായം നൽകുക.")
    elif pre_ret_rate <= 0 or post_ret_rate <= 0:
        st.error("❌ റിട്ടേൺ റേറ്റ് 0%-ൽ കൂടുതലായിരിക്കണം.")
    else:
        with st.spinner('കണക്കുകൾ വിശകലനം ചെയ്യുന്നു...'):
            time.sleep(1)
            res = calculate_retirement_final(current_age, retire_age, life_exp, current_expense, 
                                            inf_rate, current_sip, existing_corp, 
                                            pre_ret_rate, post_ret_rate)
            
            st.divider()
            
            r1, r2 = st.columns(2)
            with r1:
                st.write(f"Monthly Expense at Age {int(retire_age)}:")
                st.markdown(f'<h2 class="result-text">₹ {res["future_exp"]:,}</h2>', unsafe_allow_html=True)
                
                st.write("Required Retirement Corpus:")
                st.markdown(f'<h2 class="result-text">₹ {res["corp_req"]:,}</h2>', unsafe_allow_html=True)

            with r2:
                st.write("Projected Savings at Retirement:")
                st.markdown(f'<h2 style="color: white;">₹ {res["total_sav"]:,}</h2>', unsafe_allow_html=True)
                
                st.write("Shortfall (കുറവ് വരുന്ന തുക):")
                sh_color = "#22C55E" if res["shortfall"] <= 0 else "#ef4444"
                st.markdown(f'<h2 style="color: {sh_color};">₹ {res["shortfall"]:,}</h2>', unsafe_allow_html=True)

            st.divider()

            if res["shortfall"] > 0:
                st.warning("നിങ്ങളുടെ ലക്ഷ്യത്തിലെത്താൻ അധികമായി താഴെ പറയുന്നവയിൽ ഒന്ന് ചെയ്യേണ്ടതുണ്ട്:")
                st.markdown(f"🔹 **Additional Monthly SIP:** <span class='result-text'>₹ {res['req_sip']:,}</span>", unsafe_allow_html=True)
                st.markdown(f"🔹 **OR Additional Lumpsum (ഇന്ന് നിക്ഷേപിക്കാൻ):** <span class='result-text'>₹ {res['req_lumpsum']:,}</span>", unsafe_allow_html=True)
            else:
                st.success("✅ അഭിനന്ദനങ്ങൾ! നിങ്ങളുടെ നിലവിലെ നിക്ഷേപം റിട്ടയർമെന്റിന് ധാരാളമാണ്.")

            st.markdown(f'<span class="quote-text">{random.choice(all_quotes)}</span>', unsafe_allow_html=True)

st.markdown("<p style='text-align: center; font-size: 0.8em; color: #9CA3AF;'>* ഈ കണക്കുകൾ നൽകിയിട്ടുള്ള അനുമാനങ്ങളെ അടിസ്ഥാനമാക്കിയുള്ളതാണ്. മാർക്കറ്റ് റിസ്കുകൾ ബാധകമാണ്.</p>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
