import streamlit as st
import pandas as pd
import random
import time
from datetime import date
import io

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Retirement Planner Pro", layout="wide")

# --- CUSTOM CSS (English Only) ---
st.markdown("""<style>
.main { background-color: #0E1116; color: #E5E7EB; }
.stApp { background-color: #0E1116; }
.result-text { color: #22C55E; font-family: 'Courier New', 'Consolas', 'Monaco', monospace; font-weight: bold; }
.result-white { color: white; font-family: 'Courier New', 'Consolas', 'Monaco', monospace; font-weight: bold; }
.result-red { color: #ef4444; font-family: 'Courier New', 'Consolas', 'Monaco', monospace; font-weight: bold; }
.quote-text { color: #22C55E; font-style: italic; font-weight: bold; text-align: center; display: block; margin-top: 20px; }
.stButton>button { background-color: #22C55E; color: white; width: 100%; border: none; font-weight: bold; height: 3.5em; border-radius: 8px; }
.stButton>button:hover { background-color: #16a34a; }
</style>""", unsafe_allow_html=True)

# --- MOTIVATION QUOTES (English) ---
all_quotes = [
    "“Investing is not a one-time decision, it's a lifetime habit.”",
    "“Wealth is not created overnight; it grows steadily.”",
    "“The day you start SIP is the day your future begins.”",
    "“Build wealth with SIP, live with SWP.”",
    "“Start today, for tomorrow.”",
    "“Time in the market beats timing the market.”",
    "“Retirement is not the end, it's a new beginning. Plan well.”"
]

# --- CORE LOGIC (V6 - Legacy Amount Support) ---
def calculate_retirement_final(c_age, r_age, l_exp, c_exp, inf_rate, c_sav, e_corp, pre_ret_r, post_ret_r, legacy_amount):
    """
    Calculate retirement plan with legacy amount support
    legacy_amount: Money left for heirs at life expectancy
    """
    # Timeframes
    years_to_retire = r_age - c_age
    ret_years = l_exp - r_age
    m_to_retire = years_to_retire * 12
    ret_months = ret_years * 12

    # 1. Future Monthly Expense (Unrounded for accuracy)
    future_monthly_exp_raw = c_exp * ((1 + inf_rate/100) ** years_to_retire)
    
    # ✅ FIXED: Consistent rounding - calculate annual first
    base_annual_withdrawal = future_monthly_exp_raw * 12
    base_annual_withdrawal_rounded = round(base_annual_withdrawal)
    future_monthly_exp = round(future_monthly_exp_raw)  # For display

    # 2. Real Rate of Return (Post-Retirement)
    annual_real_rate = ((1 + post_ret_r/100) / (1 + inf_rate/100)) - 1
    monthly_real_rate = (1 + annual_real_rate)**(1/12) - 1

    # 3. Adjusted Corpus Required (Annuity + Legacy)
    if monthly_real_rate != 0:
        # PV of annuity + PV of legacy amount
        corp_req_annuity = base_annual_withdrawal * (1 - (1 + monthly_real_rate) ** (-ret_months)) / monthly_real_rate
        corp_req_legacy = legacy_amount / ((1 + monthly_real_rate) ** ret_months)
        corp_req = corp_req_annuity + corp_req_legacy
    else:
        corp_req = base_annual_withdrawal * ret_months + legacy_amount

    # 4. Projected Savings (Pre-Retirement Growth)
    pre_r_monthly = (1 + pre_ret_r/100)**(1/12) - 1
    
    existing_future = e_corp * ((1 + pre_r_monthly) ** m_to_retire)
    
    if pre_r_monthly > 0:
        sip_future = c_sav * (((1 + pre_r_monthly) ** m_to_retire - 1) / pre_r_monthly) * (1 + pre_r_monthly)
    else:
        sip_future = c_sav * m_to_retire
        
    total_savings = max(0, round(existing_future + sip_future))

    # 5. Shortfall & Additional Requirements
    shortfall = max(0.0, corp_req - total_savings)
    
    req_sip = 0
    req_lumpsum = 0
    if shortfall > 0:
        if m_to_retire > 0:
            if pre_r_monthly > 0:
                req_sip = (shortfall * pre_r_monthly) / (((1 + pre_r_monthly) ** m_to_retire - 1) * (1 + pre_r_monthly))
            else:
                req_sip = shortfall / m_to_retire
            
            req_lumpsum = shortfall / ((1 + pre_r_monthly) ** m_to_retire)

    # ✅ NEW: Yearly withdrawal schedule (consistently calculated)
    annual_withdrawals = []
    for year in range(ret_years):
        age = r_age + year
        withdrawal = base_annual_withdrawal_rounded * ((1 + inf_rate/100) ** year)
        monthly_eq = withdrawal / 12
        
        annual_withdrawals.append({
            "Age": int(age),
            "Year_in_Retirement": year + 1,
            "Annual_Withdrawal": round(withdrawal),
            "Monthly_Equivalent": round(monthly_eq)
        })

    return {
        "future_exp": future_monthly_exp,  # Monthly
        "future_exp_annual": base_annual_withdrawal_rounded,  # Annual
        "corp_req": round(corp_req),
        "total_sav": total_savings,
        "shortfall": round(shortfall),
        "req_sip": round(req_sip),
        "req_lumpsum": round(req_lumpsum),
        "annual_withdrawals": annual_withdrawals,
        "ret_years": ret_years,
        "legacy_amount": legacy_amount  # ✅ NEW: Legacy amount
    }

# --- MAIN APP ---
st.markdown("<h1 style='text-align: center;'>RETIREMENT PLANNER PRO</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #9CA3AF;'>Plan Your Financial Freedom</p>", unsafe_allow_html=True)

# --- INPUT SECTION ---
with st.container():
    st.markdown('<div style="background-color: #1A2233; padding: 25px; border-radius: 10px; border: 1px solid #374151;">', 
                unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 👤 Personal Details")
        current_age = st.number_input("Current Age", value=30, min_value=0, max_value=100, step=1)
        retire_age = st.number_input("Retirement Age", value=60, min_value=current_age+1, max_value=110, step=1)
        life_exp = st.number_input("Life Expectancy", value=85, min_value=retire_age+1, max_value=120, step=1)
        current_expense = st.number_input("Current Monthly Expenses (₹)", value=30000, min_value=1, step=500)

    with col2:
        st.markdown("### 💰 Investment Details")
        inf_rate = st.number_input("Expected Inflation (%)", value=6.0, step=0.1, format="%.1f")
        existing_corp = st.number_input("Existing Corpus (₹)", value=0, min_value=0, step=5000)
        current_sip = st.number_input("Current Monthly SIP (₹)", value=0, min_value=0, step=100)
        pre_ret_rate = st.number_input("Pre-Retirement Return (%)", value=12.0, min_value=0.1, step=0.1, format="%.1f")
        post_ret_rate = st.number_input("Post-Retirement Return (%)", value=8.0, min_value=0.1, step=0.1, format="%.1f")
        st.markdown("")  # Spacing
        legacy_amount = st.number_input("Legacy Amount for Heirs (₹) [Amount left at Life Expectancy]", value=0, min_value=0, step=100000)
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- CALCULATE BUTTON ---
if st.button("CALCULATE RETIREMENT PLAN"):
    # Validation
    if current_age >= retire_age or retire_age >= life_exp:
        st.error("❌ Invalid ages: Retirement Age must be > Current Age and Life Expectancy must be > Retirement Age.")
    elif pre_ret_rate <= 0 or post_ret_rate <= 0:
        st.error("❌ Return rates must be greater than 0%.")
    elif current_expense <= 0:
        st.error("❌ Expenses must be greater than ₹0.")
    else:
        with st.spinner('Analyzing your retirement plan...'):
            time.sleep(1)  # Smooth UX
            
            # ✅ Core calculation
            res = calculate_retirement_final(current_age, retire_age, life_exp, current_expense, 
                                            inf_rate, current_sip, existing_corp, 
                                            pre_ret_rate, post_ret_rate, legacy_amount)
            
            st.divider()
            
            # --- MAIN RESULTS (2 columns) ---
            r1, r2 = st.columns(2)
            with r1:
                st.write(f"**Monthly Expense at Age {int(retire_age)}:**")
                st.markdown(f'<h2 class="result-text">₹ {res["future_exp"]:,}</h2>', unsafe_allow_html=True)
                
                st.write(f"**Yearly Withdrawal Needed (at Retirement):**")
                st.markdown(f'<h2 class="result-text">₹ {res["future_exp_annual"]:,}</h2>', unsafe_allow_html=True)
                
                st.write(f"**Required Retirement Corpus:**")
                st.markdown(f'<h2 class="result-text">₹ {res["corp_req"]:,}</h2>', unsafe_allow_html=True)

            with r2:
                st.write(f"**Projected Savings at Retirement:**")
                st.markdown(f'<h2 class="result-white">₹ {res["total_sav"]:,}</h2>', unsafe_allow_html=True)
                
                st.write(f"**Shortfall:**")
                sh_color_class = "result-text" if res["shortfall"] <= 0 else "result-red"
                st.markdown(f'<h2 class="{sh_color_class}">₹ {res["shortfall"]:,}</h2>', unsafe_allow_html=True)
                
                # ✅ NEW: Legacy amount display
                if res["legacy_amount"] > 0:
                    st.write(f"**Legacy Amount for Heirs:**")
                    st.markdown(f'<h2 class="result-text">₹ {res["legacy_amount"]:,}</h2>', unsafe_allow_html=True)

            st.divider()

            # --- ACTION ITEMS ---
            if res["shortfall"] > 0:
                st.warning("⚠️ To meet your retirement goals, you need additional investment:")
                st.markdown(f"🔹 **Additional Monthly SIP:** <span class='result-text'>₹ {res['req_sip']:,}</span>", unsafe_allow_html=True)
                st.markdown(f"🔹 **OR Additional Lumpsum (Today):** <span class='result-text'>₹ {res['req_lumpsum']:,}</span>", unsafe_allow_html=True)
            else:
                st.success("✅ Congratulations! Your current investments are sufficient for retirement.")

            # ✅ NEW: YEARLY WITHDRAWAL SCHEDULE ---
            st.markdown("---")
            st.markdown(f"### 📅 **Yearly Withdrawal Schedule (Inflation-Adjusted)**")
            st.markdown(f"**Period:** Age {int(retire_age)} to {int(life_exp)} ({res['ret_years']} years)")
            
            withdrawal_df = pd.DataFrame(res["annual_withdrawals"])
            
            # ✅ Display table (Streamlit native formatting)
            try:
                st.dataframe(
                    withdrawal_df,
                    use_container_width=True,
                    column_config={
                        "Age": st.column_config.NumberColumn("Age", format="%d"),
                        "Year_in_Retirement": st.column_config.NumberColumn("Year", format="%d"),
                        "Annual_Withdrawal": st.column_config.NumberColumn("Annual Withdrawal", format="₹ %,d"),
                        "Monthly_Equivalent": st.column_config.NumberColumn("Monthly Equivalent", format="₹ %,d")
                    },
                    hide_index=True
                )
            except Exception as e:
                st.error("⚠️ Could not display formatted table. Showing raw data.")
                st.write(withdrawal_df)
            
            # ✅ Chart
            st.markdown("#### 📈 Withdrawal Growth Chart")
            try:
                st.line_chart(
                    withdrawal_df.set_index("Age")["Annual_Withdrawal"],
                    color="#22C55E",
                    use_container_width=True
                )
            except:
                st.info("Chart cannot be displayed.")
            
            # ✅ Summary statistics
            st.markdown("#### 📊 Summary Statistics")
            col_stats1, col_stats2, col_stats3 = st.columns(3)
            with col_stats1:
                st.metric("Total Withdrawal Years", f"{res['ret_years']}")
            with col_stats2:
                st.metric("First Year Withdrawal", f"₹ {res['annual_withdrawals'][0]['Annual_Withdrawal']:,}")
            with col_stats3:
                st.metric("Last Year Withdrawal", f"₹ {res['annual_withdrawals'][-1]['Annual_Withdrawal']:,}")
            
            # Random quote
            st.markdown(f'<span class="quote-text">{random.choice(all_quotes)}</span>', unsafe_allow_html=True)

# --- DOWNLOAD FULL RESULTS (Excel) ---
# ✅ NEW: Prepare comprehensive Excel download
if 'res' in locals() and st.button("📥 DOWNLOAD FULL RESULTS (EXCEL)"):
    # Create a comprehensive Excel file
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet 1: Summary
        summary_data = {
            'Parameter': [
                'Current Age', 'Retirement Age', 'Life Expectancy',
                'Current Monthly Expenses', 'Expected Inflation (%)',
                'Existing Corpus', 'Current Monthly SIP',
                'Pre-Retirement Return (%)', 'Post-Retirement Return (%)',
                'Legacy Amount for Heirs'
            ],
            'Value': [
                current_age, retire_age, life_exp,
                f"₹ {current_expense:,}", inf_rate,
                f"₹ {existing_corp:,}", f"₹ {current_sip:,}",
                pre_ret_rate, post_ret_rate,
                f"₹ {res['legacy_amount']:,}"
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        
        results_data = {
            'Metric': [
                'Monthly Expense at Retirement',
                'Yearly Withdrawal at Retirement',
                'Required Retirement Corpus',
                'Projected Savings at Retirement',
                'Shortfall',
                'Additional Monthly SIP Needed',
                'Additional Lumpsum Needed'
            ],
            'Amount (₹)': [
                res['future_exp'],
                res['future_exp_annual'],
                res['corp_req'],
                res['total_sav'],
                res['shortfall'],
                res['req_sip'],
                res['req_lumpsum']
            ]
        }
        results_df = pd.DataFrame(results_data)
        
        # Combine into one sheet
        summary_df.to_excel(writer, sheet_name='Summary', index=False, startrow=0)
        results_df.to_excel(writer, sheet_name='Summary', index=False, startrow=len(summary_df) + 3)
        
        # Sheet 2: Yearly Withdrawal Schedule
        withdrawal_df = pd.DataFrame(res['annual_withdrawals'])
        withdrawal_df.to_excel(writer, sheet_name='Withdrawal Schedule', index=False)
    
    # Download button
    excel_data = output.getvalue()
    st.download_button(
        label="📥 Click to Download Excel File",
        data=excel_data,
        file_name=f"retirement_plan_age_{current_age}_{date.today().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# --- FOOTER ---
st.markdown("<p style='text-align: center; font-size: 0.8em; color: #9CA3AF; margin-top: 30px;'>* Results based on provided assumptions. Market risks apply. Consult a financial advisor.</p>", unsafe_allow_html=True)
