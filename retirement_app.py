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

# --- CORE LOGIC (V4 - PRO + Legacy + Yearly Schedule) ---
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

    # 3. Adjusted Corpus Required (Annuity + Legacy)
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

    # 4. Projected Savings
    pre_r_monthly = (1 + pre_ret_r/100)**(1/12) - 1
    
    existing_future = e_corp * ((1 + pre_r_monthly) ** m_to_retire)
    
    if pre_r_monthly > 0:
        sip_future = c_sav * (((1 + pre_r_monthly) ** m_to_retire - 1) / pre_r_monthly) * (1 + pre_r_monthly)
    else:
        sip_future = c_sav * m_to_retire
        
    total_savings = max(0, round(existing_future + sip_future))

    # 5. Shortfall & Requirements
    shortfall = max(0.0, corp_req - total_savings)
    
    req_sip = 0
    req_lumpsum = 0
    if shortfall > 0 and m_to_retire > 0:
        if pre_r_monthly > 0:
            req_sip = (shortfall * pre_r_monthly) / (((1 + pre_r_monthly) ** m_to_retire - 1) * (1 + pre_r_monthly))
        else:
            req_sip = shortfall / m_to_retire
        
        req_lumpsum = shortfall / ((1 + pre_r_monthly) ** m_to_retire)

    # ✅ Yearly withdrawal schedule
    annual_withdrawals = []
    base_annual_rounded = round(base_annual_withdrawal)
    
    for year in range(ret_years):
        age = r_age + year
        withdrawal = base_annual_rounded * ((1 + inf_rate/100) ** year)
        monthly_eq = withdrawal / 12
        
        annual_withdrawals.append({
            "പ്രായം": int(age),
            "വർഷം": year + 1,
            "വർഷിക പിൻവലിക്കൽ": round(withdrawal),
            "മാസിക തുക": round(monthly_eq)
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
    
    # Legacy input
    st.markdown("### 🏦 പിന്തലമുറയ്ക്ക്")
    legacy_amount = st.number_input("ബാക്കി തുക (₹)", value=0, min_value=0, step=100000, 
                                    help="ആയുസ്സ് അവസാനത്തോടെ പിന്തലമുറയ്ക്ക് നൽകാൻ ആഗ്രഹിക്കുന്ന തുക")

st.markdown('</div>', unsafe_allow_html=True)

# ✅ FIXED: Calculate button - store results in session state
if st.button("കണക്കുകൂട്ടുക"):
    # Validation
    validation_errors = []
    if current_age >= retire_age:
        validation_errors.append("നിലവിലെ പ്രായം വിരമിക്കൽ പ്രായത്തിന് താഴെയായിരിക്കണം")
    if retire_age >= life_exp:
        validation_errors.append("വിരമിക്കൽ പ്രായം പ്രതീക്ഷിക്കുന്ന ആയുസ്സിന് താഴെയായിരിക്കണം")
    if pre_ret_rate <= 0 or post_ret_rate <= 0:
        validation_errors.append("റിട്ടേൺ 0%-ൽ കൂടുതലായിരിക്കണം")
    if current_expense <= 0:
        validation_errors.append("ചെലവ് 0-ൽ കൂടുതലായിരിക്കണം")
    
    if validation_errors:
        for error in validation_errors:
            st.error(f"❌ {error}")
        st.session_state.res = None
    else:
        with st.spinner('കണക്ക് പ്രോസസ്സ് ചെയ്യുന്നു...'):
            time.sleep(1)
            res = calculate_retirement_final(current_age, retire_age, life_exp, current_expense, 
                                            inf_rate, current_sip, existing_corp, 
                                            pre_ret_rate, post_ret_rate, legacy_amount)
            
            st.session_state.res = res
            
            st.divider()
            
            # Results display
            r1, r2 = st.columns(2)
            with r1:
                st.write(f"വിരമിക്കുമ്പോഴത്തെ പ്രതിമാസ ചെലവ്:")
                st.markdown(f'<h2 class="result-text">₹ {res["future_exp"]:,}</h2>', unsafe_allow_html=True)
                
                st.write(f"ആവശ്യമായ റിട്ടയർമെന്റ് കോർപസ്:")
                st.markdown(f'<h2 class="result-text">₹ {res["corp_req"]:,}</h2>', unsafe_allow_html=True)

            with r2:
                st.write(f"കണക്കാക്കപ്പെട്ട സമ്പാദ്യം:")
                st.markdown(f'<h2 style="color: white;">₹ {res["total_sav"]:,}</h2>', unsafe_allow_html=True)
                
                st.write(f"കുറവ്:")
                sh_color = "#22C55E" if res["shortfall"] <= 0 else "#ef4444"
                st.markdown(f'<h2 style="color: {sh_color};">₹ {res["shortfall"]:,}</h2>', unsafe_allow_html=True)
                
                if res["legacy_amount"] > 0:
                    st.write(f"പിന്തലമുറയ്ക്ക്:")
                    st.markdown(f'<h2 class="result-text">₹ {res["legacy_amount"]:,}</h2>', unsafe_allow_html=True)

            st.divider()

            if res["shortfall"] > 0:
                st.warning("അധിക നിക്ഷേപം ആവശ്യമാണ്:")
                st.markdown(f"🔹 **മാസ നിക്ഷേപം:** <span class='result-text'>₹ {res['req_sip']:,}</span>", unsafe_allow_html=True)
                st.markdown(f"🔹 **അല്ലെങ്കിൽ lumpsum ഇന്ന്:** <span class='result-text'>₹ {res['req_lumpsum']:,}</span>", unsafe_allow_html=True)
            else:
                st.success("✅ ലക്ഷ്യം പൂർത്തിയാകും!")

            # Yearly Schedule
            st.markdown("---")
            st.markdown(f"### 📅 ഓരോ വർഷവും പിൻവലിക്കേണ്ട തുക")
            st.markdown(f"**കാലം:** പ്രായം {int(retire_age)} മുതൽ {int(life_exp)} വരെ")
            
            withdrawal_df = pd.DataFrame(res["annual_withdrawals"])
            
            st.dataframe(
                withdrawal_df,
                use_container_width=True,
                column_config={
                    "പ്രായം": st.column_config.NumberColumn("പ്രായം", format="%d"),
                    "വർഷം": st.column_config.NumberColumn("വർഷം", format="%d"),
                    "വർഷിക പിൻവലിക്കൽ": st.column_config.NumberColumn("വർഷിക പിൻവലിക്കൽ", format="₹ %,d"),
                    "മാസിക തുക": st.column_config.NumberColumn("മാസിക തുക", format="₹ %,d")
                },
                hide_index=True
            )
            
            st.markdown("#### 📈 വർഷം തോറുള്ള മാറ്റം")
            st.line_chart(
                withdrawal_df.set_index("പ്രായം")["വർഷിക പിൻവലിക്കൽ"],
                color="#22C55E",
                use_container_width=True
            )
            
            st.markdown("#### 📊 സംക്ഷിപ്തം")
            col_stats1, col_stats2, col_stats3 = st.columns(3)
            col_stats1.metric("മൊത്തം വർഷം", f"{res['ret_years']}")
            col_stats2.metric("ആദ്യവർഷ പിൻവലിക്കൽ", f"₹ {res['annual_withdrawals'][0]['വർഷിക പിൻവലിക്കൽ']:,}")
            col_stats3.metric("അവസാനവർഷ പിൻവലിക്കൽ", f"₹ {res['annual_withdrawals'][-1]['വർഷിക പിൻവലിക്കൽ']:,}")
            
            st.markdown(f'<span class="quote-text">{random.choice(all_quotes)}</span>', unsafe_allow_html=True)

st.markdown("<p style='text-align: center; font-size: 0.8em; color: #9CA3AF;'>* അനുമാനങ്ങളെ അടിസ്ഥാനമാക്കിയുള്ളത്. മാർക്കറ്റ് റിസ്കുകൾ ബാധകം.</p>", unsafe_allow_html=True)

# ✅ FIXED: CSV Download (Excel-ന് പകരം, openpyxl ഇല്ലാത്ത പ്രശ്നം പരിഹരിക്കാൻ)
if 'res' in st.session_state and st.session_state.res is not None:
    # Create CSV instead of Excel
    csv_data = []
    
    # Summary section
    csv_data.append(["ഇൻപുട്ട് വിവരങ്ങൾ"])
    csv_data.append(["പരാമീറ്റർ", "മൂല്യം"])
    csv_data.append(["നിലവിലെ പ്രായം", current_age])
    csv_data.append(["വിരമിക്കൽ പ്രായം", retire_age])
    csv_data.append(["പ്രതീക്ഷിക്കുന്ന ആയുസ്സ്", life_exp])
    csv_data.append(["പ്രതിമാസ ചെലവ് (₹)", current_expense])
    csv_data.append(["വിലക്കയറ്റം (%)", inf_rate])
    csv_data.append(["നിലവിലെ സമ്പാദ്യം (₹)", existing_corp])
    csv_data.append(["മാസ നിക്ഷേപം - SIP (₹)", current_sip])
    csv_data.append(["വിരമിക്കൽ വരെയുള്ള returns (%)", pre_ret_rate])
    csv_data.append(["വിരമിച്ച ശേഷമുള്ള returns (%)", post_ret_rate])
    csv_data.append(["പിന്തലമുറയ്ക്ക് തുക (₹)", legacy_amount])
    csv_data.append([])
    
    csv_data.append(["ഫലങ്ങൾ"])
    csv_data.append(["കണക്ക്", "തുക (₹)"])
    csv_data.append(["വിരമിക്കുമ്പോഴത്തെ പ്രതിമാസ ചെലവ്", st.session_state.res['future_exp']])
    csv_data.append(["വാർഷിക പിൻവലിക്കൽ", st.session_state.res['future_exp'] * 12])
    csv_data.append(["ആവശ്യമായ റിട്ടയർമെന്റ് കോർപസ്", st.session_state.res['corp_req']])
    csv_data.append(["കണക്കാക്കപ്പെട്ട സമ്പാദ്യം", st.session_state.res['total_sav']])
    csv_data.append(["കുറവ്", st.session_state.res['shortfall']])
    csv_data.append(["അധിക SIP ആവശ്യം", st.session_state.res['req_sip']])
    csv_data.append(["അധിക lumpsum ആവശ്യം", st.session_state.res['req_lumpsum']])
    csv_data.append([])
    
    # Yearly schedule
    if 'annual_withdrawals' in st.session_state.res:
        csv_data.append(["വാർഷിക പിൻവലിക്കൽ ഷെഡ്യൂൾ"])
        csv_data.append(["പ്രായം", "വർഷം", "വർഷിക പിൻവലിക്കൽ (₹)", "മാസിക തുക (₹)"])
        for row in st.session_state.res['annual_withdrawals']:
            csv_data.append([row["പ്രായം"], row["വർഷം"], row["വർഷിക പിൻവലിക്കൽ"], row["മാസിക തുക"]])
    
    # Create CSV
    csv_buffer = io.StringIO()
    for row in csv_data:
        csv_buffer.write(",".join([str(cell) for cell in row]) + "\n")
    csv_data = csv_buffer.getvalue()
    
    st.download_button(
        label="📥 ഫലങ്ങൾ CSV ആയി ഡൗൺലോഡ് ചെയ്യുക",
        data=csv_data.encode('utf-8'),
        file_name=f"retirement_plan_{current_age}_{date.today().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
