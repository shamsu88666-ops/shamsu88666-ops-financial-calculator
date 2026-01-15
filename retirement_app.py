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
    "“നിക്ഷേപം ഒരു ഒറ്റ തീരുമാനം അല്ല, ജീവിതകാല ശീലമാണ്.”",
    "“സമ്പത്ത് പെട്ടെന്ന് ഉണ്ടാകുന്നില്ല; സ്ഥിരതയോടെ വളരുന്നു.”",
    "“SIP തുടങ്ങുന്ന ദിവസം നിങ്ങളുടെ ഭാവി ആരംഭിക്കുന്നു”",
    "“സമ്പത്ത് പണിയാൻ SIP, ജീവിക്കാൻ SWP”",
    "“ഇന്ന് തുടങ്ങൂ, നാളേയ്ക്ക് വേണ്ടി.”"
]

# --- CORE LOGIC (V4 - PRO + Legacy + Yearly Withdrawals) ---
def calculate_retirement_final(c_age, r_age, l_exp, c_exp, inf_rate, c_sav, e_corp, pre_ret_r, post_ret_r, legacy_amount):
    """
    Calculate retirement plan with legacy amount and year-wise withdrawal schedule
    """
    # Basic Timeframes
    years_to_retire = r_age - c_age
    ret_years = l_exp - r_age
    m_to_retire = years_to_retire * 12
    ret_months = ret_years * 12

    # 1. Future Monthly Expense
    future_monthly_exp_unrounded = c_exp * ((1 + inf_rate/100) ** years_to_retire)
    future_monthly_exp = round(future_monthly_exp_unrounded)
    
    # Base annual withdrawal (for schedule)
    base_annual_withdrawal = future_monthly_exp_unrounded * 12

    # 2. Real Rate of Return (Post-Retirement)
    annual_real_rate = ((1 + post_ret_r/100) / (1 + inf_rate/100)) - 1
    monthly_real_rate = (1 + annual_real_rate)**(1/12) - 1

    # 3. Accurate Corpus Required (Annuity + Legacy)
    if monthly_real_rate != 0:
        # PV of annuity
        corp_req_annuity = future_monthly_exp_unrounded * (1 - (1 + monthly_real_rate) ** (-ret_months)) / monthly_real_rate
        
        # PV of legacy
        corp_req_legacy = 0
        if legacy_amount > 0:
            corp_req_legacy = legacy_amount / ((1 + monthly_real_rate) ** ret_months)
        
        corp_req = corp_req_annuity + corp_req_legacy
    else:
        corp_req = future_monthly_exp_unrounded * ret_months + legacy_amount

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

    # 5. Shortfall & Additional Requirements
    shortfall = max(0.0, corp_req - total_savings)
    
    req_sip = 0
    req_lumpsum = 0
    if shortfall > 0 and m_to_retire > 0:
        if pre_r_monthly > 0:
            req_sip = (shortfall * pre_r_monthly) / (((1 + pre_r_monthly) ** m_to_retire - 1) * (1 + pre_r_monthly))
        else:
            req_sip = shortfall / m_to_retire
        
        req_lumpsum = shortfall / ((1 + pre_r_monthly) ** m_to_retire)

    # ✅ NEW: Yearly withdrawal schedule
    annual_withdrawals = []
    base_annual_rounded = round(base_annual_withdrawal)
    
    for year in range(ret_years):
        age = r_age + year
        withdrawal = base_annual_rounded * ((1 + inf_rate/100) ** year)
        monthly_eq = withdrawal / 12
        
        annual_withdrawals.append({
            "Age": int(age),
            "Year_in_Retirement": year + 1,
            "Annual_Withdrawal": round(withdrawal),
            "Monthly_Equivalent": round(monthly_eq)
        })

    return {
        "future_exp": future_monthly_exp,
        "corp_req": round(corp_req),
        "total_sav": total_savings,
        "shortfall": round(shortfall),
        "req_sip": round(req_sip),
        "req_lumpsum": round(req_lumpsum),
        "legacy_amount": legacy_amount,
        "annual_withdrawals": annual_withdrawals,  # ✅ NEW
        "ret_years": ret_years
    }

# --- MAIN APP ---
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
    
    # ✅ NEW: Legacy input
    st.markdown("### 🏦 പിന്തലമുറയ്ക്കുള്ള തുക (Legacy)")
    legacy_amount = st.number_input("പിന്തലമുറയ്ക്ക് ബാക്കി വെക്കാൻ ആഗ്രഹിക്കുന്ന തുക (₹)", value=0, min_value=0, step=100000, 
                                    help="ആയുസ്സ് അവസാനിക്കുമ്പോൾ പിന്തലമുറയ്ക്ക് നൽകാൻ ആഗ്രഹിക്കുന്ന തുക. 0 = ആവശ്യമില്ല")

st.markdown('</div>', unsafe_allow_html=True)

# ✅ FIXED: Calculate button - store results in session state
if st.button("CALCULATE MY RETIREMENT PLAN"):
    # Validation Logic
    validation_errors = []
    if current_age >= retire_age:
        validation_errors.append("Current Age must be less than Retirement Age")
    if retire_age >= life_exp:
        validation_errors.append("Retirement Age must be less than Life Expectancy")
    if pre_ret_rate <= 0 or post_ret_rate <= 0:
        validation_errors.append("Return rates must be greater than 0%")
    if current_expense <= 0:
        validation_errors.append("Expenses must be greater than ₹0")
    
    if validation_errors:
        for error in validation_errors:
            st.error(f"❌ {error}")
        st.session_state.res = None  # Clear previous results
    else:
        with st.spinner('കണക്കുകൾ വിശകലനം ചെയ്യുന്നു...'):
            time.sleep(1)
            # Pass legacy_amount to function
            res = calculate_retirement_final(current_age, retire_age, life_exp, current_expense, 
                                            inf_rate, current_sip, existing_corp, 
                                            pre_ret_rate, post_ret_rate, legacy_amount)
            
            # Store in session state
            st.session_state.res = res
            
            st.divider()
            
            # ✅ DISPLAY RESULTS
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
                
                if res["legacy_amount"] > 0:
                    st.write("Legacy Amount for Heirs:")
                    st.markdown(f'<h2 class="result-text">₹ {res["legacy_amount"]:,}</h2>', unsafe_allow_html=True)

            st.divider()

            if res["shortfall"] > 0:
                st.warning("നിങ്ങളുടെ ലക്ഷ്യത്തിലെത്താൻ അധികമായി താഴെ പറയുന്നവയിലൊന്ന് ചെയ്യേണ്ടതുണ്ട്:")
                st.markdown(f"🔹 **Additional Monthly SIP:** <span class='result-text'>₹ {res['req_sip']:,}</span>", unsafe_allow_html=True)
                st.markdown(f"🔹 **OR Additional Lumpsum (ഇന്ന് നിക്സപിക്കാൻ):** <span class='result-text'>₹ {res['req_lumpsum']:,}</span>", unsafe_allow_html=True)
            else:
                st.success("✅ അഭിനന്ദനങ്ങൾ! നിങ്ങളുടെ നിലവിലെ നിക്സപം റിട്ടയർമെന്റിന് ധാരാളമാണ്.")

            # ✅ NEW: Yearly Withdrawal Schedule Section
            st.markdown("---")
            st.markdown(f"### 📅 **റിട്ടയർമെന്റ് കാലത്തെ വർഷം തോറും പിൻവലിക്കൽ തുക**")
            st.markdown(f"**കാലാവധി:** പ്രായം {int(retire_age)} മുതൽ {int(life_exp)} വരെ ({res['ret_years']} വർഷം)")
            
            withdrawal_df = pd.DataFrame(res["annual_withdrawals"])
            
            # Display as interactive table
            st.dataframe(
                withdrawal_df,
                use_container_width=True,
                column_config={
                    "Age": st.column_config.NumberColumn("പ്രായം", format="%d"),
                    "Year_in_Retirement": st.column_config.NumberColumn("വർഷം", format="%d"),
                    "Annual_Withdrawal": st.column_config.NumberColumn("വർഷിക പിൻവലിക്കൽ", format="₹ %,d"),
                    "Monthly_Equivalent": st.column_config.NumberColumn("മാസിക തുക", format="₹ %,d")
                },
                hide_index=True
            )
            
            # Chart
            st.markdown("#### 📈 വർഷം തോറും പിൻവലിക്കൽ ദൃശ്യവൽക്കരണം")
            st.line_chart(
                withdrawal_df.set_index("Age")["Annual_Withdrawal"],
                color="#22C55E",
                use_container_width=True
            )
            
            # Summary statistics
            st.markdown("#### 📊 സംക്ഷിപ്ത വിവരങ്ങൾ")
            col_stats1, col_stats2, col_stats3 = st.columns(3)
            col_stats1.metric("ആകെ വർഷം", f"{res['ret_years']}")
            col_stats2.metric("ആദ്യ വർഷത്തെ തുക", f"₹ {res['annual_withdrawals'][0]['Annual_Withdrawal']:,}")
            col_stats3.metric("അവസാന വർഷത്തെ തുക", f"₹ {res['annual_withdrawals'][-1]['Annual_Withdrawal']:,}")
            
            # Quote
            st.markdown(f'<span class="quote-text">{random.choice(all_quotes)}</span>', unsafe_allow_html=True)

st.markdown("<p style='text-align: center; font-size: 0.8em; color: #9CA3AF;'>* ഈ കണക്കുകൾ നൽകിയിട്ടുള്ള അനുമാനങ്ങളെ അടിസ്ഥാനമാക്കിയുള്ളതാണ്. മാർക്കറ്റ് റിസ്കുകൾ ബാധകമാണ്.</p>", unsafe_allow_html=True)

# ✅ FIXED: Excel Download Button (Always visible, works with session state)
if 'res' in st.session_state and st.session_state.res is not None:
    # Create download button
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Summary sheet
        summary_inputs = {
            'Parameter': [
                'നിലവിലെ പ്രായം', 'വിരമിക്കുന്ന പ്രായം', 'പ്രതീക്ഷിക്കുന്ന ആയുസ്സ്',
                'പ്രതിമാസ ചെലവ് (₹)', 'വിലക്കയറ്റം (%)',
                'നിലവിലെ സമ്പാദ്യം (₹)', 'നിലവിലെ SIP തുക (₹)',
                'വിരമിക്കുന്നത് വരെയുള്ള റിട്ടേൺ (%)', 'വിരമിച്ച ശേഷമുള്ള റിട്ടേൺ (%)',
                'പിന്തലമുറയ്ക്കുള്ള തുക (₹)'
            ],
            'Value': [
                current_age, retire_age, life_exp,
                current_expense, inf_rate,
                existing_corp, current_sip,
                pre_ret_rate, post_ret_rate,
                legacy_amount
            ]
        }
        results_data = {
            'കണക്ക്': [
                'വിരമിക്കുമ്പോഴത്തെ പ്രതിമാസ ചെലവ് (₹)',
                'വിരമിക്കുമ്പോഴത്തെ വാർഷിക പിൻവലിക്കൽ (₹)',
                'ആവശ്യമായ റിട്ടയർമെന്റ് കോർപസ് (₹)',
                'കണക്കാക്കപ്പെട്ട സമ്പാദ്യം (₹)',
                'കുറവ് (₹)',
                'അധിക മാസ SIP ആവശ്യം (₹)',
                'അധിക lumpsum ആവശ്യം (₹)'
            ],
            'തുക': [
                st.session_state.res['future_exp'],
                st.session_state.res['future_exp'] * 12,
                st.session_state.res['corp_req'],
                st.session_state.res['total_sav'],
                st.session_state.res['shortfall'],
                st.session_state.res['req_sip'],
                st.session_state.res['req_lumpsum']
            ]
        }
        
        pd.DataFrame(summary_inputs).to_excel(writer, sheet_name='Summary', index=False, startrow=0)
        pd.DataFrame(results_data).to_excel(writer, sheet_name='Summary', index=False, startrow=len(summary_inputs) + 2)
        
        # Yearly schedule
        if 'annual_withdrawals' in st.session_state.res:
            withdrawal_df = pd.DataFrame(st.session_state.res['annual_withdrawals'])
            withdrawal_df.to_excel(writer, sheet_name='Yearly Withdrawals', index=False)
    
    st.download_button(
        label="📥 Excel ഫയൽ ഡൗൺലോഡ് ചെയ്യുക",
        data=output.getvalue(),
        file_name=f"retirement_plan_{current_age}_{date.today().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
