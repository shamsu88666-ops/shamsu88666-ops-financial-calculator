import streamlit as st
import pandas as pd
import numpy as np
import io
from fpdf import FPDF

# --- CORE CALCULATION ENGINE ---
def calculate_required_step_up_sip(shortfall, monthly_rate, months, step_percent):
    """Binary search to find required initial SIP with step-up"""
    low, high = 0.0, float(shortfall)
    for _ in range(50):
        test_sip = (low + high) / 2
        future_val = 0.0
        temp_sip = test_sip
        for year in range((months + 11) // 12):
            months_in_year = min(12, months - year * 12)
            for _ in range(months_in_year):
                future_val = (future_val + temp_sip) * (1 + monthly_rate)
            temp_sip *= (1 + step_percent / 100)
        if future_val < shortfall:
            low = test_sip
        else:
            high = test_sip
    return (low + high) / 2 # Using exact for calculations

def calculate_retirement_final(c_age, r_age, l_exp, c_exp, inf_rate, c_sip, e_corp, pre_ret_r, post_ret_r, legacy_amount_real, medical_corpus_today, sip_step_up_percent):
    months_to_retire = (r_age - c_age) * 12
    retirement_years = l_exp - r_age
    monthly_inf = (1 + inf_rate/100) ** (1/12) - 1
    monthly_pre_ret = (1 + pre_ret_r/100) ** (1/12) - 1
    monthly_post_ret = (1 + post_ret_r/100) ** (1/12) - 1
    # Precision Fix: Using exact values for calculations
    medical_at_retirement_exact = medical_corpus_today * (1 + inf_rate/100) ** (months_to_retire/12)
    expense_at_retirement_exact = c_exp * (1 + inf_rate/100) ** (months_to_retire/12)
    legacy_nominal_exact = legacy_amount_real * (1 + inf_rate/100) ** ((r_age + retirement_years - c_age))
    def simulate_swp(test_corp, return_rate_annual):
        m_post_ret = (1 + return_rate_annual/100) ** (1/12) - 1
        bal = test_corp - medical_at_retirement_exact
        for y in range(retirement_years):
            m_exp = expense_at_retirement_exact * (1 + inf_rate/100) ** y
            for m in range(12):
                if bal > 0:
                    bal -= m_exp
                    bal *= (1 + m_post_ret)
        return bal

    low = 0
    high = 10000000000
    for _ in range(60):
        mid = (low + high) / 2
        if simulate_swp(mid, post_ret_r) < legacy_nominal_exact:
            low = mid
        else:
            high = mid
    corp_req_exact = high

    future_existing = e_corp * (1 + monthly_pre_ret) ** months_to_retire
    # SIP with Step-up calculation
    future_sip = 0
    temp_sip = c_sip
    for year in range(r_age - c_age):
        for month in range(12):
            future_sip = (future_sip + temp_sip) * (1 + monthly_pre_ret)
        temp_sip *= (1 + sip_step_up_percent / 100)
    total_projected_savings = future_existing + future_sip
    shortfall = max(0.0, corp_req_exact - total_projected_savings)
    req_extra_sip_flat = 0.0
    req_extra_sip_stepup = 0.0
    req_extra_lumpsum = 0.0
    if shortfall > 0:
        if monthly_pre_ret > 0:
            req_extra_sip_flat = (shortfall * monthly_pre_ret) / (((1 + monthly_pre_ret) ** months_to_retire - 1) * (1 + monthly_pre_ret))
            req_extra_sip_stepup = calculate_required_step_up_sip(shortfall, monthly_pre_ret, months_to_retire, sip_step_up_percent)
        else:
            req_extra_sip_flat = shortfall / months_to_retire
            req_extra_sip_stepup = req_extra_sip_flat
        req_extra_lumpsum = shortfall / ((1 + monthly_pre_ret) ** months_to_retire)
    annual_withdrawals = []
    current_balance = corp_req_exact - medical_at_retirement_exact
    for year in range(1, retirement_years + 1):
        monthly_expense_this_year = expense_at_retirement_exact * (1 + inf_rate/100) ** (year - 1)
        yearly_withdrawn = 0
        for month in range(12):
            if current_balance > 0:
                withdrawal = min(monthly_expense_this_year, current_balance)
                current_balance -= withdrawal
                current_balance *= (1 + monthly_post_ret)
                yearly_withdrawn += withdrawal
        annual_withdrawals.append({
            "Age": int(r_age + year - 1),
            "Year": int(year),
            "Annual Withdrawal": round(yearly_withdrawn),
            "Monthly Amount": round(monthly_expense_this_year),
            "Remaining Corpus": round(max(0, current_balance))
        })
    return {
        "corp_req": round(corp_req_exact),
        "total_sav": round(total_projected_savings),
        "shortfall": round(shortfall),
        "req_sip_flat": round(req_extra_sip_flat),
        "req_sip_stepup": round(req_extra_sip_stepup),
        "req_lumpsum": round(req_extra_lumpsum),
        "legacy_nominal": round(legacy_nominal_exact),
        "first_swp": round(expense_at_retirement_exact),
        "medical_at_ret": round(medical_at_retirement_exact),
        "annual_withdrawals": annual_withdrawals
    }

# --- UI PART ---
def main():
    st.set_page_config(page_title="Retirement Planner Pro", layout="wide")
    st.markdown("""
    <style>
    .metric-card {
    background-color: #1e2130;
    padding: 15px;
    border-radius: 10px;
    border-left: 5px solid #4E9F3D;
    margin-bottom: 10px;
    }
    .metric-label { font-size: 14px; color: #b0b0b0; }
    .metric-value { font-size: 20px; font-weight: bold; color: white; white-space: nowrap; overflow: visible; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center;'>Retirement Planner Pro</h1>", unsafe_allow_html=True)
    whatsapp_link = "https://wa.me/971506404705"
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 20px;">
    <p style="margin-bottom: 10px;">Prepared by <b>Shamsudeen Abdulla</b></p>
    <a href="{whatsapp_link}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; margin-right: 10px; font-weight: bold;">WhatsApp</button></a>
    <a href="https://www.facebook.com/shamsudeen.abdulla.2025/" target="_blank"><button style="background-color: #1877F2; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; margin-right: 10px; font-weight: bold;">Facebook</button></a>
    <a href="{whatsapp_link}" target="_blank"><button style="background-color: #FF4B4B; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-weight: bold;">Contact Developer</button></a>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        user_name = st.text_input("User Name", "Valued Client")
        c_age = st.number_input("Current Age", min_value=1, max_value=100, value=30)
        r_age = st.number_input("Retirement Age", min_value=c_age+1, max_value=100, value=60)
        l_exp = st.number_input("Life Expectancy", min_value=r_age+1, max_value=120, value=85)
        c_exp = st.number_input("Monthly Expense (Today)", min_value=0, value=30000)
    with col2:
        inf = st.number_input("Inflation Rate (%)", min_value=0.0, value=7.0)
        pre_r = st.number_input("Pre-Retirement Return (%)", min_value=0.0, value=12.0)
        post_r = st.number_input("Post-Retirement Return (%)", min_value=0.0, value=8.0)
        existing_sav = st.number_input("Existing Savings", min_value=0, value=0)
        current_sip = st.number_input("Current Monthly SIP", min_value=0, value=0)
        sip_step_up_percent = st.number_input("Annual SIP Step-up (%)", min_value=0.0, value=0.0)
        st.write("Legacy (Today's Value) is the amount you wish to set aside for your heirs.")
        legacy = st.number_input("Legacy (Today's Value)", min_value=0, value=0)
        medical = st.number_input("Medical Emergency Fund (Today's Value)", min_value=0, value=0)

    if st.button("Calculate Plan"):
        res = calculate_retirement_final(c_age, r_age, l_exp, c_exp, inf, current_sip, existing_sav, pre_r, post_r, legacy, medical, sip_step_up_percent)
        st.divider()
        m_cols = st.columns(4)
        metrics = [
        ("Required Corpus", f"₹ {res['corp_req']:,}"),
        ("Projected Savings", f"₹ {res['total_sav']:,}"),
        ("Legacy Nominal", f"₹ {res['legacy_nominal']:,}"),
        ("1st Month SWP", f"₹ {res['first_swp']:,}")
        ]
        for i, (label, val) in enumerate(metrics):
            m_cols[i].markdown(f"""<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value'>{val}</div></div>""", unsafe_allow_html=True)
        if res['shortfall'] > 0:
            st.error(f"### ⚠️ Shortfall: ₹ {res['shortfall']:,}")
            st.write("To bridge this gap, you can choose one of the following options:")
            s_col1, s_col2 = st.columns(2)
            with s_col1:
                if sip_step_up_percent > 0:
                    st.info(f"**Additional Step-up SIP:**\n\n₹ {res['req_sip_stepup']:,}/month\n(Increasing by {sip_step_up_percent}% yearly)")
                else:
                    st.info(f"**Additional Flat SIP:**\n\n₹ {res['req_sip_flat']:,}/month")
            with s_col2:
                st.info(f"**Additional Lumpsum:**\n\n₹ {res['req_lumpsum']:,}")
        else:
            st.success("### ✅ Congratulations! Your current investments are sufficient.")

        st.subheader("🛡️ Risk Analysis & Protection")
        st.info(f"**Medical Corpus at Retirement:** ₹ {res['medical_at_ret']:,}")

        st.write("### Withdrawal Schedule")
        st.dataframe(pd.DataFrame(res["annual_withdrawals"]), use_container_width=True, hide_index=True)

        # --- EXCEL REPORT ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            worksheet = workbook.add_worksheet('Retirement Plan')
            # --- PROFESSIONAL FORMATS ---
            title_fmt = workbook.add_format({'bold': True, 'bg_color': '#1E5128', 'font_color': 'white', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 14})
            header_fmt = workbook.add_format({'bold': True, 'bg_color': '#4E9F3D', 'font_color': 'white', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
            cell_fmt = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
            curr_fmt = workbook.add_format({'num_format': '₹#,##0', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
            num_fmt = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
            desc_fmt = workbook.add_format({'font_size': 9, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
            disclaimer_fmt = workbook.add_format({'font_size': 10, 'italic': True, 'text_wrap': True, 'align': 'center', 'valign': 'vcenter', 'border': 1})

            # New Disclaimer Content
            disclaimer_text = (
                "Disclaimer: This report is based on basic calculations and the input values provided by you. "
                "Financial decisions should not be made solely based on this report. The developer of this "
                "calculator shall not be held responsible for any financial liabilities or losses incurred. "
                "Consult with your financial advisor before making any financial plans."
            )
            worksheet.merge_range('A1:I3', disclaimer_text, disclaimer_fmt)

            # Layout Design (Shifted down for disclaimer)
            worksheet.merge_range('A5:I6', 'PERSONALIZED RETIREMENT STRATEGY REPORT', title_fmt)
            worksheet.merge_range('A7:I7', f'Client: {user_name} | Prepared by Shamsudeen Abdulla', cell_fmt)

            # Section 1: Inputs
            worksheet.merge_range('A9:D9', '1. INVESTMENT INPUT PARAMETERS', header_fmt)
            worksheet.write('A10', 'Parameter', header_fmt)
            worksheet.write('B10', 'Value', header_fmt)
            worksheet.write('C10', 'Unit', header_fmt)
            worksheet.write('D10', 'Description', header_fmt)

            inputs = [
                ["Current Age", c_age, "Years", "The current age of the investor."],
                ["Retirement Age", r_age, "Years", "The age at which the investor plans to retire."],
                ["Life Expectancy", l_exp, "Years", "The estimated age up to which funds are needed."],
                ["Monthly Expense", c_exp, "INR", "Current monthly cost of living today."],
                ["Inflation Rate", inf, "%", "Expected annual increase in cost of living."],
                ["Pre-Ret Return", pre_r, "%", "Expected annual return before retirement."],
                ["Post-Ret Return", post_r, "%", "Expected annual return after retirement."],
                ["Existing Savings", existing_sav, "INR", "Total current retirement savings."],
                ["Current SIP", current_sip, "INR", "Current ongoing monthly investment."],
                ["SIP Step-up", sip_step_up_percent, "%", "Annual increase in monthly SIP."],
                ["Legacy (Today)", legacy, "INR", "Wealth intended for heirs (Today's value)."],
                ["Medical Fund", medical, "INR", "Medical corpus needed (Today's value)."]
            ]
            for i, row in enumerate(inputs):
                worksheet.write(10+i, 0, row[0], cell_fmt)
                if row[2] == "INR": worksheet.write(10+i, 1, row[1], curr_fmt)
                else: worksheet.write(10+i, 1, row[1], num_fmt)
                worksheet.write(10+i, 2, row[2], num_fmt)
                worksheet.write(10+i, 3, row[3], desc_fmt)

            # Section 2: Results
            worksheet.merge_range('F9:I9', '2. STRATEGIC PROJECTIONS', header_fmt)
            worksheet.write('F10', 'Result Item', header_fmt)
            worksheet.write('G10', 'Projected Value', header_fmt)
            worksheet.write('H10', 'Unit', header_fmt)
            worksheet.write('I10', 'Description', header_fmt)

            results = [
                ["Required Corpus", res['corp_req'], "INR", "Total wealth needed at retirement."],
                ["Projected Savings", res['total_sav'], "INR", "Estimated wealth based on investments."],
                ["Shortfall (Gap)", res['shortfall'], "INR", "Gap between required and projected wealth."],
                ["Extra Flat SIP", res['req_sip_flat'], "INR", "Monthly investment needed (Fixed)."],
                ["Extra Step-up SIP", res['req_sip_stepup'], "INR", "Starting SIP needed (Increasing annually)."],
                ["Extra Lumpsum", res['req_lumpsum'], "INR", "One-time investment needed today."],
                ["Legacy (Nominal)", res['legacy_nominal'], "INR", "Future value of legacy at end of life."],
                ["1st Month SWP", res['first_swp'], "INR", "Estimated first monthly withdrawal."]
            ]
            for i, row in enumerate(results):
                worksheet.write(10+i, 5, row[0], cell_fmt)
                worksheet.write(10+i, 6, row[1], curr_fmt)
                worksheet.write(10+i, 7, row[2], num_fmt)
                worksheet.write(10+i, 8, row[3], desc_fmt)

            # Section 3: Withdrawal Schedule
            w_row = 24
            worksheet.merge_range(w_row, 0, w_row, 4, '3. YEARLY WITHDRAWAL & CASHFLOW SCHEDULE', header_fmt)
            headers = ["Age", "Year", "Annual Withdrawal", "Monthly Amount", "Remaining Corpus"]
            for h_idx, h_text in enumerate(headers):
                worksheet.write(w_row+1, h_idx, h_text, header_fmt)
            for i, entry in enumerate(res['annual_withdrawals']):
                row_idx = w_row + 2 + i
                worksheet.write(row_idx, 0, entry['Age'], num_fmt)
                worksheet.write(row_idx, 1, entry['Year'], num_fmt)
                worksheet.write(row_idx, 2, entry['Annual Withdrawal'], curr_fmt)
                worksheet.write(row_idx, 3, entry['Monthly Amount'], curr_fmt)
                worksheet.write(row_idx, 4, entry['Remaining Corpus'], curr_fmt)

            # Auto-fit columns - Width set to prevent ####
            worksheet.set_column('A:A', 30)
            worksheet.set_column('B:B', 20)
            worksheet.set_column('C:C', 12)
            worksheet.set_column('D:D', 50)
            worksheet.set_column('E:E', 30) # Column E for Remaining Corpus in Withdrawal Schedule
            worksheet.set_column('F:F', 25)
            worksheet.set_column('G:G', 25)
            worksheet.set_column('H:H', 12)
            worksheet.set_column('I:I', 50)

        st.download_button("📥 Download Professional Excel Report", output.getvalue(), f"Retirement_Plan_{user_name}.xlsx", use_container_width=True)

if __name__ == "__main__":
    main()
