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
    
    # Additional SIP/Lumpsum needed to cover shortfall
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
    
    # Developer Branding
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

    st.info("The legacy amount entered will be preserved and provided to your heirs at its full inflation-adjusted value at the end of the plan period.")

    if st.button("Calculate"):
        res = calculate_retirement_final(c_age, r_age, l_exp, c_exp, inf, current_sip, existing_sav, pre_r, post_r, legacy)
        
        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("Required Corpus Fund", f"₹ {res['corp_req']:,}")
        m2.metric("Projected Total Savings", f"₹ {res['total_sav']:,}")
        m3.metric("Shortfall (Gap)", f"₹ {res['shortfall']:,}")
        
        if res['shortfall'] > 0:
            st.error(f"To bridge the shortfall of ₹ {res['shortfall']:,}, you need an additional SIP of ₹ {res['req_sip']:,} or a Lumpsum of ₹ {res['req_lumpsum']:,}")
        
        st.write("### Yearly Cashflow Schedule")
        df = pd.DataFrame(res["annual_withdrawals"])
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Excel Export with Enhanced Branding & Professional Design
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            worksheet = workbook.add_worksheet('Retirement Plan')
            
            # --- FORMAL FORMATS ---
            main_title_fmt = workbook.add_format({'bold': True, 'bg_color': '#1E5128', 'font_color': 'white', 'border': 2, 'align': 'center', 'valign': 'vcenter', 'font_size': 14})
            branding_fmt = workbook.add_format({'bold': True, 'italic': True, 'font_color': '#1E5128', 'align': 'center', 'valign': 'vcenter', 'font_size': 11})
            section_header_fmt = workbook.add_format({'bold': True, 'bg_color': '#4E9F3D', 'font_color': 'white', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
            label_fmt = workbook.add_format({'bold': True, 'border': 1, 'align': 'left', 'valign': 'vcenter', 'bg_color': '#F1F8E8'})
            value_fmt = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
            currency_fmt = workbook.add_format({'num_format': '₹#,##0', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
            description_fmt = workbook.add_format({'font_size': 9, 'italic': True, 'text_wrap': True, 'border': 1, 'align': 'left', 'valign': 'vcenter'})
            
            # --- HEADER SECTION ---
            worksheet.merge_range('A1:G2', "RETIREMENT FINANCIAL STRATEGY REPORT", main_title_fmt)
            worksheet.merge_range('A3:G3', f"This professional report was prepared for {user_name} by developer Shamsudeen Abdulla", branding_fmt)
            worksheet.write('A4', f"Report Date: {date.today()}", value_fmt)
            
            # --- CATEGORY 1: INVESTMENT INPUTS ---
            worksheet.merge_range('A6:C6', "1. INVESTMENT INPUT PARAMETERS", section_header_fmt)
            worksheet.write('A7', 'Parameter', section_header_fmt)
            worksheet.write('B7', 'Value', section_header_fmt)
            worksheet.write('C7', 'Financial Description', section_header_fmt)
            
            inputs = [
                ["Current Age", c_age, "The current age of the investor today."],
                ["Retirement Age", r_age, "The age at which the investor plans to retire from active work."],
                ["Life Expectancy", l_exp, "The total expected life span for which the fund is designed."],
                ["Monthly Expense (Today)", c_exp, "Monthly lifestyle expenses calculated in today's currency value."],
                ["Inflation Rate (%)", f"{inf}%", "The expected annual increase in the cost of goods and services."],
                ["Pre-Retirement Return (%)", f"{pre_r}%", "Expected annual return on investments until the retirement date."],
                ["Post-Retirement Return (%)", f"{post_r}%", "Expected annual return on safe assets during the retirement phase."],
                ["Existing Savings", existing_sav, "The lumpsum amount already saved for this financial goal."],
                ["Current Monthly SIP", current_sip, "Ongoing monthly systematic investment toward retirement."],
                ["Legacy (Today's Value)", legacy, "Desired wealth for heirs, measured in today's purchasing power."]
            ]
            
            for i, (p, v, d) in enumerate(inputs, start=7):
                worksheet.write(i, 0, p, label_fmt)
                if isinstance(v, (int, float)) and v > 100: worksheet.write(i, 1, v, currency_fmt)
                else: worksheet.write(i, 1, v, value_fmt)
                worksheet.write(i, 2, d, description_fmt)

            # --- CATEGORY 2: PLAN RESULTS ---
            worksheet.merge_range('E6:G6', "2. COMPREHENSIVE PLAN RESULTS", section_header_fmt)
            worksheet.write('E7', 'Metric', section_header_fmt)
            worksheet.write('F7', 'Value / Amount', section_header_fmt)
            worksheet.write('G7', 'Financial Description', section_header_fmt)
            
            results = [
                ["Required Corpus Fund", res['corp_req'], "Total target wealth needed at the moment of retirement."],
                ["Projected Total Savings", res['total_sav'], "The estimated total wealth based on current savings and SIPs."],
                ["Shortfall (Gap)", res['shortfall'], "The difference between your required corpus and total projected savings."],
                ["Additional Monthly SIP", res['req_sip'], "Extra monthly investment needed to bridge the shortfall gap."],
                ["Additional Lumpsum", res['req_lumpsum'], "A one-time investment required today to reach the goal."],
                ["Legacy Nominal Value", res['legacy_nominal'], "The actual future value available for heirs at the end of the term."],
                ["Total Withdrawn Sum", res['total_withdrawn_sum'], "The cumulative total of all withdrawals made during retirement."]
            ]
            
            for i, (p, v, d) in enumerate(results, start=7):
                worksheet.write(i, 4, p, label_fmt)
                worksheet.write(i, 5, v, currency_fmt)
                worksheet.write(i, 6, d, description_fmt)

            # --- CATEGORY 3: YEARLY SCHEDULE ---
            start_table = 18
            worksheet.merge_range(start_table, 0, start_table, 4, "3. YEARLY WITHDRAWAL & CASHFLOW SCHEDULE", section_header_fmt)
            headers = ["Age", "Year", "Annual Withdrawal", "Monthly Amount", "Remaining Corpus"]
            for col, h in enumerate(headers):
                worksheet.write(start_table + 1, col, h, section_header_fmt)
            
            for i, entry in enumerate(res['annual_withdrawals']):
                row_idx = start_table + 2 + i
                worksheet.write(row_idx, 0, entry['Age'], value_fmt)
                worksheet.write(row_idx, 1, entry['Year'], value_fmt)
                worksheet.write(row_idx, 2, entry['Annual Withdrawal'], currency_fmt)
                worksheet.write(row_idx, 3, entry['Monthly Amount'], currency_fmt)
                worksheet.write(row_idx, 4, entry['Remaining Corpus'], currency_fmt)
            
            # --- COLUMN WIDTHS & ALIGNMENT ---
            worksheet.set_column('A:A', 25)
            worksheet.set_column('B:B', 15)
            worksheet.set_column('C:C', 50)
            worksheet.set_column('D:D', 5) # Spacer
            worksheet.set_column('E:E', 25)
            worksheet.set_column('F:F', 20)
            worksheet.set_column('G:G', 50)

        st.download_button(
            label="📥 Download Professional Excel Report",
            data=output.getvalue(),
            file_name=f"Retirement_Strategy_{user_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

if __name__ == "__main__":
    main()
