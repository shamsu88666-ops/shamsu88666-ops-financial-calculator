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
    legacy_nominal = legacy_amount_real * (1 + inf_rate/100) ** ((r_age + retirement_years - c_age))
    
    def simulate_swp(test_corp):
        bal = test_corp
        for y in range(retirement_years):
            m_exp = round(expense_at_retirement * (1 + inf_rate/100) ** y)
            for m in range(12):
                if bal > 0:
                    bal -= m_exp
                    bal *= (1 + monthly_post_ret)
        return bal

    low = 0
    high = 1000000000 
    for _ in range(40): 
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
    
    # 4. Generate Year-by-Year Schedule
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
        c_age = st.number_input("Current Age", 30, help="Your current age.")
        r_age = st.number_input("Retirement Age", 60, help="Age at which you plan to retire.")
        l_exp = st.number_input("Life Expectancy", 85, help="Planning horizon for your life.")
        c_exp = st.number_input("Monthly Expense (Today's Value)", 30000, help="Average monthly lifestyle cost at today's prices.")

    with col2:
        inf = st.number_input("Inflation Rate (%)", 7.0, help="Expected annual increase in cost of living.")
        pre_r = st.number_input("Pre-Retirement Return (%)", 12.0, help="Expected annual ROI before retirement.")
        post_r = st.number_input("Post-Retirement Return (%)", 8.0, help="Expected annual ROI after retirement.")
        
        # English description for Legacy as requested
        st.info("Enter the amount you wish to leave for your heirs. This amount will be provided to them at its full nominal value at the end of your life expectancy.")
        legacy = st.number_input("Legacy (Today's Value)", 0, help="The target amount for heirs in today's currency value.")
        
        existing_sav = st.number_input("Existing Savings", 0, help="Current corpus already accumulated for retirement.")
        current_sip = st.number_input("Current Monthly SIP", 0, help="Your current monthly investment towards this goal.")

    if st.button("Calculate"):
        res = calculate_retirement_final(c_age, r_age, l_exp, c_exp, inf, current_sip, existing_sav, pre_r, post_r, legacy)
        
        st.divider()
        st.subheader("Financial Analysis Results")
        
        m1, m2 = st.columns(2)
        m1.metric("Required Corpus Fund", f"₹ {res['corp_req']:,}", help="Total wealth needed on the day of retirement.")
        m2.metric("Total Withdrawn Amount", f"₹ {res['total_withdrawn_sum']:,}", help="Total sum of all monthly withdrawals during retirement.")
        
        m3, m4 = st.columns(2)
        m3.metric("Legacy Nominal Value", f"₹ {res['legacy_nominal']:,}", help="The actual future value provided to heirs after inflation.")
        m4.metric("Shortfall (Gap)", f"₹ {res['shortfall']:,}", help="The difference between your required corpus and projected savings.")
        
        st.write("### Yearly Cashflow Schedule")
        df = pd.DataFrame(res["annual_withdrawals"])
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Excel Export
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            worksheet = workbook.add_worksheet('Retirement Plan')
            
            # Formatting
            header_fmt = workbook.add_format({'bold': True, 'bg_color': '#22C55E', 'font_color': 'white', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
            data_fmt = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
            currency_fmt = workbook.add_format({'num_format': '₹#,##0', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
            desc_fmt = workbook.add_format({'font_size': 9, 'italic': True, 'text_wrap': True, 'border': 1, 'align': 'left'})
            disclaimer_fmt = workbook.add_format({'italic': True, 'font_color': 'red', 'text_wrap': True, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
            
            # Disclaimer & Title
            worksheet.merge_range('A1:F3', "DISCLAIMER: This report is based on mathematical simulations. Market returns and inflation are subject to change. Consult a financial advisor for final decisions.", disclaimer_fmt)
            worksheet.merge_range('A5:F5', f"RETIREMENT PLAN REPORT - {user_name.upper()}", header_fmt)
            
            # Header Row
            worksheet.write('A7', 'CATEGORY', header_fmt)
            worksheet.write('B7', 'PARAMETER', header_fmt)
            worksheet.write('C7', 'VALUE', header_fmt)
            worksheet.write('D7', 'FINANCIAL DESCRIPTION', header_fmt)

            # Data sections
            row = 7
            params = [
                ["INPUT", "Current Age", c_age, "User's current age today."],
                ["INPUT", "Retirement Age", r_age, "Target age for stopping professional work."],
                ["INPUT", "Life Expectancy", l_exp, "The age until which financial support is planned."],
                ["INPUT", "Monthly Expense", c_exp, "Monthly cost of living at current market prices."],
                ["INPUT", "Inflation Rate", f"{inf}%", "The rate at which purchasing power decreases annually."],
                ["INPUT", "Pre-Ret Return", f"{pre_r}%", "Expected annual ROI on investments before retirement."],
                ["INPUT", "Post-Ret Return", f"{post_r}%", "Expected annual ROI on safe investments after retirement."],
                ["INPUT", "Legacy (Today)", legacy, "Desired wealth for heirs in today's currency terms."],
                ["RESULT", "Required Corpus", res['corp_req'], "Total target wealth needed at the start of retirement."],
                ["RESULT", "Total Withdrawn", res['total_withdrawn_sum'], "The total cumulative amount spent during retirement years."],
                ["RESULT", "Legacy (Nominal)", res['legacy_nominal'], "Actual amount available for heirs at the end of the term."],
                ["RESULT", "Shortfall (Gap)", res['shortfall'], "The deficit between target corpus and existing projections."]
            ]

            for cat, param, val, desc in params:
                row += 1
                worksheet.write(row, 0, cat, data_fmt)
                worksheet.write(row, 1, param, data_fmt)
                if isinstance(val, (int, float)) and val > 100:
                    worksheet.write(row, 2, val, currency_fmt)
                else:
                    worksheet.write(row, 2, val, data_fmt)
                worksheet.write(row, 3, desc, desc_fmt)

            # Yearly Table
            table_start = row + 3
            worksheet.merge_range(table_start, 0, table_start, 4, 'YEARLY CASHFLOW SCHEDULE (SWP SIMULATION)', header_fmt)
            headers = ["Age", "Year", "Annual Withdrawal", "Monthly Amount", "Remaining Corpus"]
            for col, h in enumerate(headers):
                worksheet.write(table_start + 1, col, h, header_fmt)
            
            for i, entry in enumerate(res['annual_withdrawals']):
                r = table_start + 2 + i
                worksheet.write(r, 0, entry['Age'], data_fmt)
                worksheet.write(r, 1, entry['Year'], data_fmt)
                worksheet.write(r, 2, entry['Annual Withdrawal'], currency_fmt)
                worksheet.write(r, 3, entry['Monthly Amount'], currency_fmt)
                worksheet.write(r, 4, entry['Remaining Corpus'], currency_fmt)
            
            worksheet.set_column('A:B', 20)
            worksheet.set_column('C:C', 18)
            worksheet.set_column('D:D', 50)
            worksheet.set_column('E:F', 20)

        st.download_button(
            label="📥 Download Professional Excel Report",
            data=output.getvalue(),
            file_name=f"Retirement_Plan_{user_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

if __name__ == "__main__":
    main()
