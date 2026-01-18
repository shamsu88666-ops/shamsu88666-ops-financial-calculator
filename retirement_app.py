import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import date

# --- CORE CALCULATION ENGINE (100% MATCHED WITH SWP) ---
def calculate_retirement_final(c_age, r_age, l_exp, c_exp, inf_rate, c_sip, e_corp, pre_ret_r, post_ret_r, legacy_amount_real):
    months_to_retire = (r_age - c_age) * 12
    retirement_years = l_exp - r_age
    retirement_months = retirement_years * 12
    
    # Monthly Rates
    monthly_inf = (1 + inf_rate/100) ** (1/12) - 1
    monthly_pre_ret = (1 + pre_ret_r/100) ** (1/12) - 1
    monthly_post_ret = (1 + post_ret_r/100) ** (1/12) - 1
    
    # 1. Expense at Retirement (Year 1 Monthly)
    expense_at_retirement = round(c_exp * (1 + inf_rate/100) ** (months_to_retire/12))
    
    # 2. Required Corpus Calculation (Simulating exactly like SWP to find corpus)
    # We use a goal-seeking approach or direct annuity due with step-up
    legacy_nominal = legacy_amount_real * (1 + inf_rate/100) ** ((r_age + retirement_years - c_age))
    
    # Annuity Due with Inflation Step-up Factor
    real_rate_annual = (1 + post_ret_r/100) / (1 + inf_rate/100) - 1
    
    # Simplified required corpus logic to match SWP's month-by-month depletion
    def simulate_swp(test_corp):
        bal = test_corp
        for y in range(retirement_years):
            m_exp = round(expense_at_retirement * (1 + inf_rate/100) ** y)
            for m in range(12):
                if bal > 0:
                    bal -= m_exp
                    bal *= (1 + monthly_post_ret)
        return bal

    # Finding the exact required corpus
    low = 0
    high = 1000000000 # 100 Cr limit
    for _ in range(40): # Binary search for precision
        mid = (low + high) / 2
        if simulate_swp(mid) < legacy_nominal:
            low = mid
        else:
            high = mid
    
    corp_req = round(high)
    
    # 3. Pre-retirement Growth
    future_existing = e_corp * (1 + monthly_pre_ret) ** months_to_retire
    if monthly_pre_ret > 0:
        future_sip = c_sip * (((1 + monthly_pre_ret) ** months_to_retire - 1) / monthly_pre_ret) * (1 + monthly_pre_ret)
    else:
        future_sip = c_sip * months_to_retire
        
    total_savings = future_existing + future_sip
    shortfall = max(0, corp_req - total_savings)
    
    # Additional SIP/Lumpsum
    req_sip = 0
    req_lumpsum = 0
    if shortfall > 0:
        req_sip = (shortfall * monthly_pre_ret) / (((1 + monthly_pre_ret) ** months_to_retire - 1) * (1 + monthly_pre_ret))
        req_lumpsum = shortfall / ((1 + monthly_pre_ret) ** months_to_retire)
    
    # 4. Generate Year-by-Year Schedule (Exact SWP Logic)
    annual_withdrawals = []
    current_balance = corp_req
    total_withdrawn_sum = 0
    
    for year in range(1, retirement_years + 1):
        monthly_expense_this_year = round(expense_at_retirement * (1 + inf_rate/100) ** (year - 1))
        yearly_withdrawn = 0
        
        for month in range(12):
            if current_balance > 0:
                withdrawal = min(monthly_expense_this_year, current_balance)
                current_balance -= withdrawal
                current_balance *= (1 + monthly_post_ret)
                yearly_withdrawn += withdrawal
        
        total_withdrawn_sum += yearly_withdrawn
        annual_withdrawals.append({
            "Age": r_age + year - 1,
            "Year": year,
            "Annual Withdrawal": round(yearly_withdrawn),
            "Monthly Amount": round(monthly_expense_this_year),
            "Remaining Corpus": round(max(0, current_balance))
        })
        
    return {
        "future_exp": expense_at_retirement,
        "corp_req": corp_req,
        "total_sav": round(total_savings),
        "shortfall": round(shortfall),
        "req_sip": round(req_sip),
        "req_lumpsum": round(req_lumpsum),
        "legacy_nominal": round(legacy_nominal),
        "annual_withdrawals": annual_withdrawals,
        "total_withdrawn_sum": round(total_withdrawn_sum)
    }

# --- UI PART ---
def main():
    st.markdown("<h1 style='text-align: center;'>Retirement Planner (Synced Edition)</h1>", unsafe_allow_html=True)
    
    # Developer Contact Buttons
    st.markdown(f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <p style="margin-bottom: 10px;">Developed by <b>Shamsudeen Abdulla</b></p>
            <a href="https://wa.me/qr/IOBUQDQMM2X3D1" target="_blank" style="text-decoration: none;">
                <button style="background-color: #25D366; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; margin-right: 10px; font-weight: bold;">WhatsApp</button>
            </a>
            <a href="https://www.facebook.com/shamsudeen.abdulla.2025/" target="_blank" style="text-decoration: none;">
                <button style="background-color: #1877F2; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-weight: bold;">Facebook</button>
            </a>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        user_name = st.text_input("User Name", "Valued User")
        c_age = st.number_input("Current Age", 30)
        r_age = st.number_input("Retirement Age", 60)
        l_exp = st.number_input("Life Expectancy", 85)
        c_exp = st.number_input("Monthly Expense", 30000)
    with col2:
        inf = st.number_input("Inflation (%)", 7.0)
        pre_r = st.number_input("Pre-Ret Return (%)", 12.0)
        post_r = st.number_input("Post-Ret Return (%)", 8.0)
        legacy = st.number_input("Legacy (Today's Value)", 0)
        existing_sav = st.number_input("Existing Savings", 0)
        current_sip = st.number_input("Current SIP", 0)

    if st.button("Calculate"):
        res = calculate_retirement_final(c_age, r_age, l_exp, c_exp, inf, current_sip, existing_sav, pre_r, post_r, legacy)
        
        st.divider()
        # Metrics including Legacy Nominal Value
        m1, m2 = st.columns(2)
        m1.metric("Required Corpus Fund", f"₹ {res['corp_req']:,}")
        m2.metric("Total Withdrawn Amount", f"₹ {res['total_withdrawn_sum']:,}")
        
        m3, m4 = st.columns(2)
        m3.metric("Legacy Nominal Value", f"₹ {res['legacy_nominal']:,}")
        m4.metric("Shortfall", f"₹ {res['shortfall']:,}")
        
        st.write("### Yearly Breakdown")
        df = pd.DataFrame(res["annual_withdrawals"])
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Excel Export with Professional Formatting
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            worksheet = workbook.add_worksheet('Retirement Plan')
            
            # Formats
            header_fmt = workbook.add_format({'bold': True, 'bg_color': '#22C55E', 'font_color': 'white', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
            data_fmt = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
            currency_fmt = workbook.add_format({'num_format': '₹#,##0', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
            disclaimer_fmt = workbook.add_format({'italic': True, 'font_color': 'red', 'text_wrap': True, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
            
            # Disclaimer
            worksheet.merge_range('A1:E3', "DISCLAIMER: This report is generated based on basic mathematics. Practical results may vary. Your financial planning should not be based solely on this report.", disclaimer_fmt)
            
            # Title
            worksheet.merge_range('A5:E5', f"RETIREMENT PLAN REPORT - {user_name.upper()}", header_fmt)
            
            # Parameters & Summary
            worksheet.write('A7', 'INPUT PARAMETERS', header_fmt)
            worksheet.write('B7', 'VALUE', header_fmt)
            worksheet.write('D7', 'RESULTS SUMMARY', header_fmt)
            worksheet.write('E7', 'AMOUNT', header_fmt)
            
            inputs = [["Current Age", c_age], ["Retirement Age", r_age], ["Life Expectancy", l_exp], ["Monthly Expense", c_exp], ["Inflation Rate", inf]]
            summary = [["Required Corpus", res['corp_req']], ["Total Withdrawn", res['total_withdrawn_sum']], ["Legacy Nominal", res['legacy_nominal']], ["Shortfall", res['shortfall']]]
            
            for i, (label, val) in enumerate(inputs, start=7):
                worksheet.write(i+1, 0, label, data_fmt)
                worksheet.write(i+1, 1, val, data_fmt)
            for i, (label, val) in enumerate(summary, start=7):
                worksheet.write(i+1, 3, label, data_fmt)
                worksheet.write(i+1, 4, val, currency_fmt)

            # Yearly Table
            worksheet.merge_range('A14:E14', 'YEARLY CASHFLOW SCHEDULE', header_fmt)
            table_headers = ["Age", "Year", "Annual Withdrawal", "Monthly Amount", "Remaining Corpus"]
            for col, h in enumerate(table_headers):
                worksheet.write(14, col, h, header_fmt)
            
            for row, entry in enumerate(res['annual_withdrawals'], start=15):
                worksheet.write(row, 0, entry['Age'], data_fmt)
                worksheet.write(row, 1, entry['Year'], data_fmt)
                worksheet.write(row, 2, entry['Annual Withdrawal'], currency_fmt)
                worksheet.write(row, 3, entry['Monthly Amount'], currency_fmt)
                worksheet.write(row, 4, entry['Remaining Corpus'], currency_fmt)
            
            worksheet.set_column('A:E', 25) # Adjust column width

        st.download_button(
            label="📥 Download Professional Excel Report",
            data=output.getvalue(),
            file_name=f"Retirement_Plan_{user_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

if __name__ == "__main__":
    main()
