import streamlit as st
import pandas as pd
import random
import time
from datetime import date
import io

# ... (മുകളിലെ കോഡ് അതേപടി തുടരും) ...

# ✅ പുതിയ: Excel ഡൗൺലോഡ് ബട്ടൺ - നിറങ്ങളും disclaimer ഉം ഉൾപ്പെടെ
if 'res' in st.session_state and st.session_state.res is not None:
    
    # Excel ഫയൽ തയ്യാറാക്കൽ
    import xlsxwriter
    
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    
    # ഫോർമാറ്റുകൾ നിർവ്വചിക്കൽ
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#22C55E',  # green color
        'font_color': 'white',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })
    
    money_format = workbook.add_format({
        'num_format': '₹ #,##0',
        'border': 1,
        'align': 'right'
    })
    
    percent_format = workbook.add_format({
        'num_format': '0.00%',
        'border': 1,
        'align': 'center'
    })
    
    text_format = workbook.add_format({
        'border': 1,
        'align': 'left'
    })
    
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 16,
        'bg_color': '#1A2233',
        'font_color': 'white',
        'align': 'center'
    })
    
    disclaimer_format = workbook.add_format({
        'text_wrap': True,
        'italic': True,
        'font_color': '#ff6b6b',
        'valign': 'top'
    })
    
    # Disclaimer ടെക്സ്റ്റ്
    DISCLAIMER = """
    DISCLAIMER: This retirement plan is based on the assumptions provided by the user and hypothetical rates of return. 
    Actual results may vary significantly due to market volatility, inflation fluctuations, tax implications, and 
    other unforeseen circumstances. This is not financial advice. Please consult with a qualified financial advisor 
    before making investment decisions. Past performance does not guarantee future returns.
    """
    
    # വർക്ക്ഷീറ്റ് 1: സംക്ഷിപ്ത ഫലങ്ങൾ
    ws1 = workbook.add_worksheet("Summary")
    ws1.set_column('A:A', 30)
    ws1.set_column('B:B', 25)
    
    # Disclaimer (മുകളിൽ)
    ws1.merge_range('A1:B4', DISCLAIMER, disclaimer_format)
    
    # ടൈറ്റിൽ
    ws1.merge_range('A6:B6', "RETIREMENT PLAN SUMMARY", title_format)
    ws1.write('A7', "Generated on:", text_format)
    ws1.write('B7', date.today().strftime('%d-%b-%Y'), text_format)
    
    # ഇൻപുട് ചെയ്ത വിവരങ്ങൾ
    ws1.write('A9', "INPUT INFORMATION", header_format)
    input_data = [
        ["Current Age", current_age, text_format],
        ["Retirement Age", retire_age, text_format],
        ["Life Expectancy", life_exp, text_format],
        ["Monthly Expense (₹)", current_expense, money_format],
        ["Inflation Rate", inf_rate/100, percent_format],
        ["Existing Savings (₹)", existing_corp, money_format],
        ["Monthly SIP (₹)", current_sip, money_format],
        ["Pre-retirement Returns", pre_ret_rate/100, percent_format],
        ["Post-retirement Returns", post_ret_rate/100, percent_format],
        ["Legacy Amount (₹)", legacy_amount, money_format],
    ]
    
    row = 10
    for item in input_data:
        ws1.write(f'A{row}', item[0], text_format)
        if item[0].endswith('Rate'):
            ws1.write(f'B{row}', item[1], item[2])
        else:
            ws1.write(f'B{row}', item[1], item[2])
        row += 1
    
    # ഫലങ്ങൾ
    row += 1
    ws1.write(f'A{row}', "RESULTS", header_format)
    row += 1
    
    result_data = [
        ["Monthly Expense at Retirement (₹)", st.session_state.res['future_exp']],
        ["Required Retirement Corpus (₹)", st.session_state.res['corp_req']],
        ["Projected Savings (₹)", st.session_state.res['total_sav']],
        ["Shortfall (₹)", st.session_state.res['shortfall']],
        ["Additional SIP Required (₹)", st.session_state.res['req_sip']],
        ["Additional Lumpsum Required (₹)", st.session_state.res['req_lumpsum']],
    ]
    
    for item in result_data:
        ws1.write(f'A{row}', item[0], text_format)
        ws1.write(f'B{row}', item[1], money_format)
        row += 1
    
    # വർക്ക്ഷീറ്റ് 2: വർഷ-wise പിൻവലിക്കൽ ഷെഡ്യൂൾ
    ws2 = workbook.add_worksheet("Yearly Withdrawal")
    ws2.set_column('A:D', 20)
    
    # ഹെഡർ
    headers = ["Age", "Year", "Annual Withdrawal (₹)", "Monthly Amount (₹)"]
    for col, header in enumerate(headers):
        ws2.write(0, col, header, header_format)
    
    # ഡാറ്റ
    if 'annual_withdrawals' in st.session_state.res:
        for row, data in enumerate(st.session_state.res['annual_withdrawals'], 1):
            ws2.write(row, 0, data["Age"], text_format)
            ws2.write(row, 1, data["Year"], text_format)
            ws2.write(row, 2, data["Annual Withdrawal"], money_format)
            ws2.write(row, 3, data["Monthly Amount"], money_format)
    
    workbook.close()
    
    # Excel ഫയൽ ഡൗൺലോഡ് ബട്ടൺ
    st.download_button(
        label="📥 Download Results as Excel (with colors)",
        data=output.getvalue(),
        file_name=f"retirement_plan_{current_age}_{date.today().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    # പഴയ CSV ഓപ്ഷനും നിലനിർത്താം
    output_csv = io.StringIO()
    writer = csv.writer(output_csv)
    
    # Disclaimer in CSV
    writer.writerow(["DISCLAIMER"])
    writer.writerow([DISCLAIMER])
    writer.writerow([])
    
    # ... (പഴയ CSV കോഡ് തുടരും) ...
