import streamlit as st
import pandas as pd
import os
import logging

# --- CONFIGURATION ---
st.set_page_config(page_title="Student Management System", page_icon="🎓", layout="wide")

EXCEL_FILE = 'danh_sach_sv.xlsx'
LOG_FILE = 'app.log'

# --- LOGGING SETUP ---
def get_logger():
    logger = logging.getLogger('student_management')
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger

logger = get_logger()

def add_log(message):
    logger.info(message)

# --- DATA HANDLING ---
COLUMNS = ['Student ID', 'Full Name', 'Class', 'Email']

def load_data():
    if not os.path.exists(EXCEL_FILE):
        df = pd.DataFrame(columns=COLUMNS)
        df.to_excel(EXCEL_FILE, index=False, engine='openpyxl')
        return df
    try:
        df = pd.read_excel(EXCEL_FILE, engine='openpyxl', dtype={'Student ID': str})
        # If columns don't match, re-align
        if list(df.columns) != COLUMNS:
            df = df.reindex(columns=COLUMNS)
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(columns=COLUMNS)

def save_data(df):
    df.to_excel(EXCEL_FILE, index=False, engine='openpyxl')

# Load data into session state
if 'df' not in st.session_state:
    st.session_state.df = load_data()

df = st.session_state.df

# --- UI STYLE ---
st.markdown("""
<style>
    .main-title {
        color: #1E88E5;
        text-align: center;
        font-weight: 700;
        margin-bottom: 20px;
    }
    div.stButton > button:first-child {
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">🎓 Student Management System</h1>', unsafe_allow_html=True)

# --- TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 View Students", 
    "➕ Add Student", 
    "✏️ Edit / 🗑️ Delete", 
    "📂 Import / Export", 
    "📜 Activity Logs"
])

with tab1:
    st.subheader("Student Directory")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Students", len(df))
    col2.metric("Total Classes", df['Class'].nunique() if not df.empty else 0)
    
    search_query = st.text_input("🔍 Search by Name or ID:")
    if search_query:
        filtered_df = df[df['Full Name'].astype(str).str.contains(search_query, case=False, na=False) | 
                         df['Student ID'].astype(str).str.contains(search_query, case=False, na=False)]
    else:
        filtered_df = df
        
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
    
    if st.button("🔄 Refresh Data"):
        st.session_state.df = load_data()
        st.rerun()

with tab2:
    st.subheader("Add New Student")
    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            new_id = st.text_input("Student ID*")
            new_name = st.text_input("Full Name*")
        with col2:
            new_class = st.text_input("Class")
            new_email = st.text_input("Email")
            
        submitted = st.form_submit_button("✅ Add Student", use_container_width=True)
        if submitted:
            if not new_id or not new_name:
                st.error("Student ID and Full Name are required!")
            elif new_id in df['Student ID'].astype(str).values:
                st.error("Student ID already exists!")
            else:
                new_student = pd.DataFrame([{
                    'Student ID': new_id, 
                    'Full Name': new_name, 
                    'Class': new_class, 
                    'Email': new_email
                }])
                df = pd.concat([df, new_student], ignore_index=True)
                save_data(df)
                st.session_state.df = df
                add_log(f"Added student: {new_name} (ID: {new_id})")
                st.success(f"Student {new_name} added successfully!")
                st.rerun()

with tab3:
    st.subheader("Edit or Delete Student")
    if df.empty:
        st.info("No students available to edit or delete.")
    else:
        student_ids = df['Student ID'].astype(str).tolist()
        selected_id = st.selectbox("Select Student by ID to Edit/Delete", options=[""] + student_ids)
        
        if selected_id:
            student_data = df[df['Student ID'].astype(str) == selected_id].iloc[0]
            
            st.markdown("---")
            st.markdown("### ✏️ Edit Student")
            with st.form("edit_form"):
                e_name = st.text_input("Full Name*", value=str(student_data['Full Name']))
                e_class = st.text_input("Class", value=str(student_data['Class']) if pd.notna(student_data['Class']) else "")
                e_email = st.text_input("Email", value=str(student_data['Email']) if pd.notna(student_data['Email']) else "")
                
                update_btn = st.form_submit_button("💾 Update Student", use_container_width=True)
                if update_btn:
                    if not e_name:
                        st.error("Full Name is required!")
                    else:
                        idx = df.index[df['Student ID'].astype(str) == selected_id][0]
                        df.at[idx, 'Full Name'] = e_name
                        df.at[idx, 'Class'] = e_class
                        df.at[idx, 'Email'] = e_email
                        save_data(df)
                        st.session_state.df = df
                        add_log(f"Edited student: {e_name} (ID: {selected_id})")
                        st.success("Student updated successfully!")
                        st.rerun()
            
            st.markdown("---")
            st.markdown("### 🗑️ Delete Student")
            with st.form("delete_form"):
                st.warning(f"Are you sure you want to delete student: **{student_data['Full Name']}**?")
                delete_btn = st.form_submit_button("🚨 Confirm Delete", use_container_width=True)
                if delete_btn:
                    student_name = student_data['Full Name']
                    df = df[df['Student ID'].astype(str) != selected_id].reset_index(drop=True)
                    save_data(df)
                    st.session_state.df = df
                    add_log(f"Deleted student: {student_name} (ID: {selected_id})")
                    st.success("Student deleted successfully!")
                    st.rerun()

with tab4:
    st.subheader("Import & Export Data")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📤 Export Data")
        st.write("Download the current student list as an Excel file.")
        
        if os.path.exists(EXCEL_FILE):
            with open(EXCEL_FILE, "rb") as file:
                st.download_button(
                    label="📥 Download Excel File",
                    data=file,
                    file_name="danh_sach_sv.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        else:
            st.warning("No data file available to download.")

    with col2:
        st.markdown("#### 📥 Import Data")
        st.write("Upload an Excel file to update system data. Note: The file must have the same columns.")
        uploaded_file = st.file_uploader("Upload Excel file (.xlsx)", type=['xlsx'])
        if uploaded_file is not None:
            if st.button("🔄 Sync with Uploaded Data", use_container_width=True):
                try:
                    new_df = pd.read_excel(uploaded_file, engine='openpyxl', dtype={'Student ID': str})
                    if list(new_df.columns) == COLUMNS:
                        save_data(new_df)
                        st.session_state.df = new_df
                        add_log("Imported data from external Excel file")
                        st.success("Data imported successfully!")
                        st.rerun()
                    else:
                        st.error(f"Invalid columns. Expected exactly: {', '.join(COLUMNS)}")
                except Exception as e:
                    st.error(f"Error importing file: {e}")

with tab5:
    st.subheader("📜 Activity Logs")
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            logs = f.readlines()
        
        if logs:
            st.markdown(f"**Total entries: {len(logs)}**")
            log_text = "".join(logs[::-1]) # Show newest first
            st.text_area("Logs (Newest First)", log_text, height=300, disabled=True)
            
            if st.button("🗑️ Clear Logs"):
                open(LOG_FILE, 'w').close()
                st.success("Logs cleared!")
                st.rerun()
        else:
            st.info("No activity logs yet.")
    else:
        st.info("No activity logs exist.")
