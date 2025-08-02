import streamlit as st
import pandas as pd
import plotly.express as px
from database import get_db_connection
from utils import create_performance_chart, get_dashboard_stats, show_notifications_sidebar, create_notification
from ai_analytics import analyze_department_performance, predict_student_outcomes
from datetime import datetime, date
import hashlib

def admin_dashboard():
    """Admin dashboard with full functionality"""
    st.title("🏛️ Admin Dashboard")
    
    # Show notifications
    show_notifications_sidebar()
    
    # Navigation tabs
    tabs = st.tabs([
        "📊 Overview", 
        "👥 User Management", 
        "🏢 Department Management", 
        "📢 Announcements", 
        "📈 Reports & Analytics",
        "🎓 Certificate Management"
    ])
    
    with tabs[0]:
        show_admin_overview()
    
    with tabs[1]:
        show_user_management()
    
    with tabs[2]:
        show_department_management()
    
    with tabs[3]:
        show_announcements_management()
    
    with tabs[4]:
        show_reports_analytics()
    
    with tabs[5]:
        show_certificate_management()

def show_admin_overview():
    """Show admin overview dashboard"""
    st.header("📊 System Overview")
    
    # Get dashboard stats
    stats = get_dashboard_stats('admin', st.session_state.user_id)
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👨‍🎓 Total Students", stats['total_students'])
        st.metric("📚 Active Assignments", stats['active_assignments'])
    
    with col2:
        st.metric("👨‍🏫 Total Teachers", stats['total_teachers'])
        st.metric("🔬 Active Projects", stats['active_projects'])
    
    with col3:
        st.metric("🏢 Departments", stats['total_departments'])
    
    with col4:
        st.metric("📖 Subjects", stats['total_subjects'])
    
    st.markdown("---")
    
    # Recent activities
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Department Performance")
        conn = get_db_connection()
        
        query = '''
            SELECT 
                d.name as department,
                COUNT(DISTINCT u.id) as student_count,
                AVG(r.total_marks) as avg_marks,
                AVG(r.attendance_percentage) as avg_attendance
            FROM departments d
            LEFT JOIN users u ON d.name = u.department AND u.role = 'student'
            LEFT JOIN results r ON u.id = r.student_id
            GROUP BY d.id
            ORDER BY avg_marks DESC
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            fig = px.bar(df, x='department', y='avg_marks', 
                        title='Average Marks by Department',
                        color='avg_marks',
                        color_continuous_scale='viridis')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No performance data available")
    
    with col2:
        st.subheader("👥 User Distribution")
        conn = get_db_connection()
        
        query = '''
            SELECT role, COUNT(*) as count
            FROM users
            WHERE is_active = 1
            GROUP BY role
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            fig = px.pie(df, values='count', names='role', 
                        title='Active Users by Role')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No user data available")

def show_user_management():
    """User management interface"""
    st.header("👥 User Management")
    
    # Sub-tabs for user management
    user_tabs = st.tabs(["👤 View Users", "➕ Add User", "✏️ Edit User"])
    
    with user_tabs[0]:
        show_users_list()
    
    with user_tabs[1]:
        add_new_user()
    
    with user_tabs[2]:
        edit_user()

def show_users_list():
    """Display list of all users"""
    st.subheader("📋 All Users")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        role_filter = st.selectbox("Filter by Role", ["All", "Admin", "Teacher", "Student"])
    
    with col2:
        department_filter = st.selectbox("Filter by Department", ["All"] + get_all_departments())
    
    with col3:
        status_filter = st.selectbox("Filter by Status", ["All", "Active", "Inactive"])
    
    # Build query based on filters
    conn = get_db_connection()
    query = "SELECT * FROM users WHERE 1=1"
    params = []
    
    if role_filter != "All":
        query += " AND role = ?"
        params.append(role_filter.lower())
    
    if department_filter != "All":
        query += " AND department = ?"
        params.append(department_filter)
    
    if status_filter != "All":
        query += " AND is_active = ?"
        params.append(1 if status_filter == "Active" else 0)
    
    query += " ORDER BY created_at DESC"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    if not df.empty:
        # Display user table
        st.dataframe(
            df[['id', 'username', 'full_name', 'role', 'email', 'department', 'is_active']],
            use_container_width=True
        )
        
        # Export functionality
        if st.button("📥 Export Users to CSV"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.info("No users found matching the criteria")

def add_new_user():
    """Add new user form"""
    st.subheader("➕ Add New User")
    
    with st.form("add_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Username*")
            full_name = st.text_input("Full Name*")
            role = st.selectbox("Role*", ["student", "teacher", "admin"])
        
        with col2:
            email = st.text_input("Email")
            department = st.selectbox("Department", get_all_departments())
            password = st.text_input("Password*", type="password")
        
        submit_button = st.form_submit_button("👤 Create User")
        
        if submit_button:
            if username and full_name and role and password:
                if create_user(username, password, role, full_name, email, department):
                    st.success("✅ User created successfully!")
                    
                    # Send notification to new user
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                    new_user = cursor.fetchone()
                    if new_user:
                        create_notification(
                            new_user[0],
                            "Welcome to AcadBoost!",
                            f"Your account has been created. Role: {role.title()}",
                            "info"
                        )
                    conn.close()
                else:
                    st.error("❌ Failed to create user. Username might already exist.")
            else:
                st.error("⚠️ Please fill in all required fields marked with *")

def edit_user():
    """Edit existing user"""
    st.subheader("✏️ Edit User")
    
    # Select user to edit
    conn = get_db_connection()
    query = "SELECT id, username, full_name FROM users ORDER BY full_name"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df.empty:
        user_options = {f"{row['full_name']} ({row['username']})": row['id'] for _, row in df.iterrows()}
        selected_user = st.selectbox("Select User to Edit", list(user_options.keys()))
        
        if selected_user:
            user_id = user_options[selected_user]
            
            # Get user details
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            conn.close()
            
            if user:
                with st.form("edit_user_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_username = st.text_input("Username", value=user['username'])
                        new_full_name = st.text_input("Full Name", value=user['full_name'])
                        new_role = st.selectbox("Role", ["student", "teacher", "admin"], 
                                              index=["student", "teacher", "admin"].index(user['role']))
                    
                    with col2:
                        new_email = st.text_input("Email", value=user['email'] or "")
                        new_department = st.selectbox("Department", get_all_departments(),
                                                    index=get_all_departments().index(user['department']) if user['department'] in get_all_departments() else 0)
                        new_password = st.text_input("New Password (leave blank to keep current)", type="password")
                    
                    is_active = st.checkbox("Active", value=bool(user['is_active']))
                    
                    update_button = st.form_submit_button("💾 Update User")
                    
                    if update_button:
                        if update_user(user_id, new_username, new_full_name, new_role, 
                                     new_email, new_department, new_password, is_active):
                            st.success("✅ User updated successfully!")
                            
                            # Send notification
                            create_notification(
                                user_id,
                                "Account Updated",
                                "Your account information has been updated by an administrator.",
                                "info"
                            )
                        else:
                            st.error("❌ Failed to update user.")
    else:
        st.info("No users available to edit")

def show_department_management():
    """Department management interface"""
    st.header("🏢 Department Management")
    
    dept_tabs = st.tabs(["📋 View Departments", "➕ Add Department", "📚 Manage Subjects"])
    
    with dept_tabs[0]:
        show_departments_list()
    
    with dept_tabs[1]:
        add_new_department()
    
    with dept_tabs[2]:
        manage_subjects()

def show_departments_list():
    """Show all departments"""
    st.subheader("📋 All Departments")
    
    conn = get_db_connection()
    query = '''
        SELECT 
            d.id,
            d.name,
            d.code,
            u.full_name as head_name,
            COUNT(DISTINCT s.id) as subject_count,
            COUNT(DISTINCT st.id) as student_count,
            COUNT(DISTINCT t.id) as teacher_count
        FROM departments d
        LEFT JOIN users u ON d.head_id = u.id
        LEFT JOIN subjects s ON d.id = s.department_id
        LEFT JOIN users st ON d.name = st.department AND st.role = 'student'
        LEFT JOIN users t ON d.name = t.department AND t.role = 'teacher'
        GROUP BY d.id
        ORDER BY d.name
    '''
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No departments found")

def add_new_department():
    """Add new department"""
    st.subheader("➕ Add New Department")
    
    with st.form("add_department_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            dept_name = st.text_input("Department Name*")
            dept_code = st.text_input("Department Code*")
        
        with col2:
            # Get available teachers for head selection
            conn = get_db_connection()
            teachers_query = "SELECT id, full_name FROM users WHERE role = 'teacher'"
            teachers_df = pd.read_sql_query(teachers_query, conn)
            conn.close()
            
            if not teachers_df.empty:
                teacher_options = {"None": None}
                teacher_options.update({row['full_name']: row['id'] for _, row in teachers_df.iterrows()})
                selected_head = st.selectbox("Department Head", list(teacher_options.keys()))
                head_id = teacher_options[selected_head]
            else:
                st.info("No teachers available to assign as department head")
                head_id = None
        
        submit_button = st.form_submit_button("🏢 Create Department")
        
        if submit_button:
            if dept_name and dept_code:
                if create_department(dept_name, dept_code, head_id):
                    st.success("✅ Department created successfully!")
                else:
                    st.error("❌ Failed to create department. Department code might already exist.")
            else:
                st.error("⚠️ Please fill in all required fields marked with *")

def manage_subjects():
    """Manage subjects"""
    st.subheader("📚 Subject Management")
    
    subject_tabs = st.tabs(["📋 View Subjects", "➕ Add Subject"])
    
    with subject_tabs[0]:
        # Show all subjects
        conn = get_db_connection()
        query = '''
            SELECT 
                s.id,
                s.name,
                s.code,
                d.name as department,
                u.full_name as teacher,
                s.credits,
                s.semester,
                COUNT(e.student_id) as enrolled_students
            FROM subjects s
            LEFT JOIN departments d ON s.department_id = d.id
            LEFT JOIN users u ON s.teacher_id = u.id
            LEFT JOIN enrollments e ON s.id = e.subject_id
            GROUP BY s.id
            ORDER BY d.name, s.name
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No subjects found")
    
    with subject_tabs[1]:
        # Add new subject
        with st.form("add_subject_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                subject_name = st.text_input("Subject Name*")
                subject_code = st.text_input("Subject Code*")
                credits = st.number_input("Credits", min_value=1, max_value=6, value=3)
            
            with col2:
                # Get departments
                departments = get_all_departments()
                selected_dept = st.selectbox("Department*", departments)
                
                # Get teachers
                conn = get_db_connection()
                teachers_query = "SELECT id, full_name FROM users WHERE role = 'teacher'"
                teachers_df = pd.read_sql_query(teachers_query, conn)
                conn.close()
                
                if not teachers_df.empty:
                    teacher_options = {"None": None}
                    teacher_options.update({row['full_name']: row['id'] for _, row in teachers_df.iterrows()})
                    selected_teacher = st.selectbox("Teacher", list(teacher_options.keys()))
                    teacher_id = teacher_options[selected_teacher]
                else:
                    teacher_id = None
                
                semester = st.number_input("Semester", min_value=1, max_value=8, value=1)
            
            submit_button = st.form_submit_button("📚 Create Subject")
            
            if submit_button:
                if subject_name and subject_code and selected_dept:
                    if create_subject(subject_name, subject_code, selected_dept, teacher_id, credits, semester):
                        st.success("✅ Subject created successfully!")
                    else:
                        st.error("❌ Failed to create subject. Subject code might already exist.")
                else:
                    st.error("⚠️ Please fill in all required fields marked with *")

def show_announcements_management():
    """Manage announcements"""
    st.header("📢 Announcements Management")
    
    ann_tabs = st.tabs(["📋 View Announcements", "➕ Create Announcement"])
    
    with ann_tabs[0]:
        show_announcements_list()
    
    with ann_tabs[1]:
        create_announcement()

def show_announcements_list():
    """Show all announcements"""
    st.subheader("📋 All Announcements")
    
    conn = get_db_connection()
    query = '''
        SELECT 
            a.id,
            a.title,
            a.content,
            u.full_name as posted_by,
            a.target_role,
            d.name as department,
            a.is_active,
            a.created_at
        FROM announcements a
        LEFT JOIN users u ON a.posted_by = u.id
        LEFT JOIN departments d ON a.department_id = d.id
        ORDER BY a.created_at DESC
    '''
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df.empty:
        for _, row in df.iterrows():
            with st.expander(f"📢 {row['title']} - {row['target_role'].title() if row['target_role'] else 'All'}"):
                st.write(f"**Content:** {row['content']}")
                st.write(f"**Posted by:** {row['posted_by']}")
                st.write(f"**Department:** {row['department'] if row['department'] else 'All Departments'}")
                st.write(f"**Status:** {'Active' if row['is_active'] else 'Inactive'}")
                st.write(f"**Created:** {row['created_at']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"{'Deactivate' if row['is_active'] else 'Activate'}", key=f"toggle_{row['id']}"):
                        toggle_announcement_status(row['id'], not row['is_active'])
                        st.rerun()
                
                with col2:
                    if st.button("🗑️ Delete", key=f"delete_{row['id']}"):
                        delete_announcement(row['id'])
                        st.rerun()
    else:
        st.info("No announcements found")

def create_announcement():
    """Create new announcement"""
    st.subheader("➕ Create New Announcement")
    
    with st.form("create_announcement_form"):
        title = st.text_input("Announcement Title*")
        content = st.text_area("Content*", height=150)
        
        col1, col2 = st.columns(2)
        
        with col1:
            target_role = st.selectbox("Target Audience", ["all", "student", "teacher", "admin"])
        
        with col2:
            departments = ["All Departments"] + get_all_departments()
            selected_dept = st.selectbox("Target Department", departments)
        
        submit_button = st.form_submit_button("📢 Create Announcement")
        
        if submit_button:
            if title and content:
                dept_id = None
                if selected_dept != "All Departments":
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM departments WHERE name = ?", (selected_dept,))
                    dept_result = cursor.fetchone()
                    if dept_result:
                        dept_id = dept_result[0]
                    conn.close()
                
                if create_announcement_record(title, content, st.session_state.user_id, 
                                            target_role if target_role != "all" else None, dept_id):
                    st.success("✅ Announcement created successfully!")
                    
                    # Send notifications to target users
                    send_announcement_notifications(title, content, target_role, dept_id)
                else:
                    st.error("❌ Failed to create announcement.")
            else:
                st.error("⚠️ Please fill in all required fields marked with *")

def show_reports_analytics():
    """Show reports and analytics"""
    st.header("📈 Reports & Analytics")
    
    report_tabs = st.tabs(["📊 Performance Analytics", "🎯 AI Insights", "📋 System Reports"])
    
    with report_tabs[0]:
        show_performance_analytics()
    
    with report_tabs[1]:
        show_ai_insights()
    
    with report_tabs[2]:
        show_system_reports()

def show_performance_analytics():
    """Show performance analytics"""
    st.subheader("📊 Performance Analytics")
    
    # Overall performance metrics
    conn = get_db_connection()
    
    # Department performance comparison
    st.write("### Department Performance Comparison")
    dept_query = '''
        SELECT 
            d.name as department,
            COUNT(DISTINCT u.id) as total_students,
            AVG(r.total_marks) as avg_marks,
            AVG(r.attendance_percentage) as avg_attendance
        FROM departments d
        LEFT JOIN users u ON d.name = u.department AND u.role = 'student'
        LEFT JOIN results r ON u.id = r.student_id
        GROUP BY d.id
        HAVING total_students > 0
        ORDER BY avg_marks DESC
    '''
    
    dept_df = pd.read_sql_query(dept_query, conn)
    
    if not dept_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = px.bar(dept_df, x='department', y='avg_marks', 
                         title='Average Marks by Department',
                         color='avg_marks', color_continuous_scale='viridis')
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            fig2 = px.bar(dept_df, x='department', y='avg_attendance', 
                         title='Average Attendance by Department',
                         color='avg_attendance', color_continuous_scale='blues')
            st.plotly_chart(fig2, use_container_width=True)
    
    # Subject-wise performance
    st.write("### Subject-wise Performance")
    subject_query = '''
        SELECT 
            s.name as subject,
            COUNT(DISTINCT r.student_id) as enrolled_students,
            AVG(r.total_marks) as avg_marks,
            AVG(r.attendance_percentage) as avg_attendance
        FROM subjects s
        LEFT JOIN results r ON s.id = r.subject_id
        GROUP BY s.id
        HAVING enrolled_students > 0
        ORDER BY avg_marks DESC
    '''
    
    subject_df = pd.read_sql_query(subject_query, conn)
    conn.close()
    
    if not subject_df.empty:
        st.dataframe(subject_df, use_container_width=True)
        
        # Subject performance chart
        fig3 = px.scatter(subject_df, x='avg_attendance', y='avg_marks', 
                         size='enrolled_students', hover_data=['subject'],
                         title='Subject Performance: Attendance vs Marks')
        st.plotly_chart(fig3, use_container_width=True)

def show_ai_insights():
    """Show AI-powered insights"""
    st.subheader("🎯 AI-Powered Insights")
    
    insight_options = st.selectbox(
        "Select Analysis Type",
        ["Department Performance Analysis", "Student Outcome Predictions", "Overall System Insights"]
    )
    
    if st.button("🤖 Generate AI Insights"):
        with st.spinner("Generating AI insights..."):
            if insight_options == "Department Performance Analysis":
                insights = analyze_department_performance()
                st.markdown("### 🏢 Department Performance Analysis")
                st.write(insights)
            
            elif insight_options == "Student Outcome Predictions":
                insights = predict_student_outcomes()
                st.markdown("### 🎯 Student Outcome Predictions")
                st.write(insights)
            
            elif insight_options == "Overall System Insights":
                # Combined analysis
                dept_insights = analyze_department_performance()
                student_insights = predict_student_outcomes()
                
                st.markdown("### 🏢 Department Analysis")
                st.write(dept_insights)
                
                st.markdown("### 🎯 Student Predictions")
                st.write(student_insights)

def show_system_reports():
    """Show system reports"""
    st.subheader("📋 System Reports")
    
    report_type = st.selectbox(
        "Select Report Type",
        ["User Activity Report", "Academic Performance Report", "Department Summary Report"]
    )
    
    if report_type == "User Activity Report":
        show_user_activity_report()
    elif report_type == "Academic Performance Report":
        show_academic_performance_report()
    elif report_type == "Department Summary Report":
        show_department_summary_report()

def show_certificate_management():
    """Certificate management interface"""
    st.header("🎓 Certificate Management")
    
    cert_tabs = st.tabs(["📋 View Certificates", "➕ Issue Certificate", "✅ Verify Certificate"])
    
    with cert_tabs[0]:
        show_certificates_list()
    
    with cert_tabs[1]:
        issue_new_certificate()
    
    with cert_tabs[2]:
        verify_certificate()

def show_certificates_list():
    """Show all certificates"""
    st.subheader("📋 All Certificates")
    
    conn = get_db_connection()
    query = '''
        SELECT 
            c.id,
            u.full_name as student_name,
            c.certificate_type,
            c.title,
            c.issue_date,
            c.certificate_id,
            c.is_verified,
            ub.full_name as issued_by
        FROM certificates c
        JOIN users u ON c.student_id = u.id
        LEFT JOIN users ub ON c.issued_by = ub.id
        ORDER BY c.issue_date DESC
    '''
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No certificates found")

def issue_new_certificate():
    """Issue new certificate"""
    st.subheader("➕ Issue New Certificate")
    
    with st.form("issue_certificate_form"):
        # Get students
        conn = get_db_connection()
        students_query = "SELECT id, full_name FROM users WHERE role = 'student' ORDER BY full_name"
        students_df = pd.read_sql_query(students_query, conn)
        conn.close()
        
        if not students_df.empty:
            student_options = {row['full_name']: row['id'] for _, row in students_df.iterrows()}
            selected_student = st.selectbox("Select Student*", list(student_options.keys()))
            student_id = student_options[selected_student]
            
            col1, col2 = st.columns(2)
            
            with col1:
                cert_type = st.selectbox("Certificate Type*", 
                                       ["Completion", "Achievement", "Participation", "Excellence"])
                title = st.text_input("Certificate Title*")
            
            with col2:
                description = st.text_area("Description")
                issue_date = st.date_input("Issue Date", value=date.today())
            
            submit_button = st.form_submit_button("🎓 Issue Certificate")
            
            if submit_button:
                if selected_student and cert_type and title:
                    cert_id = f"ACAD-{datetime.now().strftime('%Y%m%d')}-{student_id:04d}"
                    
                    if create_certificate(student_id, cert_type, title, description, 
                                        issue_date, cert_id, st.session_state.user_id):
                        st.success("✅ Certificate issued successfully!")
                        st.info(f"Certificate ID: {cert_id}")
                        
                        # Send notification to student
                        create_notification(
                            student_id,
                            "New Certificate Issued",
                            f"You have been awarded a certificate: {title}",
                            "success"
                        )
                    else:
                        st.error("❌ Failed to issue certificate.")
                else:
                    st.error("⚠️ Please fill in all required fields marked with *")
        else:
            st.info("No students available for certificate issuance")

def verify_certificate():
    """Certificate verification"""
    st.subheader("✅ Certificate Verification")
    
    cert_id = st.text_input("Enter Certificate ID")
    
    if st.button("🔍 Verify Certificate"):
        if cert_id:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    c.*,
                    u.full_name as student_name,
                    ub.full_name as issued_by_name
                FROM certificates c
                JOIN users u ON c.student_id = u.id
                LEFT JOIN users ub ON c.issued_by = ub.id
                WHERE c.certificate_id = ?
            ''', (cert_id,))
            
            cert = cursor.fetchone()
            conn.close()
            
            if cert:
                if cert['is_verified']:
                    st.success("✅ Certificate is VALID")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Student:** {cert['student_name']}")
                        st.write(f"**Certificate Type:** {cert['certificate_type']}")
                        st.write(f"**Title:** {cert['title']}")
                    
                    with col2:
                        st.write(f"**Issue Date:** {cert['issue_date']}")
                        st.write(f"**Issued By:** {cert['issued_by_name']}")
                        st.write(f"**Certificate ID:** {cert['certificate_id']}")
                    
                    if cert['description']:
                        st.write(f"**Description:** {cert['description']}")
                else:
                    st.warning("⚠️ Certificate exists but is not verified")
            else:
                st.error("❌ Certificate not found or invalid")
        else:
            st.error("⚠️ Please enter a certificate ID")

# Helper functions
def get_all_departments():
    """Get list of all departments"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM departments ORDER BY name")
    departments = [row[0] for row in cursor.fetchall()]
    conn.close()
    return departments if departments else ["No Departments"]

def create_user(username, password, role, full_name, email, department):
    """Create new user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute('''
            INSERT INTO users (username, password, role, full_name, email, department)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, hashed_password, role, full_name, email, department))
        
        conn.commit()
        conn.close()
        return True
    except:
        return False

def update_user(user_id, username, full_name, role, email, department, password, is_active):
    """Update user information"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if password:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute('''
                UPDATE users 
                SET username=?, full_name=?, role=?, email=?, department=?, password=?, is_active=?
                WHERE id=?
            ''', (username, full_name, role, email, department, hashed_password, is_active, user_id))
        else:
            cursor.execute('''
                UPDATE users 
                SET username=?, full_name=?, role=?, email=?, department=?, is_active=?
                WHERE id=?
            ''', (username, full_name, role, email, department, is_active, user_id))
        
        conn.commit()
        conn.close()
        return True
    except:
        return False

def create_department(name, code, head_id):
    """Create new department"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO departments (name, code, head_id)
            VALUES (?, ?, ?)
        ''', (name, code, head_id))
        
        conn.commit()
        conn.close()
        return True
    except:
        return False

def create_subject(name, code, department_name, teacher_id, credits, semester):
    """Create new subject"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get department ID
        cursor.execute("SELECT id FROM departments WHERE name = ?", (department_name,))
        dept = cursor.fetchone()
        
        if dept:
            cursor.execute('''
                INSERT INTO subjects (name, code, department_id, teacher_id, credits, semester)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, code, dept[0], teacher_id, credits, semester))
            
            conn.commit()
            conn.close()
            return True
        
        conn.close()
        return False
    except:
        return False

def create_announcement_record(title, content, posted_by, target_role, department_id):
    """Create announcement record"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO announcements (title, content, posted_by, target_role, department_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, content, posted_by, target_role, department_id))
        
        conn.commit()
        conn.close()
        return True
    except:
        return False

def send_announcement_notifications(title, content, target_role, department_id):
    """Send notifications for announcement"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Build query to get target users
    query = "SELECT id FROM users WHERE is_active = 1"
    params = []
    
    if target_role and target_role != "all":
        query += " AND role = ?"
        params.append(target_role)
    
    if department_id:
        cursor.execute("SELECT name FROM departments WHERE id = ?", (department_id,))
        dept = cursor.fetchone()
        if dept:
            query += " AND department = ?"
            params.append(dept[0])
    
    cursor.execute(query, params)
    users = cursor.fetchall()
    
    # Send notifications
    for user in users:
        create_notification(user[0], f"📢 {title}", content, "announcement")
    
    conn.close()

def toggle_announcement_status(announcement_id, new_status):
    """Toggle announcement active status"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE announcements SET is_active = ? WHERE id = ?", (new_status, announcement_id))
    
    conn.commit()
    conn.close()

def delete_announcement(announcement_id):
    """Delete announcement"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM announcements WHERE id = ?", (announcement_id,))
    
    conn.commit()
    conn.close()

def create_certificate(student_id, cert_type, title, description, issue_date, cert_id, issued_by):
    """Create certificate record"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO certificates (student_id, certificate_type, title, description, 
                                    issue_date, certificate_id, issued_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (student_id, cert_type, title, description, issue_date, cert_id, issued_by))
        
        conn.commit()
        conn.close()
        return True
    except:
        return False

def show_user_activity_report():
    """Show user activity report"""
    st.write("### 👥 User Activity Report")
    
    conn = get_db_connection()
    
    # Recent user registrations
    query1 = '''
        SELECT 
            role,
            COUNT(*) as count,
            DATE(created_at) as date
        FROM users 
        WHERE created_at >= DATE('now', '-30 days')
        GROUP BY role, DATE(created_at)
        ORDER BY date DESC
    '''
    
    df1 = pd.read_sql_query(query1, conn)
    
    if not df1.empty:
        fig = px.line(df1, x='date', y='count', color='role', 
                     title='User Registrations (Last 30 Days)')
        st.plotly_chart(fig, use_container_width=True)
    
    # Active users summary
    query2 = '''
        SELECT 
            role,
            COUNT(*) as total_users,
            SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_users
        FROM users
        GROUP BY role
    '''
    
    df2 = pd.read_sql_query(query2, conn)
    conn.close()
    
    if not df2.empty:
        st.dataframe(df2, use_container_width=True)

def show_academic_performance_report():
    """Show academic performance report"""
    st.write("### 📚 Academic Performance Report")
    
    conn = get_db_connection()
    
    # Grade distribution
    query = '''
        SELECT 
            grade,
            COUNT(*) as count
        FROM results
        WHERE grade IS NOT NULL
        GROUP BY grade
        ORDER BY 
            CASE grade
                WHEN 'A+' THEN 1
                WHEN 'A' THEN 2
                WHEN 'B+' THEN 3
                WHEN 'B' THEN 4
                WHEN 'C' THEN 5
                WHEN 'D' THEN 6
                WHEN 'F' THEN 7
            END
    '''
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = px.pie(df, values='count', names='grade', 
                         title='Overall Grade Distribution')
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            fig2 = px.bar(df, x='grade', y='count', 
                         title='Grade Distribution (Bar Chart)')
            st.plotly_chart(fig2, use_container_width=True)

def show_department_summary_report():
    """Show department summary report"""
    st.write("### 🏢 Department Summary Report")
    
    conn = get_db_connection()
    
    query = '''
        SELECT 
            d.name as department,
            d.code,
            u_head.full_name as department_head,
            COUNT(DISTINCT u_student.id) as total_students,
            COUNT(DISTINCT u_teacher.id) as total_teachers,
            COUNT(DISTINCT s.id) as total_subjects,
            AVG(r.total_marks) as avg_performance
        FROM departments d
        LEFT JOIN users u_head ON d.head_id = u_head.id
        LEFT JOIN users u_student ON d.name = u_student.department AND u_student.role = 'student'
        LEFT JOIN users u_teacher ON d.name = u_teacher.department AND u_teacher.role = 'teacher'
        LEFT JOIN subjects s ON d.id = s.department_id
        LEFT JOIN results r ON s.id = r.subject_id
        GROUP BY d.id
        ORDER BY d.name
    '''
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        
        # Department comparison chart
        if 'avg_performance' in df.columns:
            fig = px.bar(df, x='department', y='avg_performance', 
                        title='Average Performance by Department')
            st.plotly_chart(fig, use_container_width=True)
