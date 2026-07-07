import streamlit as st
from utils import fetch_database_records, check_password

st.set_page_config(page_title="Sales Portal", layout="wide")

# ---> THE UN-BYPASSABLE FIREWALL <---
if not check_password():
    st.stop() # Physically forces Streamlit to stop rendering anything below this line!

# This text will ONLY show if check_password() returned True
st.title("🏠 Sales Department Portal")
st.write("Welcome to the automated reporting system.")
st.info("👈 Please select a report from the menu on the left to begin.")

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refresh All Data", key="home_refresh_btn"):
    fetch_database_records.clear()
    st.rerun()