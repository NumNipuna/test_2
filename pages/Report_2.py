import streamlit as st
import pandas as pd
from utils import fetch_database_records

from utils import connect_to_sheets, fetch_database_records, check_password

st.set_page_config(page_title="Report 2", layout="wide")

if not check_password():
    st.stop()

st.title("📊 Report 2: Sample Report")


# Create tabs just like Report 1
tab1, tab2, tab3 = st.tabs(["tab 1", "tab 2","tab 3"])

with tab1:
    st.header("Data Analysis")
    st.write("This is a blank template for your next report.")
    
with tab2:
    st.write("Settings for Report 2")