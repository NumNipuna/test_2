import streamlit as st
import gspread
import json
import os
import base64

# --- ADD THIS NEW FUNCTION ---

creds_dict = json.loads(st.secrets["google_sheets_creds"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
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