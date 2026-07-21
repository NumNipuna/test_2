import streamlit as st
import gspread
import json
import os
import base64
import pandas as pd
from google.oauth2.service_account import Credentials


def get_credentials():
    """Centralized function to build credentials from Streamlit secrets."""
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    service_account_info = dict(st.secrets["gcp_service_account"])
    return Credentials.from_service_account_info(service_account_info, scopes=scope)


def get_client():
    return gspread.authorize(get_credentials())

# --- ADD THIS NEW FUNCTION ---
def add_logo():
    logo_path = "logo.png"
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode()
            
        st.markdown(f"""
            <style>
                /* 1. The Logo Background */
                [data-testid="stSidebarNav"] {{
                    background-image: url('data:image/png;base64,{img_base64}');
                    background-repeat: no-repeat;
                    background-position: center 20px;
                    background-size: 160px auto;
                    padding-top: 180px !important; /* Increased to make room for text */
                    position: relative; 
                }}
                
                /* 2. The Company Text Underneath */
                [data-testid="stSidebarNav"]::before {{
                    content: "imo chicken & agro (pvt) ltd";
                    display: block;
                    position: absolute;
                    top: 140px; /* Pushes text just below the logo */
                    width: 100%;
                    text-align: center;
                    font-weight: 700;
                    font-size: 15px;
                    color: #fafafa; /* Use #333333 if your sidebar is white */
                    text-transform: capitalize; 
                }}

                /* 4. Main Content Animation */
                @keyframes fadeInUp {{
                    from {{ transform: translateY(30px); opacity: 0; }}
                    to {{ transform: translateY(0); opacity: 1; }}
                }}
                [data-testid="stMainBlockContainer"] > div {{
                    animation: fadeInUp 0.8s ease-out forwards;
                }}
            </style>
        """, unsafe_allow_html=True)

def hide_chrome_before_login():
    """Hides Streamlit's default header, menu, and sidebar page-nav until the user logs in."""
    if not st.session_state.get("logged_in"):
        st.markdown("""
            <style>
                /* Hide the entire sidebar (this also hides the auto page-nav list) */
                [data-testid="stSidebar"] { display: none !important; }
                [data-testid="collapsedControl"] { display: none !important; }

                /* Hide Streamlit's default top toolbar (hamburger menu, Deploy button) */
                #MainMenu { visibility: hidden; }
                header[data-testid="stHeader"] { 
                    background: transparent !important; 
                    box-shadow: none !important;
                }
                footer { visibility: hidden; }
            </style>
        """, unsafe_allow_html=True)

@st.cache_resource
def connect_to_sheets():
    gc = get_client()
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






USER_DB = {
    "admin":  {"password": "admin",  "allowed_pages": ["all"]},
    "user1":  {"password": "user1",  "allowed_pages": ["Cash_Collection_&_Deposit"]},
    "user2":  {"password": "user2",  "allowed_pages": ["Production_Requirement"]},
    "user3":  {"password": "user3",  "allowed_pages": ["Settings"]},
    "user4":  {"password": "user4",  "allowed_pages": ["Cash_Collection_&_Deposit", "Production_Requirement"]},
}

# Path to a background image for the login screen (transparent PNG or JPG both work)
LOGIN_BG_IMAGE = "logo.png"  # <-- replace with e.g. "login_bg.png" later


def _get_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


def _inject_login_styles():
    bg_b64 = _get_base64(LOGIN_BG_IMAGE)
    bg_css = (
        f'linear-gradient(rgba(16,0,43,0.80), rgba(0,100,148,0.80)), url("data:image/png;base64,{bg_b64}")'
        if bg_b64 else
        "linear-gradient(to right, #10002b, #006494)"
    )

    st.markdown(f"""
        <style>
            /* Full-page background */
            [data-testid="stAppViewContainer"] {{
                background-image: {bg_css};
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
            }}
            [data-testid="stHeader"] {{
                background-color: transparent !important;
            }}

            /* Center the login card vertically */
            .block-container {{
                padding-top: 8vh !important;
            }}

            /* Glassmorphism login card — targets the st.form wrapper */
            div[data-testid="stForm"] {{
                background: rgba(255, 255, 255, 0.10);
                backdrop-filter: blur(14px);
                -webkit-backdrop-filter: blur(14px);
                border: 1px solid rgba(255, 255, 255, 0.25);
                border-radius: 18px;
                padding: 2.5rem 2rem 2rem 2rem;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
                animation: fadeInUp 0.6s ease-out forwards;
            }}

            div[data-testid="stForm"] input {{
                background-color: rgba(255,255,255,0.85) !important;
                border-radius: 8px !important;
            }}

            div[data-testid="stForm"] button {{
                width: 100%;
                border-radius: 8px !important;
                font-weight: 600;
            }}

            .login-title {{
                text-align: center;
                color: #fafafa;
                font-size: 1.6rem;
                font-weight: 700;
                margin-bottom: 0.2rem;
            }}
            .login-subtitle {{
                text-align: center;
                color: #d8d8d8;
                font-size: 0.95rem;
                margin-bottom: 1.5rem;
            }}

            @keyframes fadeInUp {{
                from {{ transform: translateY(30px); opacity: 0; }}
                to {{ transform: translateY(0); opacity: 1; }}
            }}
        </style>
    """, unsafe_allow_html=True)


def check_password():
    """Returns True if authenticated, False otherwise. Renders an attractive login form if not."""

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = None

    # Keep user logged in across refresh via URL param
    if "username" in st.query_params and not st.session_state["logged_in"]:
        qp_user = st.query_params["username"]
        if qp_user in USER_DB:
            st.session_state["logged_in"] = True
            st.session_state["username"] = qp_user

    if st.session_state["logged_in"]:
        st.sidebar.markdown(f"👤 **User:** {st.session_state['username']}")
        st.sidebar.markdown("---")
        if st.sidebar.button("🔒 Log Out", key="global_logout_btn"):
            st.session_state["logged_in"] = False
            st.session_state["username"] = None
            st.query_params.clear()
            st.rerun()
        return True

    # ---------- Login UI ----------
    _inject_login_styles()

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_form"):
            st.markdown('<div class="login-title">🔐 Sales Portal</div>', unsafe_allow_html=True)
            st.markdown('<div class="login-subtitle">Sign in to continue</div>', unsafe_allow_html=True)

            username = st.text_input("Username", key="auth_username_input")
            password = st.text_input("Password", type="password", key="auth_password_input")
            submitted = st.form_submit_button("Log In", type="primary")

            if submitted:
                if username in USER_DB and USER_DB[username]["password"] == password:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    st.query_params["username"] = username
                    st.rerun()
                else:
                    st.error("❌ Invalid Username or Password")

    return False


def check_access(page_name):
    if not st.session_state.get("logged_in"):
        return False
    username = st.session_state.get("username")
    if not username or username not in USER_DB:
        return False
    allowed_pages = USER_DB[username]["allowed_pages"]
    if "all" in allowed_pages:
        return True
    return page_name in allowed_pages


##############################################

import json
from google.oauth2.service_account import Credentials
import streamlit as st

def get_client():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # JSON string එක parse කරගන්නවා
    service_account_info = json.loads(st.secrets["gcp_service_account"])
    
    credentials = Credentials.from_service_account_info(
        service_account_info,
        scopes=scope
    )
    return gspread.authorize(credentials)

# ----- Master Data Load කරන්න -----
def load_master_data():
    """Master Data Load කරන්න - දැන් connect_to_sheets2() භාවිතා කරයි"""
    sh = connect_to_sheets2()  # <--- මෙතනදී connect_to_sheets2() දාන්න
    try:
        ws = sh.worksheet("MasterData")
        records = ws.get_all_records()
        return records
    except gspread.exceptions.WorksheetNotFound:
        # MasterData නැතිනම් හදාගෙන හිස් ලිස්ට් එකක් දෙන්න
        ws = sh.add_worksheet(title="MasterData", rows=500, cols=20)
        ws.append_row(["No", "Manager", "Route", "Representative", "Status"])
        return []
    
def load_targets_for_month(month):
    """Specific මාසයක Target data Load කරන්න"""
    sh = connect_to_sheets2()
    try:
        ws = sh.worksheet("MonthlyTargets")
        records = ws.get_all_records()
        df_all = pd.DataFrame(records)
        if df_all.empty:
            return pd.DataFrame()
        df_month = df_all[df_all["Month"] == month]
        if not df_month.empty and "No" in df_month.columns:
            return df_month[["No", "Target"]]
        return pd.DataFrame()
    except gspread.exceptions.WorksheetNotFound:
        return pd.DataFrame()
    

# ----- Master Data Update කරන්න (Settings වලින්) -----
def update_master_data(df):
    client = get_client()
    sheet = client.open("Sales data2").worksheet("MasterData")
    
    # පැරණි දත්ත මකන්න (Header එක හැර)
    all_rows = sheet.get_all_values()
    if len(all_rows) > 1:
        sheet.delete_rows(2, len(all_rows))
    
    # හෙඩර් එක නැවත ලියන්න (DataFrame එකේ තියෙන Columns)
    headers = df.columns.tolist()
    if not sheet.get_all_values():  # හිස් නම් header දාන්න
        sheet.append_row(headers)
    
    # අලුත් දත්ත rows විදියට දාන්න
    for _, row in df.iterrows():
        sheet.append_row(row.tolist())
    return True

# ----- Monthly Targets Save කරන්න (මාසය අනුව) -----
def save_monthly_data(month, data_list):
    client = get_client()
    sheet = client.open("Sales data2").worksheet("MonthlyTargets")
    
    # 1. ඒ මාසයට අදාළ පැරණි පේළි හොයා මකන්න (අනිත් මාස වලට හානි නොවෙන්න)
    all_values = sheet.get_all_values()
    rows_to_delete = []
    if len(all_values) > 1:  # Header එක හැර
        for idx, row in enumerate(all_values, start=1):
            if idx == 1:
                continue  # Header එක පැත්තකින් තියන්න
            if len(row) > 0 and row[0] == month:
                rows_to_delete.append(idx)
    
    # පහළින් ඉඳලා මකන්න (ඉහළින් මැකුවොත් index මාරු වෙන නිසා)
    for idx in sorted(rows_to_delete, reverse=True):
        sheet.delete_rows(idx)
    
    # 2. අලුත් දත්ත එකතු කරන්න
    for row in data_list:
        new_row = [
            month,
            row.get("No", ""),
            row.get("Manager", ""),
            row.get("Route", ""),
            row.get("Representative", ""),
            row.get("Status", ""),
            row.get("Target", "")
        ]
        sheet.append_row(new_row)
    
    return True


@st.cache_resource
def connect_to_sheets2():
    gc = get_client()
    sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1xO3xNDYkC-97BHksfiq9BRpJ9rDP9_snTzTLP-sJbMg/edit?usp=sharing")
    return sh

def save_monthly_data(month, data_list):
    """
    Save monthly targets to the same Google Sheet used by connect_to_sheets().
    """
    # මෙතනදී get_client() වෙනුවට connect_to_sheets() භාවිතා කරන්න
    sh = connect_to_sheets2()
    
    # MonthlyTargets Tab එක හොයන්න, නැතිනම් හදාගන්න
    try:
        ws = sh.worksheet("MonthlyTargets")
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title="MonthlyTargets", rows=1000, cols=20)
        ws.append_row(["Month", "No", "Manager", "Route", "Representative", "Status", "Target"])
    
    # ඒ මාසයට අදාළ පැරණි දත්ත මකන්න (Duplicate නොවෙන්න)
    all_values = ws.get_all_values()
    rows_to_delete = []
    if len(all_values) > 1:
        for idx, row in enumerate(all_values, start=1):
            if idx == 1:
                continue  # Header එක පැත්තකින් තියන්න
            if len(row) > 0 and row[0] == month:
                rows_to_delete.append(idx)
    
    # පහළින් ඉඳලා මකන්න (index මාරු නොවෙන්න)
    for idx in sorted(rows_to_delete, reverse=True):
        ws.delete_rows(idx)
    
    # අලුත් දත්ත එකතු කරන්න
    for row in data_list:
        new_row = [
            month,
            row.get("No", ""),
            row.get("Manager", ""),
            row.get("Route", ""),
            row.get("Representative", ""),
            row.get("Status", ""),
            row.get("Target", "")
        ]
        ws.append_row(new_row)
    
    return True 


# ----- Sales Day Book -----
def get_sales_daybook_ws():
    """Get (or create) the Sales_day_book worksheet."""
    sh = connect_to_sheets2()
    try:
        ws = sh.worksheet("Sales_day_book")
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title="Sales_day_book", rows=2000, cols=20)
        ws.append_row(["new_date", "Date", "Agent", "Customer ID", "Customer",
                        "Group", "Invoice", "Item", "Qty", "Amount", "VAT"])
    return ws

def get_rows_for_date(ws, date_col_name, date_value):
    """Return all rows from ws where date_col_name matches date_value."""
    records = ws.get_all_records()
    df = pd.DataFrame(records)
    if df.empty or date_col_name not in df.columns:
        return pd.DataFrame()
    return df[df[date_col_name].astype(str) == str(date_value)]

def delete_rows_for_date(ws, date_col_name, date_value):
    """Delete all rows from ws where date_col_name matches date_value.
    Uses a single batched API call instead of one call per row (avoids rate limits)."""
    all_values = ws.get_all_values()
    if len(all_values) < 2:
        return
    header = all_values[0]
    if date_col_name not in header:
        return
    col_idx = header.index(date_col_name)
    target = pd.to_datetime(date_value).normalize()

    rows_to_delete = []
    for idx, row in enumerate(all_values, start=1):
        if idx == 1:
            continue
        if len(row) > col_idx and row[col_idx].strip():
            cell_date = pd.to_datetime(row[col_idx].strip(), errors="coerce")
            if pd.notna(cell_date) and cell_date.normalize() == target:
                rows_to_delete.append(idx)

    if not rows_to_delete:
        return

    # --- Group consecutive row numbers into ranges, e.g. [5,6,7,10,11] -> [(5,7),(10,11)] ---
    rows_to_delete.sort()
    ranges = []
    start = prev = rows_to_delete[0]
    for r in rows_to_delete[1:]:
        if r == prev + 1:
            prev = r
        else:
            ranges.append((start, prev))
            start = prev = r
    ranges.append((start, prev))

    # --- Build one batch_update request with all delete ranges ---
    # Delete from bottom to top so earlier deletions don't shift later ranges
    sheet_id = ws.id
    requests = []
    for (start_row, end_row) in reversed(ranges):
        requests.append({
            "deleteDimension": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "ROWS",
                    "startIndex": start_row - 1,   # 0-indexed, inclusive
                    "endIndex": end_row              # 0-indexed, exclusive
                }
            }
        })

    ws.spreadsheet.batch_update({"requests": requests})