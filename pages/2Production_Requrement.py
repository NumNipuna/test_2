import streamlit as st
import pandas as pd
import numpy as np
from gspread_dataframe import set_with_dataframe
import gspread
from utils import connect_to_sheets, fetch_database_records, add_logo, check_password, check_access
import datetime
import time
import plotly.express as px
import plotly.graph_objects as go
import io
import base64
from xhtml2pdf import pisa
import streamlit.components.v1 as components

st.set_page_config(page_title="Report 2", layout="wide")

# ==========================================================================
# GLOBAL STYLE — background gradient, glass content card, tab pills,
# buttons, dataframes, metrics, file uploader
# ==========================================================================
PALETTE = ["#667eea", "#764ba2", "#f093fb", "#4facfe", "#43e97b", "#fa709a", "#feca57"]

st.markdown("""
<style>
/* Animated gradient app background */
.stApp {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #4facfe 75%, #43e97b 100%);
    background-size: 400% 400%;
    animation: gradientShift 22s ease infinite;
}
@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* Frosted glass content card — dark, so the app's default light text
   is naturally visible without having to override every widget */
.block-container {
    background: rgba(17, 24, 39, 0.82);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border-radius: 26px;
    padding: 2rem 2.6rem 3rem 2.6rem !important;
    margin-top: 1rem;
    box-shadow: 0 10px 40px rgba(0,0,0,0.35);
    border: 1px solid rgba(255,255,255,0.12);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1f2937 0%, #111827 100%);
}
[data-testid="stSidebar"] * { color: #f3f4f6 !important; }

/* Headings */
h1, h2, h3 { color: #f1f5f9; font-weight: 800; }
h1 { background: linear-gradient(135deg, #a5b4fc, #f0abfc);
     -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

/* ---- Tabs (works for main tabs AND nested sub-tabs) ---- */
button[data-baseweb="tab"] {
    background: linear-gradient(135deg, #f5f7fa 0%, #e4ecf7 100%) !important;
    border-radius: 14px 14px 0 0 !important;
    padding: 10px 22px !important;
    margin-right: 6px !important;
    font-weight: 700 !important;
    color: #475569 !important;
    border: none !important;
    transition: all 0.25s ease;
}
button[data-baseweb="tab"]:hover {
    background: linear-gradient(135deg, #a5b4fc 0%, #818cf8 100%) !important;
    color: white !important;
    transform: translateY(-2px);
}
button[data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    box-shadow: 0 4px 14px rgba(118,75,162,0.45);
}
[data-baseweb="tab-highlight"] { background-color: transparent !important; }
[data-baseweb="tab-border"] { display: none !important; }
[data-baseweb="tab-list"] { gap: 2px; }

/* Buttons */
.stButton>button, .stDownloadButton>button {
    border-radius: 10px;
    border: none;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white !important;
    font-weight: 700;
    padding: 0.5rem 1.3rem;
    box-shadow: 0 4px 12px rgba(102,126,234,0.35);
    transition: all .2s ease;
}
.stButton>button:hover, .stDownloadButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 18px rgba(102,126,234,0.5);
}

/* Dataframe / data_editor containers */
[data-testid="stDataFrame"], [data-testid="stDataEditor"] {
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 4px 18px rgba(0,0,0,0.10);
    border: 1px solid #e2e8f0;
}

/* Dividers */
hr { border-top: 2px solid rgba(118,75,162,0.2) !important; }

/* Metric cards */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(102,126,234,0.15) 100%);
    border-radius: 16px;
    padding: 1rem;
    box-shadow: 0 4px 14px rgba(0,0,0,0.15);
    border: 1px solid rgba(255,255,255,0.12);
}

/* File uploader */
[data-testid="stFileUploader"] {
    border-radius: 14px;
    padding: 0.6rem;
    background: rgba(255,255,255,0.06);
    border: 1px dashed #a5b4fc;
}

/* Section banner */
.section-banner {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white; padding: 14px 20px; border-radius: 14px;
    font-size: 20px; font-weight: 800; margin-bottom: 14px;
    box-shadow: 0 4px 14px rgba(102,126,234,0.3);
}
</style>
""", unsafe_allow_html=True)

st.title("Production Requrement")
add_logo()
# -------------------------------------------------------------------
# Require login
if not check_password():
 st.stop()
if not check_access("Production_Requirement"):
 st.error("🚫 You do not have permission to view this page.")
 st.stop()
# -------------------------------------------------------------------

CACHE_TTL_SECONDS = 600  # 10 minutes - how long data is reused before a fresh Google Sheets call is made

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refresh All Data", key="home_refresh_btn"):
    fetch_database_records.clear()
    try:
        _cached_records.clear()
    except NameError:
        pass
    try:
        get_connection.clear()
    except NameError:
        pass
    try:
        get_or_create_ws.clear()
    except NameError:
        pass
    st.rerun()


# --- CONNECTION (cached as a resource, not re-created on every rerun) ---
@st.cache_resource(show_spinner=False)
def get_connection():
    sh = connect_to_sheets()
    ws_main = sh.worksheet("Data_Entry")
    ws_working_days = sh.worksheet("Working_Days")
    ws_daily_sales = sh.worksheet("Daily_Sales")
    ws_inventory = sh.worksheet("Inventory")
    return sh, ws_main, ws_working_days, ws_daily_sales, ws_inventory


try:
    Working_Days, Daily_Sales, Inventory = fetch_database_records()
    sh, ws_main, ws_working_days, ws_daily_sales, ws_inventory = get_connection()
except Exception as e:
    st.error(f"Error connecting to Google Sheets: {e}")
    st.stop()


# --- AUTO-CREATE NEW WORKSHEETS IF THEY DON'T EXIST (also cached as a resource) ---
@st.cache_resource(show_spinner=False)
def get_or_create_ws(title, rows=3000, cols=15):
    try:
        return sh.worksheet(title)
    except gspread.exceptions.WorksheetNotFound:
        return sh.add_worksheet(title=title, rows=rows, cols=cols)


ws_items = get_or_create_ws("Items_Master")
ws_forecast = get_or_create_ws("Forecast")
ws_report = get_or_create_ws("Report")


# --- CACHED READS ---
# Every widget interaction re-runs this whole script. Without caching, that meant
# live Google Sheets calls on every single click/keystroke. Data is now cached for
# CACHE_TTL_SECONDS (10 minutes) and gets invalidated immediately after any save,
# so you still always see fresh data right after you save something - the 10 minute
# window only applies to changes made directly in the Google Sheet itself, outside
# this app (use the "Refresh All Data" button in the sidebar to pull those in early).
@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def _cached_records(_ws, sheet_key):
    return _ws.get_all_records()


def get_records(ws_obj, sheet_key):
    return _cached_records(ws_obj, sheet_key)


def invalidate_sheet_cache():
    _cached_records.clear()


def save_and_refresh(message, seconds=3):
    """Call after any write: invalidates the cache, shows a success message
    right at this point in the page (so it appears near the button that
    triggered it), holds it for `seconds`, then refreshes the page."""
    invalidate_sheet_cache()
    msg_placeholder = st.empty()
    msg_placeholder.success(message)
    time.sleep(seconds)
    msg_placeholder.empty()
    st.rerun()

# --- DEFAULT 53-ITEM MASTER LIST (now managed from Settings — kept here only
# as the seed used the very first time the Items_Master sheet is created) ---
DEFAULT_CODES = [
    "01CW01", "01CW02", "01CW03", "01CW05", "01CW06",
    "02CW01", "02CW03", "02CW04", "02CW05", "02CW09",
    "03CW01", "03CW03", "03CW04", "03CW05", "03CW08",
    "04CP01", "04CP02", "04CP03", "04CP04", "04CP05", "04CP06", "04CP07",
    "04CP08", "04CP09", "04CP10", "04CP11", "04CP12", "04CP13", "04CP14",
    "04CP16", "04CP17", "04CP19", "04CP20", "04CP23", "04CP24", "04CP26",
    "04CP28", "04CP29", "04CP30", "04CP31", "04CP32", "04CP33", "04CP34",
    "04CP37", "04CP40", "04CP41",
    "05CM01", "05CM02", "05CM03",
    "06CE01", "06CE02", "06CE03", "06CE05",
]
DEFAULT_NAMES = [
    "Whole Chicken (S)", "Whole Chicken (L)", "Whole Chicken (XL)", "Krosher Whole Chicken", "Half Chicken",
    "Whole Chicken - Without Giblets (S)", "Whole Chicken - Without Giblets (L)",
    "Whole Chicken - Without Giblets (XL)", "Whole Chicken - Without Giblets (XXL)",
    "Whole Chicken - Without Giblets (M) Special",
    "Skinless Whole Chicken (S)", "Skinless Whole Chicken (L)", "Skinless Whole Chicken (XL)",
    "Skinless Whole Chicken (XXL)", "Skinless Whole Chicken (M) Special",
    "Skinless Breast", "Skinon Breast", "Skinless Drumstick", "Skinon Drumstick",
    "Skinon Drumstick - Special", "Skinless Thigh", "Skinless Thigh - Special",
    "Skinon Thigh", "Skinless Leg", "Skinless Leg - Special", "Skinon Leg",
    "Skinless Back Quarter", "Skinless Back Quarter - Special", "Skinon Back Quarter",
    "Whole Wings", "Winglet", "D. Winglet. / Lolipop", "Wing Tip", "Bite Pieces",
    "Liver 500g", "Gizzard 500g", "Gadget 500g", "Curry Pieses 500g", "Soup Bone",
    "Thigh Bone", "Kitchen Pack 500g", "Broiler Chicken Feet", "Pet Food - Minced 500g",
    "MDM Material 500g", "Middle Wings 500g", "Neck 500g", "Skinless Boneless Breast",
    "Skinless Boneless Thigh", "Chicken Skin - Loose Meat 5Kg",
    "Easy 250g", "Easy 400g", "Easy 700g", "Easy 5 kg",
]


def init_items_master():
    existing = ws_items.get_all_values()
    if not existing or existing[0][:2] != ["Product Code", "Item Name"]:
        df = pd.DataFrame({"Product Code": DEFAULT_CODES, "Item Name": DEFAULT_NAMES})
        ws_items.clear()
        set_with_dataframe(ws_items, df)


# Only do this check once per browser session, not on every rerun/click
if not st.session_state.get("_items_master_checked"):
    init_items_master()
    st.session_state["_items_master_checked"] = True

# Shared dropdown option lists
year_options = [str(y) for y in range(2024, 2035)]
month_options = ["January", "February", "March", "April", "May", "June", "July",
                  "August", "September", "October", "November", "December"]
day_options = [str(d) for d in range(0, 32)]


def get_rows_for_date(ws_obj, sheet_key, date_str):
    """Return existing rows in a sheet that match a given Date (YYYY-MM-DD)."""
    records = get_records(ws_obj, sheet_key)
    df = pd.DataFrame(records)
    if df.empty or "Date" not in df.columns:
        return pd.DataFrame()
    return df[df["Date"].astype(str) == date_str]


def delete_rows_for_date(ws_obj, sheet_key, date_str):
    """Permanently remove all rows matching a given Date from a sheet, keeping everything else."""
    records = get_records(ws_obj, sheet_key)
    df = pd.DataFrame(records)
    if df.empty or "Date" not in df.columns:
        return
    remaining = df[df["Date"].astype(str) != date_str]
    ws_obj.clear()
    set_with_dataframe(ws_obj, remaining if not remaining.empty else pd.DataFrame(columns=df.columns))


def section_banner(text):
    st.markdown(f'<div class="section-banner">{text}</div>', unsafe_allow_html=True)


def styled_table(df, gradient_cols=None, cmap="Blues"):
    """Return a pandas Styler with a soft background-gradient on numeric columns
    plus tidy fonts/borders, for use with st.dataframe (read-only preview tables)."""
    if df.empty:
        return df
    styler = df.style
    gradient_cols = [c for c in (gradient_cols or []) if c in df.columns]
    if gradient_cols:
        styler = styler.background_gradient(subset=gradient_cols, cmap=cmap)
    styler = styler.set_properties(**{"font-size": "13px", "border-color": "#e2e8f0"})
    styler = styler.set_table_styles([
        {"selector": "th", "props": [("background-color", "#667eea"), ("color", "white"),
                                      ("font-weight", "700")]}
    ])
    return styler


def kpi_card(label, value, icon, gradient):
    return f"""
    <div style="background:{gradient};border-radius:18px;padding:1.1rem 0.6rem;color:white;
    box-shadow:0 6px 18px rgba(0,0,0,0.18);text-align:center;height:100%;">
        <div style="font-size:26px;">{icon}</div>
        <div style="font-size:12px;opacity:0.92;margin-top:4px;">{label}</div>
        <div style="font-size:22px;font-weight:800;margin-top:2px;">{value}</div>
    </div>
    """


def money_fmt(value):
    """Format a LKR amount, abbreviating to millions once it gets large."""
    if value >= 1_000_000:
        return f"LKR {value / 1_000_000:,.2f} M"
    return f"LKR {value:,.0f}"


# ==========================================================================
# PRODUCT GROUPS — used for the group-wise dashboard visualization
# ==========================================================================
PRODUCT_GROUPS = {
    "Easy": ["05CM03", "06CE01", "06CE02", "06CE03", "06CE05"],
    "Potion": [
        "03CW01", "03CW03", "03CW04", "03CW05", "03CW08",
        "04CP01", "04CP02", "04CP03", "04CP04", "04CP05", "04CP06", "04CP07",
        "04CP08", "04CP09", "04CP10", "04CP11", "04CP12", "04CP13", "04CP14",
        "04CP16", "04CP17", "04CP19", "04CP20", "04CP23", "04CP24", "04CP26",
        "04CP28", "04CP29", "04CP30", "04CP31", "04CP32", "04CP33", "04CP34",
        "04CP37", "04CP40", "04CP41",
        "05CM01", "05CM02",
    ],
    "Chicken": [
        "01CW01", "01CW02", "01CW03", "01CW05", "01CW06",
        "02CW01", "02CW03", "02CW04", "02CW05", "02CW09",
    ],
}
CODE_TO_GROUP = {code: group for group, codes in PRODUCT_GROUPS.items() for code in codes}
GROUP_COLORS = {"Chicken": "#f97316", "Potion": "#ec4899", "Easy": "#10b981", "Other": "#94a3b8"}
GROUP_ORDER = ["Chicken", "Potion", "Easy", "Other"]


def get_group(code):
    return CODE_TO_GROUP.get(str(code), "Other")


# ==========================================================================
# SHARED: Item-wise summary report builder (used by the Dashboard tab)
# ==========================================================================
def build_report(report_date):
    """Compute one day's report rows for every item and upsert them into the Report sheet,
    without disturbing rows for any other date.

    Qty = weight sold (Kg); Total Amount = revenue (LKR). Sale / MTD Sale / Forecast /
    Achievement stay in Kg (production planning terms); Revenue (LKR) / MTD Revenue (LKR)
    are the money figures used for the Dashboard's Day's Sale / MTD Sale KPI cards."""
    report_date_str = report_date.strftime("%Y-%m-%d")
    year_str = str(report_date.year)
    month_str = month_options[report_date.month - 1]
    month_start = report_date.replace(day=1)
    days_elapsed = (report_date - month_start).days + 1

    # Items
    df_items_r = pd.DataFrame(get_records(ws_items, "items"))
    df_items_r["Product Code"] = df_items_r["Product Code"].astype(str)

    # Sales — Qty = weight sold (Kg), Total Amount = revenue (LKR)
    df_sales_r = pd.DataFrame(get_records(ws_daily_sales, "daily_sales"))
    if df_sales_r.empty:
        df_sales_r = pd.DataFrame(columns=["Date", "Product Code", "Qty", "Total Amount"])
    df_sales_r["Product Code"] = df_sales_r["Product Code"].astype(str)
    df_sales_r["Qty"] = pd.to_numeric(df_sales_r.get("Qty", 0), errors="coerce").fillna(0)
    df_sales_r["Total Amount"] = pd.to_numeric(df_sales_r.get("Total Amount", 0), errors="coerce").fillna(0)

    daily_sale_by_item = df_sales_r[df_sales_r["Date"] == report_date_str].groupby("Product Code")["Qty"].sum()
    daily_revenue_by_item = df_sales_r[df_sales_r["Date"] == report_date_str].groupby("Product Code")["Total Amount"].sum()

    mtd_mask = (df_sales_r["Date"] >= month_start.strftime("%Y-%m-%d")) & (df_sales_r["Date"] <= report_date_str)
    mtd_sale_by_item = df_sales_r[mtd_mask].groupby("Product Code")["Qty"].sum()
    mtd_revenue_by_item = df_sales_r[mtd_mask].groupby("Product Code")["Total Amount"].sum()

    # Inventory - latest value on/before report_date, per item
    df_inv_r = pd.DataFrame(get_records(ws_inventory, "inventory"))
    inv_by_item = {}
    if not df_inv_r.empty and "Item Code" in df_inv_r.columns:
        df_inv_r["Item Code"] = df_inv_r["Item Code"].astype(str)
        df_inv_r["Available Qty"] = pd.to_numeric(df_inv_r.get("Available Qty", 0), errors="coerce").fillna(0)
        df_inv_valid = df_inv_r[df_inv_r["Date"] <= report_date_str]
        if not df_inv_valid.empty:
            idx = df_inv_valid.groupby("Item Code")["Date"].idxmax()
            latest_inv = df_inv_valid.loc[idx]
            inv_by_item = dict(zip(latest_inv["Item Code"], latest_inv["Available Qty"]))

    # Forecast for this month
    df_fc_r = pd.DataFrame(get_records(ws_forecast, "forecast"))
    forecast_by_item = {}
    if not df_fc_r.empty:
        df_fc_r["Product Code"] = df_fc_r["Product Code"].astype(str)
        month_fc = df_fc_r[(df_fc_r["Year"].astype(str) == year_str) & (df_fc_r["Month"] == month_str)]
        forecast_by_item = dict(zip(month_fc["Product Code"],
                                    pd.to_numeric(month_fc["Forecast Qty"], errors="coerce").fillna(0)))

    # Working days for this month
    df_wd_r = pd.DataFrame(get_records(ws_working_days, "working_days"))
    working_days_val = 0
    if not df_wd_r.empty:
        match = df_wd_r[(df_wd_r["Year"].astype(str) == year_str) & (df_wd_r["Month"] == month_str)]
        if not match.empty:
            wd = pd.to_numeric(match.iloc[0]["Working Days"], errors="coerce")
            working_days_val = wd if pd.notna(wd) and wd > 0 else 0

    rows = []
    for _, item_row in df_items_r.iterrows():
        code = str(item_row["Product Code"])
        name = item_row.get("Item Name", "")
        sale = float(daily_sale_by_item.get(code, 0))
        mtd_sale = float(mtd_sale_by_item.get(code, 0))
        revenue = float(daily_revenue_by_item.get(code, 0))
        mtd_revenue = float(mtd_revenue_by_item.get(code, 0))
        forecast = float(forecast_by_item.get(code, 0))
        achievement = (mtd_sale / forecast * 100) if forecast > 0 else 0.0
        balance = mtd_sale - forecast
        inventory_qty = float(inv_by_item.get(code, 0))
        inventory_balance = inventory_qty + balance
        day_target = (forecast / working_days_val) if working_days_val else 0.0
        avg_total_sale = (mtd_sale / days_elapsed) if days_elapsed else 0.0
        avg_daily_target = (avg_total_sale / day_target) if day_target else 0.0

        rows.append({
            "Date": report_date_str,
            "Product Code": code,
            "Item Name": name,
            "Sale": round(sale, 2),
            "MTD Sale": round(mtd_sale, 2),
            "Revenue (LKR)": round(revenue, 2),
            "MTD Revenue (LKR)": round(mtd_revenue, 2),
            "Forecast": round(forecast, 2),
            "Forecast Achievement (%)": round(achievement, 2),
            "Balance": round(balance, 2),
            "Inventory": round(inventory_qty, 2),
            "Inventory Balance": round(inventory_balance, 2),
            "Day Target": round(day_target, 2),
            "Average of Total Sale": round(avg_total_sale, 2),
            "Average Daily Target": round(avg_daily_target, 2),
        })

    new_report_df = pd.DataFrame(rows)

    # Upsert: keep every other date untouched, replace only this date's rows
    df_existing_report = pd.DataFrame(get_records(ws_report, "report"))
    if not df_existing_report.empty and "Date" in df_existing_report.columns:
        df_existing_report = df_existing_report[df_existing_report["Date"] != report_date_str]
        final_df = pd.concat([df_existing_report, new_report_df], ignore_index=True)
    else:
        final_df = new_report_df

    ws_report.clear()
    set_with_dataframe(ws_report, final_df)
    invalidate_sheet_cache()
    return new_report_df


# ==========================================================================
# MAIN TABS
# ==========================================================================
main_tab1, main_tab2, main_tab3 = st.tabs(["📝 Data Entry", "📄 Report", "📊 Dashboard"])

with main_tab1:
    selected_date = st.date_input("Select Date:", value=datetime.date.today())
    selected_date_str = selected_date.strftime('%Y-%m-%d')
    st.divider()

    de_tab1, de_tab2, de_tab3, de_tab4 = st.tabs([
        "1️⃣ Upload Daily Sales CSV",
        "2️⃣ Update Inventory",
        "3️⃣ Set Monthly Forecast",
        "4️⃣ Manage Working Days",
    ])

    # ==========================================
    # SUB-TAB 1: DAILY SALES CSV UPLOAD
    # ==========================================
    with de_tab1:
        section_banner("📤 Upload Daily Sales CSV")

        existing_sales = get_rows_for_date(ws_daily_sales, "daily_sales", selected_date_str)
        if not existing_sales.empty:
            st.warning(f"⚠️ Sales data already exists for **{selected_date_str}** ({len(existing_sales)} rows).")
            st.dataframe(styled_table(existing_sales.head(10), gradient_cols=["Qty", "Total Amount"], cmap="Purples"),
                         use_container_width=True)
            if len(existing_sales) > 10:
                st.caption(f"Showing 10 of {len(existing_sales)} rows.")

            if st.button("🗑️ Delete sales data for this date", key="delete_sales_btn"):
                st.session_state["confirm_delete_sales"] = True

            if st.session_state.get("confirm_delete_sales"):
                st.error(f"Permanently delete all {len(existing_sales)} sales rows for {selected_date_str}? This cannot be undone.")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Yes, delete it", key="confirm_delete_sales_yes", type="primary"):
                        delete_rows_for_date(ws_daily_sales, "daily_sales", selected_date_str)
                        st.session_state["confirm_delete_sales"] = False
                        save_and_refresh(f"🗑️ Sales data for {selected_date_str} deleted.")
                with c2:
                    if st.button("Cancel", key="confirm_delete_sales_no"):
                        st.session_state["confirm_delete_sales"] = False
                        st.rerun()

        st.info("CSV must contain 5 columns: Product Code, Product Name, Category, Qty, Total Amount")
        uploaded_file = st.file_uploader("Upload CSV File", type=["csv"], key="sales_upload")
        if uploaded_file is not None:
            try:
                df_csv = pd.read_csv(uploaded_file)

                if st.button("Submit to Google Sheets", type="primary", key="sales_submit"):
                    with st.spinner("Processing and uploading..."):
                        formatted_date = selected_date_str
                        df_csv.insert(0, "Date", formatted_date)
                        df_csv["Qty"] = pd.to_numeric(df_csv["Qty"], errors="coerce").fillna(0)
                        df_csv["Total Amount"] = pd.to_numeric(df_csv["Total Amount"], errors="coerce").fillna(0)
                        df_csv = df_csv.fillna("")
                        data_to_upload = df_csv.values.tolist()
                        ws_daily_sales.append_rows(data_to_upload)
                    save_and_refresh("✅ Daily sales successfully uploaded!")

            except Exception as e:
                st.error(f"Error processing file: {e}")

    # ==========================================
    # SUB-TAB 2: INVENTORY UPDATE
    # ==========================================
    with de_tab2:
        section_banner("📦 Update Inventory")

        existing_inventory = get_rows_for_date(ws_inventory, "inventory", selected_date_str)
        if not existing_inventory.empty:
            st.warning(f"⚠️ Inventory data already exists for **{selected_date_str}** ({len(existing_inventory)} rows).")
            st.dataframe(styled_table(existing_inventory.head(10), gradient_cols=["Available Qty"], cmap="Greens"),
                         use_container_width=True)
            if len(existing_inventory) > 10:
                st.caption(f"Showing 10 of {len(existing_inventory)} rows.")

            if st.button("🗑️ Delete inventory data for this date", key="delete_inv_btn"):
                st.session_state["confirm_delete_inv"] = True

            if st.session_state.get("confirm_delete_inv"):
                st.error(f"Permanently delete all {len(existing_inventory)} inventory rows for {selected_date_str}? This cannot be undone.")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Yes, delete it", key="confirm_delete_inv_yes", type="primary"):
                        delete_rows_for_date(ws_inventory, "inventory", selected_date_str)
                        st.session_state["confirm_delete_inv"] = False
                        save_and_refresh(f"🗑️ Inventory data for {selected_date_str} deleted.")
                with c2:
                    if st.button("Cancel", key="confirm_delete_inv_no"):
                        st.session_state["confirm_delete_inv"] = False
                        st.rerun()

        st.info("Upload an updated inventory CSV with columns: Product Name, Item Code, Available Qty")
        inv_file = st.file_uploader("Upload Inventory CSV", type=["csv"], key="inv_upload")
        if inv_file is not None:
            try:
                df_inv = pd.read_csv(inv_file)

                if st.button("Add to Inventory in Google Sheets", type="primary", key="inv_submit"):
                    with st.spinner("Appending inventory..."):
                        formatted_date = selected_date_str
                        df_inv.insert(0, "Date", formatted_date)
                        df_inv = df_inv.fillna("")
                        inv_data_to_upload = df_inv.values.tolist()
                        ws_inventory.append_rows(inv_data_to_upload)
                    save_and_refresh("✅ Inventory successfully added!")

            except Exception as e:
                st.error(f"Error processing inventory file: {e}")

    # ==========================================
    # SUB-TAB 3: MONTHLY FORECAST ENTRY
    # ==========================================
    with de_tab3:
        section_banner("🎯 Set Monthly Forecast")
        st.caption("Enter the forecast quantity/amount for each item for a given month. "
                   "Saving only updates the selected month — other months are kept untouched.")

        fc_col1, fc_col2 = st.columns(2)
        with fc_col1:
            forecast_year = st.selectbox("Forecast Year", year_options,
                                        index=year_options.index(str(datetime.date.today().year))
                                        if str(datetime.date.today().year) in year_options else 0,
                                        key="forecast_year_select")
        with fc_col2:
            forecast_month = st.selectbox("Forecast Month", month_options,
                                        index=datetime.date.today().month - 1,
                                        key="forecast_month_select")

        items_records = get_records(ws_items, "items")
        df_items_now = pd.DataFrame(items_records) if items_records else pd.DataFrame(columns=["Product Code", "Item Name"])

        forecast_records = get_records(ws_forecast, "forecast")
        df_forecast_all = pd.DataFrame(forecast_records) if forecast_records else pd.DataFrame(
            columns=["Year", "Month", "Product Code", "Item Name", "Forecast Qty"])

        if not df_forecast_all.empty:
            df_forecast_month = df_forecast_all[
                (df_forecast_all["Year"].astype(str) == forecast_year) &
                (df_forecast_all["Month"] == forecast_month)
            ][["Product Code", "Forecast Qty"]]
        else:
            df_forecast_month = pd.DataFrame(columns=["Product Code", "Forecast Qty"])

        merged_forecast = df_items_now.merge(df_forecast_month, on="Product Code", how="left")
        merged_forecast["Forecast Qty"] = pd.to_numeric(merged_forecast.get("Forecast Qty"), errors="coerce").fillna(0)

        edited_forecast = st.data_editor(
            merged_forecast,
            use_container_width=True,
            hide_index=True,
            disabled=["Product Code", "Item Name"],
            key="forecast_editor",
        )

        if st.button("Save Forecast", type="primary", key="save_forecast_btn"):
            with st.spinner("Saving forecast..."):
                edited_forecast = edited_forecast.copy()
                edited_forecast["Year"] = forecast_year
                edited_forecast["Month"] = forecast_month
                save_cols = ["Year", "Month", "Product Code", "Item Name", "Forecast Qty"]
                save_df = edited_forecast[save_cols]

                if not df_forecast_all.empty:
                    remainder = df_forecast_all[~(
                        (df_forecast_all["Year"].astype(str) == forecast_year) &
                        (df_forecast_all["Month"] == forecast_month)
                    )]
                else:
                    remainder = pd.DataFrame(columns=save_cols)

                final_forecast = pd.concat([remainder, save_df], ignore_index=True)
                ws_forecast.clear()
                set_with_dataframe(ws_forecast, final_forecast)
            save_and_refresh(f"✅ Forecast for {forecast_month} {forecast_year} saved!")

    # ==========================================
    # SUB-TAB 4: WORKING DAYS SETUP
    # ==========================================
    with de_tab4:
        section_banner("📅 Manage Monthly Working Days")
        try:
            working_days_data = get_records(ws_working_days, "working_days")
            df_working = pd.DataFrame(working_days_data)
            if not df_working.empty:
                df_working["Year"] = df_working["Year"].astype(str)
                df_working["Working Days"] = df_working["Working Days"].astype(str)
            else:
                df_working = pd.DataFrame(columns=["Year", "Month", "Working Days"])
        except Exception:
            df_working = pd.DataFrame(columns=["Year", "Month", "Working Days"])

        edited_working_days = st.data_editor(
            df_working,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            column_config={
                "Year": st.column_config.SelectboxColumn("Year", options=year_options, required=True),
                "Month": st.column_config.SelectboxColumn("Month", options=month_options, required=True),
                "Working Days": st.column_config.SelectboxColumn("Working Days", options=day_options, required=True),
            },
            key="working_days_editor",
        )
        if st.button("Save Working Days", type="primary", key="save_wd_btn"):
            with st.spinner("Saving changes..."):
                ws_working_days.clear()
                set_with_dataframe(ws_working_days, edited_working_days)
            save_and_refresh("✅ Working days successfully updated!")


# ==========================================================================
# TAB 2: ITEM WISE DETAILED REPORT (table + PDF export)
# ==========================================================================

def compute_detailed_report(report_date):
    """Build the full 53-item detailed report for a single date: sale, MTD sale,
    forecast, achievement, buffer levels, and a week-by-week sales breakdown for
    the month.

    NOTE: "Sale" / "MTD Sale" figures in this report are based on the Qty column
    (column E) of the Daily_Sales sheet - i.e. weight sold in Kg - not the Total
    Amount (revenue) column, since Forecast is also entered in quantity."""
    report_date_str = report_date.strftime("%Y-%m-%d")
    year_str = str(report_date.year)
    month_str = month_options[report_date.month - 1]
    month_start = report_date.replace(day=1)
    days_elapsed = (report_date - month_start).days + 1
    elapsed_weeks = ((report_date.day - 1) // 7) + 1

    # Items
    df_items_r = pd.DataFrame(get_records(ws_items, "items"))
    if df_items_r.empty or "Product Code" not in df_items_r.columns:
        return pd.DataFrame()
    df_items_r["Product Code"] = df_items_r["Product Code"].astype(str)

    # Sales - use Qty (column E) as the sale quantity, NOT Total Amount
    df_sales_r = pd.DataFrame(get_records(ws_daily_sales, "daily_sales"))
    if df_sales_r.empty:
        df_sales_r = pd.DataFrame(columns=["Date", "Product Code", "Qty"])
    df_sales_r["Product Code"] = df_sales_r["Product Code"].astype(str)
    df_sales_r["Qty"] = pd.to_numeric(df_sales_r.get("Qty", 0), errors="coerce").fillna(0)

    daily_sale_by_item = df_sales_r[df_sales_r["Date"] == report_date_str].groupby("Product Code")["Qty"].sum()

    month_mask = (df_sales_r["Date"] >= month_start.strftime("%Y-%m-%d")) & (df_sales_r["Date"] <= report_date_str)
    df_month_sales = df_sales_r[month_mask].copy()
    mtd_sale_by_item = df_month_sales.groupby("Product Code")["Qty"].sum() if not df_month_sales.empty else pd.Series(dtype=float)

    # Weekly buckets: days 1-7 -> week 1, 8-14 -> week 2, 15-21 -> week 3, 22-28 -> week 4, 29-31 -> week 5
    week_pivot = pd.DataFrame()
    if not df_month_sales.empty:
        df_month_sales["Day"] = pd.to_datetime(df_month_sales["Date"]).dt.day
        df_month_sales["Week"] = ((df_month_sales["Day"] - 1) // 7) + 1
        week_pivot = df_month_sales.groupby(["Product Code", "Week"])["Qty"].sum().unstack(fill_value=0)

    # Inventory - latest value on/before report_date, per item
    df_inv_r = pd.DataFrame(get_records(ws_inventory, "inventory"))
    inv_by_item = {}
    if not df_inv_r.empty and "Item Code" in df_inv_r.columns:
        df_inv_r["Item Code"] = df_inv_r["Item Code"].astype(str)
        df_inv_r["Available Qty"] = pd.to_numeric(df_inv_r.get("Available Qty", 0), errors="coerce").fillna(0)
        df_inv_valid = df_inv_r[df_inv_r["Date"] <= report_date_str]
        if not df_inv_valid.empty:
            idx = df_inv_valid.groupby("Item Code")["Date"].idxmax()
            latest_inv = df_inv_valid.loc[idx]
            inv_by_item = dict(zip(latest_inv["Item Code"], latest_inv["Available Qty"]))

    # Forecast for this month
    df_fc_r = pd.DataFrame(get_records(ws_forecast, "forecast"))
    forecast_by_item = {}
    if not df_fc_r.empty:
        df_fc_r["Product Code"] = df_fc_r["Product Code"].astype(str)
        month_fc = df_fc_r[(df_fc_r["Year"].astype(str) == year_str) & (df_fc_r["Month"] == month_str)]
        forecast_by_item = dict(zip(month_fc["Product Code"],
                                    pd.to_numeric(month_fc["Forecast Qty"], errors="coerce").fillna(0)))

    # Working days for this month
    df_wd_r = pd.DataFrame(get_records(ws_working_days, "working_days"))
    working_days_val = 0
    if not df_wd_r.empty:
        match = df_wd_r[(df_wd_r["Year"].astype(str) == year_str) & (df_wd_r["Month"] == month_str)]
        if not match.empty:
            wd = pd.to_numeric(match.iloc[0]["Working Days"], errors="coerce")
            working_days_val = wd if pd.notna(wd) and wd > 0 else 0

    rows = []
    for i, item_row in df_items_r.reset_index(drop=True).iterrows():
        code = str(item_row["Product Code"])
        name = item_row.get("Item Name", "")
        sale = float(daily_sale_by_item.get(code, 0))
        mtd_sale = float(mtd_sale_by_item.get(code, 0))
        forecast = float(forecast_by_item.get(code, 0))
        achievement = (mtd_sale / forecast * 100) if forecast > 0 else 0.0
        balance = mtd_sale - forecast
        inventory_qty = float(inv_by_item.get(code, 0))
        day_target = (forecast / working_days_val) if working_days_val else 0.0
        buffer_level = day_target * 6
        avg_sale_per_day = (mtd_sale / days_elapsed) if days_elapsed else 0.0
        avg_sale_per_week = (mtd_sale / elapsed_weeks) if elapsed_weeks else 0.0
        buffer_balance = inventory_qty - avg_sale_per_week

        week_sales = {}
        for w in range(1, 6):
            if not week_pivot.empty and code in week_pivot.index and w in week_pivot.columns:
                week_sales[w] = float(week_pivot.loc[code, w])
            else:
                week_sales[w] = 0.0

        rows.append({
            "Index No": i + 1,
            "Item Code": code,
            "Item Name": name,
            "Sale": round(sale, 2),
            "MTD Sale": round(mtd_sale, 2),
            "Forecast": round(forecast, 2),
            "Forecast Achievement (%)": round(achievement, 2),
            "Balance": round(balance, 2),
            "Inventory": round(inventory_qty, 2),
            "Buffer Level": round(buffer_level, 2),
            "Average Sale per Week": round(avg_sale_per_week, 2),
            "Buffer Balance": round(buffer_balance, 2),
            "Day Target": round(day_target, 2),
            "Average Sale per Day": round(avg_sale_per_day, 2),
            "Week 1 Sale": round(week_sales[1], 2),
            "Week 2 Sale": round(week_sales[2], 2),
            "Week 3 Sale": round(week_sales[3], 2),
            "Week 4 Sale": round(week_sales[4], 2),
            "Week 5 Sale": round(week_sales[5], 2),
        })

    return pd.DataFrame(rows)


DETAILED_REPORT_COLUMNS = [
    "Index No", "Item Code", "Item Name", "Sale", "MTD Sale", "Forecast", "Forecast Achievement (%)",
    "Balance", "Inventory", "Buffer Level", "Average Sale per Week", "Buffer Balance",
    "Day Target", "Average Sale per Day",
    "Week 1 Sale", "Week 2 Sale", "Week 3 Sale", "Week 4 Sale", "Week 5 Sale",
]

# Columns that get red/green/amber conditional coloring
_CONDITIONAL_COLS = {"Forecast Achievement (%)", "Balance", "Buffer Balance"}

# How many decimal places to show per column (kept tight so PDF cells never overflow)
_DECIMALS = {
    "Sale": 0, "MTD Sale": 0, "Forecast": 0, "Balance": 1, "Inventory": 0, "Buffer Level": 1,
    "Average Sale per Week": 1, "Buffer Balance": 1, "Day Target": 1, "Average Sale per Day": 1,
    "Week 1 Sale": 0, "Week 2 Sale": 0, "Week 3 Sale": 0, "Week 4 Sale": 0, "Week 5 Sale": 0,
}

# Short header labels used ONLY in the PDF (keeps a landscape page from overflowing);
# the on-screen table keeps the full, readable names.
_PDF_HEADER_ABBR = {
    "Index No": "#", "Item Code": "Code", "Item Name": "Item Name",
    "Sale": "Sale", "MTD Sale": "MTD", "Forecast": "Fcst", "Forecast Achievement (%)": "Achv %",
    "Balance": "Balance", "Inventory": "Inv.", "Buffer Level": "Buf. Lvl",
    "Average Sale per Week": "Avg/Wk", "Buffer Balance": "Buf. Bal",
    "Day Target": "Day Tgt", "Average Sale per Day": "Avg/Day",
    "Week 1 Sale": "Wk1", "Week 2 Sale": "Wk2", "Week 3 Sale": "Wk3",
    "Week 4 Sale": "Wk4", "Week 5 Sale": "Wk5",
}

# Relative column-width weights for the PDF (normalised to 100% at render time).
# Item Name gets the most room; narrow numeric columns get the least.
_PDF_COLUMN_WEIGHTS = {
    "Index No": 2.2, "Item Code": 5.5, "Item Name": 15,
    "Sale": 4, "MTD Sale": 4, "Forecast": 4, "Forecast Achievement (%)": 5,
    "Balance": 4.5, "Inventory": 4, "Buffer Level": 4.5,
    "Average Sale per Week": 5, "Buffer Balance": 5,
    "Day Target": 4.5, "Average Sale per Day": 5,
    "Week 1 Sale": 4, "Week 2 Sale": 4, "Week 3 Sale": 4, "Week 4 Sale": 4, "Week 5 Sale": 4,
}


def _cell_class(col, value):
    """Return a CSS class name for conditional-colour cells."""
    if col == "Forecast Achievement (%)":
        if value >= 100:
            return "good"
        elif value >= 80:
            return "warn"
        else:
            return "bad"
    if col in ("Balance", "Buffer Balance"):
        if value > 0:
            return "good"
        elif value == 0:
            return ""
        else:
            return "bad"
    return ""


def _format_value(col, value):
    if col == "Index No":
        return str(int(value))
    if col in ("Item Code", "Item Name"):
        return str(value)
    if col == "Forecast Achievement (%)":
        return f"{value:,.1f}%"
    decimals = _DECIMALS.get(col, 2)
    return f"{value:,.{decimals}f}"


def _build_table_rows(df):
    """Shared row-building logic used by both the screen and PDF renderers."""
    body_rows = []
    for ridx, row in df.iterrows():
        row_class = "even" if ridx % 2 == 0 else "odd"
        cells = []
        for col in DETAILED_REPORT_COLUMNS:
            val = row[col]
            css_class = _cell_class(col, val) if col in _CONDITIONAL_COLS else ""
            extra_class = "item-name" if col == "Item Name" else ""
            classes = " ".join(c for c in [css_class, extra_class] if c)
            class_attr = f' class="{classes}"' if classes else ""
            cells.append(f"<td{class_attr}>{_format_value(col, val)}</td>")
        body_rows.append(f'<tr class="{row_class}">' + "".join(cells) + "</tr>")
    return "".join(body_rows)


def build_pdf_html(df, report_date_str):
    """Build a landscape, xhtml2pdf-compatible HTML document for the detailed report.
    Uses abbreviated headers + weighted fixed column widths so every number fits
    cleanly inside its cell instead of being clipped."""
    total_weight = sum(_PDF_COLUMN_WEIGHTS.values())
    colgroup = "".join(
        f'<col style="width:{(_PDF_COLUMN_WEIGHTS[col] / total_weight * 100):.2f}%;">'
        for col in DETAILED_REPORT_COLUMNS
    )
    header_cells = "".join(f"<th>{_PDF_HEADER_ABBR[col]}</th>" for col in DETAILED_REPORT_COLUMNS)
    body_html = _build_table_rows(df)

    legend_line = (
        "Fcst=Forecast | Achv%=Forecast Achievement | Inv.=Inventory | Buf. Lvl=Buffer Level "
        "(Day Target x 6) | Avg/Wk=Average Sale per Week | Buf. Bal=Buffer Balance "
        "(Inventory - Avg/Wk) | Day Tgt=Day Target | Avg/Day=Average Sale per Day | Wk1-5=Weekly Sale"
    )

    style = """
    <style>
        @page { size: A4 landscape; margin: 1cm 0.6cm 1cm 0.6cm; }
        body { font-family: Helvetica, Arial, sans-serif; }
        h2 { color: #154360; margin: 0 0 4px 0; }
        p.sub { color: #555555; margin: 0 0 6px 0; font-size: 9px; }
        p.legend { color: #7a7a7a; margin: 0 0 10px 0; font-size: 7px; }
        table { border-collapse: collapse; width: 100%; table-layout: fixed; font-size: 7.5px; }
        thead { display: table-header-group; }
        tr { page-break-inside: avoid; }
        th {
            background-color: #154360; color: #ffffff; padding: 5px 3px;
            text-align: center; border: 1px solid #0e2f44; word-wrap: break-word;
        }
        td {
            padding: 4px 3px; text-align: center; border: 1px solid #d0d7de;
            word-wrap: break-word; overflow-wrap: break-word;
        }
        tr.even { background-color: #f2f6fa; }
        tr.odd { background-color: #ffffff; }
        td.item-name { text-align: left; }
        td.good { background-color: #d4f7dc; color: #1b6e34; font-weight: bold; }
        td.bad { background-color: #fbdcdc; color: #a41c1c; font-weight: bold; }
        td.warn { background-color: #fdf0cd; color: #8a5a00; font-weight: bold; }
    </style>
    """

    html = f"""
    <html><head>{style}</head>
    <body>
        <h2>Item Wise Detailed Report</h2>
        <p class="sub">Report date: {report_date_str} &nbsp;|&nbsp; Total items: {len(df)}</p>
        <p class="legend">{legend_line}</p>
        <table>
            <colgroup>{colgroup}</colgroup>
            <thead><tr>{header_cells}</tr></thead>
            <tbody>{body_html}</tbody>
        </table>
    </body></html>
    """
    return html


def build_screen_html(df, report_date_str):
    """Build the interactive on-screen table: full column names, a synced scrollbar
    ABOVE the table (so you don't need to scroll past all 53 rows to scroll sideways),
    and a 'Save as Image' button that captures the table as a PNG. Meant to be
    rendered with st.components.v1.html (needs real JS execution, unlike st.markdown)."""
    header_cells = "".join(f"<th>{col}</th>" for col in DETAILED_REPORT_COLUMNS)
    body_html = _build_table_rows(df)
    safe_filename = f"Item_Report_{report_date_str}"

    html = f"""
    <style>
        html, body {{ margin:0; padding:0; font-family: 'Segoe UI', Arial, sans-serif; }}
        .report-title {{ font-size: 20px; font-weight: 700; color: #154360; margin-bottom: 2px; }}
        .report-sub {{ color: #5b6b79; margin-bottom: 10px; font-size: 13px; }}
        .legend-row {{ display:flex; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:10px; }}
        .legend-chip {{ display:inline-block; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; }}
        .snap-btn {{
            margin-left:auto; padding:7px 14px; border:none; border-radius:8px; cursor:pointer;
            background: linear-gradient(135deg, #1f6faa 0%, #154360 100%); color:#fff;
            font-size:13px; font-weight:600; box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        }}
        .snap-btn:hover {{ opacity: 0.92; }}
        .top-scroll {{ overflow-x: scroll; overflow-y: hidden; height: 16px; margin-bottom: 4px; }}
        .top-scroll-content {{ height: 1px; }}
        .report-wrap {{
            overflow: auto; max-height: 620px; border-radius: 14px;
            box-shadow: 0 4px 18px rgba(0,0,0,0.12); border: 1px solid #dbe4ec;
        }}
        table.detailed-report {{
            border-collapse: collapse; width: 100%; min-width: 1700px; font-size: 13px;
        }}
        table.detailed-report thead th {{
            position: sticky; top: 0;
            background: linear-gradient(135deg, #154360 0%, #1f6faa 100%);
            color: #ffffff; padding: 12px 8px; text-align: center; font-weight: 600;
            letter-spacing: 0.3px; border-bottom: 2px solid #0e2f44; white-space: nowrap;
        }}
        table.detailed-report tbody td {{
            padding: 9px 8px; text-align: center; border-bottom: 1px solid #e6ebf0; white-space: nowrap;
        }}
        table.detailed-report tbody td.item-name {{ text-align: left; font-weight: 500; color: #1b2a38; }}
        table.detailed-report tbody tr:nth-child(even) {{ background-color: #f4f8fb; }}
        table.detailed-report tbody tr:nth-child(odd) {{ background-color: #ffffff; }}
        table.detailed-report tbody tr:hover {{ background-color: #eaf3fb; }}
        table.detailed-report td.good {{ background-color: #d9f7e3 !important; color: #157347; font-weight: 700; }}
        table.detailed-report td.bad {{ background-color: #fde2e1 !important; color: #b3261e; font-weight: 700; }}
        table.detailed-report td.warn {{ background-color: #fdf1cd !important; color: #8a5a00; font-weight: 700; }}
    </style>

    <div id="captureArea">
        <div class="report-title">📋 Item Wise Detailed Report</div>
        <div class="report-sub">Report date: <b>{report_date_str}</b> &nbsp;|&nbsp; Total items: <b>{len(df)}</b></div>
        <div class="report-wrap" id="bottomScroll">
            <table class="detailed-report" id="reportTable">
                <thead><tr>{header_cells}</tr></thead>
                <tbody>{body_html}</tbody>
            </table>
        </div>
    </div>

    <div class="legend-row" style="margin-top:10px;">
        <span class="legend-chip" style="background:#d9f7e3;color:#157347;">🟢 On/above target</span>
        <span class="legend-chip" style="background:#fdf1cd;color:#8a5a00;">🟡 Near target (80-99%)</span>
        <span class="legend-chip" style="background:#fde2e1;color:#b3261e;">🔴 Below target / shortfall</span>
        <button id="snapshotBtn" class="snap-btn">📸 Save as Image</button>
    </div>

    <div class="top-scroll" id="topScroll" title="Drag to scroll the table sideways">
        <div class="top-scroll-content" id="topScrollContent"></div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <script>
        const topScroll = document.getElementById('topScroll');
        const topContent = document.getElementById('topScrollContent');
        const bottomScroll = document.getElementById('bottomScroll');
        const table = document.getElementById('reportTable');

        function syncTopWidth() {{ topContent.style.width = table.scrollWidth + 'px'; }}
        syncTopWidth();
        window.addEventListener('resize', syncTopWidth);

        let syncingTop = false, syncingBottom = false;
        topScroll.addEventListener('scroll', function () {{
            if (syncingTop) {{ syncingTop = false; return; }}
            syncingBottom = true;
            bottomScroll.scrollLeft = topScroll.scrollLeft;
        }});
        bottomScroll.addEventListener('scroll', function () {{
            if (syncingBottom) {{ syncingBottom = false; return; }}
            syncingTop = true;
            topScroll.scrollLeft = bottomScroll.scrollLeft;
        }});

        document.getElementById('snapshotBtn').addEventListener('click', function () {{
            const captureArea = document.getElementById('captureArea');
            html2canvas(captureArea, {{ scale: 2, backgroundColor: '#ffffff' }}).then(function (canvas) {{
                const link = document.createElement('a');
                link.download = '{safe_filename}.png';
                link.href = canvas.toDataURL('image/png');
                link.click();
            }});
        }});
    </script>
    """
    return html


def generate_report_pdf(df, report_date_str):
    """Convert the detailed report to a landscape PDF file (bytes) using xhtml2pdf.
    Returns None if conversion fails."""
    html = build_pdf_html(df, report_date_str)
    output = io.BytesIO()
    result = pisa.CreatePDF(src=html, dest=output)
    if result.err:
        return None
    return output.getvalue()


# ==========================================================================
# DASHBOARD PDF EXPORT — charts rendered as static images (needs "kaleido")
# ==========================================================================
def build_dashboard_pdf_html(report_date_str, kpis, chart_images, group_summary_df):
    """kpis: list of (label, value, accent_hex). chart_images: dict title -> base64 png or None."""
    kpi_cells = "".join(
        f'''<td width="25%" align="center" valign="middle" style="padding:10px 6px;background-color:#f7fafc;
             border-left:5px solid {accent};border-top:1px solid #ccc;border-right:1px solid #ccc;border-bottom:1px solid #ccc;">
                <div style="font-size:17px;font-weight:bold;color:#262730;">{value}</div>
                <div style="font-size:10px;color:#666;letter-spacing:0.5px;">{label.upper()}</div>
            </td>'''
        for (label, value, accent) in kpis
    )

    chart_blocks = ""
    for title, img_b64 in chart_images.items():
        if img_b64:
            chart_blocks += f'''
            <h3 style="color:#154360;font-size:14px;margin-top:16px;margin-bottom:4px;">{title}</h3>
            <img src="data:image/png;base64,{img_b64}" width="100%" />
            '''
        else:
            chart_blocks += f'''
            <h3 style="color:#154360;font-size:14px;margin-top:16px;margin-bottom:4px;">{title}</h3>
            <p style="color:#a41c1c;font-size:10px;">Chart image unavailable — install the "kaleido" package to enable chart export.</p>
            '''

    group_rows = "".join(
        f"<tr><td style='border:1px solid #ddd;padding:5px;'>{row['Group']}</td>"
        f"<td style='border:1px solid #ddd;padding:5px;text-align:right;'>{row['MTD Sale']:,.0f}</td>"
        f"<td style='border:1px solid #ddd;padding:5px;text-align:right;'>{row['Forecast']:,.0f}</td>"
        f"<td style='border:1px solid #ddd;padding:5px;text-align:right;'>{row['Achievement %']:,.1f}%</td>"
        f"<td style='border:1px solid #ddd;padding:5px;text-align:right;'>LKR {row['MTD Revenue']:,.0f}</td></tr>"
        for _, row in group_summary_df.iterrows()
    )

    html = f"""
    <html><head>
    <style>
        @page {{ size: A4 landscape; margin: 1cm; }}
        body {{ font-family: Helvetica, Arial, sans-serif; color: #333; margin: 0; padding: 0; }}
        h2 {{ color: #154360; margin: 0 0 2px 0; }}
        p.sub {{ color: #666; font-size: 11px; margin: 0 0 12px 0; }}
        table.grouptbl {{ border-collapse: collapse; width: 100%; font-size: 10px; margin-top: 6px; }}
        table.grouptbl th {{ background-color: #154360; color: #ffffff; padding: 6px; border: 1px solid #0e2f44; }}
    </style>
    </head>
    <body>
        <h2>Production Requirement — Dashboard Summary</h2>
        <p class="sub">Report date: {report_date_str}</p>
        <table width="100%" cellpadding="0" cellspacing="6"><tr>{kpi_cells}</tr></table>
        {chart_blocks}
        <h3 style="color:#154360;font-size:14px;margin-top:16px;margin-bottom:4px;">Group-wise Summary</h3>
        <table class="grouptbl">
            <thead><tr><th>Group</th><th>MTD Sale (Kg)</th><th>Forecast (Kg)</th><th>Achievement %</th><th>MTD Revenue</th></tr></thead>
            <tbody>{group_rows}</tbody>
        </table>
    </body></html>
    """
    return html


def generate_dashboard_pdf(report_date_str, kpis, chart_images, group_summary_df):
    """Convert the dashboard (KPIs + chart images + group table) to a landscape PDF (bytes).
    Returns None if the HTML-to-PDF conversion itself fails."""
    html = build_dashboard_pdf_html(report_date_str, kpis, chart_images, group_summary_df)
    output = io.BytesIO()
    result = pisa.CreatePDF(src=html, dest=output)
    if result.err:
        return None
    return output.getvalue()


with main_tab2:
    st.markdown("### 📋 Item Wise Detailed Report")
    st.caption("Pick a date to see the full breakdown for every item, including weekly sales and buffer levels. "
               "Sale / MTD Sale figures are based on units sold (Qty, in Kg), not revenue.")

    fcol1, fcol2 = st.columns([1, 3])
    with fcol1:
        tab2_report_date = st.date_input(
            "📅 Filter by Date:",
            value=datetime.date.today(),
            key="tab2_report_date_filter",
        )

    tab2_date_str = tab2_report_date.strftime("%Y-%m-%d")
    detailed_df = compute_detailed_report(tab2_report_date)

    if detailed_df.empty:
        st.warning("No items found in the Item Master List. Add items in Settings first.")
    else:
        screen_html = build_screen_html(detailed_df, tab2_date_str)
        # components.html actually executes the embedded JS (scroll sync + snapshot button);
        # st.markdown silently strips <script> tags, so it can't be used here.
        components.html(screen_html, height=800, scrolling=False)

        st.divider()

        export_col1, export_col2 = st.columns([1, 3])
        with export_col1:
            if st.button("📄 Prepare PDF", type="primary", key="prepare_pdf_btn"):
                with st.spinner("Building PDF..."):
                    pdf_bytes = generate_report_pdf(detailed_df, tab2_date_str)
                if pdf_bytes:
                    st.session_state["tab2_pdf_bytes"] = pdf_bytes
                    st.session_state["tab2_pdf_date"] = tab2_date_str
                    st.toast("✅ PDF ready to download!")
                else:
                    st.error("Could not generate the PDF. Make sure the 'xhtml2pdf' package is installed "
                              "(pip install xhtml2pdf) and added to your requirements.txt.")

        with export_col2:
            if st.session_state.get("tab2_pdf_bytes") and st.session_state.get("tab2_pdf_date") == tab2_date_str:
                st.download_button(
                    label=f"⬇️ Download Report_{tab2_date_str}.pdf",
                    data=st.session_state["tab2_pdf_bytes"],
                    file_name=f"Item_Report_{tab2_date_str}.pdf",
                    mime="application/pdf",
                    key="download_pdf_btn",
                )


# ==========================================================================
# TAB 3: DASHBOARD
# ==========================================================================
with main_tab3:
    st.markdown("### 📊 Sales & Inventory Dashboard")
    st.caption("Generate (or refresh) the item-wise summary report for a date, then explore it below.")

    sales_records_all = get_records(ws_daily_sales, "daily_sales")
    df_sales_dates = pd.DataFrame(sales_records_all)
    if not df_sales_dates.empty and "Date" in df_sales_dates.columns:
        available_dates = sorted(df_sales_dates["Date"].dropna().astype(str).unique().tolist(), reverse=True)
    else:
        available_dates = []

    if not available_dates:
        st.warning("No sales data uploaded yet. Upload a Daily Sales CSV in the Data Entry tab first.")
    else:
        dcol1, dcol2 = st.columns([1, 3])
        with dcol1:
            dash_date_str = st.selectbox("📅 Select Date:", available_dates, key="dash_date_select")
        with dcol2:
            st.write("")
            st.write("")
            if st.button("⚙️ Generate / Refresh Report", type="primary", key="dash_generate_btn"):
                with st.spinner("Calculating report..."):
                    dash_date_obj = datetime.datetime.strptime(dash_date_str, "%Y-%m-%d").date()
                    result_df = build_report(dash_date_obj)
                    st.session_state["dash_report"] = result_df
                    st.session_state["dash_report_date"] = dash_date_str
                st.toast(f"✅ Report generated and saved for {dash_date_str}")

        if "dash_report" not in st.session_state and dash_date_str:
            # Auto-generate on first load for the selected date so the dashboard isn't empty
            with st.spinner("Calculating report..."):
                dash_date_obj = datetime.datetime.strptime(dash_date_str, "%Y-%m-%d").date()
                st.session_state["dash_report"] = build_report(dash_date_obj)
                st.session_state["dash_report_date"] = dash_date_str

        if "dash_report" in st.session_state:
            rpt = st.session_state["dash_report"]
            rpt_date = st.session_state["dash_report_date"]
            rpt["Group"] = rpt["Product Code"].apply(get_group)

            # ---------------- KPI CARDS ----------------
            # Day's Sale / MTD Sale are shown as REVENUE (LKR) here; Forecast /
            # Achievement stay in Kg since Forecast is entered in quantity.
            total_sale_rev = rpt["Revenue (LKR)"].sum()
            total_mtd_rev = rpt["MTD Revenue (LKR)"].sum()
            total_forecast = rpt["Forecast"].sum()
            avg_achv = rpt.loc[rpt["Forecast"] > 0, "Forecast Achievement (%)"].mean()
            avg_achv = 0 if pd.isna(avg_achv) else avg_achv

            k1, k2, k3, k4 = st.columns(4)
            gradients = [
                "linear-gradient(135deg,#667eea,#764ba2)",
                "linear-gradient(135deg,#43e97b,#38f9d7)",
                "linear-gradient(135deg,#4facfe,#00f2fe)",
                "linear-gradient(135deg,#fa709a,#fee140)",
            ]
            with k1:
                st.markdown(kpi_card("Day's Sale", money_fmt(total_sale_rev), "💰", gradients[0]), unsafe_allow_html=True)
            with k2:
                st.markdown(kpi_card("MTD Sale", money_fmt(total_mtd_rev), "📈", gradients[1]), unsafe_allow_html=True)
            with k3:
                st.markdown(kpi_card("MTD Forecast (Kg)", f"{total_forecast:,.0f}", "🎯", gradients[2]), unsafe_allow_html=True)
            with k4:
                st.markdown(kpi_card("Avg Achievement", f"{avg_achv:,.1f}%", "🏆", gradients[3]), unsafe_allow_html=True)

            st.write("")
            st.markdown(f"<p style='color:#94a3b8;'>Showing summary for <b>{rpt_date}</b> across "
                        f"<b>{len(rpt)}</b> items.</p>", unsafe_allow_html=True)
            st.divider()

            # ---------------- CHARTS ----------------
            chart_tab1, chart_tab2, chart_tab3, chart_tab4, chart_tab5 = st.tabs(
                ["📦 MTD Sale vs Forecast", "🎯 Achievement %", "🧮 Inventory Balance",
                 "🥇 Top / Bottom Items", "🗂️ Group Overview"]
            )

            plotly_layout = dict(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"),
                height=520,
            )

            with chart_tab1:
                fig1 = px.bar(
                    rpt, x="Item Name", y=["MTD Sale", "Forecast"], barmode="group",
                    title="Month-to-Date Sale vs Forecast by Item (Kg)",
                    color_discrete_sequence=["#667eea", "#f093fb"],
                )
                fig1.update_layout(xaxis_tickangle=-45, **plotly_layout)
                st.plotly_chart(fig1, use_container_width=True)

            with chart_tab2:
                fig2 = px.bar(
                    rpt.sort_values("Forecast Achievement (%)"),
                    x="Item Name", y="Forecast Achievement (%)",
                    title="Forecast Achievement % by Item",
                    color="Forecast Achievement (%)",
                    color_continuous_scale=["#ef4444", "#f59e0b", "#22c55e"],
                )
                fig2.update_layout(xaxis_tickangle=-45, **plotly_layout)
                fig2.add_hline(y=100, line_dash="dash", line_color="#e2e8f0")
                st.plotly_chart(fig2, use_container_width=True)

            with chart_tab3:
                fig3 = px.bar(
                    rpt, x="Item Name", y="Inventory Balance",
                    title="Inventory Balance by Item",
                    color="Inventory Balance",
                    color_continuous_scale=["#4facfe", "#43e97b"],
                )
                fig3.update_layout(xaxis_tickangle=-45, **plotly_layout)
                st.plotly_chart(fig3, use_container_width=True)

            with chart_tab4:
                top5 = rpt.sort_values("MTD Sale", ascending=False).head(5)
                bottom5 = rpt[rpt["Forecast"] > 0].sort_values("Forecast Achievement (%)").head(5)

                donut_labels = ["On/Above Target", "Near Target (80-99%)", "Below Target (<80%)"]
                donut_values = [
                    int((rpt["Forecast Achievement (%)"] >= 100).sum()),
                    int(((rpt["Forecast Achievement (%)"] >= 80) & (rpt["Forecast Achievement (%)"] < 100)).sum()),
                    int((rpt["Forecast Achievement (%)"] < 80).sum()),
                ]
                fig4 = go.Figure(data=[go.Pie(
                    labels=donut_labels, values=donut_values, hole=0.55,
                    marker=dict(colors=["#22c55e", "#f59e0b", "#ef4444"]),
                )])
                fig4.update_layout(title="Items by Target Status", **plotly_layout)

                cc1, cc2 = st.columns([1, 1])
                with cc1:
                    st.plotly_chart(fig4, use_container_width=True)
                with cc2:
                    st.markdown("**🏅 Top 5 by MTD Sale**")
                    st.dataframe(styled_table(top5[["Item Name", "MTD Sale", "Forecast Achievement (%)"]],
                                               gradient_cols=["MTD Sale"], cmap="Greens"),
                                 use_container_width=True, hide_index=True)
                    st.markdown("**🔻 Bottom 5 by Achievement %**")
                    st.dataframe(styled_table(bottom5[["Item Name", "MTD Sale", "Forecast Achievement (%)"]],
                                               gradient_cols=["Forecast Achievement (%)"], cmap="Reds"),
                                 use_container_width=True, hide_index=True)

            with chart_tab5:
                st.caption("Items are grouped into **Chicken** (whole/cut birds), **Potion** (portioned cuts), "
                           "and **Easy** (ready-to-cook packs).")

                group_summary = rpt.groupby("Group").agg(
                    **{
                        "MTD Sale": ("MTD Sale", "sum"),
                        "Forecast": ("Forecast", "sum"),
                        "MTD Revenue": ("MTD Revenue (LKR)", "sum"),
                        "Inventory": ("Inventory", "sum"),
                    }
                ).reset_index()
                group_summary["Achievement %"] = np.where(
                    group_summary["Forecast"] > 0,
                    group_summary["MTD Sale"] / group_summary["Forecast"] * 100,
                    0,
                )
                group_summary["Group"] = pd.Categorical(group_summary["Group"], categories=GROUP_ORDER, ordered=True)
                group_summary = group_summary.sort_values("Group").reset_index(drop=True)

                # KPI strip per group
                gk_cols = st.columns(len(group_summary))
                for gk_col, (_, g_row) in zip(gk_cols, group_summary.iterrows()):
                    with gk_col:
                        grad = f"linear-gradient(135deg,{GROUP_COLORS.get(g_row['Group'], '#94a3b8')},#1f2937)"
                        st.markdown(
                            kpi_card(f"{g_row['Group']} — MTD Revenue", money_fmt(g_row["MTD Revenue"]), "🧺", grad),
                            unsafe_allow_html=True,
                        )

                st.write("")
                gcol1, gcol2 = st.columns([3, 2])
                with gcol1:
                    fig_group_bar = px.bar(
                        group_summary, x="Group", y=["MTD Sale", "Forecast"], barmode="group",
                        title="MTD Sale vs Forecast by Product Group (Kg)",
                        color_discrete_sequence=["#667eea", "#f093fb"],
                    )
                    fig_group_bar.update_layout(**plotly_layout)
                    st.plotly_chart(fig_group_bar, use_container_width=True)
                with gcol2:
                    fig_group_donut = go.Figure(data=[go.Pie(
                        labels=group_summary["Group"].astype(str), values=group_summary["MTD Revenue"], hole=0.55,
                        marker=dict(colors=[GROUP_COLORS.get(g, "#94a3b8") for g in group_summary["Group"]]),
                    )])
                    fig_group_donut.update_layout(title="MTD Revenue Share by Group", **plotly_layout)
                    st.plotly_chart(fig_group_donut, use_container_width=True)

                fig_group_achv = px.bar(
                    group_summary, x="Group", y="Achievement %",
                    title="Forecast Achievement % by Product Group",
                    color="Group",
                    color_discrete_map=GROUP_COLORS,
                )
                fig_group_achv.update_layout(**plotly_layout)
                fig_group_achv.add_hline(y=100, line_dash="dash", line_color="#e2e8f0")
                st.plotly_chart(fig_group_achv, use_container_width=True)

                st.markdown("**📋 Group Summary Table**")
                st.dataframe(
                    styled_table(group_summary[["Group", "MTD Sale", "Forecast", "Achievement %", "MTD Revenue", "Inventory"]],
                                 gradient_cols=["MTD Sale", "MTD Revenue"], cmap="Purples"),
                    use_container_width=True, hide_index=True,
                )

            st.divider()
            with st.expander("📄 View full report table"):
                st.dataframe(
                    styled_table(rpt, gradient_cols=["MTD Sale", "Forecast", "Forecast Achievement (%)", "MTD Revenue (LKR)"],
                                 cmap="Blues"),
                    use_container_width=True, hide_index=True,
                )

            # ---------------- DASHBOARD PDF EXPORT ----------------
            st.divider()
            # Colors used ONLY when rendering chart PNGs for the PDF export — dark text,
            # since the PDF page is white (unlike the on-screen dark glass card).
            PDF_CHART_LAYOUT = dict(
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(color="#1e293b", size=13),
                title_font=dict(color="#154360", size=16),
                legend=dict(font=dict(color="#1e293b")),
                height=480,
            )


            def render_chart_for_pdf(fig_obj):
                """Return a PDF-safe PNG (bytes) for a plotly figure: same data/traces,
                but with dark titles/axis labels/legend so text is readable on a white page."""
                pdf_fig = go.Figure(fig_obj)  # copy — leaves the on-screen figure untouched
                pdf_fig.update_layout(**PDF_CHART_LAYOUT)
                pdf_fig.update_xaxes(
                    color="#1e293b", tickfont=dict(color="#1e293b"),
                    title_font=dict(color="#154360"),
                    gridcolor="#e2e8f0", linecolor="#94a3b8", zerolinecolor="#94a3b8",
                )
                pdf_fig.update_yaxes(
                    color="#1e293b", tickfont=dict(color="#1e293b"),
                    title_font=dict(color="#154360"),
                    gridcolor="#e2e8f0", linecolor="#94a3b8", zerolinecolor="#94a3b8",
                )
                return pdf_fig.to_image(format="png", width=900, height=480, scale=2)
            
            if st.button("📄 Prepare Dashboard PDF", type="primary", key="prepare_dash_pdf_btn"):
                with st.spinner("Rendering charts and building PDF..."):
                    chart_images = {}
                    for chart_title, fig_obj in [
                        ("MTD Sale vs Forecast by Item", fig1),
                        ("Forecast Achievement % by Item", fig2),
                        ("Inventory Balance by Item", fig3),
                        ("MTD Sale vs Forecast by Group", fig_group_bar),
                        ("MTD Revenue Share by Group", fig_group_donut),
                        ("Forecast Achievement % by Group", fig_group_achv),
                    ]:
                        try:
                            img_bytes = render_chart_for_pdf(fig_obj)
                            chart_images[chart_title] = base64.b64encode(img_bytes).decode()
                        except Exception:
                            chart_images[chart_title] = None

                    kpis_for_pdf = [
                        ("Day's Sale", money_fmt(total_sale_rev), "#38bdf8"),
                        ("MTD Sale", money_fmt(total_mtd_rev), "#34d399"),
                        ("MTD Forecast (Kg)", f"{total_forecast:,.0f}", "#a78bfa"),
                        ("Avg Achievement", f"{avg_achv:,.1f}%", "#facc15"),
                    ]
                    pdf_bytes = generate_dashboard_pdf(rpt_date, kpis_for_pdf, chart_images, group_summary)

                if pdf_bytes:
                    st.session_state["dash_pdf_bytes"] = pdf_bytes
                    st.session_state["dash_pdf_date"] = rpt_date
                    st.toast("✅ Dashboard PDF ready to download!")
                else:
                    st.error("Could not generate the PDF.")

            if st.session_state.get("dash_pdf_bytes") and st.session_state.get("dash_pdf_date") == rpt_date:
                st.download_button(
                    label=f"⬇️ Download Dashboard_{rpt_date}.pdf",
                    data=st.session_state["dash_pdf_bytes"],
                    file_name=f"Dashboard_{rpt_date}.pdf",
                    mime="application/pdf",
                    key="download_dash_pdf_btn",
                )
                st.caption("If a chart shows as a note instead of an image in the PDF, install the 'kaleido' "
                        "package (pip install -U kaleido), add it to requirements.txt, then rebuild the PDF.")

            style_block = """
            <style>
                h2 { color: #154360; }          /* main heading */
                p.sub { color: #666; }          /* date/subtitle line */
                table.grouptbl th { background-color: #154360; color: #ffffff; }
            </style>
            """