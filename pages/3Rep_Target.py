import streamlit as st
import pandas as pd
import time
import gspread
from utils import (
    add_logo, check_password, check_access, load_master_data,
    save_monthly_data, load_targets_for_month,
    get_sales_daybook_ws, get_rows_for_date, delete_rows_for_date
)
st.set_page_config(page_title="Target Entry System", layout="wide")

# --- CSS STYLING ---
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #96ceb4 0%, #ffeead 20%, #ffcc5c 40%, #ff6f69 70%, #88d8b0 100%);
    background-size: 400% 400%;
    animation: gradientShift 22s ease infinite;
}
@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
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
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1f2937 0%, #111827 100%);
}
[data-testid="stSidebar"] * { color: #f3f4f6 !important; }
h1, h2, h3 { color: #f1f5f9; font-weight: 800; }
h1 {
    background: linear-gradient(135deg, #ff6f69, #ffcc5c);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
button[data-baseweb="tab"] {
    background: linear-gradient(135deg, #ffeead 0%, #96ceb4 100%) !important;
    border-radius: 14px 14px 0 0 !important;
    padding: 10px 22px !important;
    margin-right: 6px !important;
    font-weight: 700 !important;
    color: #2d3748 !important;
    border: none !important;
    transition: all 0.25s ease;
}
button[data-baseweb="tab"]:hover {
    background: linear-gradient(135deg, #88d8b0 0%, #96ceb4 100%) !important;
    color: white !important;
    transform: translateY(-2px);
}
button[data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #ff6f69 0%, #ffcc5c 100%) !important;
    color: white !important;
    box-shadow: 0 4px 14px rgba(255, 111, 105, 0.45);
}
.stButton>button, .stDownloadButton>button {
    border-radius: 10px;
    border: none;
    background: linear-gradient(135deg, #ff6f69 0%, #ffcc5c 100%);
    color: white !important;
    font-weight: 700;
    padding: 0.5rem 1.3rem;
    box-shadow: 0 4px 12px rgba(255, 111, 105, 0.35);
    transition: all .2s ease;
}
.stButton>button:hover, .stDownloadButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 18px rgba(255, 111, 105, 0.5);
}
[data-testid="stDataFrame"], [data-testid="stDataEditor"] {
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 4px 18px rgba(0,0,0,0.10);
    border: 1px solid #e2e8f0;
}
hr { border-top: 2px solid rgba(150, 206, 180, 0.3) !important; }
.section-banner {
    background: linear-gradient(135deg, #ff6f69 0%, #ffcc5c 100%);
    color: white; padding: 14px 20px; border-radius: 14px;
    font-size: 20px; font-weight: 800; margin-bottom: 14px;
    box-shadow: 0 4px 14px rgba(255, 111, 105, 0.3);
}
</style>
""", unsafe_allow_html=True)

# --- LOGIN AND ACCESS CONTROL ---
#add_logo()
#if not check_password():
#    st.stop()
#if not check_access("Rep_Target"):  # ඔබගේ page name එක මෙතන දාන්න
#    st.error("🚫 You do not have permission to view this page.")
#    st.stop()

st.title("Rep Target System")

# ---- Master Data Load කරන්න (Cached) ----
@st.cache_data
def get_master():
    data = load_master_data()
    return pd.DataFrame(data)


main_tab1, main_tab2, main_tab3 = st.tabs(["📝 Data Entry", "📄 Report", "📊 Dashboard"])

# ==========================================
# TAB 1 - DATA ENTRY
# ==========================================
with main_tab1:
    df_master = get_master()

    st.subheader("Update Rep Targets & Sales Day Book")
    st.caption("Manage representative targets and sales day book information from this page.")
    st.divider()

    de_tab1, de_tab2 = st.tabs([
        "1️⃣ Enter Target",
        "2️⃣ Upload Sales day"
    ])

    with de_tab1:

        col1, col2 = st.columns([1, 3])
        with col1:
            month = st.selectbox("Select Month", 
                                ["2026-Jan", "2026-Feb", "2026-Mar", "2026-Apr", 
                                "2026-May", "2026-Jun", "2026-Jul", "2026-Aug",
                                "2026-Sep", "2026-Oct", "2026-Nov", "2026-Dec",
                                "2027-Jan", "2027-Feb", "2027-Mar", "2027-Apr", 
                                "2027-May", "2027-Jun", "2027-Jul", "2027-Aug",
                                "2027-Sep", "2027-Oct", "2027-Nov", "2027-Dec"],
                                key="month_select")
        
        st.subheader(f"📍 Enter the target for {month}")
        
        # --- Load the exsisting data ---
        df_existing = load_targets_for_month(month)
        
        # --- Create a Data Frame---
        df_editable = df_master.copy()
        if "Target" not in df_editable.columns:
            df_editable["Target"] = ""
        
        if not df_existing.empty and "No" in df_existing.columns:
            df_editable = df_editable.merge(df_existing, on="No", how="left", suffixes=("", "_existing"))
            if "Target_existing" in df_editable.columns:
                df_editable["Target"] = df_editable["Target_existing"].fillna("")
                df_editable = df_editable.drop(columns=["Target_existing"])
        
        # Show the data editor
        column_config = {
            "No": st.column_config.TextColumn("No", disabled=True, width="small"),
            "Manager": st.column_config.TextColumn("Manager", disabled=True),
            "Route": st.column_config.TextColumn("Route", disabled=True),
            "Representative": st.column_config.TextColumn("Representative", disabled=True),
            "Status": st.column_config.TextColumn("Status", disabled=True, width="small"),
            "Target": st.column_config.TextColumn("🎯 Target", help="Enter Target here")
        }
        
        edited_df = st.data_editor(
            df_editable,
            column_config=column_config,
            use_container_width=True,
            hide_index=True,
            height=500
        )
        
        # --- Save Button ---
        if st.button("💾 Save this month Target", type="primary"):
            try:
                data_to_save = edited_df.to_dict('records')
                save_monthly_data(month, data_to_save)  #
                st.success(f"✅ Data successfully saved for {month}!")
                st.balloons()
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")



    with de_tab2:
        st.subheader("📤 Upload Sales Day Book")
        st.caption("Select the date this sales data belongs to, then upload the CSV file.")

        col1, col2 = st.columns([1, 3])
        with col1:
            selected_date = st.date_input("📅 Select Date", key="sales_day_date")
        selected_date_str = str(selected_date)

        ws_sales_day = get_sales_daybook_ws()

        # --- Show existing data for the selected date ---
        with st.spinner("Checking existing data for this date..."):
            existing_sales = get_rows_for_date(ws_sales_day, "new_date", selected_date_str)

        if not existing_sales.empty:
            st.warning(f"⚠️ Sales day book data already exists for **{selected_date_str}** ({len(existing_sales)} rows).")
            st.dataframe(existing_sales, use_container_width=True, height=400)

            if st.button("🗑️ Delete sales day book data for this date", key="delete_sales_btn"):
                st.session_state["confirm_delete_sales"] = True

            if st.session_state.get("confirm_delete_sales"):
                st.error(f"Permanently delete all {len(existing_sales)} rows for {selected_date_str}? This cannot be undone.")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Yes, delete it", key="confirm_delete_sales_yes", type="primary"):
                        with st.spinner("Deleting rows..."):
                            delete_rows_for_date(ws_sales_day, "new_date", selected_date_str)
                        st.session_state["confirm_delete_sales"] = False
                        st.success(f"🗑️ Sales day book data for {selected_date_str} deleted.")
                        time.sleep(1)
                        st.rerun()
                with c2:
                    if st.button("Cancel", key="confirm_delete_sales_no"):
                        st.session_state["confirm_delete_sales"] = False
                        st.rerun()
        else:
            st.info(f"No sales day book data found for {selected_date_str} yet.")

        st.divider()

        # --- Upload new data ---
        st.info("Upload a Sales Day Book CSV with columns: Date, Agent, Customer ID, Customer, Group, Invoice, Item, Qty, Amount, VAT")
        sales_file = st.file_uploader("Upload Sales Day Book CSV", type=["csv"], key="sales_day_upload")
        if sales_file is not None:
            try:
                df_sales = pd.read_csv(sales_file)
                st.write(f"Preview — {len(df_sales)} rows found:")
                st.dataframe(df_sales.head(10), use_container_width=True)

                if st.button("Add to Sales Day Book in Google Sheets", type="primary", key="sales_submit"):
                    with st.spinner("Appending sales day book data..."):
                        df_sales.insert(0, "new_date", selected_date_str)
                        df_sales = df_sales.fillna("")
                        sales_data_to_upload = df_sales.values.tolist()
                        ws_sales_day.append_rows(sales_data_to_upload)
                    st.success("✅ Sales day book data successfully added!")
                    time.sleep(1)
                    st.rerun()

            except Exception as e:
                st.error(f"Error processing sales day book file: {e}")

# ==========================================
# TAB 2 - REPORT 
# ==========================================
with main_tab2:
    st.markdown("Report")

# ==========================================
# TAB 3 - DASHBOARD
# ==========================================
with main_tab3:
    st.info("📊 Dashboard tab coming soon...")
    st.caption("Pick a date to see the full breakdown for every item, including weekly sales and buffer levels. ")




