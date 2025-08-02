import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import get_db_connection
from utils import (create_performance_chart, get_dashboard_stats, show_notifications_sidebar, 
                   create_notification, calculate_grade, format_date, save_uploaded_file, 
                   validate_file_upload, create_attendance_chart, generate_certificate_pdf)
from ai_analytics import analyze_student_performance, generate_personalized_recommendations
from datetime import datetime, date, timedelta
import os
import uuid

def student_dashboard():
    """Student dashboard with full functionality"""
    st.title("👨‍🎓 Student Dashboard")
    
    # Show notifications
    show_notifications_sidebar()
    
    # Navigation tabs
    tabs = st.tabs([
        "📊 Overview", 
        "📝 Assignments", 
        "🔬 Projects",
        "📋 Attendance",
        "📈 Results & Analytics",
        "📄 Resume",
        "🎓 Certificates",
        "👤 Profile"
    ])
    
    with tabs[0]:
        show_student_overview()
    
    with tabs[1]:
        show_student_assignments()
    
    with tabs[2]:
        show_student_projects()
    
    with tabs[3]:
        show_student_attendance()
    
    with tabs[4]:
        show_student_results()
    
    with tabs[5]:
        from resume_module import show_resume_dashboard
        show_resume_dashboard()
    
    with tabs[6]:
        show_student_certificates()
    
    with tabs[7]:
        show_student_profile()

def show_student_overview():
    """Show student overview dashboard"""
    st.header("📊 Academic Overview")
    
    # Get dashboard stats
    stats = get_dashboard_stats('student', st.session_state.user_id)
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📚 Enrolled Subjects", stats['enrolled_subjects'])
        st.metric("📋 Avg Attendance", f"{stats['avg_attendance']}%")
    
    with col2:
        st.metric("📝 Assignments Submitted", stats['submitted_assignments'])
        st.metric("📊 Avg Marks", f"{stats['avg_marks']}%")
    
    with col3:
        st.metric("🔬 Projects Submitted", stats['submitted_projects'])
    
    with col4:
        st.metric("🎓 Certificates Earned", stats['certificates_earned'])
    
    st.markdown("---")
    
    # Recent activities and performance
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📚 Subject Performance")
        conn = get_db_connection()
        
        query = '''
            SELECT 
                s.name as subject,
                r.total_marks,
                r.attendance_percentage,
                r.grade
            FROM results r
            JOIN subjects s ON r.subject_id = s.id
            WHERE r.student_id = ?
            ORDER BY r.total_marks DESC
        '''
        
        df = pd.read_sql_query(query, conn, params=(st.session_state.user_id,))
        
        if not df.empty:
            fig = px.bar(df, x='subject', y='total_marks', 
                        title='Performance by Subject',
                        color='total_marks',
                        color_continuous_scale='viridis')
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No performance data available yet")
        
        conn.close()
    
    with col2:
        st.subheader("📋 Recent Activities")
        conn = get_db_connection()
        
        # Get recent submissions
        recent_query = '''
            SELECT 
                'Assignment' as type,
                a.title as title,
                asub.submitted_at as date,
                asub.marks_obtained as marks,
                a.max_marks as max_marks
            FROM assignment_submissions asub
            JOIN assignments a ON asub.assignment_id = a.id
            WHERE asub.student_id = ?
            
            UNION ALL
            
            SELECT 
                'Project' as type,
                p.title as title,
                psub.submitted_at as date,
                psub.marks_obtained as marks,
                p.max_marks as max_marks
            FROM project_submissions psub
            JOIN projects p ON psub.project_id = p.id
            WHERE psub.student_id = ?
            
            ORDER BY date DESC
            LIMIT 5
        '''
        
        recent_df = pd.read_sql_query(recent_query, conn, params=(st.session_state.user_id, st.session_state.user_id))
        
        if not recent_df.empty:
            for _, activity in recent_df.iterrows():
                with st.container():
                    icon = "📝" if activity['type'] == 'Assignment' else "🔬"
                    st.write(f"{icon} **{activity['title']}**")
                    st.write(f"📅 {format_date(activity['date'])}")
                    
                    if pd.notna(activity['marks']):
                        percentage = (activity['marks'] / activity['max_marks']) * 100
                        st.write(f"📊 Score: {activity['marks']}/{activity['max_marks']} ({percentage:.1f}%)")
                    else:
                        st.write("⏳ Pending evaluation")
                    
                    st.markdown("---")
        else:
            st.info("No recent activities")
        
        conn.close()
    
    # Upcoming deadlines
    st.subheader("⏰ Upcoming Deadlines")
    conn = get_db_connection()
    
    deadlines_query = '''
        SELECT 
            'Assignment' as type,
            a.title as title,
            a.due_date as deadline,
            s.name as subject,
            CASE WHEN asub.id IS NULL THEN 0 ELSE 1 END as submitted
        FROM assignments a
        JOIN subjects s ON a.subject_id = s.id
        JOIN enrollments e ON s.id = e.subject_id
        LEFT JOIN assignment_submissions asub ON a.id = asub.assignment_id AND asub.student_id = ?
        WHERE e.student_id = ? AND a.is_active = 1 AND a.due_date >= date('now')
        
        UNION ALL
        
        SELECT 
            'Project' as type,
            p.title as title,
            p.end_date as deadline,
            s.name as subject,
            CASE WHEN psub.id IS NULL THEN 0 ELSE 1 END as submitted
        FROM projects p
        JOIN subjects s ON p.subject_id = s.id
        JOIN enrollments e ON s.id = e.subject_id
        LEFT JOIN project_submissions psub ON p.id = psub.project_id AND psub.student_id = ?
        WHERE e.student_id = ? AND p.status = 'active' AND p.end_date >= date('now')
        
        ORDER BY deadline ASC
        LIMIT 5
    '''
    
    deadlines_df = pd.read_sql_query(deadlines_query, conn, 
                                   params=(st.session_state.user_id, st.session_state.user_id,
                                          st.session_state.user_id, st.session_state.user_id))
    
    if not deadlines_df.empty:
        for _, deadline in deadlines_df.iterrows():
            with st.container():
                icon = "📝" if deadline['type'] == 'Assignment' else "🔬"
                status_icon = "✅" if deadline['submitted'] else "⏳"
                
                col_a, col_b = st.columns([3, 1])
                
                with col_a:
                    st.write(f"{icon} **{deadline['title']}**")
                    st.write(f"📚 {deadline['subject']}")
                    st.write(f"📅 Due: {format_date(deadline['deadline'])}")
                
                with col_b:
                    st.write(f"{status_icon} {'Submitted' if deadline['submitted'] else 'Pending'}")
                
                st.markdown("---")
    else:
        st.info("No upcoming deadlines")
    
    conn.close()

def show_student_assignments():
    """Show student assignments"""
    st.header("📝 My Assignments")
    
    assignment_tabs = st.tabs(["📋 All Assignments", "➕ Submit Assignment", "📊 Assignment History"])
    
    with assignment_tabs[0]:
        show_all_assignments()
    
    with assignment_tabs[1]:
        submit_assignment()
    
    with assignment_tabs[2]:
        show_assignment_history()

def show_all_assignments():
    """Show all assignments for student"""
    st.subheader("📋 Available Assignments")
    
    # Get student's enrolled subjects
    conn = get_db_connection()
    
    query = '''
        SELECT 
            a.id,
            a.title,
            a.description,
            s.name as subject,
            a.due_date,
            a.max_marks,
            asub.submitted_at,
            asub.marks_obtained,
            asub.feedback,
            CASE WHEN asub.id IS NULL THEN 0 ELSE 1 END as submitted
        FROM assignments a
        JOIN subjects s ON a.subject_id = s.id
        JOIN enrollments e ON s.id = e.subject_id
        LEFT JOIN assignment_submissions asub ON a.id = asub.assignment_id AND asub.student_id = ?
        WHERE e.student_id = ? AND a.is_active = 1
        ORDER BY a.due_date ASC
    '''
    
    df = pd.read_sql_query(query, conn, params=(st.session_state.user_id, st.session_state.user_id))
    conn.close()
    
    if not df.empty:
        # Filter options
        col1, col2 = st.columns(2)
        
        with col1:
            subject_filter = st.selectbox("Filter by Subject", 
                                        ["All Subjects"] + list(df['subject'].unique()))
        
        with col2:
            status_filter = st.selectbox("Filter by Status", 
                                       ["All", "Submitted", "Pending", "Overdue"])
        
        # Apply filters
        filtered_df = df.copy()
        
        if subject_filter != "All Subjects":
            filtered_df = filtered_df[filtered_df['subject'] == subject_filter]
        
        if status_filter == "Submitted":
            filtered_df = filtered_df[filtered_df['submitted'] == 1]
        elif status_filter == "Pending":
            filtered_df = filtered_df[filtered_df['submitted'] == 0]
        elif status_filter == "Overdue":
            today = date.today().strftime('%Y-%m-%d')
            filtered_df = filtered_df[(filtered_df['submitted'] == 0) & (filtered_df['due_date'] < today)]
        
        # Display assignments
        for _, assignment in filtered_df.iterrows():
            due_date = datetime.strptime(assignment['due_date'], '%Y-%m-%d').date()
            is_overdue = due_date < date.today() and not assignment['submitted']
            
            status_color = "🔴" if is_overdue else ("✅" if assignment['submitted'] else "⏳")
            
            with st.expander(f"{status_color} {assignment['title']} - {assignment['subject']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Subject:** {assignment['subject']}")
                    st.write(f"**Due Date:** {format_date(assignment['due_date'])}")
                    st.write(f"**Max Marks:** {assignment['max_marks']}")
                    
                    if assignment['description']:
                        st.write("**Description:**")
                        st.write(assignment['description'])
                
                with col2:
                    if assignment['submitted']:
                        st.write(f"**Submitted:** {format_date(assignment['submitted_at'])}")
                        
                        if pd.notna(assignment['marks_obtained']):
                            percentage = (assignment['marks_obtained'] / assignment['max_marks']) * 100
                            st.write(f"**Score:** {assignment['marks_obtained']}/{assignment['max_marks']} ({percentage:.1f}%)")
                            grade = calculate_grade(percentage)
                            st.write(f"**Grade:** {grade}")
                            
                            if assignment['feedback']:
                                st.write("**Feedback:**")
                                st.write(assignment['feedback'])
                        else:
                            st.write("**Status:** ⏳ Pending evaluation")
                    else:
                        if is_overdue:
                            st.error("🔴 **Overdue!**")
                        else:
                            days_left = (due_date - date.today()).days
                            if days_left <= 3:
                                st.warning(f"⚠️ Due in {days_left} day(s)")
                            else:
                                st.info(f"📅 Due in {days_left} day(s)")
                        
                        if st.button(f"📝 Submit Assignment", key=f"submit_{assignment['id']}"):
                            st.session_state.submit_assignment_id = assignment['id']
                            st.session_state.submit_assignment_title = assignment['title']
                            st.rerun()
    else:
        st.info("No assignments available")

def submit_assignment():
    """Submit assignment form"""
    st.subheader("➕ Submit Assignment")
    
    # Check if redirected from assignment list
    if hasattr(st.session_state, 'submit_assignment_id'):
        assignment_id = st.session_state.submit_assignment_id
        assignment_title = st.session_state.submit_assignment_title
        
        # Clear session state
        del st.session_state.submit_assignment_id
        del st.session_state.submit_assignment_title
        
        show_assignment_submission_form(assignment_id, assignment_title)
    else:
        # Show assignment selection
        conn = get_db_connection()
        
        query = '''
            SELECT 
                a.id,
                a.title,
                s.name as subject,
                a.due_date
            FROM assignments a
            JOIN subjects s ON a.subject_id = s.id
            JOIN enrollments e ON s.id = e.subject_id
            LEFT JOIN assignment_submissions asub ON a.id = asub.assignment_id AND asub.student_id = ?
            WHERE e.student_id = ? AND a.is_active = 1 AND asub.id IS NULL
            ORDER BY a.due_date ASC
        '''
        
        df = pd.read_sql_query(query, conn, params=(st.session_state.user_id, st.session_state.user_id))
        conn.close()
        
        if not df.empty:
            assignment_options = {f"{row['title']} - {row['subject']} (Due: {format_date(row['due_date'])})": row['id'] 
                                for _, row in df.iterrows()}
            
            selected_assignment = st.selectbox("Select Assignment to Submit", list(assignment_options.keys()))
            
            if selected_assignment:
                assignment_id = assignment_options[selected_assignment]
                assignment_title = selected_assignment.split(' - ')[0]
                
                if st.button("📝 Proceed to Submit"):
                    show_assignment_submission_form(assignment_id, assignment_title)
        else:
            st.info("No pending assignments to submit")

def show_assignment_submission_form(assignment_id, assignment_title):
    """Show assignment submission form"""
    st.subheader(f"📝 Submit: {assignment_title}")
    
    with st.form("assignment_submission_form"):
        submission_text = st.text_area("Assignment Text/Description", height=150,
                                     help="Describe your solution or approach")
        
        uploaded_file = st.file_uploader(
            "Upload Assignment File",
            type=['pdf', 'doc', 'docx', 'txt', 'zip', 'py', 'java', 'cpp', 'c'],
            help="Upload your assignment file (PDF, DOC, TXT, ZIP, or code files)"
        )
        
        submit_button = st.form_submit_button("📤 Submit Assignment")
        
        if submit_button:
            if submission_text or uploaded_file:
                file_path = None
                file_name = None
                
                if uploaded_file:
                    # Validate file
                    allowed_types = [
                        'application/pdf', 'application/msword', 
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        'text/plain', 'application/zip', 'text/x-python-script',
                        'text/x-java-source', 'text/x-c++src', 'text/x-csrc'
                    ]
                    
                    is_valid, message = validate_file_upload(uploaded_file, allowed_types, max_size_mb=25)
                    
                    if is_valid:
                        file_path = save_uploaded_file(uploaded_file, "assignment_submissions")
                        file_name = uploaded_file.name
                    else:
                        st.error(f"File upload error: {message}")
                        return
                
                if submit_assignment_record(assignment_id, st.session_state.user_id, 
                                          submission_text, file_name, file_path):
                    st.success("✅ Assignment submitted successfully!")
                    st.info("Your assignment has been submitted and will be evaluated by your teacher.")
                    
                    # Send notification to teacher
                    send_submission_notification(assignment_id, st.session_state.user_id, "assignment")
                else:
                    st.error("❌ Failed to submit assignment. Please try again.")
            else:
                st.error("⚠️ Please provide either text description or upload a file")

def show_assignment_history():
    """Show assignment submission history"""
    st.subheader("📊 Assignment History")
    
    conn = get_db_connection()
    
    query = '''
        SELECT 
            a.title,
            s.name as subject,
            asub.submitted_at,
            asub.marks_obtained,
            a.max_marks,
            asub.feedback,
            a.due_date
        FROM assignment_submissions asub
        JOIN assignments a ON asub.assignment_id = a.id
        JOIN subjects s ON a.subject_id = s.id
        WHERE asub.student_id = ?
        ORDER BY asub.submitted_at DESC
    '''
    
    df = pd.read_sql_query(query, conn, params=(st.session_state.user_id,))
    conn.close()
    
    if not df.empty:
        # Summary statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_submissions = len(df)
            st.metric("📝 Total Submissions", total_submissions)
        
        with col2:
            graded_submissions = df['marks_obtained'].notna().sum()
            st.metric("✅ Graded Submissions", graded_submissions)
        
        with col3:
            if graded_submissions > 0:
                avg_score = df['marks_obtained'].mean()
                st.metric("📊 Average Score", f"{avg_score:.1f}%")
            else:
                st.metric("📊 Average Score", "N/A")
        
        # Performance trend
        graded_df = df[df['marks_obtained'].notna()].copy()
        if len(graded_df) > 1:
            graded_df['percentage'] = (graded_df['marks_obtained'] / graded_df['max_marks']) * 100
            
            fig = px.line(graded_df, x='submitted_at', y='percentage',
                         title='Assignment Performance Trend',
                         markers=True)
            fig.update_layout(xaxis_title='Submission Date', yaxis_title='Score (%)')
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed history
        st.markdown("### 📋 Detailed History")
        
        for _, submission in df.iterrows():
            with st.expander(f"📝 {submission['title']} - {submission['subject']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Submitted:** {format_date(submission['submitted_at'])}")
                    st.write(f"**Due Date:** {format_date(submission['due_date'])}")
                
                with col2:
                    if pd.notna(submission['marks_obtained']):
                        percentage = (submission['marks_obtained'] / submission['max_marks']) * 100
                        st.write(f"**Score:** {submission['marks_obtained']}/{submission['max_marks']} ({percentage:.1f}%)")
                        grade = calculate_grade(percentage)
                        st.write(f"**Grade:** {grade}")
                    else:
                        st.write("**Status:** ⏳ Pending evaluation")
                
                if submission['feedback']:
                    st.write("**Teacher Feedback:**")
                    st.info(submission['feedback'])
    else:
        st.info("No assignment submissions yet")

def show_student_projects():
    """Show student projects"""
    st.header("🔬 My Projects")
    
    project_tabs = st.tabs(["📋 All Projects", "➕ Submit Project", "📊 Project History"])
    
    with project_tabs[0]:
        show_all_projects()
    
    with project_tabs[1]:
        submit_project()
    
    with project_tabs[2]:
        show_project_history()

def show_all_projects():
    """Show all projects for student"""
    st.subheader("📋 Available Projects")
    
    conn = get_db_connection()
    
    query = '''
        SELECT 
            p.id,
            p.title,
            p.description,
            s.name as subject,
            p.start_date,
            p.end_date,
            p.max_marks,
            psub.submitted_at,
            psub.marks_obtained,
            psub.feedback,
            CASE WHEN psub.id IS NULL THEN 0 ELSE 1 END as submitted
        FROM projects p
        JOIN subjects s ON p.subject_id = s.id
        JOIN enrollments e ON s.id = e.subject_id
        LEFT JOIN project_submissions psub ON p.id = psub.project_id AND psub.student_id = ?
        WHERE e.student_id = ? AND p.status = 'active'
        ORDER BY p.end_date ASC
    '''
    
    df = pd.read_sql_query(query, conn, params=(st.session_state.user_id, st.session_state.user_id))
    conn.close()
    
    if not df.empty:
        # Filter options
        subject_filter = st.selectbox("Filter by Subject", 
                                    ["All Subjects"] + list(df['subject'].unique()))
        
        if subject_filter != "All Subjects":
            df = df[df['subject'] == subject_filter]
        
        # Display projects
        for _, project in df.iterrows():
            end_date = datetime.strptime(project['end_date'], '%Y-%m-%d').date()
            is_overdue = end_date < date.today() and not project['submitted']
            
            status_color = "🔴" if is_overdue else ("✅" if project['submitted'] else "⏳")
            
            with st.expander(f"{status_color} {project['title']} - {project['subject']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Subject:** {project['subject']}")
                    st.write(f"**Start Date:** {format_date(project['start_date'])}")
                    st.write(f"**End Date:** {format_date(project['end_date'])}")
                    st.write(f"**Max Marks:** {project['max_marks']}")
                    
                    if project['description']:
                        st.write("**Description:**")
                        st.write(project['description'])
                
                with col2:
                    if project['submitted']:
                        st.write(f"**Submitted:** {format_date(project['submitted_at'])}")
                        
                        if pd.notna(project['marks_obtained']):
                            percentage = (project['marks_obtained'] / project['max_marks']) * 100
                            st.write(f"**Score:** {project['marks_obtained']}/{project['max_marks']} ({percentage:.1f}%)")
                            grade = calculate_grade(percentage)
                            st.write(f"**Grade:** {grade}")
                            
                            if project['feedback']:
                                st.write("**Feedback:**")
                                st.write(project['feedback'])
                        else:
                            st.write("**Status:** ⏳ Pending evaluation")
                    else:
                        if is_overdue:
                            st.error("🔴 **Overdue!**")
                        else:
                            days_left = (end_date - date.today()).days
                            if days_left <= 7:
                                st.warning(f"⚠️ Due in {days_left} day(s)")
                            else:
                                st.info(f"📅 Due in {days_left} day(s)")
                        
                        if st.button(f"🔬 Submit Project", key=f"submit_proj_{project['id']}"):
                            st.session_state.submit_project_id = project['id']
                            st.session_state.submit_project_title = project['title']
                            st.rerun()
    else:
        st.info("No projects available")

def submit_project():
    """Submit project form"""
    st.subheader("➕ Submit Project")
    
    # Check if redirected from project list
    if hasattr(st.session_state, 'submit_project_id'):
        project_id = st.session_state.submit_project_id
        project_title = st.session_state.submit_project_title
        
        # Clear session state
        del st.session_state.submit_project_id
        del st.session_state.submit_project_title
        
        show_project_submission_form(project_id, project_title)
    else:
        # Show project selection
        conn = get_db_connection()
        
        query = '''
            SELECT 
                p.id,
                p.title,
                s.name as subject,
                p.end_date
            FROM projects p
            JOIN subjects s ON p.subject_id = s.id
            JOIN enrollments e ON s.id = e.subject_id
            LEFT JOIN project_submissions psub ON p.id = psub.project_id AND psub.student_id = ?
            WHERE e.student_id = ? AND p.status = 'active' AND psub.id IS NULL
            ORDER BY p.end_date ASC
        '''
        
        df = pd.read_sql_query(query, conn, params=(st.session_state.user_id, st.session_state.user_id))
        conn.close()
        
        if not df.empty:
            project_options = {f"{row['title']} - {row['subject']} (Due: {format_date(row['end_date'])})": row['id'] 
                             for _, row in df.iterrows()}
            
            selected_project = st.selectbox("Select Project to Submit", list(project_options.keys()))
            
            if selected_project:
                project_id = project_options[selected_project]
                project_title = selected_project.split(' - ')[0]
                
                if st.button("🔬 Proceed to Submit"):
                    show_project_submission_form(project_id, project_title)
        else:
            st.info("No pending projects to submit")

def show_project_submission_form(project_id, project_title):
    """Show project submission form"""
    st.subheader(f"🔬 Submit: {project_title}")
    
    with st.form("project_submission_form"):
        submission_title = st.text_input("Project Title*", 
                                       help="Title of your project submission")
        
        submission_description = st.text_area("Project Description*", height=150,
                                            help="Detailed description of your project, methodology, and findings")
        
        github_url = st.text_input("GitHub Repository URL (Optional)",
                                 help="Link to your project's GitHub repository")
        
        uploaded_file = st.file_uploader(
            "Upload Project File",
            type=['pdf', 'zip', 'rar', 'doc', 'docx', 'ppt', 'pptx'],
            help="Upload your project report, presentation, or source code (ZIP/RAR)"
        )
        
        submit_button = st.form_submit_button("📤 Submit Project")
        
        if submit_button:
            if submission_title and submission_description:
                file_path = None
                file_name = None
                
                if uploaded_file:
                    # Validate file
                    allowed_types = [
                        'application/pdf', 'application/zip', 'application/x-rar-compressed',
                        'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
                    ]
                    
                    is_valid, message = validate_file_upload(uploaded_file, allowed_types, max_size_mb=50)
                    
                    if is_valid:
                        file_path = save_uploaded_file(uploaded_file, "project_submissions")
                        file_name = uploaded_file.name
                    else:
                        st.error(f"File upload error: {message}")
                        return
                
                if submit_project_record(project_id, st.session_state.user_id, 
                                       submission_title, submission_description, 
                                       file_name, file_path, github_url):
                    st.success("✅ Project submitted successfully!")
                    st.info("Your project has been submitted and will be evaluated by your teacher.")
                    
                    # Send notification to teacher
                    send_submission_notification(project_id, st.session_state.user_id, "project")
                else:
                    st.error("❌ Failed to submit project. Please try again.")
            else:
                st.error("⚠️ Please fill in all required fields marked with *")

def show_project_history():
    """Show project submission history"""
    st.subheader("📊 Project History")
    
    conn = get_db_connection()
    
    query = '''
        SELECT 
            p.title as project_title,
            psub.title as submission_title,
            s.name as subject,
            psub.submitted_at,
            psub.marks_obtained,
            p.max_marks,
            psub.feedback,
            psub.github_url,
            p.end_date
        FROM project_submissions psub
        JOIN projects p ON psub.project_id = p.id
        JOIN subjects s ON p.subject_id = s.id
        WHERE psub.student_id = ?
        ORDER BY psub.submitted_at DESC
    '''
    
    df = pd.read_sql_query(query, conn, params=(st.session_state.user_id,))
    conn.close()
    
    if not df.empty:
        # Summary statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_submissions = len(df)
            st.metric("🔬 Total Projects", total_submissions)
        
        with col2:
            graded_submissions = df['marks_obtained'].notna().sum()
            st.metric("✅ Graded Projects", graded_submissions)
        
        with col3:
            if graded_submissions > 0:
                avg_score = df['marks_obtained'].mean()
                st.metric("📊 Average Score", f"{avg_score:.1f}%")
            else:
                st.metric("📊 Average Score", "N/A")
        
        # Detailed history
        st.markdown("### 📋 Detailed History")
        
        for _, submission in df.iterrows():
            with st.expander(f"🔬 {submission['submission_title']} - {submission['subject']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Project:** {submission['project_title']}")
                    st.write(f"**Submitted:** {format_date(submission['submitted_at'])}")
                    st.write(f"**Deadline:** {format_date(submission['end_date'])}")
                    
                    if submission['github_url']:
                        st.write(f"**GitHub:** [View Repository]({submission['github_url']})")
                
                with col2:
                    if pd.notna(submission['marks_obtained']):
                        percentage = (submission['marks_obtained'] / submission['max_marks']) * 100
                        st.write(f"**Score:** {submission['marks_obtained']}/{submission['max_marks']} ({percentage:.1f}%)")
                        grade = calculate_grade(percentage)
                        st.write(f"**Grade:** {grade}")
                    else:
                        st.write("**Status:** ⏳ Pending evaluation")
                
                if submission['feedback']:
                    st.write("**Teacher Feedback:**")
                    st.info(submission['feedback'])
    else:
        st.info("No project submissions yet")

def show_student_attendance():
    """Show student attendance"""
    st.header("📋 My Attendance")
    
    attendance_tabs = st.tabs(["📊 Overview", "📈 Subject-wise Analysis", "📋 Detailed Records"])
    
    with attendance_tabs[0]:
        show_attendance_overview()
    
    with attendance_tabs[1]:
        show_attendance_analysis()
    
    with attendance_tabs[2]:
        show_detailed_attendance()

def show_attendance_overview():
    """Show attendance overview"""
    st.subheader("📊 Attendance Overview")
    
    conn = get_db_connection()
    
    # Overall attendance stats
    stats_query = '''
        SELECT 
            COUNT(CASE WHEN a.status = 'present' THEN 1 END) as present_count,
            COUNT(CASE WHEN a.status = 'absent' THEN 1 END) as absent_count,
            COUNT(CASE WHEN a.status = 'late' THEN 1 END) as late_count,
            COUNT(*) as total_classes,
            ROUND((COUNT(CASE WHEN a.status = 'present' THEN 1 END) * 100.0 / COUNT(*)), 2) as attendance_percentage
        FROM attendance a
        WHERE a.student_id = ?
    '''
    
    stats_df = pd.read_sql_query(stats_query, conn, params=(st.session_state.user_id,))
    
    if not stats_df.empty and stats_df.iloc[0]['total_classes'] > 0:
        stats = stats_df.iloc[0]
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Overall Attendance", f"{stats['attendance_percentage']:.1f}%")
        
        with col2:
            st.metric("✅ Present Days", int(stats['present_count']))
        
        with col3:
            st.metric("❌ Absent Days", int(stats['absent_count']))
        
        with col4:
            st.metric("⏰ Late Days", int(stats['late_count']))
        
        # Attendance pie chart
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.pie(
                values=[stats['present_count'], stats['absent_count'], stats['late_count']],
                names=['Present', 'Absent', 'Late'],
                title='Attendance Distribution',
                color_discrete_map={
                    'Present': '#28a745',
                    'Absent': '#dc3545', 
                    'Late': '#ffc107'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Monthly attendance trend
            monthly_query = '''
                SELECT 
                    strftime('%Y-%m', a.date) as month,
                    COUNT(CASE WHEN a.status = 'present' THEN 1 END) as present,
                    COUNT(*) as total,
                    ROUND((COUNT(CASE WHEN a.status = 'present' THEN 1 END) * 100.0 / COUNT(*)), 2) as percentage
                FROM attendance a
                WHERE a.student_id = ? AND a.date >= date('now', '-12 months')
                GROUP BY strftime('%Y-%m', a.date)
                ORDER BY month
            '''
            
            monthly_df = pd.read_sql_query(monthly_query, conn, params=(st.session_state.user_id,))
            
            if not monthly_df.empty:
                fig = px.line(monthly_df, x='month', y='percentage',
                             title='Monthly Attendance Trend',
                             markers=True)
                fig.update_layout(xaxis_title='Month', yaxis_title='Attendance %')
                st.plotly_chart(fig, use_container_width=True)
        
        # Attendance warnings
        if stats['attendance_percentage'] < 75:
            st.error("⚠️ **Warning:** Your attendance is below 75%. This may affect your eligibility for exams.")
        elif stats['attendance_percentage'] < 85:
            st.warning("🔔 **Notice:** Your attendance is below 85%. Please improve your attendance.")
        else:
            st.success("✅ **Good:** Your attendance is above 85%. Keep it up!")
    else:
        st.info("No attendance records available yet")
    
    conn.close()

def show_attendance_analysis():
    """Show subject-wise attendance analysis"""
    st.subheader("📈 Subject-wise Attendance Analysis")
    
    conn = get_db_connection()
    
    query = '''
        SELECT 
            s.name as subject,
            COUNT(CASE WHEN a.status = 'present' THEN 1 END) as present_count,
            COUNT(CASE WHEN a.status = 'absent' THEN 1 END) as absent_count,
            COUNT(CASE WHEN a.status = 'late' THEN 1 END) as late_count,
            COUNT(*) as total_classes,
            ROUND((COUNT(CASE WHEN a.status = 'present' THEN 1 END) * 100.0 / COUNT(*)), 2) as attendance_percentage
        FROM attendance a
        JOIN subjects s ON a.subject_id = s.id
        WHERE a.student_id = ?
        GROUP BY s.id
        ORDER BY attendance_percentage DESC
    '''
    
    df = pd.read_sql_query(query, conn, params=(st.session_state.user_id,))
    conn.close()
    
    if not df.empty:
        # Subject attendance comparison
        fig = px.bar(df, x='subject', y='attendance_percentage',
                    title='Subject-wise Attendance Percentage',
                    color='attendance_percentage',
                    color_continuous_scale='RdYlGn')
        fig.update_layout(xaxis_tickangle=-45, yaxis_title='Attendance %')
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed table
        st.subheader("📋 Subject-wise Details")
        st.dataframe(df, use_container_width=True)
        
        # Subject selection for detailed view
        selected_subject = st.selectbox("Select Subject for Detailed View", df['subject'].tolist())
        
        if selected_subject:
            show_subject_attendance_details(selected_subject)
    else:
        st.info("No subject-wise attendance data available")

def show_subject_attendance_details(subject_name):
    """Show detailed attendance for specific subject"""
    st.subheader(f"📊 Detailed Attendance: {subject_name}")
    
    conn = get_db_connection()
    
    query = '''
        SELECT 
            a.date,
            a.status,
            u.full_name as marked_by
        FROM attendance a
        JOIN subjects s ON a.subject_id = s.id
        LEFT JOIN users u ON a.marked_by = u.id
        WHERE a.student_id = ? AND s.name = ?
        ORDER BY a.date DESC
        LIMIT 30
    '''
    
    df = pd.read_sql_query(query, conn, params=(st.session_state.user_id, subject_name))
    conn.close()
    
    if not df.empty:
        # Display recent attendance
        for _, record in df.iterrows():
            status_icon = {"present": "✅", "absent": "❌", "late": "⏰"}
            status_color = {"present": "success", "absent": "error", "late": "warning"}
            
            col1, col2, col3 = st.columns([2, 1, 2])
            
            with col1:
                st.write(f"📅 {format_date(record['date'])}")
            
            with col2:
                status = record['status'].title()
                if record['status'] == 'present':
                    st.success(f"✅ {status}")
                elif record['status'] == 'absent':
                    st.error(f"❌ {status}")
                else:
                    st.warning(f"⏰ {status}")
            
            with col3:
                st.write(f"👨‍🏫 {record['marked_by']}")
    else:
        st.info(f"No attendance records found for {subject_name}")

def show_detailed_attendance():
    """Show detailed attendance records"""
    st.subheader("📋 Detailed Attendance Records")
    
    # Date range filter
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input("Start Date", value=date.today() - timedelta(days=30))
    
    with col2:
        end_date = st.date_input("End Date", value=date.today())
    
    if st.button("🔍 Filter Records"):
        conn = get_db_connection()
        
        query = '''
            SELECT 
                a.date,
                s.name as subject,
                a.status,
                u.full_name as marked_by
            FROM attendance a
            JOIN subjects s ON a.subject_id = s.id
            LEFT JOIN users u ON a.marked_by = u.id
            WHERE a.student_id = ? AND a.date BETWEEN ? AND ?
            ORDER BY a.date DESC, s.name
        '''
        
        df = pd.read_sql_query(query, conn, params=(st.session_state.user_id, start_date, end_date))
        conn.close()
        
        if not df.empty:
            # Summary for the period
            col1, col2, col3 = st.columns(3)
            
            with col1:
                present_count = len(df[df['status'] == 'present'])
                st.metric("✅ Present", present_count)
            
            with col2:
                absent_count = len(df[df['status'] == 'absent'])
                st.metric("❌ Absent", absent_count)
            
            with col3:
                late_count = len(df[df['status'] == 'late'])
                st.metric("⏰ Late", late_count)
            
            # Detailed records
            st.dataframe(df, use_container_width=True)
            
            # Export option
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Attendance Report",
                data=csv,
                file_name=f"attendance_report_{start_date}_{end_date}.csv",
                mime="text/csv"
            )
        else:
            st.info("No attendance records found for the selected period")

def show_student_results():
    """Show student results and analytics"""
    st.header("📈 Results & Analytics")
    
    results_tabs = st.tabs(["📊 Performance Overview", "📈 Trends & Analysis", "🤖 AI Insights"])
    
    with results_tabs[0]:
        show_performance_overview()
    
    with results_tabs[1]:
        show_performance_trends()
    
    with results_tabs[2]:
        show_ai_insights()

def show_performance_overview():
    """Show performance overview"""
    st.subheader("📊 Academic Performance Overview")
    
    conn = get_db_connection()
    
    # Get overall performance
    query = '''
        SELECT 
            s.name as subject,
            r.total_marks,
            r.attendance_percentage,
            r.grade,
            r.assignment_marks,
            r.project_marks,
            r.exam_marks,
            r.semester
        FROM results r
        JOIN subjects s ON r.subject_id = s.id
        WHERE r.student_id = ?
        ORDER BY r.semester DESC, s.name
    '''
    
    df = pd.read_sql_query(query, conn, params=(st.session_state.user_id,))
    conn.close()
    
    if not df.empty:
        # Overall metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            overall_avg = df['total_marks'].mean()
            st.metric("📊 Overall Average", f"{overall_avg:.1f}%")
        
        with col2:
            current_semester = df['semester'].max()
            st.metric("📚 Current Semester", int(current_semester))
        
        with col3:
            total_subjects = len(df)
            st.metric("📖 Total Subjects", total_subjects)
        
        with col4:
            # Calculate GPA (simple 4.0 scale)
            gpa = calculate_gpa(df['total_marks'].tolist())
            st.metric("🎯 GPA", f"{gpa:.2f}")
        
        # Performance visualization
        col1, col2 = st.columns(2)
        
        with col1:
            # Subject performance
            fig1 = px.bar(df, x='subject', y='total_marks',
                         title='Subject-wise Performance',
                         color='total_marks',
                         color_continuous_scale='viridis')
            fig1.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # Grade distribution
            grade_counts = df['grade'].value_counts()
            fig2 = px.pie(values=grade_counts.values, names=grade_counts.index,
                         title='Grade Distribution')
            st.plotly_chart(fig2, use_container_width=True)
        
        # Detailed performance breakdown
        fig3 = go.Figure()
        
        fig3.add_trace(go.Bar(name='Assignment Marks', x=df['subject'], y=df['assignment_marks']))
        fig3.add_trace(go.Bar(name='Project Marks', x=df['subject'], y=df['project_marks']))
        fig3.add_trace(go.Bar(name='Exam Marks', x=df['subject'], y=df['exam_marks']))
        
        fig3.update_layout(
            title='Performance Breakdown by Component',
            xaxis_title='Subject',
            yaxis_title='Marks',
            barmode='group',
            xaxis_tickangle=-45
        )
        
        st.plotly_chart(fig3, use_container_width=True)
        
        # Detailed table
        st.subheader("📋 Detailed Results")
        st.dataframe(df, use_container_width=True)
        
        # Export results
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Results",
            data=csv,
            file_name=f"academic_results_{st.session_state.username}.csv",
            mime="text/csv"
        )
    else:
        st.info("No academic results available yet")

def show_performance_trends():
    """Show performance trends and analysis"""
    st.subheader("📈 Performance Trends & Analysis")
    
    conn = get_db_connection()
    
    # Semester-wise performance
    semester_query = '''
        SELECT 
            r.semester,
            AVG(r.total_marks) as avg_marks,
            AVG(r.attendance_percentage) as avg_attendance,
            COUNT(*) as subject_count
        FROM results r
        WHERE r.student_id = ?
        GROUP BY r.semester
        ORDER BY r.semester
    '''
    
    semester_df = pd.read_sql_query(semester_query, conn, params=(st.session_state.user_id,))
    
    if not semester_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Semester-wise performance trend
            fig1 = px.line(semester_df, x='semester', y='avg_marks',
                          title='Semester-wise Performance Trend',
                          markers=True)
            fig1.update_layout(xaxis_title='Semester', yaxis_title='Average Marks (%)')
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # Attendance trend
            fig2 = px.line(semester_df, x='semester', y='avg_attendance',
                          title='Semester-wise Attendance Trend',
                          markers=True)
            fig2.update_traces(line_color='green')
            fig2.update_layout(xaxis_title='Semester', yaxis_title='Average Attendance (%)')
            st.plotly_chart(fig2, use_container_width=True)
    
    # Assignment vs Project performance comparison
    comparison_query = '''
        SELECT 
            s.name as subject,
            r.assignment_marks,
            r.project_marks
        FROM results r
        JOIN subjects s ON r.subject_id = s.id
        WHERE r.student_id = ? AND r.assignment_marks IS NOT NULL AND r.project_marks IS NOT NULL
    '''
    
    comparison_df = pd.read_sql_query(comparison_query, conn, params=(st.session_state.user_id,))
    
    if not comparison_df.empty:
        st.subheader("📊 Assignment vs Project Performance")
        
        fig3 = px.scatter(comparison_df, x='assignment_marks', y='project_marks',
                         hover_data=['subject'],
                         title='Assignment vs Project Performance Correlation')
        fig3.update_layout(xaxis_title='Assignment Marks', yaxis_title='Project Marks')
        st.plotly_chart(fig3, use_container_width=True)
        
        # Correlation analysis
        correlation = comparison_df['assignment_marks'].corr(comparison_df['project_marks'])
        if correlation > 0.7:
            st.success(f"✅ Strong positive correlation ({correlation:.2f}) between assignment and project performance!")
        elif correlation > 0.3:
            st.info(f"📊 Moderate correlation ({correlation:.2f}) between assignment and project performance.")
        else:
            st.warning(f"⚠️ Weak correlation ({correlation:.2f}) between assignment and project performance.")
    
    # Performance analytics
    st.subheader("📊 Performance Analytics")
    
    # Strengths and weaknesses analysis
    all_results_query = '''
        SELECT 
            s.name as subject,
            r.total_marks,
            r.assignment_marks,
            r.project_marks,
            r.exam_marks,
            r.attendance_percentage
        FROM results r
        JOIN subjects s ON r.subject_id = s.id
        WHERE r.student_id = ?
    '''
    
    all_results_df = pd.read_sql_query(all_results_query, conn, params=(st.session_state.user_id,))
    
    if not all_results_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### 💪 Top Performing Subjects")
            top_subjects = all_results_df.nlargest(3, 'total_marks')[['subject', 'total_marks']]
            for _, subject in top_subjects.iterrows():
                st.write(f"🏆 **{subject['subject']}**: {subject['total_marks']:.1f}%")
        
        with col2:
            st.write("### 📈 Areas for Improvement")
            bottom_subjects = all_results_df.nsmallest(3, 'total_marks')[['subject', 'total_marks']]
            for _, subject in bottom_subjects.iterrows():
                st.write(f"📊 **{subject['subject']}**: {subject['total_marks']:.1f}%")
    
    conn.close()

def show_ai_insights():
    """Show AI-powered insights and recommendations"""
    st.subheader("🤖 AI-Powered Academic Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Analyze My Performance", use_container_width=True):
            with st.spinner("Analyzing your academic performance..."):
                analysis = analyze_student_performance(st.session_state.user_id)
                
                st.markdown("### 📊 Performance Analysis")
                st.write(analysis)
    
    with col2:
        if st.button("💡 Get Personalized Recommendations", use_container_width=True):
            with st.spinner("Generating personalized recommendations..."):
                recommendations = generate_personalized_recommendations(st.session_state.user_id)
                
                st.markdown("### 💡 Personalized Recommendations")
                st.write(recommendations)
    
    # Additional AI insights
    st.markdown("---")
    
    if st.button("🎯 Comprehensive AI Analysis"):
        with st.spinner("Generating comprehensive AI analysis..."):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📊 Detailed Performance Analysis")
                analysis = analyze_student_performance(st.session_state.user_id)
                st.write(analysis)
            
            with col2:
                st.markdown("### 💡 Action Plan")
                recommendations = generate_personalized_recommendations(st.session_state.user_id)
                st.write(recommendations)

def show_student_certificates():
    """Show student certificates"""
    st.header("🎓 My Certificates")
    
    cert_tabs = st.tabs(["📋 My Certificates", "✅ Verify Certificate"])
    
    with cert_tabs[0]:
        show_my_certificates()
    
    with cert_tabs[1]:
        verify_certificate_form()

def show_my_certificates():
    """Show student's certificates"""
    st.subheader("📋 My Certificates")
    
    conn = get_db_connection()
    
    query = '''
        SELECT 
            c.id,
            c.certificate_type,
            c.title,
            c.description,
            c.issue_date,
            c.certificate_id,
            c.is_verified,
            u.full_name as issued_by
        FROM certificates c
        LEFT JOIN users u ON c.issued_by = u.id
        WHERE c.student_id = ?
        ORDER BY c.issue_date DESC
    '''
    
    df = pd.read_sql_query(query, conn, params=(st.session_state.user_id,))
    conn.close()
    
    if not df.empty:
        # Summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_certs = len(df)
            st.metric("🎓 Total Certificates", total_certs)
        
        with col2:
            verified_certs = len(df[df['is_verified'] == 1])
            st.metric("✅ Verified Certificates", verified_certs)
        
        with col3:
            cert_types = df['certificate_type'].nunique()
            st.metric("📊 Certificate Types", cert_types)
        
        # Certificate type distribution
        if len(df) > 1:
            type_counts = df['certificate_type'].value_counts()
            fig = px.pie(values=type_counts.values, names=type_counts.index,
                        title='Certificate Types Distribution')
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Display certificates
        for _, cert in df.iterrows():
            with st.expander(f"🎓 {cert['title']} - {cert['certificate_type'].title()}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Certificate Type:** {cert['certificate_type'].title()}")
                    st.write(f"**Issue Date:** {format_date(cert['issue_date'])}")
                    st.write(f"**Certificate ID:** {cert['certificate_id']}")
                    
                    if cert['description']:
                        st.write("**Description:**")
                        st.write(cert['description'])
                
                with col2:
                    verification_status = "✅ Verified" if cert['is_verified'] else "⚠️ Not Verified"
                    st.write(f"**Status:** {verification_status}")
                    st.write(f"**Issued By:** {cert['issued_by']}")
                
                # Action buttons
                col_a, col_b = st.columns(2)
                
                with col_a:
                    if st.button(f"📥 Download Certificate", key=f"download_{cert['id']}"):
                        # Generate and download certificate PDF
                        pdf_buffer = generate_certificate_pdf(
                            st.session_state.full_name,
                            cert['certificate_type'],
                            cert['title'],
                            cert['issue_date'],
                            cert['certificate_id']
                        )
                        
                        st.download_button(
                            label="📄 Download PDF",
                            data=pdf_buffer.getvalue(),
                            file_name=f"certificate_{cert['certificate_id']}.pdf",
                            mime="application/pdf"
                        )
                
                with col_b:
                    if st.button(f"🔗 Share Certificate", key=f"share_{cert['id']}"):
                        st.info(f"Certificate ID: {cert['certificate_id']}")
                        st.info("Share this ID for certificate verification")
    else:
        st.info("No certificates earned yet")

def verify_certificate_form():
    """Certificate verification form"""
    st.subheader("✅ Verify Certificate")
    
    st.info("Use this tool to verify the authenticity of any AcadBoost certificate")
    
    cert_id = st.text_input("Enter Certificate ID", 
                           help="Enter the certificate ID you want to verify")
    
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
                    st.success("✅ **CERTIFICATE IS VALID AND VERIFIED**")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Student Name:** {cert['student_name']}")
                        st.write(f"**Certificate Type:** {cert['certificate_type'].title()}")
                        st.write(f"**Title:** {cert['title']}")
                    
                    with col2:
                        st.write(f"**Issue Date:** {format_date(cert['issue_date'])}")
                        st.write(f"**Issued By:** {cert['issued_by_name']}")
                        st.write(f"**Certificate ID:** {cert['certificate_id']}")
                    
                    if cert['description']:
                        st.write(f"**Description:** {cert['description']}")
                    
                    st.info("🔒 This certificate is digitally verified and authentic.")
                else:
                    st.warning("⚠️ **Certificate exists but is not verified**")
                    st.write("Please contact the issuing authority for verification.")
            else:
                st.error("❌ **Certificate not found or invalid**")
                st.write("Please check the certificate ID and try again.")
        else:
            st.error("⚠️ Please enter a certificate ID")

def show_student_profile():
    """Show student profile management"""
    st.header("👤 My Profile")
    
    profile_tabs = st.tabs(["📊 Profile Overview", "✏️ Edit Profile", "📧 Contact Information"])
    
    with profile_tabs[0]:
        show_profile_overview()
    
    with profile_tabs[1]:
        edit_profile()
    
    with profile_tabs[2]:
        show_contact_info()

def show_profile_overview():
    """Show profile overview"""
    st.subheader("📊 Profile Overview")
    
    # User information
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### 👤 Personal Information")
        st.write(f"**Full Name:** {st.session_state.full_name}")
        st.write(f"**Username:** {st.session_state.username}")
        st.write(f"**Email:** {st.session_state.email}")
        st.write(f"**Department:** {st.session_state.department}")
        st.write(f"**Role:** {st.session_state.user_role.title()}")
    
    with col2:
        st.write("### 📊 Academic Summary")
        
        conn = get_db_connection()
        
        # Get academic summary
        summary_query = '''
            SELECT 
                COUNT(DISTINCT e.subject_id) as enrolled_subjects,
                COUNT(DISTINCT asub.assignment_id) as submitted_assignments,
                COUNT(DISTINCT psub.project_id) as submitted_projects,
                COUNT(DISTINCT c.id) as certificates,
                AVG(r.total_marks) as avg_marks,
                AVG(r.attendance_percentage) as avg_attendance
            FROM users u
            LEFT JOIN enrollments e ON u.id = e.student_id
            LEFT JOIN assignment_submissions asub ON u.id = asub.student_id
            LEFT JOIN project_submissions psub ON u.id = psub.student_id
            LEFT JOIN certificates c ON u.id = c.student_id
            LEFT JOIN results r ON u.id = r.student_id
            WHERE u.id = ?
        '''
        
        summary_df = pd.read_sql_query(summary_query, conn, params=(st.session_state.user_id,))
        
        if not summary_df.empty:
            summary = summary_df.iloc[0]
            
            st.write(f"**Enrolled Subjects:** {int(summary['enrolled_subjects']) if pd.notna(summary['enrolled_subjects']) else 0}")
            st.write(f"**Assignments Submitted:** {int(summary['submitted_assignments']) if pd.notna(summary['submitted_assignments']) else 0}")
            st.write(f"**Projects Submitted:** {int(summary['submitted_projects']) if pd.notna(summary['submitted_projects']) else 0}")
            st.write(f"**Certificates Earned:** {int(summary['certificates']) if pd.notna(summary['certificates']) else 0}")
            
            if pd.notna(summary['avg_marks']):
                st.write(f"**Average Marks:** {summary['avg_marks']:.1f}%")
            
            if pd.notna(summary['avg_attendance']):
                st.write(f"**Average Attendance:** {summary['avg_attendance']:.1f}%")
        
        conn.close()
    
    st.markdown("---")
    
    # Recent achievements
    st.write("### 🏆 Recent Achievements")
    
    conn = get_db_connection()
    
    achievements_query = '''
        SELECT 
            'Certificate' as type,
            c.title as achievement,
            c.issue_date as date
        FROM certificates c
        WHERE c.student_id = ?
        
        UNION ALL
        
        SELECT 
            'High Score' as type,
            CASE 
                WHEN asub.marks_obtained >= (a.max_marks * 0.9) THEN 'Excellent Assignment: ' || a.title
                WHEN psub.marks_obtained >= (p.max_marks * 0.9) THEN 'Excellent Project: ' || p.title
            END as achievement,
            CASE 
                WHEN asub.marks_obtained >= (a.max_marks * 0.9) THEN asub.graded_at
                WHEN psub.marks_obtained >= (p.max_marks * 0.9) THEN psub.graded_at
            END as date
        FROM assignment_submissions asub
        JOIN assignments a ON asub.assignment_id = a.id
        LEFT JOIN project_submissions psub ON 1=0
        LEFT JOIN projects p ON 1=0
        WHERE asub.student_id = ? AND asub.marks_obtained >= (a.max_marks * 0.9)
        
        ORDER BY date DESC
        LIMIT 5
    '''
    
    achievements_df = pd.read_sql_query(achievements_query, conn, 
                                      params=(st.session_state.user_id, st.session_state.user_id))
    
    if not achievements_df.empty:
        for _, achievement in achievements_df.iterrows():
            if achievement['achievement']:  # Skip null achievements
                icon = "🎓" if achievement['type'] == 'Certificate' else "🏆"
                st.write(f"{icon} **{achievement['achievement']}** - {format_date(achievement['date'])}")
    else:
        st.info("No recent achievements to display")
    
    conn.close()

def edit_profile():
    """Edit profile form"""
    st.subheader("✏️ Edit Profile")
    
    with st.form("edit_profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_full_name = st.text_input("Full Name", value=st.session_state.full_name)
            new_email = st.text_input("Email", value=st.session_state.email)
        
        with col2:
            # Get available departments
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM departments ORDER BY name")
            departments = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if st.session_state.department in departments:
                dept_index = departments.index(st.session_state.department)
            else:
                dept_index = 0
            
            new_department = st.selectbox("Department", departments, index=dept_index)
        
        # Password change section
        st.markdown("### 🔒 Change Password")
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        submit_button = st.form_submit_button("💾 Update Profile")
        
        if submit_button:
            # Validate password change if provided
            password_change_valid = True
            if current_password or new_password or confirm_password:
                if not (current_password and new_password and confirm_password):
                    st.error("⚠️ Please fill in all password fields to change password")
                    password_change_valid = False
                elif new_password != confirm_password:
                    st.error("⚠️ New passwords do not match")
                    password_change_valid = False
                else:
                    # Verify current password
                    from database import hash_password
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT password FROM users WHERE id = ?", (st.session_state.user_id,))
                    stored_password = cursor.fetchone()[0]
                    conn.close()
                    
                    if hash_password(current_password) != stored_password:
                        st.error("⚠️ Current password is incorrect")
                        password_change_valid = False
            
            if password_change_valid:
                if update_student_profile(st.session_state.user_id, new_full_name, new_email, 
                                        new_department, new_password if new_password else None):
                    st.success("✅ Profile updated successfully!")
                    
                    # Update session state
                    st.session_state.full_name = new_full_name
                    st.session_state.email = new_email
                    st.session_state.department = new_department
                    
                    st.rerun()
                else:
                    st.error("❌ Failed to update profile")

def show_contact_info():
    """Show contact information and support"""
    st.subheader("📧 Contact Information & Support")
    
    # Contact information
    st.write("### 📞 Contact Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Academic Office:**")
        st.write("📧 academic@acadboost.com")
        st.write("📞 +1 (555) 123-4567")
        st.write("🕒 Mon-Fri: 9:00 AM - 5:00 PM")
        
        st.write("**Technical Support:**")
        st.write("📧 support@acadboost.com")
        st.write("📞 +1 (555) 123-4568")
        st.write("🕒 24/7 Support Available")
    
    with col2:
        st.write("**Department Contact:**")
        
        # Get department head info
        conn = get_db_connection()
        
        query = '''
            SELECT u.full_name, u.email
            FROM departments d
            JOIN users u ON d.head_id = u.id
            WHERE d.name = ?
        '''
        
        df = pd.read_sql_query(query, conn, params=(st.session_state.department,))
        
        if not df.empty:
            head_info = df.iloc[0]
            st.write(f"**Department Head:** {head_info['full_name']}")
            st.write(f"**Email:** {head_info['email']}")
        else:
            st.write("**Department Head:** Not assigned")
        
        conn.close()
    
    st.markdown("---")
    
    # Quick support form
    st.write("### 💬 Quick Support Request")
    
    with st.form("support_request_form"):
        support_type = st.selectbox("Request Type", 
                                  ["Academic Query", "Technical Issue", "Account Problem", "General Inquiry"])
        
        subject = st.text_input("Subject")
        message = st.text_area("Message", height=100)
        
        if st.form_submit_button("📤 Send Request"):
            if subject and message:
                # Create notification for admin
                create_notification(
                    1,  # Assuming admin user ID is 1
                    f"Support Request: {support_type}",
                    f"From: {st.session_state.full_name} ({st.session_state.email})\nSubject: {subject}\nMessage: {message}",
                    "info"
                )
                
                st.success("✅ Support request sent successfully!")
                st.info("You will receive a response within 24 hours.")
            else:
                st.error("⚠️ Please fill in all fields")

# Helper functions for student module

def submit_assignment_record(assignment_id, student_id, submission_text, file_name, file_path):
    """Submit assignment record to database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO assignment_submissions 
            (assignment_id, student_id, submission_text, file_name, file_path)
            VALUES (?, ?, ?, ?, ?)
        ''', (assignment_id, student_id, submission_text, file_name, file_path))
        
        conn.commit()
        conn.close()
        return True
    except:
        return False

def submit_project_record(project_id, student_id, title, description, file_name, file_path, github_url):
    """Submit project record to database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO project_submissions 
            (project_id, student_id, title, description, file_name, file_path, github_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (project_id, student_id, title, description, file_name, file_path, github_url))
        
        conn.commit()
        conn.close()
        return True
    except:
        return False

def send_submission_notification(item_id, student_id, item_type):
    """Send notification to teacher about new submission"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if item_type == "assignment":
        cursor.execute('''
            SELECT a.title, a.teacher_id, u.full_name as student_name
            FROM assignments a
            JOIN users u ON u.id = ?
            WHERE a.id = ?
        ''', (student_id, item_id))
    else:  # project
        cursor.execute('''
            SELECT p.title, p.teacher_id, u.full_name as student_name
            FROM projects p
            JOIN users u ON u.id = ?
            WHERE p.id = ?
        ''', (student_id, item_id))
    
    result = cursor.fetchone()
    
    if result:
        title, teacher_id, student_name = result
        create_notification(
            teacher_id,
            f"New {item_type.title()} Submission",
            f"{student_name} has submitted {item_type}: {title}",
            "info"
        )
    
    conn.close()

def calculate_gpa(marks_list):
    """Calculate GPA from marks list"""
    if not marks_list:
        return 0.0
    
    gpa_points = []
    for mark in marks_list:
        if pd.notna(mark):
            if mark >= 90:
                gpa_points.append(4.0)
            elif mark >= 80:
                gpa_points.append(3.5)
            elif mark >= 70:
                gpa_points.append(3.0)
            elif mark >= 60:
                gpa_points.append(2.5)
            elif mark >= 50:
                gpa_points.append(2.0)
            elif mark >= 40:
                gpa_points.append(1.5)
            else:
                gpa_points.append(0.0)
    
    return sum(gpa_points) / len(gpa_points) if gpa_points else 0.0

def update_student_profile(user_id, full_name, email, department, new_password=None):
    """Update student profile"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if new_password:
            from database import hash_password
            hashed_password = hash_password(new_password)
            cursor.execute('''
                UPDATE users 
                SET full_name = ?, email = ?, department = ?, password = ?
                WHERE id = ?
            ''', (full_name, email, department, hashed_password, user_id))
        else:
            cursor.execute('''
                UPDATE users 
                SET full_name = ?, email = ?, department = ?
                WHERE id = ?
            ''', (full_name, email, department, user_id))
        
        conn.commit()
        conn.close()
        return True
    except:
        return False
