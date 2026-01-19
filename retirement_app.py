
import streamlit as st

# --- MAINTENANCE PAGE CONFIGURATION ---
st.set_page_config(page_title="App Under Maintenance", layout="centered")

# --- UI DISPLAY ---
st.markdown("<br><br><br>", unsafe_allow_html=True) # സ്പേസിന് വേണ്ടി

# മെയിന്റനൻസ് അറിയിപ്പ്
st.error("## ⚠️ App Under Maintenance")

st.markdown("""
### Please Try Again Later
We are currently performing scheduled maintenance to improve our services. 
Our app will be back online shortly. We apologize for any inconvenience caused.
""")

# ഒരു ചെറിയ ലോഡിംഗ് ഐക്കൺ പോലെ തോന്നിക്കാൻ
with st.spinner('Updating system...'):
    pass

st.divider()
st.info("For urgent queries, please contact the administrator.")
