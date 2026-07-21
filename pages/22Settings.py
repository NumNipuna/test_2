import streamlit as st
import pandas as pd
from utils import connect_to_sheets, fetch_database_records, add_logo,check_password, check_access # Import the functions
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from utils import get_client
client = get_client()

st.set_page_config(page_title="Settings", layout="wide")
st.title("⚙️ Settings")

add_logo()

#-------------------------------------------------------------------

# Require login
#if not check_password():
#    st.stop()

# Check access specifically for THIS page
#if not check_access("Report_2"):
#    st.error("🚫 You do not have permission to view this page.")
#    st.stop()

#st.title("Report 2")
#st.write("Only user2 and master_admin can see this.")

#-------------------------------------------------------------------------

st.markdown("""
    <style>
        div[data-testid="stTextInput"],
        div[data-testid="stSelectbox"],
        div[data-testid="stButton"],
        div[data-testid="stForm"] {
            max-width: 600px;
        }
            

        .admin-card{
            border:1px solid rgba(250,250,250,.15);
            border-radius:10px;
            padding:20px;
            margin-bottom:20px;
            }
            
        /* 2. Header and core element block wrappers color or (transparent is better) */
        [data-testid="stHeader"], [data-testid="stVerticalBlock"] {
            background-color: transparent !important;
        }
            
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(to right,#0d1321, #748cab);
        }
        
        /* Your animations can live here safely */
        @keyframes fadeInUp {
            from { transform: translateY(30px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        [data-testid="stMainBlockContainer"] > div {
            animation: fadeInUp 0.8s ease-out forwards;
        }
            

        /* 5. Custom Isolated Metric Card UI styling */
        .metric-card {
            background-color: #ccdbdc !important;                           /* Change KPI Card color here */
            padding: 10px;                                                  /* Change height of KPI card */                              
            border-radius: 12px;                                            /* Change border radius */
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;           /* Modern, soft UI shadow */
            border-left: 20px solid;                                        /*color currently this is over write from belowe html code */
            text-align: center;
            max-width: 600px;                /* if we add KPI cards in raw wise, these line */
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
            
/* Customize space between title and top ----------------------------------------------------------*/
        
        [data-testid="stAppViewContainer"] .block-container {
            padding-top: 4.5rem !important;       /* Default is close to 6rem; 1rem = 16px */
            padding-bottom: 1.5rem !important;    /* Space in bottom (last plot and bottom)
/*-------------------------------------------------------------------------------------------------*/
            
</style>
""", unsafe_allow_html=True)

# 1. CACHE THE GOOGLE CONNECTION
# @st.cache_resource ensures we only authenticate once per session, speeding up load times significantly.
@st.cache_resource
def get_google_client():
    from utils import get_client
    return get_client()

client = get_google_client()

# Define the sheet objects
sheet_reps = client.open("Sales data").worksheet("Sales_Reps")
sheet_banks = client.open("Sales data").worksheet("Banks")

# 2. CACHE THE DATA
# @st.cache_data stores the dataframe so it doesn't re-download on every click.
@st.cache_data
def get_reps_data():
    return pd.DataFrame(sheet_reps.get_all_records())

@st.cache_data
def get_banks_data():
    return pd.DataFrame(sheet_banks.get_all_records())


# Create tabs
tab1, tab2, tab3 = st.tabs(["Cash Collection & Deposit", "Rep Target","tab 3"])

with tab1:

    df_reps = get_reps_data()
    df_banks = get_banks_data()

    kpi_col1, kpi_col2 = st.columns(2)

    with kpi_col1:
        # len(df_reps) counts the number of rows (reps) in your dataframe
        st.markdown(f'<div class="metric-card" style="border-left-color:#048ba8;"><div class="metric-value">{len(df_reps):,.0f}</div><div class="metric-label">Total Sales Reps</div></div>', unsafe_allow_html=True)
        
    with kpi_col2:
        st.markdown(f'<div class="metric-card" style="border-left-color:#048ba8;"><div class="metric-value">{len(df_banks):,.0f}</div><div class="metric-label">Total Banks</div></div>', unsafe_allow_html=True)

    st.divider() # Draws a nice horizontal line to separate KPIs from the tables


    col1, col2 = st.columns(2)
    # --- SALES REPS COLUMN ---
    with col1:
        st.subheader("Manage Active Sales Representatives")

        # Fetch cached data
        df_reps = get_reps_data()
        st.dataframe(df_reps, width=600, height=350, hide_index=True)
            
        # --- ADD NEW REP ---
        st.markdown("**➕ Add New Sales Rep**")
        with st.form("add_rep_form", clear_on_submit=True):
            new_rep = st.text_input("Enter Sales Rep Name:")
            add_submit = st.form_submit_button("Add Rep")

            if add_submit and new_rep:
                sheet_reps.append_row([new_rep])
                st.success(f"Added {new_rep} successfully!")
                get_reps_data.clear() # Clear the cache so the new rep shows up
                st.rerun() 

        # --- DELETE EXISTING REP ---
        st.markdown("**❌ Delete Sales Rep**")
        if not df_reps.empty:
            rep_col_name = df_reps.columns[0] 
            
            # 3. WRAP DELETE IN A FORM
            # This prevents the app from refreshing when you click the dropdown
            with st.form("delete_rep_form"):
                rep_to_delete = st.selectbox("Select Rep to Delete:", df_reps[rep_col_name].tolist())
                delete_submit = st.form_submit_button("Delete Rep")

                if delete_submit and rep_to_delete:
                    cell = sheet_reps.find(rep_to_delete)
                    if cell:
                        sheet_reps.delete_rows(cell.row)
                        st.success(f"Deleted {rep_to_delete} successfully!")
                        get_reps_data.clear() # Clear the cache so the deleted rep is removed
                        st.rerun() 
        else:
            st.info("No sales reps found in the sheet.")

    # --- BANKS COLUMN ---
    with col2:
        st.subheader("Manage your list of Banks")

        # Fetch cached data
        df_banks = get_banks_data()
        st.dataframe(df_banks, width=600, height=350, hide_index=True)

        # --- ADD NEW BANK ---
        st.markdown("**➕ Add New Bank**")
        with st.form("add_bank_form", clear_on_submit=True):
            new_bank = st.text_input("Enter Bank Name:")
            add_submit = st.form_submit_button("Add Bank")

            if add_submit and new_bank:
                sheet_banks.append_row([new_bank])
                st.success(f"Added {new_bank} successfully!")
                get_banks_data.clear() # Clear cache
                st.rerun()

        # --- DELETE EXISTING BANK ---
        st.markdown("**❌ Delete Bank**")
        if not df_banks.empty:
            bank_col_name = df_banks.columns[0] 

            # Wrap delete in a form just like the reps
            with st.form("delete_bank_form"):
                bank_to_delete = st.selectbox("Select Bank to Delete:", df_banks[bank_col_name].tolist())
                delete_submit = st.form_submit_button("Delete Bank")

                if delete_submit and bank_to_delete:
                    cell = sheet_banks.find(bank_to_delete)
                    if cell:
                        sheet_banks.delete_rows(cell.row)
                        st.success(f"Deleted {bank_to_delete} successfully!")
                        get_banks_data.clear() # Clear cache
                        st.rerun() 
        else:
            st.info("No banks found in the sheet.")


###############################################################################################################
import streamlit as st
import pandas as pd
from utils import update_master_data

@st.cache_data
def get_master():
    data = load_master_data()
    return pd.DataFrame(data)


with tab2:
    st.warning("⚠️ The changes made here will be permanently applied to the Master List. (They will not affect the targets of months that have already been saved.)")
    
    # Settings වලදී මුලු Dataframe එකම Edit කරන්න දෙමු (Rows එකතු කිරීමට/මැකීමටත් ඉඩ දෙන්න)
    df_settings = get_master().copy()  # Cache එකෙන් ගමු
    
    edited_settings = st.data_editor(
        df_settings,
        use_container_width=True,
        height=400,
        num_rows="dynamic"  # මෙය rows එකතු කිරීමට/මැකීමට ඉඩ දෙයි
    )
    
    if st.button("💾 Master Data Update කරන්න", type="primary"):
        try:
            update_master_data(edited_settings)
            # Cache එක Clear කරන්න (ඊළඟ වතාවේ අලුත් Data එනවා)
            st.cache_data.clear()
            st.success("✅ Master Data සාර්ථකව යාවත්කාලීන කරන ලදී!")
            st.rerun()  # පිටුව Refresh කරන්න
        except Exception as e:
            st.error(f"❌ දෝෂයක්: {e}")