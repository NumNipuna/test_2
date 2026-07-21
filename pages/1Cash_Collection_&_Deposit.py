import gspread
import streamlit as st
import pandas as pd
import streamlit.components.v1 as components  
from gspread_dataframe import set_with_dataframe
from utils import connect_to_sheets, fetch_database_records, add_logo,check_password, check_access # Import the functions
import datetime 
import time 
import plotly.express as px
import base64
import plotly.graph_objects as go
from oauth2client.service_account import ServiceAccountCredentials
import io
from xhtml2pdf import pisa
from utils import get_client
client = get_client()


st.set_page_config(page_title=" Cash Collection & Cash Deposit", layout="wide")

add_logo()
# --- CUSTOM CSS FOR BRANDING & STYLING --------------------------------------------------------------------------------
# Using a professional corporate theme (Deep Blues, Teals, and Clean Greys)


st.markdown("""
<style>
/* =========================================================
   CUSTOM EARTHY SUNSET THEME
   Palette:
   #edc951 (gold)
   #eb6841 (orange)
   #cc2a36 (deep red)
   #4f372d (dark brown)
   #00a0b0 (teal)
========================================================= */

/* Animated gradient app background */
.stApp {
    background: linear-gradient(135deg, #4f372d 0%, #cc2a36 25%, #eb6841 50%, #edc951 75%, #00a0b0 100%);
    background-size: 400% 400%;
    animation: gradientShift 22s ease infinite;
}

@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* Main frosted glass container */
.block-container {
    background: rgba(28, 20, 18, 0.84);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border-radius: 26px;
    padding: 2rem 2.6rem 3rem 2.6rem !important;
    margin-top: 1rem;
    box-shadow: 0 12px 42px rgba(0,0,0,0.40);
    border: 1px solid rgba(237,201,81,0.18);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #4f372d 0%, #2d211c 100%);
}
[data-testid="stSidebar"] * {
    color: #f8f5ef !important;
}

/* Headings */
h1, h2, h3 {
    color: #f8f5ef;
    font-weight: 800;
}

h1 {
    background: linear-gradient(135deg, #edc951, #eb6841);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Tabs */
button[data-baseweb="tab"] {
    background: linear-gradient(135deg, #f5efe6 0%, #ead9c7 100%) !important;
    border-radius: 14px 14px 0 0 !important;
    padding: 10px 22px !important;
    margin-right: 6px !important;
    font-weight: 700 !important;
    color: #4f372d !important;
    border: none !important;
    transition: all 0.25s ease;
}

button[data-baseweb="tab"]:hover {
    background: linear-gradient(135deg, #edc951 0%, #eb6841 100%) !important;
    color: #2b1f1a !important;
    transform: translateY(-2px);
}

button[data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #cc2a36 0%, #4f372d 100%) !important;
    color: white !important;
    box-shadow: 0 4px 14px rgba(204,42,54,0.45);
}

[data-baseweb="tab-highlight"] {
    background-color: transparent !important;
}

[data-baseweb="tab-border"] {
    display: none !important;
}

[data-baseweb="tab-list"] {
    gap: 2px;
}

/* Buttons */
.stButton>button,
.stDownloadButton>button {
    border-radius: 10px;
    border: none;
    background: linear-gradient(135deg, #eb6841 0%, #cc2a36 100%);
    color: white !important;
    font-weight: 700;
    padding: 0.5rem 1.3rem;
    box-shadow: 0 4px 12px rgba(204,42,54,0.35);
    transition: all .2s ease;
}

.stButton>button:hover,
.stDownloadButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 18px rgba(204,42,54,0.5);
}

/* Dataframe / data editor */
[data-testid="stDataFrame"],
[data-testid="stDataEditor"] {
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 4px 18px rgba(0,0,0,0.14);
    border: 1px solid rgba(237,201,81,0.28);
}

/* Divider */
hr {
    border-top: 2px solid rgba(237,201,81,0.22) !important;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: linear-gradient(
        135deg,
        rgba(237,201,81,0.10) 0%,
        rgba(0,160,176,0.10) 100%
    );
    border-radius: 16px;
    padding: 1rem;
    box-shadow: 0 4px 14px rgba(0,0,0,0.18);
    border: 1px solid rgba(237,201,81,0.18);
}

/* File uploader */
[data-testid="stFileUploader"] {
    border-radius: 14px;
    padding: 0.6rem;
    background: rgba(255,255,255,0.05);
    border: 1px dashed #edc951;
}

/* Section banner */
.section-banner {
    background: linear-gradient(135deg, #00a0b0 0%, #4f372d 100%);
    color: white;
    padding: 14px 20px;
    border-radius: 14px;
    font-size: 20px;
    font-weight: 800;
    margin-bottom: 14px;
    box-shadow: 0 4px 14px rgba(0,160,176,0.30);
}

/* Success / warning / error accents */
.stAlert {
    border-radius: 12px;
}

.stSuccess {
    border-left: 6px solid #00a0b0 !important;
}

.stWarning {
    border-left: 6px solid #edc951 !important;
}

.stError {
    border-left: 6px solid #cc2a36 !important;
}

/* General text */
html, body, [class*="css"] {
    color: #f8f5ef;
}
            
/* 5. Custom Isolated Metric Card UI styling */
        .metric-card {
            background-color: #ffffff !important;                           /* Change KPI Card color here */
            padding: 10px;                                                  /* Change height of KPI card */                              
            border-radius: 12px;                                            /* Change border radius */
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;           /* Modern, soft UI shadow */
            border-left: 20px solid;                                        /*color currently this is over write from belowe html code */
            text-align: center;
            /* max-width: 250px; */                /* if we add KPI cards in raw wise, these line */
            /* margin: 0 auto 20px auto; */        /* needs to edit KPI cards */
        }
        .metric-value {
            font-size: 32px;                    /* font size of KPI card value */
            font-weight: bolder;                /* font weight of KPI card value ex :- bolder, normal, 500, 600, 900*/
            color: #11001c !important;          /* change font color */
        }
        .metric-label {
            font-size: 17px;                    /* Change KPI card label font size */
            color: #11001c !important;          /* Change KPI Card font label color */
            font-weight: bolder;                /* font weight of KPI card lable ex :- bolder, normal, 500, 600, 900*/
            text-transform: uppercase;          /* Keep always KPI card label in uppercase */ 
            letter-spacing: 1px;                /* Space between two letters in KPI card label */
            margin-top: 3px;
        }

</style>
""", unsafe_allow_html=True)

#---------------------------------------------------------------
#Animation for the main content to fade in from the bottom
st.markdown("""
    <style>
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(to right,#290025, #5e548e);
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


#if not check_password():
#    st.stop()



# Require login
if not check_password():
    st.stop()

# Check access specifically for THIS page
if not check_access("Cash_Collection_&_Deposit"):
    st.error("🚫 You do not have permission to view this page.")
    st.stop()


#-------------------------------------------------------------------------


st.title("Cash Collection & Cash Deposit")

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refresh All Data", key="home_refresh_btn"):
    fetch_database_records.clear()
    st.rerun()

# Load data using our helper file
try:
    main_records, reps_records, banks_records = fetch_database_records()
    sh = connect_to_sheets()
    ws_main = sh.worksheet("Data_Entry")
except Exception as e:
    st.error(f"Error connecting to Google Sheets: {e}")
    st.stop()

tab1, tab2, tab3 = st.tabs(["Data Entry", "Daily Cash Collection", "Dashboard"])

# 600 seconds = 10 minutes
@st.cache_data(ttl=600)
def fetch_database_records():
    # Your code that downloads main_records, reps_records, etc.
    return data

 

with tab1:
    st.header("Enter Transactions")
    
    # --- 1. Load Data ---
    # (This uses cached data unless it expires or is manually cleared)
    df_main = pd.DataFrame(main_records) if main_records else pd.DataFrame(columns=["Sales Rep", "Date", "Total Cash Collection", "Cash Deposit", "Cash Deposit Date", "Bank", "Cash In Hand", "Balance"])
    df_reps = pd.DataFrame(reps_records) if reps_records else pd.DataFrame(columns=["Rep Name"])
    df_banks = pd.DataFrame(banks_records) if banks_records else pd.DataFrame(columns=["Bank Name"])

    # --- 2. Extract Lists ---
    rep_list = []
    if "Rep Name" in df_reps.columns:
        rep_list = df_reps["Rep Name"].dropna().tolist()
    elif "Rep_Name" in df_reps.columns: 
        rep_list = df_reps["Rep_Name"].dropna().tolist()

    bank_list = []
    if "Bank Name" in df_banks.columns:
        bank_list = df_banks["Bank Name"].dropna().astype(str).tolist()
        
    # --- 3. Select Rep ---
    selected_rep = st.selectbox("Select a Sales Rep:", [""] + rep_list)
    
    if selected_rep != "":
        st.subheader(f"Add New Transaction for: {selected_rep}")
        
        # --- 4. DEDICATED DATA ENTRY FORM ---
        with st.form("new_transaction_form", clear_on_submit=True):
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            
            with col1:
                entry_date = st.date_input("Date", value=datetime.date.today())
            with col2:
                total_collection = st.text_input("Collection", placeholder="0.00", key="collection_input")
            with col3:
                cash_deposit = st.text_input("Deposit", placeholder="0.00", key="deposit_input")
            with col4:
                deposit_date = st.date_input("Deposit Date", value=datetime.date.today())
            with col5:
                bank_name = st.selectbox("Bank", [""] + bank_list)
            with col6:
                cash_in_hand = st.text_input("Cash In Hand", placeholder="0.00", key="cash_in_hand_input")

            components.html(r"""
            <script>
            (function() {
                const targetLabels = ["Collection", "Deposit", "Cash In Hand"];

                function setNativeValue(el, value) {
                    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                    setter.call(el, value);
                    el.dispatchEvent(new Event("input", { bubbles: true }));
                }

                function formatWithCommas(el) {
                    const cursor = el.selectionStart;
                    const oldLen = el.value.length;

                    let raw = el.value.replace(/[^0-9.]/g, "");
                    const firstDot = raw.indexOf(".");
                    if (firstDot !== -1) {
                        raw = raw.slice(0, firstDot + 1) + raw.slice(firstDot + 1).replace(/\./g, "");
                    }

                    let [intPart, decPart] = raw.split(".");
                    intPart = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
                    const formatted = decPart !== undefined ? intPart + "." + decPart : intPart;

                    if (formatted === el.value) return;
                    setNativeValue(el, formatted);

                    const newPos = Math.max(0, cursor + (formatted.length - oldLen));
                    el.setSelectionRange(newPos, newPos);
                }

                function attach() {
                    targetLabels.forEach(function(label) {
                        const input = window.parent.document.querySelector('input[aria-label="' + label + '"]');
                        if (input && !input.dataset.commaBound) {
                            input.dataset.commaBound = "true";
                            input.addEventListener("input", function() { formatWithCommas(input); });
                        }
                    });
                }

                attach();
                new MutationObserver(attach).observe(window.parent.document.body, { childList: true, subtree: true });
            })();
            </script>
            """, height=0)
                
            submit_btn = st.form_submit_button("Submit New Transaction", type="primary")

            if submit_btn:
                def parse_amount(text_value):
                    cleaned = (text_value or "").replace(",", "").strip()
                    try:
                        return float(cleaned) if cleaned else 0.0
                    except ValueError:
                        return 0.0

                safe_collection = parse_amount(total_collection)
                safe_deposit = parse_amount(cash_deposit)
                safe_in_hand = parse_amount(cash_in_hand)

                balance = safe_collection - safe_deposit
                
                new_row = [
                    selected_rep,
                    entry_date.strftime('%Y-%m-%d'),
                    safe_collection,
                    safe_deposit,
                    deposit_date.strftime('%Y-%m-%d'),
                    bank_name,
                    safe_in_hand,
                    balance
                ]
                
                with st.spinner("Adding new transaction..."):
                    # Append ONLY the new row to the database
                    ws_main.append_row(new_row)
                    
                    # 1. Create a temporary placeholder
                    msg_placeholder = st.empty()
                    
                    # 2. Put the success message inside the placeholder
                    msg_placeholder.success("New transaction successfully saved to Google Sheets!")
                    
                    # 3. Wait for n seconds
                    time.sleep(1)  # Adjust the time as needed for user visibility
                    
                    # 4. Clear the placeholder so the message disappears
                    msg_placeholder.empty()
        
        st.divider()
        
        
        if not df_main.empty and "Sales Rep" in df_main.columns:
            rep_data = df_main[df_main["Sales Rep"] == selected_rep].copy()
        else:
            rep_data = pd.DataFrame(columns=["Sales Rep", "Date", "Total Cash Collection", "Cash Deposit", "Cash Deposit Date", "Bank", "Cash In Hand", "Balance"])
            
        if "Date" in rep_data.columns:
            rep_data["Date"] = pd.to_datetime(rep_data["Date"], errors="coerce")
        if "Cash Deposit Date" in rep_data.columns:
            rep_data["Cash Deposit Date"] = pd.to_datetime(rep_data["Cash Deposit Date"], errors="coerce")
        if "Cash In Hand" in rep_data.columns:
            rep_data["Cash In Hand"] = pd.to_numeric(rep_data["Cash In Hand"], errors="coerce").fillna(0.0)
            
        edited_data = st.data_editor(
            rep_data,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            column_config={
                "Sales Rep": st.column_config.TextColumn("Sales Rep", disabled=True),
                "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                "Total Cash Collection": st.column_config.NumberColumn("Total Cash Collection", format="%,.2f"),
                "Cash Deposit": st.column_config.NumberColumn("Cash Deposit", format="%,.2f"),
                "Cash Deposit Date": st.column_config.DateColumn("Cash Deposit Date", format="YYYY-MM-DD"),
                "Bank": st.column_config.SelectboxColumn("Bank", options=bank_list),
                "Cash In Hand": st.column_config.NumberColumn("Cash In Hand", format="%,.2f"),
                "Balance": st.column_config.NumberColumn("Balance", format="%,.2f", disabled=True)
            }
        )
        
        if st.button("Update Edited History"):
            with st.spinner("Saving bulk changes to Google Sheets..."):
                edited_data["Total Cash Collection"] = pd.to_numeric(edited_data["Total Cash Collection"]).fillna(0)
                edited_data["Cash Deposit"] = pd.to_numeric(edited_data["Cash Deposit"]).fillna(0)
                edited_data["Balance"] = edited_data["Total Cash Collection"] - edited_data["Cash Deposit"]
                
                if "Date" in edited_data.columns:
                    edited_data["Date"] = pd.to_datetime(edited_data["Date"], errors="coerce").dt.strftime('%Y-%m-%d').fillna("")
                if "Cash Deposit Date" in edited_data.columns:
                    edited_data["Cash Deposit Date"] = pd.to_datetime(edited_data["Cash Deposit Date"], errors="coerce").dt.strftime('%Y-%m-%d').fillna("")
                
                edited_data["Sales Rep"] = selected_rep
                
                if not df_main.empty and "Sales Rep" in df_main.columns:
                    df_main_cleaned = df_main[df_main["Sales Rep"] != selected_rep]
                    final_df = pd.concat([df_main_cleaned, edited_data], ignore_index=True)
                else:
                    final_df = edited_data
                
                ws_main.clear()
                # from gspread_dataframe import set_with_dataframe
                set_with_dataframe(ws_main, final_df)
                
                fetch_database_records.clear()
                
                # Show the success message
                st.toast("✅ Historical edits successfully saved!")
                
                # Pause the script for 2 seconds so the user can see the message
                time.sleep(2) 
                
                # Now refresh the page
                st.rerun()

with tab2:
        st.markdown("<h2 style='text-align: left;'>Daily Cash Collection</h2>", unsafe_allow_html=True)
        
        selected_date = st.date_input(
            label="Select Date for Report",
            value=None,                      # Starts completely blank
            format="DD/MM/YYYY",             # Formats to Day/Month/Year
            max_value=datetime.date.today(), # Grays out any future dates on the calendar
            help="Pick a date to generate the collection and deposit summary."
        )
        

        # Add logo
        def get_base64_logo(path):
            with open(path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()

        logo_base64 = get_base64_logo("C:/Users/Asus/Desktop/Python/Sales departmet reports/Sales_App/logo.png")
        
        # 1. Authenticate and Connect to the Separate Google Sheet
        @st.cache_data(ttl=660)
        def load_google_sheet_data():
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            file_path = 'C:/Users/Asus/Desktop/Python/Sales departmet reports/Sales_App/service_account.json'
            creds = ServiceAccountCredentials.from_json_keyfile_name(file_path, scope)
            client = gspread.authorize(creds) 
            
            sheet_daily = client.open("Sales data").worksheet("Data_Entry")
            data_daily = sheet_daily.get_all_records()
            return pd.DataFrame(data_daily)

        # Call the cached function (Streamlit uses memory instead of downloading again)
        df_main = load_google_sheet_data()

        df_display = df_main.copy()
        
        # Ensure a date is selected and data exists
        if selected_date and not df_display.empty and "Date" in df_display.columns:
            df_display['Date'] = pd.to_datetime(df_display['Date'], errors='coerce')
            daily_report = df_display[df_display['Date'].dt.date == selected_date].copy()
            
            if not daily_report.empty:
                col1, col2 = st.columns(2)
                
                # --- METRIC CARDS ---
                with col1:
                    total_coll = daily_report["Total Cash Collection"].sum()
                    if total_coll >= 1000000:
                        st.markdown(f'<div class="metric-card" style="border-left-color:#a53860;"><div class="metric-value">LKR {total_coll/1000000:,.2f} M</div><div class="metric-label">Total Cash Collection</div></div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="metric-card" style="border-left-color:#a53860;"><div class="metric-value">LKR {total_coll:,.2f}</div><div class="metric-label">Total Cash Collection</div></div>', unsafe_allow_html=True)
                
                with col2:
                    total_dep = daily_report["Cash Deposit"].sum()
                    if total_dep >= 1000000:    
                        st.markdown(f'<div class="metric-card" style="border-left-color:#38b000;"><div class="metric-value">LKR {total_dep/1000000:,.2f} M</div><div class="metric-label">Total Cash Deposits</div></div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="metric-card" style="border-left-color:#38b000;"><div class="metric-value">LKR {total_dep:,.2f}</div><div class="metric-label">Total Cash Deposits</div></div>', unsafe_allow_html=True)
                
                # --- DATA PREPARATION ---
                display_df = daily_report.copy()
                display_df['Bank'] = display_df['Bank'].astype(str).str[:3]
                display_df['Total Cash Collection'] = display_df['Total Cash Collection'].replace(0, None)
                display_df = display_df.sort_values('Sales Rep')

                st.subheader("Detailed Transactions")
                
                html_table = """
                <style>
                .custom-table { 
                    width: 100%; 
                    border-collapse: separate;
                    border-spacing: 0;
                    margin-top: 10px; 
                    font-family: 'Segoe UI', Arial, sans-serif; 
                    font-size: 14px;
                    color: #fafafa;
                    border-radius: 12px;
                    overflow: hidden;
                }
                .custom-table th { 
                    background-color: #262730; 
                    color: #55a630; 
                    padding: 12px; 
                    border: 1px solid #444; 
                    text-align: left; 
                    font-weight: bold; 
                    font-size: 15px;
                }
                .custom-table td { 
                    padding: 10px; 
                    border: 1px solid #444; 
                    text-align: left; 
                    background-color: #0e1117; 
                }
                .custom-table tr:hover td { background-color: #1a1c23; }

                .custom-table th:first-child { border-top-left-radius: 12px; }
                .custom-table th:last-child { border-top-right-radius: 12px; }
                .custom-table tr:last-child td:first-child { border-bottom-left-radius: 12px; }
                .custom-table tr:last-child td:last-child { border-bottom-right-radius: 12px; }
                </style>
                <table class="custom-table">
                    <thead>
                        <tr>
                            <th>Sales Rep</th>
                            <th>Total Cash Collection</th>
                            <th>Cash Deposit</th>
                            <th>Cash Deposit Date</th>
                            <th>Bank</th>
                        </tr>
                    </thead>
                    <tbody>
                """

                # --- 2. BUILD THE PDF TABLE (LIGHT MODE) ---
                pdf_table_style = """
                <table width="100%" cellpadding="6" cellspacing="0" style="border-collapse: collapse; font-family: Helvetica, sans-serif; font-size: 11px;">
                    <thead>
                        <tr style="background-color: #262730; color: white;">
                            <th align="left" style="border: 1px solid #ddd;">Sales Rep</th>
                            <th align="left" style="border: 1px solid #ddd;">Total Cash Collection</th>
                            <th align="left" style="border: 1px solid #ddd;">Cash Deposit</th>
                            <th align="left" style="border: 1px solid #ddd;">Deposit Date</th>
                            <th align="left" style="border: 1px solid #ddd;">Bank</th>
                        </tr>
                    </thead>
                    <tbody>
                """

                current_rep = None
                table_rows = "" # Used for PDF table logic
                
                # Loop through rows ONCE to build both the Dark UI table and the Light PDF table
                for index, row in display_df.iterrows():
                    rep = str(row['Sales Rep'])
                    
                    collection_val = row['Total Cash Collection']
                    deposit_val = row['Cash Deposit']
                    
                    collection = f"LKR {float(collection_val):,.2f}" if pd.notnull(collection_val) else ""
                    deposit = f"LKR {float(deposit_val):,.2f}" if pd.notnull(deposit_val) and deposit_val != 0 else ""
                    dep_date = str(row['Cash Deposit Date']) if pd.notnull(row['Cash Deposit Date']) else ""
                    bank = str(row['Bank']) if pd.notnull(row['Bank']) else ""

                    html_table += "<tr>"
                    table_rows += "<tr>"
                    
                    if rep != current_rep:
                        rowspan = len(display_df[display_df['Sales Rep'] == rep])
                        
                        # Add to UI Table
                        html_table += f"<td rowspan='{rowspan}' style='vertical-align: middle; font-weight: bold;'>{rep}</td>"
                        html_table += f"<td rowspan='{rowspan}' style='vertical-align: middle;'>{collection}</td>"
                        
                        # Add to PDF Table
                        table_rows += f"<td rowspan='{rowspan}' align='left' valign='middle' style='border: 1px solid #ddd; font-weight: bold;'>{rep}</td>"
                        table_rows += f"<td rowspan='{rowspan}' align='left' valign='middle' style='border: 1px solid #ddd;'>{collection}</td>"
                        
                        current_rep = rep
                        
                    # UI Table Columns
                    html_table += f"<td>{deposit}</td><td>{dep_date}</td><td>{bank}</td></tr>"
                    
                    # PDF Table Columns
                    table_rows += f"<td align='left' style='border: 1px solid #ddd;'>{deposit}</td>"
                    table_rows += f"<td align='left' style='border: 1px solid #ddd;'>{dep_date}</td>"
                    table_rows += f"<td align='left' style='border: 1px solid #ddd;'>{bank}</td></tr>"

                html_table += "</tbody></table>"

                # Render the Dark UI HTML table on the screen
                st.markdown(html_table, unsafe_allow_html=True)


                # --- 3. BUILD THE FULL PDF DOCUMENT ---
                pdf_html = f"""
                <html>
                <head>
                <style>
                    body {{ font-family: Times New Roman, sans-serif; color: #333; margin: 0; padding: 0; }}
                    .val {{ font-size: 16px; font-weight: bold; color: #262730; margin: 0; line-height: 1.2; }}
                    .lbl {{ font-size: 10px; color: #666; margin: 0; line-height: 1.2; letter-spacing: 0.5px; }}
                </style>
                </head>
                <body>
                    <!-- OUTER BORDER WRAPPER -->
                    <table width="100%" cellpadding="15" cellspacing="0" style="border: 2px solid #262730;">
                        <tr>
                            <td>

                                <!-- HEADER: LOGO + COMPANY NAME WITH GRADIENT BACKGROUND -->
                                <table width="100%" cellpadding="10" cellspacing="0" style="background: linear-gradient(90deg, rgba(38,39,48,0.9) 0%, rgba(38,39,48,0.4) 100%); margin-bottom: 15px;">
                                    <tr>
                                        <td width="15%" align="center" valign="middle">
                                            <img src="data:image/png;base64,{logo_base64}" width="90" height="78" />
                                        </td>
                                        <td width="85%" align="left" valign="middle">
                                            <span style="color: #000000; font-size: 30px; font-weight: bold;">Imo chicken and Agro (Pvt) Ltd</span><br/>
                                            <span style="color: #65737e; font-size: 18px;">Sales Department Reports</span>
                                        </td>
                                    </tr>
                                </table>

                                <h2 align="center" style="color: #262730; font-size: 22px; margin-bottom: 0px;">Daily Cash Collection Report</h2>
                                <p align="center" style="color: #666; font-size: 14px; margin-bottom: 20px;">Report Date: {selected_date.strftime('%d/%m/%Y')}</p>

                                <!-- KPI CARDS -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 15px;">
                                    <tr>
                                        <td width="48%" align="center" valign="middle" style="padding: 8px 5px; background-color: #f9f9f9; border-left: 5px solid #a53860; border-top: 1px solid #ccc; border-right: 1px solid #ccc; border-bottom: 1px solid #ccc;">
                                            <div class="val">LKR {total_coll:,.2f}</div>
                                            <div class="lbl">TOTAL CASH COLLECTION</div>
                                        </td>
                                        <td width="4%"></td>
                                        <td width="48%" align="center" valign="middle" style="padding: 8px 5px; background-color: #f9f9f9; border-left: 5px solid #38b000; border-top: 1px solid #ccc; border-right: 1px solid #ccc; border-bottom: 1px solid #ccc;">
                                            <div class="val">LKR {total_dep:,.2f}</div>
                                            <div class="lbl">TOTAL CASH DEPOSITS</div>
                                        </td>
                                    </tr>
                                </table>

                                {pdf_table_style + table_rows + "</tbody></table>"}

                                <!-- FOOTER -->
                                <table width="100%" cellpadding="1" cellspacing="0" style="margin-top: 20px; background-color: #052b6c; height: 23px;">
                                    <tr>
                                        <td align="center">
                                            <span style="color: #ffffff; font-size: 12px;">Copyright &#169; 2026 | MIS Department | All Rights Reserved</span>
                                        </td>
                                    </tr>
                                </table>

                            </td>
                        </tr>
                    </table>
                </body>
                </html>
                """

                # Convert the HTML string into a PDF file in the background
                pdf_buffer = io.BytesIO()
                pisa.CreatePDF(io.StringIO(pdf_html), dest=pdf_buffer)

                # SHOW THE DOWNLOAD BUTTON
                st.write("")
                st.download_button(
                    label="📄 Download Report as PDF",
                    data=pdf_buffer.getvalue(),
                    file_name=f"Daily_Report_{selected_date}.pdf",
                    mime="application/pdf"
                )
#-----------------------------------------------------------Dashboard-----------------------------------------------------------#

with tab3:

    st.header("📈 Financial Performance Dashboard")

    if not df_main.empty and "Date" in df_main.columns:
        # Data Preparation
        df_dash = df_main.copy()
        df_dash["Date"] = pd.to_datetime(df_dash["Date"], errors="coerce")
        df_dash["Total Cash Collection"] = pd.to_numeric(df_dash["Total Cash Collection"], errors="coerce").fillna(0)
        df_dash["Cash Deposit"] = pd.to_numeric(df_dash["Cash Deposit"], errors="coerce").fillna(0)
        df_dash["Month"] = df_dash["Date"].dt.strftime("%Y-%m")
        df_dash["Cash In Hand"] = pd.to_numeric(df_dash["Cash In Hand"], errors="coerce").fillna(0)

        # Filters
        col1, col2 = st.columns(2)
        with col1: selected_month = st.selectbox("Select Month:", sorted(df_dash["Month"].unique(), reverse=True))
        with col2: selected_rep_dash = st.selectbox("Select Sales Rep:", ["All"] + sorted(df_dash["Sales Rep"].dropna().unique().tolist()))

        # Logic
        df_this_month = df_dash[df_dash["Month"] == selected_month]
        df_filtered = df_this_month[df_this_month["Sales Rep"] == selected_rep_dash] if selected_rep_dash != "All" else df_this_month
        
        total_c = df_filtered["Total Cash Collection"].sum()
        total_d = df_filtered["Cash Deposit"].sum()
        total_cih = df_filtered["Cash In Hand"].sum()
        var = total_c - total_d - total_cih

        col1, col2, col3, col4 = st.columns(4)
        

        if total_c >= 1000000:
            with col1:
                st.markdown(f'<div class="metric-card" style="border-left-color:#d9ed92;"><div class="metric-value">{"LKR "}{total_c/1000000:,.2f} M</div><div class="metric-label">Total Cash Collection</div></div>', unsafe_allow_html=True)
        else:
            with col1:
                st.markdown(f'<div class="metric-card" style="border-left-color:#d9ed92;"><div class="metric-value">{"LKR "}{total_c:,.2f}</div><div class="metric-label">Total Cash Collection</div></div>', unsafe_allow_html=True)

        if total_d >= 1000000:
            with col2:
                st.markdown(f'<div class="metric-card" style="border-left-color:#faa307;"><div class="metric-value">{"LKR "}{total_d/1000000:,.2f} M</div><div class="metric-label">Cash Deposit</div></div>', unsafe_allow_html=True)
        else:
            with col2:
                st.markdown(f'<div class="metric-card" style="border-left-color:#faa307;"><div class="metric-value">{"LKR "}{total_d:,.2f}</div><div class="metric-label">Cash Deposit</div></div>', unsafe_allow_html=True)

        if total_cih >= 1000000:
            with col3:
                st.markdown(f'<div class="metric-card" style="border-left-color:#f99195;"><div class="metric-value">{"LKR "}{total_cih/1000000:,.2f} M</div><div class="metric-label">Cash In Hand</div></div>', unsafe_allow_html=True)
        else:
            with col3:
                st.markdown(f'<div class="metric-card" style="border-left-color:#f99195;"><div class="metric-value">{"LKR "}{total_cih:,.2f}</div><div class="metric-label">Cash In Hand</div></div>', unsafe_allow_html=True)

        if var >= 1000000:
            with col4:
                st.markdown(f'<div class="metric-card" style="border-left-color:{"#c90d0d" if var > 0 else "#28a745"};"><div class="metric-value">{"LKR "}{var/1000000:,.2f} M</div><div class="metric-label">Variance</div></div>', unsafe_allow_html=True)    
        else:
            with col4:
                st.markdown(f'<div class="metric-card" style="border-left-color:{"#c90d0d" if var > 0 else "#28a745"};"><div class="metric-value">{"LKR "}{var:,.2f}</div><div class="metric-label">Variance</div></div>', unsafe_allow_html=True)


        st.divider()

        # Performance Table (Independent of Rep Slicer)
        st.subheader("Monthly Performance Comparison")
        prev_m = (pd.to_datetime(selected_month + "-01") - pd.DateOffset(months=1)).strftime("%Y-%m")
        df_prev = df_dash[df_dash["Month"] == prev_m].groupby("Sales Rep")["Total Cash Collection"].sum()
        df_curr = df_this_month.groupby("Sales Rep")["Total Cash Collection"].sum()
        
        comp_df = pd.DataFrame({"Previous Month": df_prev, "This Month": df_curr}).fillna(0)
        comp_df["Difference"] = comp_df["This Month"] - comp_df["Previous Month"]
        st.dataframe(comp_df.style.format("{:,.2f}"), use_container_width=True)
        st.divider()

        # Charts
        

        # 1. Prepare the data (added value_name="Amount" to make your y="Amount" work)
        chart_data = df_filtered.groupby("Sales Rep")[["Total Cash Collection", "Cash Deposit"]].sum().reset_index().melt(id_vars="Sales Rep", value_name="Amount")

        # 2. Build the basic chart and set specific Bar Colors
        fig1 = px.bar(
            chart_data, 
            x="Sales Rep", 
            y="Amount", 
            color="variable", 
            barmode="group", 
            title="Collections vs Deposits by Rep",
            text_auto=',.0f',
            # Set the exact colors you want for your bars using a dictionary
            color_discrete_map={
                "Total Cash Collection": "#9a031e", # A nice blue
                "Cash Deposit": "#0f4c5c"           # A nice green
            }
        )

        # 3. Style the bars and position the data labels
        fig1.update_traces(
            textfont_size=14,          # <--- Data label font size
            textangle=0,               # <--- Keeps data labels horizontal
            textfont_color="white",   # <--- ADD THIS TO CHANGE DATA LABEL COLOR (e.g., "white", "#FFFFFF", "yellow")
            textposition="outside",    # <--- Puts the labels on top of the bars (use "inside" if you prefer)
            cliponaxis=False,          # <--- Prevents labels on very tall bars from getting cut off at the top
            opacity=1,
            marker=dict(
                line=dict(width=1.5, color="rgba(255,255,231,0.8)"), # Adds a subtle white border to the bars
                cornerradius=0  
            )
        )

        # Customize X-Axis Font Sizes
        fig1.update_xaxes(
            title_text="Sales Representative",        # You can change the axis title text here
            title_font=dict(size=18, color="white"),  # <--- X-Axis Title Font Size & Color
            tickfont=dict(size=14, color="gray")      # <--- X-Axis Tick (Rep Names) Font Size
        )

        # Customize Y-Axis Font Sizes
        fig1.update_yaxes(
            title_text="Amount",                      # You can change the axis title text here
            title_font=dict(size=18, color="white"),  # <--- Y-Axis Title Font Size & Color
            tickfont=dict(size=14, color="gray"),     # <--- Y-Axis Tick (Numbers) Font Size
            showgrid=True,                            # Optional: Keeps the background grid lines
            gridcolor="rgba(128, 128, 128, 0.2)"      # Makes the grid lines subtle
        )

        

        # Customize Backgrounds, Fonts, and Text Sizes
        fig1.update_layout(
            # Background Colors
            paper_bgcolor="#0e1117",  # Background color of the entire image/frame
            plot_bgcolor="#0e1117",   # Background color of the chart area itself

            # Global Font Settings (Applies to axis labels, ticks, and legend)
            font=dict(
                family="Arial, sans-serif",
                size=14,
                color="#333333"       # Dark gray text
            ),

            # Title Customization (Overrides global font just for the title)
            title=dict(
                text="Collections vs Deposits by Rep",
                font=dict(
                    family="Helvetica, sans-serif",
                    size=30,
                    color="#FFFFFF"   # Darker text for the title
                ),
                x=0.5,                # Centers the title (0 is left, 1 is right)
                xanchor="center"
            ),

            # Customize the Legend
            legend_title_text="Transaction Type",
            legend=dict(
                bgcolor="#0e1117",    # Match the paper_bgcolor so it blends in
                bordercolor="#585656",
                borderwidth=1,
                yanchor="top",
                y=10,
                xanchor="left",
                x=0.01
            )
        )

        # 4. Show it in Streamlit
        st.plotly_chart(fig1, use_container_width=True)
        
        # Optional: Add a visual divider between the charts
        st.divider() 
        
#-----------------------------------------------------------Heatmap-----------------------------------------------------------#
        # 1. Prepare the Data
        df_filtered["Date"] = pd.to_datetime(df_filtered["Date"], errors="coerce")
        df_filtered["Day"] = df_filtered["Date"].dt.strftime('%Y-%m-%d')
        grouped_data = df_filtered.groupby(["Bank", "Day"])["Cash Deposit"].sum().reset_index()

        # Pivot the data into a 2D Matrix Grid
        heatmap_matrix = grouped_data.pivot(index="Bank", columns="Day", values="Cash Deposit").fillna(0)

        # 2. Build the Heatmap
        fig3 = px.imshow(
            heatmap_matrix,
            text_auto='.3s',                 # <--- FORMATS TO 'k' (e.g., 685k, 199k)
            aspect="equal",                  # <--- FORCES PERFECT SQUARES
            color_continuous_scale="YlGnBu", 
            title="Daily Cash Deposits by Bank"
        )

        # 3. Customize Text and Add Grid Lines
        fig3.update_traces(
            xgap=3,                          # <--- ADDS VERTICAL LINES BETWEEN SQUARES
            ygap=3,                          # <--- ADDS HORIZONTAL LINES BETWEEN SQUARES
            textfont=dict(
                size=12,
                family="Arial Black" 
                #color="#111111"              
            )
        )

        # 4. Customize Backgrounds, Global Fonts, and Title
        fig3.update_layout(
            paper_bgcolor="rgba(14,17,23,1)",  # Dark background for the entire chart
            plot_bgcolor="rgba(14,17,23,1)",
            height=960,                       # Optional: gives the chart enough height so squares aren't tiny
            
            title=dict(
                font=dict(family="Helvetica, sans-serif", size=30, color="white"),
                x=0.5,
                xanchor="center"
            ),
            
            coloraxis_colorbar=dict(
                title="Deposit",
                title_font=dict(size=14, color="white"),
                tickfont=dict(size=12, color="gray")
            )
        )

        # 5. Customize X-Axis (Days)
        fig3.update_xaxes(                     # Ensures all days are shown even if no deposits
            title_text="Date",
            title_font=dict(size=18, color="white"),
            tickfont=dict(size=14, color="white"), 
            tickangle=-45,                        
            side="bottom",
            showgrid=False,                    # Keeps the background clean behind the gaps
            dtick=86400000
        )

        # 6. Customize Y-Axis (Banks)
        fig3.update_yaxes(
            title_text="Bank Accounts",
            title_font=dict(size=20, color="white"),
            tickfont=dict(size=16, color="white"),
            showgrid=False                    # Keeps the background clean behind the gaps
        )

        # 7. Show in Streamlit
        st.plotly_chart(fig3, use_container_width=True)
        st.divider() 


#-----------------------------------------------------------------------------------------------------------------------#
# --- NEW HIERARCHICAL OVERLAY CHART ---

# --- NEW HIERARCHICAL OVERLAY CHART (3-TIER AXIS) ---

    # --- NEW HIERARCHICAL "NESTED" BAR CHART ---
    # Replaces the previous barmode="group" version.
    #
    # Why the old version couldn't produce the mock-up look:
    # barmode="group" on a 3-level multicategory axis draws the
    # "Total Collected" bar ONCE PER ROW of plot_df -- so a collection
    # split across 3 deposit dates showed the same teal bar 3 times,
    # side by side with each green bar, instead of once as a backdrop.
    #
    # This version instead computes bar x-positions by hand: one wide
    # teal bar per (Sales Rep, Date) collection, and the green deposit
    # bars for that collection are placed narrower, nested inside its
    # span (barmode="overlay"). Two more label rows (Cash collect date,
    # Rep Name) are added underneath as annotations, boxed to match the
    # mock-up's visual language.

    # ----------------------------------------------------------------------
    # 1. Aggregate: one row per collection (Rep + Date), one row per deposit
    # ----------------------------------------------------------------------
    col_df = (
        df_filtered.groupby(["Sales Rep", "Date"])["Total Cash Collection"]
        .sum()
        .reset_index()
    )
    dep_df = (
        df_filtered.groupby(["Sales Rep", "Date", "Cash Deposit Date"])["Cash Deposit"]
        .sum()
        .reset_index()
    )

    col_df["Date"] = pd.to_datetime(col_df["Date"], errors="coerce")
    dep_df["Date"] = pd.to_datetime(dep_df["Date"], errors="coerce")
    dep_df["Cash Deposit Date"] = pd.to_datetime(dep_df["Cash Deposit Date"], errors="coerce")

    col_df = col_df.sort_values(["Sales Rep", "Date"]).reset_index(drop=True)
    dep_df = dep_df.sort_values(["Sales Rep", "Date", "Cash Deposit Date"]).reset_index(drop=True)

    col_df["Collect_Str"] = col_df["Date"].dt.strftime("%b %d, %Y")
    dep_df["Deposit_Str"] = dep_df["Cash Deposit Date"].dt.strftime("%b %d").fillna("Pending")

    # ----------------------------------------------------------------------
    # 2. Lay bars out by hand on a numeric x-axis.
    #    Tune these three numbers to taste -- they control spacing only.
    # ----------------------------------------------------------------------
    BAR_SLOT = 1.0     # x-space reserved for each individual deposit bar
    GROUP_GAP = 0.6    # gap between collection-date clusters
    REP_GAP = 1.0      # extra gap between sales reps

    dep_x, dep_y, dep_text, dep_ticks = [], [], [], []
    dep_colors = []
    grp_x, grp_y, grp_w, grp_labels = [], [], [], []
    rep_x, rep_labels = [], []

    cursor = 0.0
    for rep, rep_rows in col_df.groupby("Sales Rep", sort=False):
        rep_start = cursor
        for _, row in rep_rows.iterrows():
            deposits = dep_df[
                (dep_df["Sales Rep"] == rep) & (dep_df["Date"] == row["Date"])
            ]
            n = max(len(deposits), 1)  # reserve 1 slot even if nothing deposited yet

            grp_start = cursor
            # Sum of deposits for this collection
            total_deposit = deposits["Cash Deposit"].sum()

            # Decide color for this collection
            if total_deposit == row["Total Cash Collection"]:
                group_color = "#55a630"   # Green
            elif total_deposit > row["Total Cash Collection"]:
                group_color = "#f77f00"   # Orange
            else:
                group_color = "#d62828"   # Red

            for k, (_, drow) in enumerate(deposits.iterrows()):
                x = cursor + k * BAR_SLOT
                dep_x.append(x)
                dep_y.append(drow["Cash Deposit"])
                dep_text.append(f"LKR {drow['Cash Deposit']:,.0f}")
                dep_ticks.append(drow["Deposit_Str"])
                dep_colors.append(group_color)
            grp_end = cursor + (n - 1) * BAR_SLOT

            grp_x.append((grp_start + grp_end) / 2)
            grp_y.append(row["Total Cash Collection"])
            grp_w.append(n * BAR_SLOT + 0.25)
            grp_labels.append(row["Collect_Str"])

            cursor = grp_end + BAR_SLOT + GROUP_GAP

        rep_x.append((rep_start + cursor - GROUP_GAP) / 2)
        rep_labels.append(rep)
        cursor += REP_GAP

    # ----------------------------------------------------------------------
    # 3. Draw: wide teal "Total Collected" bars, narrow green "Amount
    #    Deposited" bars nested inside them, same numeric axis, overlay mode
    # ----------------------------------------------------------------------
    fig4 = go.Figure()

    fig4.add_trace(go.Bar(
        x=grp_x,
        y=grp_y,
        width=grp_w,
        name="Total Collected",
        marker_color="#1c638a",
        text=[f"LKR {v:,.0f}" for v in grp_y],
        textposition="outside",
        hovertemplate="<b>Total Collected:</b> LKR %{y:,.2f}<extra></extra>",
    ))

    fig4.add_trace(go.Bar(
        x=dep_x,
        y=dep_y,
        width=BAR_SLOT * 0.7,
        showlegend=False,
        marker_color=dep_colors,
        text=dep_text,
        textposition="outside",
        hovertemplate="<b>Amount Deposited:</b> LKR %{y:,.2f}<extra></extra>",
    ))
    # Legend: Fully Deposited (Green)
    fig4.add_trace(go.Bar(
        x=[None],
        y=[None],
        name="Fully Deposited",
        marker_color="#55a630",
        showlegend=True,
    ))

    # Legend: Over Deposited (Orange)
    fig4.add_trace(go.Bar(
        x=[None],
        y=[None],
        name="Over Deposited",
        marker_color="#f77f00",
        showlegend=True,
    ))

    # Legend: Under Deposited (Red)
    fig4.add_trace(go.Bar(
        x=[None],
        y=[None],
        name="Under Deposited",
        marker_color="#d62828",
        showlegend=True,
    ))

    # ----------------------------------------------------------------------
    # 4. Axis + two extra label rows underneath (Cash collect date, Rep Name)
    # ----------------------------------------------------------------------
    fig4.update_layout(
        title=dict(
            text="<b>Cash Collection vs Cash Deposit Analysis</b>",
            x=0.5,          # Center the title (0 = left, 0.5 = center, 1 = right)
            xanchor="center",
            y=0.95,          # Position the title slightly above the plot area
            yanchor="top",
            font=dict(
                family="Calibri",
                size=30,
                color="#ffffff"
            )
        ),
        barmode="overlay",
        legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="right", x=1),
        margin=dict(t=70, b=170, l=10, r=10),
        height=600,
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            tickmode="array",
            tickvals=dep_x,
            ticktext=dep_ticks,
            tickangle=-45,
            showgrid=False,
            zeroline=False,
            range=[-0.6, cursor - REP_GAP + 0.6],
        ),
        yaxis=dict(title="Amount (LKR)", showgrid=True, gridcolor="rgba(128, 128, 128, 0.2)"),
    )

    # "Cash collect date" row (boxed, like the mock-up)
    for x, label in zip(grp_x, grp_labels):
        fig4.add_annotation(
            x=x, y=-0.24, xref="x", yref="paper",
            text=label, showarrow=False, font=dict(size=12, color="white"),
            bordercolor="#ffffff", borderwidth=1, borderpad=3,
        )

    # "Rep Name" row (boxed, bold, one per rep -- spans that rep's whole cluster)
    for x, label in zip(rep_x, rep_labels):
        fig4.add_annotation(
            x=x, y=-0.40, xref="x", yref="paper",
            text=f"<b>{label}</b>", showarrow=False, font=dict(size=13, color="black"),
            bgcolor="white", bordercolor="#1c638a", borderwidth=1, borderpad=4,
        )

    st.plotly_chart(fig4, use_container_width=True)