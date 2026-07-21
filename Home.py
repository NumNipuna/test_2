import streamlit as st
from utils import fetch_database_records, check_password, add_logo, check_access # Import the functions
import os
import base64
from utils import get_client
client = get_client()

st.set_page_config(page_title="Sales Portal", layout="wide")

add_logo()



# ================================================================================================

st.markdown("""
    <style>
        /* 2. Header and core element block wrappers color or (transparent is better) */
        [data-testid="stHeader"], [data-testid="stVerticalBlock"] {
            background-color: transparent !important;
        }

        /* 3. change title sub title, chart title color (transparent can be used) */
        [data-testid="stElementContainer"] div[data-testid="stMarkdownContainer"] {
            background-color: transparent !important;
            border-radius: 8px
        }
        
        /* 4. Fix Plotly chart background containers specifically so they don't leak (looks like unnecessary)*/
        .js-plotly-plot .plotly, .user-select-none {
            background-color: #ffffff !important;
            border-radius: 12px;
        }

        
        /* Customize space between title and top ----------------------------------------------------------*/
        
        [data-testid="stAppViewContainer"] .block-container {
            padding-top: 1.5rem !important;       /* Default is close to 6rem; 1rem = 16px */
            padding-bottom: 1.5rem !important;    /* Space in bottom (last plot and bottom)
        /*-------------------------------------------------------------------------------------------------*/
    </style>
""", unsafe_allow_html=True)


#---------------------------------------------------------------
#Animation for the main content to fade in from the bottom
st.markdown("""
    <style>
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(to right,#10002b, #006494);
        }
        
        /* Your animations can live here safely */
        @keyframes fadeInUp {
            from { transform: translateY(30px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        [data-testid="stMainBlockContainer"] > div {
            animation: fadeInUp 0.8s ease-out forwards;
        }
    </style>
""", unsafe_allow_html=True)
#---------------------------------------------------------------


# ---> THE UN-BYPASSABLE FIREWALL <---
#if not check_password():
#    st.stop() # Physically forces Streamlit to stop rendering anything below this line!


# --- Inside pages/dashboard.py ---

# 1. Require login first
if not check_password():
    st.stop()

# 2. Check if this specific user has access to this specific page
# The string here MUST match the exact string in their "allowed_pages" list
if not check_access("Dashboard"):
    st.error("🚫 You do not have permission to view this page.")
    st.stop() # Immediately halts execution of the rest of the page

# --- The rest of your page code goes here ---
st.title("Dashboard")
st.write("Welcome to the dashboard. Only user1 and master_admin can see this.")



# This text will ONLY show if check_password() returned True
st.title("🏠 Sales Department Portal")
st.write("Welcome to the automated reporting system.")
st.info("👈 Please select a report from the menu on the left to begin.")

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refresh All Data", key="home_refresh_btn"):
    fetch_database_records.clear()
    st.rerun()