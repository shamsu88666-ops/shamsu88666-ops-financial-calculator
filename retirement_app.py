import streamlit as st
import pandas as pd
import numpy as np
import io
from decimal import Decimal, getcontext
import math

# --- CORE CALCULATION ENGINE ---
getcontext().prec = 30

def calculate_retirement_final(c_age, r_age, l_exp, c_exp, inf_rate, c_sip, e_corp, pre_ret_r, post_ret_r, step_up_rate):
    # കൺവേർഷൻ Decimal-ലേക്ക്
    c_exp = Decimal(str(c_exp))
    inf_rate = Decimal(str(inf_rate))
    pre_ret_r = Decimal(str(pre_ret_r))
    post_ret_r = Decimal(str(post_ret_r))
    step_up_rate = Decimal(str(step_up_rate))
    e_corp = Decimal(str(e_corp))
    c_sip = Decimal(str(c_sip))
    
    months_to_retire = (r_age - c_age) * 12
    retirement_years = l_exp - r_age
    retirement_months = retirement_years * 12
    
    monthly_inf = (Decimal('1') + inf_rate/100) ** (Decimal('1')/Decimal('12')) - 1
    monthly_pre_ret = (Decimal('1') + pre_ret_r/100) ** (Decimal('1')/Decimal('12')) - 1
    monthly_post_ret = (Decimal('1') + post_ret_r/100) ** (Decimal('1')/Decimal('12')) - 1
    
    expense_at_retirement_start = c_exp * (Decimal('1') + monthly_inf) ** months_to_retire
    
    def simulate_swp(test_corp):
        bal = Decimal(str(test_corp))
        for m in range(retirement_months):
            current_m_exp = expense_at_retirement_start * (Decimal('1') + monthly_inf) ** m
            bal -= current_m_exp
            if bal > 0:
                bal *= (Decimal('1') + monthly_post_ret)
        return bal

    # Find corpus required
    low, high = Decimal('0'), Decimal('5000000000')
    while (high - low) > Decimal('0.01'):
        mid = (low + high) / 2
        if simulate_swp(mid) < 0:
            low = mid
        else:
            high = mid
    
    corp_req = high
    
    # Savings calculation
    future_existing = e_corp * (Decimal('1') + monthly_pre_ret) ** months_to_retire
    future_sip = Decimal('0')
    temp_sip = c_sip
    years_to_retire = months_to_retire // 12
    extra_months = months_to_retire % 12
    
    for y in range(years_to_retire):
        for m in range(12):
            future_sip = (future_sip + temp_sip) * (Decimal('1') + monthly_pre_ret)
        if y < years_to_retire - 1:
            temp_sip *= (Decimal('1') + step_up_rate / 100)
    
    for m in range(extra_months):
        future_sip = (future_sip + temp_sip) * (Decimal('1') + monthly_pre_ret)
    
    total_projected_savings = future_existing + future_sip
    shortfall = max(Decimal('0'), corp_req - total_projected_savings)
    
    req_extra_sip, req_extra_lumpsum, req_extra_stepup_sip = Decimal('0'), Decimal('0'), Decimal('0')
    if shortfall > 0:
        if monthly_pre_ret > 0:
            req_extra_sip = (shortfall * monthly_pre_ret) / (((Decimal('1') + monthly_pre_ret) ** months_to_retire - 1) * (Decimal('1') + monthly_pre_ret))
            req_extra_lumpsum = shortfall / ((Decimal('1') + monthly_pre_ret) ** months_to_retire)
            
            s_low, s_high = Decimal('0'), shortfall
            while (s_high - s_low) > Decimal('0.01'):
                s_mid = (s_low + s_high) / 2
                f_val = Decimal('0')
                t_sip = s_mid
                for y in range(years_to_retire):
                    for m in range(12):
                        f_val = (f_val + t_sip) * (Decimal('1') + monthly_pre_ret)
                    if y < years_to_retire - 1:
                        t_sip *= (Decimal('1') + step_up_rate / 100)
                for m in range(extra_months):
                    f_val = (f_val + t_sip) * (Decimal('1') + monthly_pre_ret)
                if f_val < shortfall: s_low = s_mid
                else: s_high = s_mid
            req_extra_stepup_sip = s_high
        else:
            req_extra_sip = shortfall / months_to_retire
            req_extra_lumpsum = shortfall
            req_extra_stepup_sip = shortfall / months_to_retire
    
    # Schedule Simulation
    current_balance = total_projected_savings
    annual_withdrawals, total_withdrawn_sum = [], Decimal('0')
    
    for year in range(1, retirement_years + 1):
        yearly_withdrawn = Decimal('0')
        for month in range(12):
            m_idx = (year - 1) * 12 + month
            monthly_expense = expense_at_retirement_start * (Decimal('1') + monthly_inf) ** m_idx
            withdrawal = min(monthly_expense, max(Decimal('0'), current_balance))
            current_balance -= withdrawal
            if current_balance > 0:
                current_balance *= (Decimal('1') + monthly_post_ret)
            yearly_withdrawn += withdrawal
        
        total_withdrawn_sum += yearly_withdrawn
        annual_withdrawals.append({
            "Age": r_age + year - 1,
            "Year": year,
            "Annual Withdrawal": round(float(yearly_withdrawn)),
            "Monthly Amount": round(float(expense_at_retirement_start * (Decimal('1') + monthly_inf) ** ((year-1)*12))),
            "Remaining Corpus": round(float(max(Decimal('0'), current_balance)))
        })
    
    final_legacy = simulate_swp(total_projected_savings)
        
    return {
        "corp_req": round(float(corp_req)),
        "total_sav": round(float(total_projected_savings)),
        "shortfall": round(float(shortfall)),
        "req_sip": round(float(req_extra_sip)),
        "req_lumpsum": round(float(req_extra_lumpsum)),
        "req_stepup_sip": round(float(req_extra_stepup_sip)),
        "legacy_value": round(float(max(Decimal('0'), final_legacy))),
        "annual_withdrawals": annual_withdrawals,
        "total_withdrawn_sum": round(float(total_withdrawn_sum)),
        "first_swp": round(float(expense_at_retirement_start))
    }

# --- UI PART ---
def main():
    st.set_page_config(page_title="Retirement Planner Pro", layout="wide")
    st.markdown("<h1 style='text-align: center;'>Retirement Planner Pro</h1>", unsafe_allow_html=True)
    
    st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <p style="margin-bottom: 10px;">Prepared by <b>Shamsudeen Abdulla</b></p>
            <a href="https://wa.me/qr/IOBUQDQMM2X3D1" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; margin-right: 10px; font-weight: bold;">WhatsApp</button></a>
            <a href="https://www.facebook.com/shamsudeen.abdulla.2025/" target="_blank"><button style="background-color: #1877F2; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-weight: bold;">Facebook</button></a>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        user_name = st.text_input("User Name", "Valued Client")
        c_age = st.number_input("Current Age", min_value=0, max_value=100, value=0)
        r_age = st.number_input("Retirement Age", min_value=0, max_value=100, value=0)
        l_exp = st.number_input("Life Expectancy", min_value=0, max_value=120, value=0)
        c_exp = st.number_input("Monthly Expense (Today)", value=0)
    with col2:
        inf = st.number_input("Inflation Rate (%)", value=0.0)
        pre_r = st.number_input("Pre-Retirement Return (%)", value=0.0)
        post_r = st.number_input("Post-Retirement Return (%)", value=0.0)
        existing_sav = st.number_input("Existing Savings", value=0)
        current_sip = st.number_input("Current Monthly SIP", value=0)
        step_up_sip = st.number_input("SIP Step-up (%) annually", value=0.0, min_value=0.0, max_value=100.0)

    if st.button("Calculate Plan"):
        if r_age <= c_age or l_exp <= r_age:
            st.warning("Please enter valid ages.")
        else:
            res = calculate_retirement_final(c_age, r_age, l_exp, c_exp, inf, current_sip, existing_sav, pre_r, post_r, step_up_sip)
            
            st.divider()
            m1, m2, m3, m4 = st.columns(4)
            with m1: st.markdown(f"<p style='font-size:16px;'>Required Corpus</p><h3>₹ {res['corp_req']:,}</h3>", unsafe_allow_html=True)
            with m2: st.markdown(f"<p style='font-size:16px;'>Projected Savings</p><h3>₹ {res['total_sav']:,}</h3>", unsafe_allow_html=True)
            with m3: st.markdown(f"<p style='font-size:16px;'>Legacy Value</p><h3>₹ {res['legacy_value']:,}</h3>", unsafe_allow_html=True)
            with m4: st.markdown(f"<p style='font-size:16px;'>1st Month SWP</p><h3>₹ {res['first_swp']:,}</h3>", unsafe_allow_html=True)
            
            if res['shortfall'] <= 0:
                st.success(f"🎉 Congratulations {user_name}! Your plan is on track.")
            else:
                st.error(f"Shortfall: ₹ {res['shortfall']:,}")
                if step_up_sip > 0:
                    st.warning(f"Extra **Step-up SIP: ₹ {res['req_stepup_sip']:,}** OR **Lumpsum: ₹ {res['req_lumpsum']:,}**")
                else:
                    st.warning(f"Extra **SIP: ₹ {res['req_sip']:,}** OR **Lumpsum: ₹ {res['req_lumpsum']:,}**")
            
            st.write("### Withdrawal Schedule")
            st.dataframe(pd.DataFrame(res["annual_withdrawals"]), use_container_width=True, hide_index=True)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                workbook = writer.book
                worksheet = workbook.add_worksheet('Retirement Plan')
                
                header_fmt = workbook.add_format({'bold': True, 'bg_color': '#1E5128', 'font_color': 'white', 'border': 1, 'align': 'center'})
                cell_fmt = workbook.add_format({'border': 1, 'align': 'center'})
                curr_fmt = workbook.add_format({'num_format': '₹#,##0', 'border': 1, 'align': 'center'})
                num_only_fmt = workbook.add_format({'border': 1, 'align': 'center'}) # Format without currency symbol
                disclaimer_fmt = workbook.add_format({'italic': True, 'font_color': 'red', 'text_wrap': True, 'align': 'left', 'valign': 'top'})

                # Disclaimer Section at the top
                disclaimer_text = "DISCLAIMER: This report is based on basic calculations and the input values provided by you. Financial decisions should not be made solely based on this report. Please consult with your financial advisor to create a professional retirement plan. The developer of this calculator shall not be held liable for any liabilities or losses arising from the use of this report."
                worksheet.merge_range('A1:G3', disclaimer_text, disclaimer_fmt)

                # Adjusted row start for inputs to make space for disclaimer
                start_row = 4

                # Inputs section
                worksheet.merge_range(f'A{start_row}:C{start_row}', "INVESTMENT INPUTS", header_fmt)
                # Added descriptions for each input
                inputs = [
                    ["User Name", user_name, "Name of the client"], 
                    ["Current Age", c_age, "Age at the start of planning"], 
                    ["Retirement Age", r_age, "Planned age to stop working"], 
                    ["Life Expectancy", l_exp, "Estimated age for planning duration"], 
                    ["Monthly Expense", c_exp, "Current monthly cost of living"], 
                    ["Inflation Rate", f"{inf}%", "Annual rate of price increase"], 
                    ["Pre-Ret Return", f"{pre_r}%", "Expected ROI before retirement"], 
                    ["Post-Ret Return", f"{post_r}%", "Expected ROI after retirement"], 
                    ["Existing Savings", existing_sav, "Current total investments"], 
                    ["Current SIP", current_sip, "Ongoing monthly investment"], 
                    ["Step-up SIP", f"{step_up_sip}%", "Annual percentage increase in SIP"]
                ]
                
                worksheet.write(start_row - 1, 2, "Description", header_fmt)
                for i, (k, v, d) in enumerate(inputs):
                    curr_row = start_row + i
                    worksheet.write(curr_row, 0, k, cell_fmt)
                    if k in ["Current Age", "Retirement Age", "Life Expectancy"]:
                        worksheet.write(curr_row, 1, v, num_only_fmt)
                    else:
                        worksheet.write(curr_row, 1, v, curr_fmt if isinstance(v, (int, float)) else cell_fmt)
                    worksheet.write(curr_row, 2, d, cell_fmt)

                # Results section
                worksheet.merge_range(f'E{start_row}:G{start_row}', "PLAN RESULTS", header_fmt)
                # Added descriptions for each result
                results = [
                    ["Required Corpus", res['corp_req'], "Total money needed at retirement"], 
                    ["Projected Savings", res['total_sav'], "Estimated money you will have"], 
                    ["Shortfall", res['shortfall'], "Gap between needed and projected amount"], 
                    ["Extra SIP", res['req_sip'], "Additional SIP needed without step-up"], 
                    ["Extra Step-up SIP", res['req_stepup_sip'], "Additional SIP needed with step-up"], 
                    ["Extra Lumpsum", res['req_lumpsum'], "One-time investment needed now"], 
                    ["Legacy Value", res['legacy_value'], "Estimated wealth left for heirs"]
                ]
                
                worksheet.write(start_row - 1, 6, "Description", header_fmt)
                for i, (k, v, d) in enumerate(results):
                    curr_row = start_row + i
                    worksheet.write(curr_row, 4, k, cell_fmt)
                    worksheet.write(curr_row, 5, v, curr_fmt)
                    worksheet.write(curr_row, 6, d, cell_fmt)

                # Schedule
                row = start_row + 13
                cols = ["Age", "Year", "Annual Withdrawal", "Monthly Amount", "Remaining Corpus"]
                for c, h in enumerate(cols): worksheet.write(row, c, h, header_fmt)
                for i, entry in enumerate(res['annual_withdrawals']):
                    worksheet.write(row+1+i, 0, entry['Age'], num_only_fmt) # No currency symbol
                    worksheet.write(row+1+i, 1, entry['Year'], num_only_fmt) # No currency symbol
                    worksheet.write(row+1+i, 2, entry['Annual Withdrawal'], curr_fmt)
                    worksheet.write(row+1+i, 3, entry['Monthly Amount'], curr_fmt)
                    worksheet.write(row+1+i, 4, entry['Remaining Corpus'], curr_fmt)
                
                # Column widths - C and G increased specifically, D set to be visible
                worksheet.set_column('A:B', 20)
                worksheet.set_column('C:C', 45) 
                worksheet.set_column('D:D', 25) # Column D width increased to show values
                worksheet.set_column('E:F', 20)
                worksheet.set_column('G:G', 45) 

            st.download_button("📥 Download Report", output.getvalue(), f"Retirement_Report_{user_name}.xlsx", use_container_width=True)

if __name__ == "__main__":
    main()
