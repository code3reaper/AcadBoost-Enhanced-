import streamlit as st
from database import get_user_by_credentials

def login(username, password, role):
    """Authenticate user and set session state"""
    user = get_user_by_credentials(username, password, role)
    
    if user:
        st.session_state.logged_in = True
        st.session_state.user_id = user['id']
        st.session_state.username = user['username']
        st.session_state.user_role = user['role']
        st.session_state.full_name = user['full_name']
        st.session_state.email = user['email']
        st.session_state.department = user['department']
        return True
    
    return False

def logout():
    """Clear session state and logout user"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.logged_in = False

def get_current_user():
    """Get current logged in user info"""
    if st.session_state.logged_in:
        return {
            'id': st.session_state.user_id,
            'username': st.session_state.username,
            'role': st.session_state.user_role,
            'full_name': st.session_state.full_name,
            'email': st.session_state.email,
            'department': st.session_state.department
        }
    return None

def require_role(allowed_roles):
    """Decorator to require specific roles"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not st.session_state.logged_in or st.session_state.user_role not in allowed_roles:
                st.error("🚫 Access denied. You don't have permission to access this page.")
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator
