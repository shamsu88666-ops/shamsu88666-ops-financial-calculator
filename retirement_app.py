import streamlit as st
import pandas as pd
import random
import time
from datetime import date
import io
import csv

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

    # Yearly withdrawal schedule
    annual_withdrawals = []
    base_annual_rounded = round(base_annual_withdrawal)
    
    for year in range(ret_years):
        age = r_age + year
        withdrawal = base_annual_rounded * ((1 + inf_rate/100) ** year)
        monthly_eq = withdrawal / 12
        
        annual_withdrawals.append({
            "Age": int(age),
            "Year": year + 1,
            "Annual Withdrawal": round(withdrawal),
            "Monthly Amount": round(monthly_eq)
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
    
    # Legacy input
    st.markdown("### 🏦 Legacy Planning")
    legacy_amount = st.number_input("Legacy Amount (₹)", value=0, min_value=0, step=100000, 
                                    help="The amount you wish to leave for the next generation")

st.markdown('</div>', unsafe_allow_html=True)

if st.button("Calculate"):
    # Validation
    validation_errors = []
    if current_age >= retire_age:
        validation_errors.append("Current age must be less than retirement age")
    if retire_age >= life_exp:
        validation_errors.append("Retirement age must be less than life expectancy")
    if pre_ret_rate <= 0 or post_ret_rate <= 0:
        validation_errors.append("Returns must be greater than 0%")
    if current_expense <= 0:
        validation_errors.append("Expense must be greater than 0")
    
    if validation_errors:
        for error in validation_errors:
            st.error(f"❌ {error}")
        st.session_state.res = None
    else:
        with st.spinner('Calculating Plan...'):
            time.sleep(1)
            res = calculate_retirement_final(current_age, retire_age, life_exp, current_expense, 
                                            inf_rate, current_sip, existing_corp, 
                                            pre_ret_rate, post_ret_rate, legacy_amount)
            
            st.session_state.res = res
            
            st.divider()
            
            # Results display
            r1, r2 = st.columns(2)
            with r1:
                st.write(f"Monthly Expense at Retirement:")
                st.markdown(f'<h2 class="result-text">₹ {res["future_exp"]:,}</h2>', unsafe_allow_html=True)
                
                st.write(f"Required Retirement Corpus:")
                st.markdown(f'<h2 class="result-text">₹ {res["corp_req"]:,}</h2>', unsafe_allow_html=True)

            with r2:
                st.write(f"Projected Savings:")
                st.markdown(f'<h2 style="color: white;">₹ {res["total_sav"]:,}</h2>', unsafe_allow_html=True)
                
                st.write(f"Shortfall:")
                sh_color = "#22C55E" if res["shortfall"] <= 0 else "#ef4444"
                st.markdown(f'<h2 style="color: {sh_color};">₹ {res["shortfall"]:,}</h2>', unsafe_allow_html=True)
                
                if res["legacy_amount"] > 0:
                    st.write(f"Legacy for Next Gen:")
                    st.markdown(f'<h2 class="result-text">₹ {res["legacy_amount"]:,}</h2>', unsafe_allow_html=True)

            st.divider()

            if res["shortfall"] > 0:
                st.warning("Additional Investment Required:")
                st.markdown(f"🔹 **Monthly SIP:** <span class='result-text'>₹ {res['req_sip']:,}</span>", unsafe_allow_html=True)
                st.markdown(f"🔹 **OR Lumpsum Today:** <span class='result-text'>₹ {res['req_lumpsum']:,}</span>", unsafe_allow_html=True)
            else:
                st.success("✅ Goal will be achieved!")

            # Yearly Schedule
            st.markdown("---")
            st.markdown(f"### 📅 Yearly Withdrawal Schedule")
            st.markdown(f"**Period:** From Age {int(retire_age)} to {int(life_exp)}")
            
            withdrawal_df = pd.DataFrame(res["annual_withdrawals"])
            
            st.dataframe(
                withdrawal_df,
                use_container_width=True,
                column_config={
                    "Age": st.column_config.NumberColumn("Age", format="%d"),
                    "Year": st.column_config.NumberColumn("Year", format="%d"),
                    "Annual Withdrawal": st.column_config.NumberColumn("Annual Withdrawal", format="₹ %,d"),
                    "Monthly Amount": st.column_config.NumberColumn("Monthly Amount", format="₹ %,d")
                },
                hide_index=True
            )
            
            st.markdown("#### 📈 Year-on-Year Trend")
            st.line_chart(
                withdrawal_df.set_index("Age")["Annual Withdrawal"],
                color="#22C55E",
                use_container_width=True
            )
            
            st.markdown("#### 📊 Summary Statistics")
            col_stats1, col_stats2, col_stats3 = st.columns(3)
            col_stats1.metric("Total Years", f"{res['ret_years']}")
            col_stats2.metric("First Year Withdrawal", f"₹ {res['annual_withdrawals'][0]['Annual Withdrawal']:,}")
            col_stats3.metric("Final Year Withdrawal", f"₹ {res['annual_withdrawals'][-1]['Annual Withdrawal']:,}")
            
            st.markdown(f'<span class="quote-text">{random.choice(all_quotes)}</span>', unsafe_allow_html=True)

st.markdown("<p style='text-align: center; font-size: 0.8em; color: #9CA3AF;'>* Based on assumptions. Market risks apply.</p>", unsafe_allow_html=True)

# ✅ FIXED: CSV Download - Removed manual BOM, using utf-8-sig encoding only
if 'res' in st.session_state and st.session_state.res is not None:
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Summary section
    writer.writerow(["Input Information"])
    writer.writerow(["Parameter", "Value"])
    writer.writerow(["Current Age", current_age])
    writer.writerow(["Retirement Age", retire_age])
    writer.writerow(["Life Expectancy", life_exp])
    writer.writerow(["Monthly Expense (₹)", current_expense])
    writer.writerow(["Inflation Rate (%)", inf_rate])
    writer.writerow(["Existing Savings (₹)", existing_corp])
    writer.writerow(["Monthly SIP (₹)", current_sip])
    writer.writerow(["Pre-retirement Returns (%)", pre_ret_rate])
    writer.writerow(["Post-retirement Returns (%)", post_ret_rate])
    writer.writerow(["Legacy Amount (₹)", legacy_amount])
    writer.writerow([])
    
    writer.writerow(["Results"])
    writer.writerow(["Metric", "Amount (₹)"])
    writer.writerow(["Monthly Expense at Retirement", st.session_state.res['future_exp']])
    writer.writerow(["Annual Withdrawal", st.session_state.res['future_exp'] * 12])
    writer.writerow(["Required Retirement Corpus", st.session_state.res['corp_req']])
    writer.writerow(["Projected Savings", st.session_state.res['total_sav']])
    writer.writerow(["Shortfall", st.session_state.res['shortfall']])
    writer.writerow(["Additional SIP Required", st.session_state.res['req_sip']])
    writer.writerow(["Additional Lumpsum Required", st.session_state.res['req_lumpsum']])
    writer.writerow([])
    
    # Yearly schedule
    if 'annual_withdrawals' in st.session_state.res:
        writer.writerow(["Yearly Withdrawal Schedule"])
        writer.writerow(["Age", "Year", "Annual Withdrawal (₹)", "Monthly Amount (₹)"])
        for row in st.session_state.res['annual_withdrawals']:
            writer.writerow([row["Age"], row["Year"], row["Annual Withdrawal"], row["Monthly Amount"]])
    
    csv_data = output.getvalue()
    output.close()  # Added proper cleanup
    
    st.download_button(
        label="📥 Download Results as CSV",
        data=csv_data.encode('utf-8-sig'),  # BOM handled by encoding
        file_name=f"retirement_plan_{current_age}_{date.today().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
