import streamlit as st
import os
from database import init_database, create_sample_users
from auth import login, logout, get_current_user
from admin_module import admin_dashboard
from teacher_module import teacher_dashboard
from student_module import student_dashboard

# Set up environment variables
os.environ["GEMINI_API_KEY"] = "AIzaSyB_l1JJrCFXp6bkzGuvdlY7gzoFFe3DCdM"

# Page configuration
st.set_page_config(
    page_title="AcadBoost - Academic Management System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database and sample users
init_database()
create_sample_users()  # Ensure sample users always exist

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None

def main():
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #FF6B35 0%, #F7931E 100%);
        padding: 1rem;
        margin: -1rem -1rem 2rem -1rem;
        color: white;
        text-align: center;
        border-radius: 0 0 10px 10px;
    }
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background: #f8f9fa;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .credentials-info {
        background: linear-gradient(135deg, #e7f3ff 0%, #f0f8ff 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border: 2px solid #0066cc;
        box-shadow: 0 4px 8px rgba(0, 102, 204, 0.1);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(90deg, #FF6B35 0%, #F7931E 100%);
        color: white;
        border-radius: 8px;
        padding: 8px 16px;
    }
    .stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #FF6B35 0%, #F7931E 100%);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎓 AcadBoost</h1>
        <p>Comprehensive Academic Management System</p>
    </div>
    """, unsafe_allow_html=True)

    # Check if user is logged in
    if not st.session_state.logged_in:
        show_login_page()
    else:
        show_dashboard()

def show_login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        st.markdown("### 🔐 Login Portal")
        
        # Welcome message
        st.info("Welcome to AcadBoost! Use the sample credentials below to explore different user roles, or create your own account.")
        
        # Sample credentials in tabs
        st.markdown("#### 🔑 Sample Login Credentials")
        
        cred_tabs = st.tabs(["👨‍💼 Admin", "👨‍🏫 Teacher", "👨‍🎓 Student"])
        
        with cred_tabs[0]:
            st.info("**Admin Portal Access**")
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Username:** `admin`")
            with col2:
                st.write("**Password:** `admin123`")
        
        with cred_tabs[1]:
            st.info("**Teacher Portal Access**")
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Username:** `teacher1`")
                st.write("**Username:** `teacher2`")
            with col2:
                st.write("**Password:** `teacher123`")
                st.write("**Password:** `teacher123`")
        
        with cred_tabs[2]:
            st.info("**Student Portal Access**")
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Username:** `student1`")
                st.write("**Username:** `student2`")
                st.write("**Username:** `student3`")
            with col2:
                st.write("**Password:** `student123`")
                st.write("**Password:** `student123`")
                st.write("**Password:** `student123`")
        
        st.markdown("---")
        
        # Login form
        with st.form("login_form"):
            username = st.text_input("👤 Username")
            password = st.text_input("🔒 Password", type="password")
            role = st.selectbox("🎭 Select Role", ["Admin", "Teacher", "Student"])
            
            login_button = st.form_submit_button("🚀 Login")
            
            if login_button:
                if username and password:
                    if login(username, password, role.lower()):
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials. Please check username, password, and role.")
                else:
                    st.error("⚠️ Please fill in all fields.")
        
        # Quick login buttons
        st.markdown("#### ⚡ Quick Login")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚀 Login as Admin", use_container_width=True):
                if login("admin", "admin123", "admin"):
                    st.rerun()
        
        with col2:
            if st.button("🚀 Login as Teacher", use_container_width=True):
                if login("teacher1", "teacher123", "teacher"):
                    st.rerun()
        
        with col3:
            if st.button("🚀 Login as Student", use_container_width=True):
                if login("student1", "student123", "student"):
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

def show_dashboard():
    # Sidebar with user info and logout
    with st.sidebar:
        st.markdown("### 👋 Welcome!")
        st.write(f"**User:** {st.session_state.username}")
        st.write(f"**Role:** {st.session_state.user_role.title()}")
        
        if st.button("🚪 Logout"):
            logout()
            st.rerun()
        
        st.markdown("---")
    
    # Show appropriate dashboard based on role
    if st.session_state.user_role == 'admin':
        admin_dashboard()
    elif st.session_state.user_role == 'teacher':
        teacher_dashboard()
    elif st.session_state.user_role == 'student':
        student_dashboard()

if __name__ == "__main__":
    main()
