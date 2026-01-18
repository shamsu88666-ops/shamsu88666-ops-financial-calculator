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
    .stApp { background-color: #0E1116 !important; color: #E5E7EB !important; }
    .main { background-color: #0E1116 !important; }
    .input-card {
        background-color: #1A2233 !important; padding: 25px; border-radius: 10px;
        border: 1px solid #374151; color: #E5E7EB !important;
    }
    .result-text { color: #22C55E !important; font-family: 'Courier New', monospace; font-weight: bold; }
    .quote-text { color: #22C55E !important; font-style: italic; font-weight: bold; text-align: center; display: block; margin-top: 20px; }
    .stButton>button {
        background-color: #22C55E !important; color: white !important; width: 100%;
        border: none; font-weight: bold; height: 3.5em; border-radius: 8px;
    }
    .stButton>button:hover { background-color: #16a34a !important; }
    label, p, span, h1, h2, h3 { color: #E5E7EB !important; }
    [data-testid="stMetricLabel"] { color: #9CA3AF !important; }
    [data-testid="stMetricValue"] { color: #FFFFFF !important; }

    /* New CSS for Developer Contact Buttons */
    .dev-container {
        text-align: center;
        margin-bottom: 25px;
    }
    .dev-btn {
        display: inline-block;
        padding: 8px 16px;
        margin: 5px;
        border-radius: 5px;
        text-decoration: none !important;
        font-weight: bold;
        color: white !important;
        font-size: 13px;
    }
    .wa-btn { background-color: #25D366; }
    .fb-btn { background-color: #1877F2; }
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

# --- CORE LOGIC (100% MONTHLY BASIS) ---
def calculate_retirement_final(c_age, r_age, l_exp, c_exp, inf_rate, c_sav, e_corp, pre_ret_r, post_ret_r, legacy_amount_real):
    months_to_retire = (r_age - c_age) * 12
    retirement_months = (l_exp - r_age) * 12
    total_months = (l_exp - c_age) * 12
    
    monthly_inf = (1 + inf_rate/100) ** (1/12) - 1
    monthly_pre_ret = (1 + pre_ret_r/100) ** (1/12) - 1
    monthly_post_ret = (1 + post_ret_r/100) ** (1/12) - 1
    
    legacy_nominal = legacy_amount_real * (1 + monthly_inf) ** total_months
    
    expense_at_retirement = c_exp * (1 + monthly_inf) ** months_to_retire
    
    if abs(monthly_post_ret - monthly_inf) > 0.0001:
        pv_expenses = expense_at_retirement * (
            1 - ((1 + monthly_inf) / (1 + monthly_post_ret)) ** retirement_months
        ) / (monthly_post_ret - monthly_inf)
    else:
        pv_expenses = expense_at_retirement * retirement_months
    
    pv_legacy = legacy_nominal / (1 + monthly_post_ret) ** retirement_months if legacy_nominal > 0 else 0
    
    corp_req = pv_expenses + pv_legacy
    
    future_existing = e_corp * (1 + monthly_pre_ret) ** months_to_retire
    
    if monthly_pre_ret > 0:
        future_sip = c_sav * (((1 + monthly_pre_ret) ** months_to_retire - 1) / monthly_pre_ret) * (1 + monthly_pre_ret)
    else:
        future_sip = c_sav * months_to_retire
        
    total_savings = future_existing + future_sip
    shortfall = max(0, corp_req - total_savings)
    
    req_sip = 0
    req_lumpsum = 0
    if shortfall > 0 and months_to_retire > 0:
        if monthly_pre_ret > 0:
            req_sip = (shortfall * monthly_pre_ret) / (((1 + monthly_pre_ret) ** months_to_retire - 1) * (1 + monthly_pre_ret))
            req_lumpsum = shortfall / ((1 + monthly_pre_ret) ** months_to_retire)
        else:
            req_sip = shortfall / months_to_retire
            req_lumpsum = shortfall
    
    annual_withdrawals = []
    current_balance = corp_req
    
    for year in range(retirement_months // 12):
        monthly_expense_this_year = expense_at_retirement * (1 + monthly_inf) ** (year * 12)
        
        for month in range(12):
            current_balance = (current_balance * (1 + monthly_post_ret)) - monthly_expense_this_year
        
        annual_withdrawals.append({
            "Age": r_age + year,
            "Year": year + 1,
            "Annual Withdrawal": round(monthly_expense_this_year * 12),
            "Monthly Amount": round(monthly_expense_this_year),
            "Remaining Corpus": round(current_balance)
        })
    
    return {
        "future_exp": round(expense_at_retirement),
        "corp_req": round(corp_req),
        "total_sav": round(total_savings),
        "shortfall": round(shortfall),
        "req_sip": round(req_sip),
        "req_lumpsum": round(req_lumpsum),
        "legacy_real": round(legacy_amount_real),
        "legacy_nominal": round(legacy_nominal),
        "annual_withdrawals": annual_withdrawals
    }

# --- MAIN APP ---
st.markdown("<h1 style='text-align: center;'>RETIREMENT PLANNER PRO</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #9CA3AF;'>Designed for Your Future Wealth</p>", unsafe_allow_html=True)
# ✅ DEVELOPER NAME AND CONTACT BUTTONS
st.markdown(f"""
    <div class="dev-container">
        <p style='margin-bottom: 5px; font-size: 0.9em; color: #6B7280;'>Developed by Shamsudeen abdulla</p>
        <a href="https://wa.me/qr/IOBUQDQMM2X3D1" target="_blank" class="dev-btn wa-btn">WhatsApp Developer</a>
        <a href="https://www.facebook.com/shamsudeen.abdulla.2025/" target="_blank" class="dev-btn fb-btn">Facebook Profile</a>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="input-card">', unsafe_allow_html=True)
user_name = st.text_input("Name of the User", value="Valued User")
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 👤 Personal Information")
    current_age = st.number_input("Current Age", value=30, min_value=0, max_value=100, step=1)
    retire_age = st.number_input("Retirement Age", value=60, min_value=current_age+1, max_value=110, step=1)
    life_exp = st.number_input("Expected Life Expectancy", value=85, min_value=retire_age+1, max_value=120, step=1)
    current_expense = st.number_input("Current Monthly Expense (₹)", value=30000, min_value=1, step=500)

with col2:
    st.markdown("### 💰 Investment Details")
    inf_rate = st.number_input("Inflation Rate (%)", value=6.0, step=0.1, format="%.1f")
    existing_corp = st.number_input("Existing Savings (₹)", value=0, min_value=0, step=5000)
    current_sip = st.number_input("Current Monthly SIP (₹)", value=0, min_value=0, step=100)
    pre_ret_rate = st.number_input("Pre-retirement Returns (%)", value=12.0, min_value=0.1, step=0.1, format="%.1f")
    post_ret_rate = st.number_input("Post-retirement Returns (%)", value=8.0, min_value=0.1, step=0.1, format="%.1f")
    
    # ✅ EXACT LEGACY EXPLANATION TEXT PROVIDED (WITH BRACKET PART)
    st.markdown("""
        <div style='background-color: #1F2937; padding: 15px; border-radius: 8px; 
                    border-left: 5px solid #22C55E; margin-bottom: 12px;'>
            <p style='color: #E5E7EB; margin: 0; font-size: 14px; line-height: 1.6;'>
                <strong>💡 LEGACY എമൗണ്ട് എന്താണ്?</strong><br>
                "നിങ്ങളുടെ അനന്തരാവകാശികൾക്കായി മാറ്റിവെക്കാൻ ആഗ്രഹിക്കുന്ന തുക ഇവിടെ രേഖപ്പെടുത്തുക. നിങ്ങൾ കണക്കാക്കുന്ന കാലയളവ് വരെ ജീവിച്ചാൽ, ഈ തുക അതിന്റെ പൂർണ്ണ മൂല്യത്തിൽ തന്നെ അവർക്ക് ലഭ്യമാകും."
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    legacy_amount = st.number_input(
        "Legacy Amount - Today's Real Value (₹)", 
        value=0, 
        min_value=0, 
        step=100000,
        help="അന്തരാവകാശികൾക്ക് വേണ്ടി ബാക്കി വയ്ക്കാൻ ആഗ്രഹിക്കുന്ന ഇന്നത്തെ മൂല്യം"
    )
st.markdown('</div>', unsafe_allow_html=True)

if st.button("Calculate"):
    res = calculate_retirement_final(current_age, retire_age, life_exp, current_expense, inf_rate, current_sip, existing_corp, pre_ret_rate, post_ret_rate, legacy_amount)
    st.session_state.res = res
    st.session_state.user_name = user_name
    
    st.divider()
    r1, r2 = st.columns(2)
    with r1:
        st.metric("Expense at Retirement (Monthly)", f"₹ {res['future_exp']:,}")
        st.metric("Required Retirement Corpus", f"₹ {res['corp_req']:,}")
        st.metric("Legacy (Today's Real Value)", f"₹ {res['legacy_real']:,}")
    with r2:
        st.metric("Projected Savings", f"₹ {res['total_sav']:,}")
        st.metric("Shortfall", f"₹ {res['shortfall']:,}", delta_color="inverse")
        st.metric(f"Legacy Nominal at Age {life_exp}", f"₹ {res['legacy_nominal']:,}")

    if res["shortfall"] > 0:
        st.error("📉 SHORTFALL ANALYSIS")
        st.markdown(f"To cover the shortfall of **₹ {res['shortfall']:,}**, you need to invest:")
        st.markdown(f"🔹 **Additional Monthly SIP:** <span style='font-size:1.2em; color:#22C55E;'>₹ {res['req_sip']:,}</span>", unsafe_allow_html=True)
        st.markdown(f"🔹 **OR One-time Lumpsum Today:** <span style='font-size:1.2em; color:#22C55E;'>₹ {res['req_lumpsum']:,}</span>", unsafe_allow_html=True)
    else:
        st.success("✅ Your current savings plan is on track!")

    st.write("### Post-Retirement Yearly Cashflow & Remaining Corpus")
    st.dataframe(pd.DataFrame(res["annual_withdrawals"]), use_container_width=True, hide_index=True)
    st.markdown(f'<span class="quote-text">{random.choice(all_quotes)}</span>', unsafe_allow_html=True)

st.markdown("<p style='text-align: center; font-size: 0.8em; color: #9CA3AF;'>* Based on assumptions. Market risks apply.</p>", unsafe_allow_html=True)

# --- EXCEL DOWNLOAD (WITH FIXED COLUMN WIDTHS) ---
if 'res' in st.session_state and st.session_state.res is not None:
    res = st.session_state.res
    u_name = st.session_state.user_name
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet('Retirement Plan')
        
        header_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#22C55E', 'font_color': 'white', 
            'border': 1, 'align': 'center', 'valign': 'vcenter'
        })
        normal_fmt = workbook.add_format({
            'border': 1, 'align': 'center', 'valign': 'vcenter'
        })
        currency_fmt = workbook.add_format({
            'num_format': '₹ #,##0', 'border': 1, 'align': 'center', 'valign': 'vcenter'
        })
        disclaimer_fmt = workbook.add_format({
            'italic': True, 'font_color': '#C00000', 'text_wrap': True, 
            'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 10
        })
        title_fmt = workbook.add_format({
            'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter'
        })

        # 1. DISCLAIMER
        worksheet.merge_range('A1:E4', 
            "DISCLAIMER: This report is generated based on basic mathematics and the inputs provided by you. "
            "Practical results may vary significantly. Your financial planning should not be based solely on this report. "
            "The app developer shall not be held responsible for any financial liabilities, losses, or other damages "
            "incurred based on the information provided in this report.", 
            disclaimer_fmt)

        # 2. REPORT INFO
        worksheet.merge_range('A6:E6', 'RETIREMENT PLAN REPORT', title_fmt)
        worksheet.write('A7', 'User Name:', workbook.add_format({'bold': True, 'align': 'right'}))
        worksheet.write('B7', u_name, normal_fmt)
        worksheet.write('D7', 'Date:', workbook.add_format({'bold': True, 'align': 'right'}))
        worksheet.write('E7', str(date.today()), normal_fmt)

        # 3. INPUT PARAMETERS
        worksheet.merge_range('A9:B9', '1. INPUT PARAMETERS', header_fmt)
        inputs = [
            ["Current Age", current_age], ["Retirement Age", retire_age], ["Life Expectancy", life_exp],
            ["Monthly Expense", current_expense], ["Inflation Rate (%)", inf_rate],
            ["Existing Savings", existing_corp], ["Monthly SIP", current_sip],
            ["Pre-ret Return (%)", pre_ret_rate], ["Post-ret Return (%)", post_ret_rate],
            ["Legacy (Real Value)", legacy_amount]
        ]
        for i, (l, v) in enumerate(inputs):
            worksheet.write(i+10, 0, l, normal_fmt)
            worksheet.write(i+10, 1, v, normal_fmt)

        # 4. RESULTS SUMMARY
        worksheet.merge_range('D9:E9', '2. RESULTS SUMMARY', header_fmt)
        summary = [
            ["Exp at Retirement", res['future_exp']], ["Required Corpus", res['corp_req']],
            ["Projected Savings", res['total_sav']], ["Shortfall", res['shortfall']],
            ["Additional SIP", res['req_sip']], ["Lumpsum Needed", res['req_lumpsum']],
            ["Legacy (Real)", res['legacy_real']], ["Legacy (Nominal)", res['legacy_nominal']]
        ]
        for i, (l, v) in enumerate(summary):
            worksheet.write(i+10, 3, l, normal_fmt)
            worksheet.write(i+10, 4, v, currency_fmt)

        # 5. CASHFLOW TABLE (Fixed Header for "Annual Withdrawal")
        worksheet.merge_range('A22:E22', '3. YEARLY CASHFLOW & REMAINING CORPUS', header_fmt)
        table_headers = ["Age", "Year", "Annual Withdrawal", "Monthly Amount", "Remaining Corpus"]
        for c, h in enumerate(table_headers):
            worksheet.write(23, c, h, header_fmt)
        
        for r, row in enumerate(res['annual_withdrawals']):
            worksheet.write(r+24, 0, row["Age"], normal_fmt)
            worksheet.write(r+24, 1, row["Year"], normal_fmt)
            worksheet.write(r+24, 2, row["Annual Withdrawal"], currency_fmt)
            worksheet.write(r+24, 3, row["Monthly Amount"], currency_fmt)
            worksheet.write(r+24, 4, row["Remaining Corpus"], currency_fmt)

        # 6. ADJUST COLUMN WIDTHS (Perfect Fit for Large Numbers)
        # സംഖ്യകൾ വലുതായാലും '#####' വരാതിരിക്കാൻ വീതി കൂട്ടിയിട്ടുണ്ട്.
        worksheet.set_column('A:A', 25) # Label
        worksheet.set_column('B:B', 18) # Value
        worksheet.set_column('C:C', 20) # Withdrawal (ഇവിടെയാണ് ##### കണ്ടിരുന്നത്)
        worksheet.set_column('D:D', 22) # Monthly Amount
        worksheet.set_column('E:E', 25) # Remaining Corpus

    st.download_button(
        label="📥 Download Excel Report", 
        data=buffer.getvalue(), 
        file_name=f"Retirement_Plan_{u_name}_{date.today()}.xlsx", 
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
