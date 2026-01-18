import streamlit as st
import pandas as pd
import random
import io
from datetime import date

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Retirement Planner Pro - Final Edition", layout="wide")

# (CSS ഭാഗം മാറ്റമില്ലാതെ തുടരുന്നു...)
st.markdown("""
    <style>
    .stApp { background-color: #0E1116 !important; color: #E5E7EB !important; }
    .input-card { background-color: #1A2233 !important; padding: 25px; border-radius: 10px; border: 1px solid #374151; }
    .stButton>button { background-color: #22C55E !important; color: white !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- CORE LOGIC (SYNCED WITH SWP LOGIC) ---
def calculate_retirement_final(c_age, r_age, l_exp, c_exp, inf_rate, c_sip, e_corp, pre_ret_r, post_ret_r, legacy_amount_real):
    months_to_retire = (r_age - c_age) * 12
    retirement_months = (l_exp - r_age) * 12
    total_months = (l_exp - c_age) * 12
    
    # കൃത്യമായ മന്ത്ലി റേറ്റുകൾ (CAGR Basis)
    monthly_inf = (1 + inf_rate/100) ** (1/12) - 1
    monthly_pre_ret = (1 + pre_ret_r/100) ** (1/12) - 1
    monthly_post_ret = (1 + post_ret_r/100) ** (1/12) - 1
    
    # Legacy Nominal Value
    legacy_nominal = legacy_amount_real * (1 + inf_rate/100) ** (total_months/12)
    
    # Expense at the beginning of Retirement
    expense_at_retirement = c_exp * (1 + inf_rate/100) ** (months_to_retire/12)
    
    # Required Corpus Calculation (Using Annuity Due formula as we withdraw at start of month)
    # ഇത് SWP ലോജിക്കുമായി സിങ്ക് ചെയ്യാൻ സഹായിക്കുന്നു
    real_rate = (1 + monthly_post_ret) / (1 + monthly_inf) - 1
    
    if real_rate != 0:
        pv_expenses = expense_at_retirement * ((1 - (1 + real_rate) ** -retirement_months) / real_rate) * (1 + real_rate)
    else:
        pv_expenses = expense_at_retirement * retirement_months
        
    pv_legacy = legacy_nominal / (1 + monthly_post_ret) ** retirement_months
    corp_req = pv_expenses + pv_legacy
    
    # Pre-retirement growth
    future_existing = e_corp * (1 + monthly_pre_ret) ** months_to_retire
    
    if monthly_pre_ret > 0:
        future_sip = c_sip * (((1 + monthly_pre_ret) ** months_to_retire - 1) / monthly_pre_ret) * (1 + monthly_pre_ret)
    else:
        future_sip = c_sip * months_to_retire
        
    total_savings = future_existing + future_sip
    shortfall = max(0, corp_req - total_savings)
    
    # Additional SIP/Lumpsum needed
    req_sip = 0
    req_lumpsum = 0
    if shortfall > 0:
        req_sip = (shortfall * monthly_pre_ret) / (((1 + monthly_pre_ret) ** months_to_retire - 1) * (1 + monthly_pre_ret))
        req_lumpsum = shortfall / ((1 + monthly_pre_ret) ** months_to_retire)
    
    # Cashflow generation (Exactly like SWP Report)
    annual_withdrawals = []
    current_balance = corp_req
    total_withdrawn_sum = 0
    
    for year in range(1, (retirement_months // 12) + 1):
        # ഓരോ വർഷവും ഇൻഫ്ലേഷൻ അഡ്ജസ്റ്റ്മെന്റ്
        monthly_expense_this_year = expense_at_retirement * (1 + inf_rate/100) ** (year - 1)
        yearly_sum = 0
        
        for month in range(12):
            if current_balance > 0:
                withdrawal = min(monthly_expense_this_year, current_balance)
                current_balance -= withdrawal
                current_balance *= (1 + monthly_post_ret)
                yearly_sum += withdrawal
        
        total_withdrawn_sum += yearly_sum
        annual_withdrawals.append({
            "Age": r_age + year - 1,
            "Year": year,
            "Annual Withdrawal": round(yearly_sum),
            "Monthly Amount": round(monthly_expense_this_year),
            "Remaining Corpus": round(max(0, current_balance))
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
        "annual_withdrawals": annual_withdrawals,
        "total_withdrawn_sum": round(total_withdrawn_sum)
    }

# --- UI (Main logic unchanged, only calling the updated function) ---
def main():
    st.markdown("<h1 style='text-align: center;'>RETIREMENT PLANNER PRO</h1>", unsafe_allow_html=True)
    
    # Input Cards (നിങ്ങൾ നൽകിയ അതേ UI)
    st.markdown('<div class="input-card">', unsafe_allow_html=True)
    user_name = st.text_input("Name of the User", value="Valued User")
    col1, col2 = st.columns(2)
    
    with col1:
        current_age = st.number_input("Current Age", value=30, step=1)
        retire_age = st.number_input("Retirement Age", value=60, step=1)
        life_exp = st.number_input("Expected Life Expectancy", value=85, step=1)
        current_expense = st.number_input("Current Monthly Expense (₹)", value=30000, step=500)
    
    with col2:
        inf_rate = st.number_input("Inflation Rate (%)", value=7.0, step=0.1) # 7% default as per your report
        existing_corp = st.number_input("Existing Savings (₹)", value=0, step=5000)
        current_sip = st.number_input("Current Monthly SIP (₹)", value=0, step=100)
        pre_ret_rate = st.number_input("Pre-retirement Returns (%)", value=12.0, step=0.1)
        post_ret_rate = st.number_input("Post-retirement Returns (%)", value=8.0, step=0.1)
        legacy_amount = st.number_input("Legacy Amount (Today's Value) (₹)", value=0, step=100000)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("Calculate"):
        res = calculate_retirement_final(current_age, retire_age, life_exp, current_expense, inf_rate, current_sip, existing_corp, pre_ret_rate, post_ret_rate, legacy_amount)
        
        st.divider()
        # Metrics Display
        m1, m2, m3 = st.columns(3)
        m1.metric("Required Corpus", f"₹ {res['corp_req']:,}")
        m2.metric("Expense at Retirement", f"₹ {res['future_exp']:,}")
        m3.metric("Shortfall", f"₹ {res['shortfall']:,}")
        
        st.write("### Yearly Cashflow (Synced with SWP Logic)")
        st.dataframe(pd.DataFrame(res["annual_withdrawals"]), use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
