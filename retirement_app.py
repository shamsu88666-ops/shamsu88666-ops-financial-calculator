import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import date

# --- CORE CALCULATION ENGINE (100% MATCHED WITH SWP) ---
def calculate_retirement_final(c_age, r_age, l_exp, c_exp, inf_rate, c_sip, e_corp, pre_ret_r, post_ret_r, legacy_amount_real):
    months_to_retire = (r_age - c_age) * 12
    retirement_years = l_exp - r_age
    
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
        
    total_projected_savings = future_existing + future_sip
    shortfall = max(0, corp_req - total_projected_savings)
    
    # Additional SIP/Lumpsum needed
    req_extra_sip = 0
    req_extra_lumpsum = 0
    if shortfall > 0:
        if monthly_pre_ret > 0:
            req_extra_sip = (shortfall * monthly_pre_ret) / (((1 + monthly_pre_ret) ** months_to_retire - 1) * (1 + monthly_pre_ret))
        else:
            req_extra_sip = shortfall / months_to_retire
        req_extra_lumpsum = shortfall / ((1 + monthly_pre_ret) ** months_to_retire)
    
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
        "total_sav": round(total_projected_savings),
        "shortfall": round(shortfall),
        "req_sip": round(req_extra_sip),
        "req_lumpsum": round(req_extra_lumpsum),
        "legacy_nominal": round(legacy_nominal),
        "annual_withdrawals": annual_withdrawals,
        "total_withdrawn_sum": round(total_withdrawn_sum)
    }

# --- UI PART ---
def main():
    st.markdown("<h1 style='text-align: center;'>Retirement Planner (Synced Edition)</h1>", unsafe_allow_html=True)
    
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
        user_name = st.text_input("User Name", "Valued Client")
        c_age = st.number_input("Current Age", 30)
        r_age = st.number_input("Retirement Age", 60)
        l_exp = st.number_input("Life Expectancy", 85)
        c_exp = st.number_input("Monthly Expense (Today)", 30000)
    with col2:
        inf = st.number_input("Inflation Rate (%)", 7.0)
        pre_r = st.number_input("Pre-Retirement Return (%)", 12.0)
        post_r = st.number_input("Post-Retirement Return (%)", 8.0)
        existing_sav = st.number_input("Existing Savings", 0)
        current_sip = st.number_input("Current Monthly SIP", 0)
        legacy = st.number_input("Legacy (Today's Value)", 0)

    if st.button("Calculate"):
        res = calculate_retirement_final(c_age, r_age, l_exp, c_exp, inf, current_sip, existing_sav, pre_r, post_r, legacy)
        
        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("Required Corpus", f"₹ {res['corp_req']:,}")
        m2.metric("Projected Savings", f"₹ {res['total_sav']:,}")
        m3.metric("Shortfall (Gap)", f"₹ {res['shortfall']:,}")
        
        if res['shortfall'] > 0:
            st.warning(f"To cover the gap, you need additional SIP of ₹ {res['req_sip']:,} or Lumpsum of ₹ {res['req_lumpsum']:,}")
        
        st.write("### Yearly Cashflow Schedule")
        df = pd.DataFrame(res["annual_withdrawals"])
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Excel Export with Enhanced Design
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            worksheet = workbook.add_worksheet('Retirement Plan')
            
            # Formats
            main_header = workbook.add_format({'bold': True, 'bg_color': '#166534', 'font_color': 'white', 'border': 2, 'align': 'center', 'font_size': 14})
            sub_header = workbook.add_format({'bold': True, 'bg_color': '#22C55E', 'font_color': 'white', 'border': 1, 'align': 'center'})
            cell_center = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
            currency_center = workbook.add_format({'num_format': '₹#,##0', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
            desc_text = workbook.add_format({'font_size': 9, 'italic': True, 'text_wrap': True, 'border': 1, 'valign': 'vcenter'})
            dev_info = workbook.add_format({'bold': True, 'italic': True, 'font_color': '#166534', 'align': 'center'})
            
            # Header Section
            worksheet.merge_range('A1:G2', "RETIREMENT FINANCIAL PLAN", main_header)
            worksheet.merge_range('A3:G3', f"Prepared by Shamsudeen Abdulla for {user_name}", dev_info)
            worksheet.write('A4', f"Date: {date.today()}", cell_center)
            
            # Investment Inputs
            worksheet.merge_range('A6:D6', "INVESTMENT INPUT PARAMETERS", sub_header)
            worksheet.write('A7', 'Parameter', sub_header)
            worksheet.write('B7', 'Value', sub_header)
            worksheet.write('C7', 'Financial Description', sub_header)
            
            input_list = [
                ["Current Age", c_age, "User's current age at the beginning of the plan."],
                ["Retirement Age", r_age, "Age at which professional income stops and withdrawals begin."],
                ["Life Expectancy", l_exp, "The total lifespan for which the corpus is intended to last."],
                ["Monthly Expense", c_exp, "Estimated monthly living cost in today's market value."],
                ["Inflation Rate", f"{inf}%", "Annual rate of increase in price levels."],
                ["Pre-Ret Return", f"{pre_r}%", "Expected annual return on investments before retirement."],
                ["Post-Ret Return", f"{post_r}%", "Expected annual return during the retirement phase."],
                ["Existing Savings", existing_sav, "Lumpsum amount already available for retirement."],
                ["Current Monthly SIP", current_sip, "Ongoing monthly systematic investment amount."],
                ["Legacy (Today)", legacy, "Wealth target for heirs in today's currency value."]
            ]
            
            for i, (p, v, d) in enumerate(input_list, start=7):
                worksheet.write(i, 0, p, cell_center)
                if isinstance(v, (int, float)) and v > 100: worksheet.write(i, 1, v, currency_center)
                else: worksheet.write(i, 1, v, cell_center)
                worksheet.write(i, 2, d, desc_text)

            # Plan Results
            worksheet.merge_range('E6:H6', "RETIREMENT PLAN RESULTS", sub_header)
            worksheet.write('E7', 'Metric', sub_header)
            worksheet.write('F7', 'Amount', sub_header)
            worksheet.write('G7', 'Financial Description', sub_header)
            
            result_list = [
                ["Required Corpus", res['corp_req'], "Total fund needed at the point of retirement."],
                ["Projected Savings", res['total_sav'], "Fund accumulated through current savings and SIP."],
                ["Shortfall (Gap)", res['shortfall'], "The deficit between target corpus and projected fund."],
                ["Additional SIP", res['req_sip'], "Extra monthly investment needed to bridge the gap."],
                ["Additional Lumpsum", res['req_lumpsum'], "One-time investment required today to bridge the gap."],
                ["Legacy (Nominal)", res['legacy_nominal'], "Final amount available for heirs after the plan period."],
                ["Total Withdrawn", res['total_withdrawn_sum'], "Total sum spent during the retirement years."]
            ]
            
            for i, (p, v, d) in enumerate(result_list, start=7):
                worksheet.write(i, 4, p, cell_center)
                worksheet.write(i, 5, v, currency_center)
                worksheet.write(i, 6, d, desc_text)

            # Cashflow Schedule
            start_row = 18
            worksheet.merge_range(start_row, 0, start_row, 4, "YEARLY WITHDRAWAL & CASHFLOW SCHEDULE", sub_header)
            table_headers = ["Age", "Year", "Annual Withdrawal", "Monthly Amount", "Remaining Corpus"]
            for col, h in enumerate(table_headers):
                worksheet.write(start_row + 1, col, h, sub_header)
            
            for i, entry in enumerate(res['annual_withdrawals']):
                r = start_row + 2 + i
                worksheet.write(r, 0, entry['Age'], cell_center)
                worksheet.write(r, 1, entry['Year'], cell_center)
                worksheet.write(r, 2, entry['Annual Withdrawal'], currency_center)
                worksheet.write(r, 3, entry['Monthly Amount'], currency_center)
                worksheet.write(r, 4, entry['Remaining Corpus'], currency_center)
            
            # Width and Alignment Adjustments
            worksheet.set_column('A:A', 20)
            worksheet.set_column('B:B', 15)
            worksheet.set_column('C:C', 45)
            worksheet.set_column('E:E', 20)
            worksheet.set_column('F:F', 18)
            worksheet.set_column('G:G', 45)

        st.download_button(
            label="📥 Download Professional Financial Report",
            data=output.getvalue(),
            file_name=f"Retirement_Plan_{user_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

if __name__ == "__main__":
    main()
