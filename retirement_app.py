import streamlit as st
import pandas as pd
import numpy as np
import io

# --- CORE CALCULATION ENGINE ---
def calculate_retirement_final(c_age, r_age, l_exp, c_exp, inf_rate, c_sip, e_corp, pre_ret_r, post_ret_r, legacy_amount_real):
    months_to_retire = (r_age - c_age) * 12
    retirement_years = l_exp - r_age
    
    monthly_inf = (1 + inf_rate/100) ** (1/12) - 1
    monthly_pre_ret = (1 + pre_ret_r/100) ** (1/12) - 1
    monthly_post_ret = (1 + post_ret_r/100) ** (1/12) - 1
    
    expense_at_retirement = round(c_exp * (1 + inf_rate/100) ** (months_to_retire/12))
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
    high = 5000000000 
    for _ in range(50): 
        mid = (low + high) / 2
        if simulate_swp(mid) < legacy_nominal:
            low = mid
        else:
            high = mid
    
    corp_req = round(high)
    
    future_existing = e_corp * (1 + monthly_pre_ret) ** months_to_retire
    if monthly_pre_ret > 0:
        future_sip = c_sip * (((1 + monthly_pre_ret) ** months_to_retire - 1) / monthly_pre_ret) * (1 + monthly_pre_ret)
    else:
        future_sip = c_sip * months_to_retire
        
    total_projected_savings = future_existing + future_sip
    shortfall = max(0, corp_req - total_projected_savings)
    
    req_extra_sip = 0
    req_extra_lumpsum = 0
    if shortfall > 0:
        if monthly_pre_ret > 0:
            req_extra_sip = (shortfall * monthly_pre_ret) / (((1 + monthly_pre_ret) ** months_to_retire - 1) * (1 + monthly_pre_ret))
        else:
            req_extra_sip = shortfall / months_to_retire
        req_extra_lumpsum = shortfall / ((1 + monthly_pre_ret) ** months_to_retire)
    
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
    st.set_page_config(page_title="Retirement Planner Pro", layout="wide")
    st.markdown("<h1 style='text-align: center;'>Retirement Planner Pro</h1>", unsafe_allow_html=True)
    
    st.markdown(f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <p style="margin-bottom: 10px;">Prepared by <b>Shamsudeen Abdulla</b></p>
            <a href="https://wa.me/qr/IOBUQDQMM2X3D1" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; margin-right: 10px; font-weight: bold;">WhatsApp</button></a>
            <a href="https://www.facebook.com/shamsudeen.abdulla.2025/" target="_blank"><button style="background-color: #1877F2; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-weight: bold;">Facebook</button></a>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        user_name = st.text_input("User Name", "Valued Client")
        c_age = st.number_input("Current Age", min_value=1, max_value=100, value=30)
        r_age = st.number_input("Retirement Age", min_value=c_age+1, max_value=100, value=60)
        l_exp = st.number_input("Life Expectancy", min_value=r_age+1, max_value=120, value=85)
        c_exp = st.number_input("Monthly Expense (Today)", value=30000)
    with col2:
        inf = st.number_input("Inflation Rate (%)", value=7.0)
        pre_r = st.number_input("Pre-Retirement Return (%)", value=12.0)
        post_r = st.number_input("Post-Retirement Return (%)", value=8.0)
        existing_sav = st.number_input("Existing Savings", value=0)
        current_sip = st.number_input("Current Monthly SIP", value=0)
        
        # UI IMPROVEMENT: Clearly displaying Legacy description in UI
        st.info("Legacy (Today's Value): നിങ്ങളുടെ അനന്തരാവകാശികൾക്കായി ഇന്നത്തെ മൂല്യത്തിൽ മാറ്റിവെക്കാൻ ആഗ്രഹിക്കുന്ന തുക.")
        legacy = st.number_input("Legacy Amount", value=0)

    if st.button("Calculate Plan"):
        res = calculate_retirement_final(c_age, r_age, l_exp, c_exp, inf, current_sip, existing_sav, pre_r, post_r, legacy)
        
        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("Required Corpus", f"₹ {res['corp_req']:,}")
        m2.metric("Projected Savings", f"₹ {res['total_sav']:,}")
        m3.metric("Legacy Nominal Value", f"₹ {res['legacy_nominal']:,}")
        
        if res['shortfall'] <= 0:
            st.success(f"🎉 Congratulations {user_name}! Your current savings plan is perfectly on track.")
        else:
            st.error(f"Shortfall: ₹ {res['shortfall']:,}")
            st.warning(f"To reach the goal, you need an additional Monthly SIP of ₹ {res['req_sip']:,} OR a Lumpsum of ₹ {res['req_lumpsum']:,}")
        
        st.write("### Withdrawal Schedule")
        st.dataframe(pd.DataFrame(res["annual_withdrawals"]), use_container_width=True, hide_index=True)

        # Excel Export
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            worksheet = workbook.add_worksheet('Retirement Plan')
            
            # Formats
            disclaimer_fmt = workbook.add_format({'italic': True, 'font_color': 'red', 'text_wrap': True, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 10})
            main_title_fmt = workbook.add_format({'bold': True, 'bg_color': '#1E5128', 'font_color': 'white', 'border': 2, 'align': 'center', 'valign': 'vcenter', 'font_size': 14})
            branding_fmt = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 11})
            section_header_fmt = workbook.add_format({'bold': True, 'bg_color': '#4E9F3D', 'font_color': 'white', 'border': 1, 'align': 'center'})
            cell_center = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
            currency_fmt = workbook.add_format({'num_format': '₹#,##0', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
            desc_fmt = workbook.add_format({'font_size': 9, 'italic': True, 'text_wrap': True, 'border': 1, 'align': 'left'})

            # Full Disclaimer
            disclaimer_text = ("IMPORTANT NOTICE: This report is generated based on basic mathematical calculations and the input values provided by you. "
                               "Your financial planning should not be based solely on this report. The developer (Shamsudeen Abdulla) shall not be held "
                               "responsible for any financial losses or liabilities incurred. Please consult a professional Financial Advisor.")
            worksheet.merge_range('A1:G4', disclaimer_text, disclaimer_fmt)
            
            worksheet.merge_range('A6:G7', "RETIREMENT FINANCIAL STRATEGY REPORT", main_title_fmt)
            worksheet.merge_range('A8:G8', f"Prepared by Shamsudeen Abdulla for {user_name}", branding_fmt)
            
            # Data Rows
            inputs = [
                ["Current Age", c_age, "Investor's current age."],
                ["Retirement Age", r_age, "Target age to stop working."],
                ["Life Expectancy", l_exp, "Total planning horizon."],
                ["Monthly Expense", c_exp, "Cost of living in today's value."],
                ["Inflation Rate", f"{inf}%", "Annual price increase rate."],
                ["Pre-Ret Return", f"{pre_r}%", "ROI before retirement."],
                ["Post-Ret Return", f"{post_r}%", "ROI during retirement."],
                ["Existing Savings", existing_sav, "Lumpsum already available."],
                ["Current Monthly SIP", current_sip, "Ongoing investment."],
                ["Legacy (Today)", legacy, "Desired inheritance for heirs."]
            ]
            
            results = [
                ["Required Corpus", res['corp_req'], "Total fund needed at retirement."],
                ["Projected Savings", res['total_sav'], "Estimated wealth with current plan."],
                ["Shortfall (Gap)", res['shortfall'], "Amount missing to reach goal."],
                ["Extra SIP Needed", res['req_sip'], "Additional SIP to bridge the gap."],
                ["Extra Lumpsum", res['req_lumpsum'], "One-time investment needed."],
                ["Legacy Nominal", res['legacy_nominal'], "Actual amount heirs will get."],
                ["Total Withdrawn", res['total_withdrawn_sum'], "Sum of all life withdrawals."]
            ]

            worksheet.merge_range('A10:C10', "INVESTMENT INPUTS", section_header_fmt)
            worksheet.merge_range('E10:G10', "PLAN RESULTS", section_header_fmt)

            for i, item in enumerate(inputs):
                worksheet.write(11+i, 0, item[0], cell_center)
                # FIX: Remove Currency Format for Age inputs (Rows 11, 12, 13 in Excel)
                if i < 3:
                    worksheet.write(11+i, 1, item[1], cell_center)
                else:
                    worksheet.write(11+i, 1, item[1], currency_fmt if isinstance(item[1], (int, float)) and 'Rate' not in item[0] and 'Return' not in item[0] else cell_center)
                worksheet.write(11+i, 2, item[2], desc_fmt)

            for i, item in enumerate(results):
                worksheet.write(11+i, 4, item[0], cell_center)
                worksheet.write(11+i, 5, item[1], currency_fmt)
                worksheet.write(11+i, 6, item[2], desc_fmt)

            # Cashflow Table
            table_row = 24
            worksheet.merge_range(table_row, 0, table_row, 4, "YEARLY WITHDRAWAL & CASHFLOW SCHEDULE", section_header_fmt)
            cols = ["Age", "Year", "Annual Withdrawal", "Monthly Amount", "Remaining Corpus"]
            for c, h in enumerate(cols): worksheet.write(table_row + 1, c, h, section_header_fmt)
            
            for i, entry in enumerate(res['annual_withdrawals']):
                r = table_row + 2 + i
                worksheet.write(r, 0, entry['Age'], cell_center) # Age is a plain number
                worksheet.write(r, 1, entry['Year'], cell_center)
                worksheet.write(r, 2, entry['Annual Withdrawal'], currency_fmt)
                worksheet.write(r, 3, entry['Monthly Amount'], currency_fmt)
                worksheet.write(r, 4, entry['Remaining Corpus'], currency_fmt)

            # Column Widths to prevent ######
            worksheet.set_column('A:A', 22); worksheet.set_column('B:B', 18); worksheet.set_column('C:C', 45)
            worksheet.set_column('E:E', 22); worksheet.set_column('F:F', 22); worksheet.set_column('G:G', 45)
            worksheet.set_column('D:D', 25)

        st.download_button("📥 Download Report", output.getvalue(), f"Retirement_Strategy_{user_name}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

if __name__ == "__main__":
    main()
