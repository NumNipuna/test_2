import streamlit as st
import gspread

@st.cache_resource
def connect_to_sheets():
    gc = gspread.service_account(filename="service_account.json")
    sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1TWSwwcEElojBnoqY_hPllfb3l9xn1_9ed4Xy4FQdq98/edit")
    return sh

@st.cache_data
def fetch_database_records():
    sh = connect_to_sheets()
    main_records = sh.worksheet("Data_Entry").get_all_records()
    reps_records = sh.worksheet("Sales_Reps").get_all_records()
    try:
        banks_records = sh.worksheet("Banks").get_all_records()
    except:
        banks_records = []
    return main_records, reps_records, banks_records

def check_password():
    """Returns True if authorized, False if unauthorized (handling UI display)."""
    # 1. Check if browser URL has a valid login token (keeps user logged in on refresh)
    if "user_logged_in" in st.query_params and st.query_params["user_logged_in"] == "true":
        st.session_state["logged_in"] = True

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    # 2. If already logged in, show the Logout button and return True
    if st.session_state["logged_in"]:
        st.sidebar.markdown("---")
        if st.sidebar.button("🔒 Log Out", key="global_logout_btn"):
            st.session_state["logged_in"] = False
            st.query_params.clear() # Clears URL parameters
            st.rerun()
        return True

    # 3. Show Login UI if they aren't authenticated yet
    st.title("🔐 Sales Portal Login")
    username = st.text_input("Username", key="auth_username_input")
    password = st.text_input("Password", type="password", key="auth_password_input")
    
    USER_CREDENTIALS = {
        "admin": "admin123",
        "niroshan": "sales2026",
        "testuser": "password123"
    }
    
    if st.button("Log In", type="primary", key="auth_login_btn"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.session_state["logged_in"] = True
            st.query_params["user_logged_in"] = "true" # Save login status to browser URL
            st.rerun()
        else:
            st.error("❌ Invalid Username or Password")
            
    return False