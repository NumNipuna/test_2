import streamlit as st
import pandas as pd
from gspread_dataframe import set_with_dataframe
from utils import connect_to_sheets, fetch_database_records

# ---> CRITICAL: Make sure 'check_password' is added to this line! <---
from utils import connect_to_sheets, fetch_database_records, check_password

st.set_page_config(page_title=" Cash Collection & Cash Deposit", layout="wide")

if not check_password():
    st.stop()

st.title("💰 Cash Collection & Cash Deposit")

# Load data using our helper file
try:
    main_records, reps_records, banks_records = fetch_database_records()
    sh = connect_to_sheets()
    ws_main = sh.worksheet("Data_Entry")
except Exception as e:
    st.error(f"Error connecting to Google Sheets: {e}")
    st.stop()

tab1, tab2, tab3 = st.tabs(["Data Entry", "Daily Cash Collection", "Settings"])

with tab1:
    st.header("Enter Transactions")
    
    df_main = pd.DataFrame(main_records) if main_records else pd.DataFrame(columns=["Sales Rep", "Date", "Total Cash Collection", "Cash Deposit", "Cash Deposit Date", "Bank", "Cash In Hand", "Balance"])
    df_reps = pd.DataFrame(reps_records) if reps_records else pd.DataFrame(columns=["Rep Name"])
    df_banks = pd.DataFrame(banks_records) if banks_records else pd.DataFrame(columns=["Bank Name"])

    rep_list = []
    if "Rep Name" in df_reps.columns:
        rep_list = df_reps["Rep Name"].dropna().tolist()
    elif "Rep_Name" in df_reps.columns: 
        rep_list = df_reps["Rep_Name"].dropna().tolist()

    bank_list = []
    if "Bank Name" in df_banks.columns:
        bank_list = df_banks["Bank Name"].dropna().astype(str).tolist()
        
    selected_rep = st.selectbox("Select a Sales Rep:", [""] + rep_list)
    
    if selected_rep != "":
        st.subheader(f"Ledger for: {selected_rep}")
        
        if not df_main.empty and "Sales Rep" in df_main.columns:
            rep_data = df_main[df_main["Sales Rep"] == selected_rep].copy()
        else:
            rep_data = pd.DataFrame(columns=["Sales Rep", "Date", "Total Cash Collection", "Cash Deposit", "Cash Deposit Date", "Bank", "Cash In Hand", "Balance"])
            
        if "Date" in rep_data.columns:
            rep_data["Date"] = pd.to_datetime(rep_data["Date"], errors="coerce")
        if "Cash Deposit Date" in rep_data.columns:
            rep_data["Cash Deposit Date"] = pd.to_datetime(rep_data["Cash Deposit Date"], errors="coerce")
            
        edited_data = st.data_editor(
            rep_data,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            column_config={
                "Sales Rep": st.column_config.TextColumn("Sales Rep", disabled=True),
                "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                "Total Cash Collection": st.column_config.NumberColumn("Total Cash Collection", format="%.2f"),
                "Cash Deposit": st.column_config.NumberColumn("Cash Deposit", format="%.2f"),
                "Cash Deposit Date": st.column_config.DateColumn("Cash Deposit Date", format="YYYY-MM-DD"),
                "Bank": st.column_config.SelectboxColumn("Bank", options=bank_list),
                "Cash In Hand": st.column_config.NumberColumn("Cash In Hand", format="%.2f"),
                "Balance": st.column_config.NumberColumn("Balance", format="%.2f", disabled=True)
            }
        )
        
        if st.button("Save Changes to Database", type="primary"):
            with st.spinner("Saving to Google Sheets..."):
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
                set_with_dataframe(ws_main, final_df)
                fetch_database_records.clear()
                st.success("Data successfully saved!")
                st.rerun()

with tab2:
    st.header("Daily Cash Collection")
    selected_date = st.date_input("Select Date for Report")
    
    df_display = df_main.copy()
    if not df_display.empty and "Date" in df_display.columns:
        df_display['Date'] = pd.to_datetime(df_display['Date'], errors='coerce')
        daily_report = df_display[df_display['Date'].dt.date == selected_date].copy()
        
        if not daily_report.empty:
            col1, col2 = st.columns(2)
            col1.metric("Total Collection", f"{daily_report['Total Cash Collection'].sum():,.2f}")
            col2.metric("Total Deposits", f"{daily_report['Cash Deposit'].sum():,.2f}")
            
            display_df = daily_report.copy()
            display_df['Bank'] = display_df['Bank'].astype(str).str[:3]
            display_df['Sales Rep'] = display_df['Sales Rep'].mask(display_df['Sales Rep'].duplicated(), '')
            display_df['Total Cash Collection'] = display_df['Total Cash Collection'].replace(0, None)
            
            st.subheader("Detailed Transactions")
            st.dataframe(
                display_df[['Sales Rep', 'Total Cash Collection', 'Cash Deposit', 'Cash Deposit Date', 'Bank']], 
                use_container_width=True, hide_index=True
            )
        else:
            st.info(f"No transactions recorded for {selected_date}.")
    else:
        st.info("No data available yet.")

with tab3:
    st.write("Settings and Sales Rep management will go here.")