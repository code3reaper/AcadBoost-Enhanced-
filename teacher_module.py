import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import get_db_connection
from utils import (create_performance_chart, get_dashboard_stats, show_notifications_sidebar, 
                   create_notification, calculate_grade, format_date, save_uploaded_file, 
                   validate_file_upload, create_attendance_chart)
from ai_analytics import generate_teaching_insights, analyze_student_performance, generate_personalized_recommendations, predict_student_outcomes
from datetime import datetime, date, timedelta
import os

def teacher_dashboard():
    """Teacher dashboard with full functionality"""
    st.title("👨‍🏫 Teacher Dashboard")
    
    # Show notifications
    show_notifications_sidebar()
    
    # Navigation tabs
    tabs = st.tabs([
        "📊 Overview", 
        "👥 My Students", 
        "📝 Assignments", 
        "🔬 Projects",
        "📋 Attendance",
        "📈 Analytics & Reports"
    ])
    
    with tabs[0]:
        show_teacher_overview()
    
    with tabs[1]:
        show_student_management()
    
    with tabs[2]:
        show_assignment_management()
    
    with tabs[3]:
        show_project_management()
    
    with tabs[4]:
        show_attendance_management()
    
    with tabs[5]:
        show_teacher_analytics()

def show_teacher_overview():
    """Show teacher overview dashboard"""
    st.header("📊 Teaching Overview")
    
    # Get dashboard stats
    stats = get_dashboard_stats('teacher', st.session_state.user_id)
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📖 My Subjects", stats['my_subjects'])
        st.metric("📝 Active Assignments", stats['my_assignments'])
    
    with col2:
        st.metric("👨‍🎓 My Students", stats['my_students'])
        st.metric("🔬 Active Projects", stats['my_projects'])
    
    with col3:
        st.metric("⏳ Pending Grading", stats['pending_grading'])
    
    with col4:
        # Quick actions
        st.markdown("### 🚀 Quick Actions")
        if st.button("➕ Create Assignment", use_container_width=True):
            st.session_state.quick_action = "create_assignment"
            st.rerun()
        
        if st.button("📋 Mark Attendance", use_container_width=True):
            st.session_state.quick_action = "mark_attendance"
            st.rerun()
    
    st.markdown("---")
    
    # Recent activities and subject performance
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📚 My Subjects Performance")
        conn = get_db_connection()
        
        query = '''
            SELECT 
                s.name as subject,
                COUNT(DISTINCT e.student_id) as enrolled_students,
                AVG(r.total_marks) as avg_marks,
                AVG(r.attendance_percentage) as avg_attendance
            FROM subjects s
            LEFT JOIN enrollments e ON s.id = e.subject_id
            LEFT JOIN results r ON s.id = r.subject_id
            WHERE s.teacher_id = ?
            GROUP BY s.id
            ORDER BY avg_marks DESC
        '''
        
        df = pd.read_sql_query(query, conn, params=(st.session_state.user_id,))
        conn.close()
        
        if not df.empty:
            fig = px.bar(df, x='subject', y='avg_marks', 
                        title='Average Performance by Subject',
                        color='avg_marks',
                        color_continuous_scale='viridis')
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No subject data available")
    
    with col2:
        st.subheader("📈 Recent Assignment Submissions")
        conn = get_db_connection()
        
        query = '''
            SELECT 
                a.title as assignment,
                COUNT(asub.id) as submissions,
                COUNT(CASE WHEN asub.marks_obtained IS NOT NULL THEN 1 END) as graded,
                a.due_date
            FROM assignments a
            LEFT JOIN assignment_submissions asub ON a.id = asub.assignment_id
            WHERE a.teacher_id = ? AND a.is_active = 1
            GROUP BY a.id
            ORDER BY a.due_date DESC
            LIMIT 5
        '''
        
        df = pd.read_sql_query(query, conn, params=(st.session_state.user_id,))
        conn.close()
        
        if not df.empty:
            for _, row in df.iterrows():
                with st.container():
                    st.write(f"**{row['assignment']}**")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"📝 Submissions: {row['submissions']}")
                    with col_b:
                        st.write(f"✅ Graded: {row['graded']}")
                    st.write(f"📅 Due: {format_date(row['due_date'])}")
                    st.markdown("---")
        else:
            st.info("No recent assignments")

def show_student_management():
    """Student management for teachers"""
    st.header("👥 My Students")
    
    # Get teacher's subjects and students
    conn = get_db_connection()
    
    # Get subjects taught by this teacher
    subjects_query = '''
        SELECT id, name FROM subjects 
        WHERE teacher_id = ? 
        ORDER BY name
    '''
    subjects_df = pd.read_sql_query(subjects_query, conn, params=(st.session_state.user_id,))
    
    if subjects_df.empty:
        st.info("No subjects assigned to you yet.")
        conn.close()
        return
    
    # Subject filter
    subject_options = {"All Subjects": None}
    subject_options.update({row['name']: row['id'] for _, row in subjects_df.iterrows()})
    selected_subject = st.selectbox("Filter by Subject", list(subject_options.keys()), key="student_mgmt_subject")
    subject_id = subject_options[selected_subject]
    
    # Get students based on filter
    if subject_id:
        students_query = '''
            SELECT DISTINCT
                u.id,
                u.full_name,
                u.email,
                s.name as subject,
                AVG(r.total_marks) as avg_marks,
                AVG(r.attendance_percentage) as avg_attendance,
                COUNT(asub.id) as assignments_submitted
            FROM users u
            JOIN enrollments e ON u.id = e.student_id
            JOIN subjects s ON e.subject_id = s.id
            LEFT JOIN results r ON u.id = r.student_id AND s.id = r.subject_id
            LEFT JOIN assignment_submissions asub ON u.id = asub.student_id
            LEFT JOIN assignments a ON asub.assignment_id = a.id AND a.subject_id = s.id
            WHERE u.role = 'student' AND s.id = ? AND s.teacher_id = ?
            GROUP BY u.id, s.id
            ORDER BY u.full_name
        '''
        df = pd.read_sql_query(students_query, conn, params=(subject_id, st.session_state.user_id))
    else:
        students_query = '''
            SELECT DISTINCT
                u.id,
                u.full_name,
                u.email,
                AVG(r.total_marks) as avg_marks,
                AVG(r.attendance_percentage) as avg_attendance,
                COUNT(DISTINCT asub.id) as assignments_submitted
            FROM users u
            JOIN enrollments e ON u.id = e.student_id
            JOIN subjects s ON e.subject_id = s.id
            LEFT JOIN results r ON u.id = r.student_id
            LEFT JOIN assignment_submissions asub ON u.id = asub.student_id
            LEFT JOIN assignments a ON asub.assignment_id = a.id
            WHERE u.role = 'student' AND s.teacher_id = ?
            GROUP BY u.id
            ORDER BY u.full_name
        '''
        df = pd.read_sql_query(students_query, conn, params=(st.session_state.user_id,))
    
    conn.close()
    
    if not df.empty:
        st.subheader(f"📊 Students Overview ({len(df)} students)")
        
        # Performance summary
        col1, col2, col3 = st.columns(3)
        with col1:
            avg_performance = df['avg_marks'].mean()
            st.metric("📊 Class Average", f"{avg_performance:.1f}%" if pd.notna(avg_performance) else "N/A")
        
        with col2:
            avg_attendance = df['avg_attendance'].mean()
            st.metric("📋 Average Attendance", f"{avg_attendance:.1f}%" if pd.notna(avg_attendance) else "N/A")
        
        with col3:
            total_submissions = df['assignments_submitted'].sum()
            st.metric("📝 Total Submissions", int(total_submissions) if pd.notna(total_submissions) else 0)
        
        st.markdown("---")
        
        # Student list with actions
        for _, student in df.iterrows():
            with st.expander(f"👨‍🎓 {student['full_name']} - {student['email']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Average Marks:** {student['avg_marks']:.1f}%" if pd.notna(student['avg_marks']) else "**Average Marks:** N/A")
                    st.write(f"**Attendance:** {student['avg_attendance']:.1f}%" if pd.notna(student['avg_attendance']) else "**Attendance:** N/A")
                
                with col2:
                    st.write(f"**Assignments Submitted:** {int(student['assignments_submitted']) if pd.notna(student['assignments_submitted']) else 0}")
                    if 'subject' in student and pd.notna(student['subject']):
                        st.write(f"**Subject:** {student['subject']}")
                
                # Action buttons
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    if st.button(f"📊 View Performance", key=f"perf_{student['id']}"):
                        show_student_detailed_performance(student['id'], student['full_name'])
                
                with col_b:
                    if st.button(f"🤖 AI Insights", key=f"ai_{student['id']}"):
                        show_student_ai_insights(student['id'], student['full_name'])
                
                with col_c:
                    if st.button(f"💬 Send Message", key=f"msg_{student['id']}"):
                        show_send_message_form(student['id'], student['full_name'])
    else:
        st.info("No students found for the selected criteria.")

def show_student_detailed_performance(student_id, student_name):
    """Show detailed performance for a specific student"""
    st.subheader(f"📊 Detailed Performance: {student_name}")
    
    conn = get_db_connection()
    
    # Get detailed performance data
    query = '''
        SELECT 
            s.name as subject,
            r.total_marks,
            r.attendance_percentage,
            r.grade,
            r.assignment_marks,
            r.project_marks,
            r.exam_marks
        FROM results r
        JOIN subjects s ON r.subject_id = s.id
        WHERE r.student_id = ? AND s.teacher_id = ?
        ORDER BY s.name
    '''
    
    df = pd.read_sql_query(query, conn, params=(student_id, st.session_state.user_id))
    
    # Get assignment history
    assignments_query = '''
        SELECT 
            a.title,
            a.max_marks,
            asub.marks_obtained,
            asub.submitted_at,
            asub.feedback
        FROM assignments a
        LEFT JOIN assignment_submissions asub ON a.id = asub.assignment_id AND asub.student_id = ?
        WHERE a.teacher_id = ?
        ORDER BY a.created_at DESC
    '''
    
    assignments_df = pd.read_sql_query(assignments_query, conn, params=(student_id, st.session_state.user_id))
    conn.close()
    
    if not df.empty:
        # Performance metrics
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(df, x='subject', y='total_marks', 
                        title='Subject-wise Performance',
                        color='total_marks',
                        color_continuous_scale='viridis')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(df, x='subject', y='attendance_percentage', 
                        title='Subject-wise Attendance',
                        color='attendance_percentage',
                        color_continuous_scale='blues')
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed table
        st.subheader("📋 Detailed Results")
        st.dataframe(df, use_container_width=True)
    
    if not assignments_df.empty:
        st.subheader("📝 Assignment History")
        
        for _, assignment in assignments_df.iterrows():
            with st.container():
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**{assignment['title']}**")
                    if pd.notna(assignment['submitted_at']):
                        st.write(f"📅 Submitted: {format_date(assignment['submitted_at'])}")
                    else:
                        st.write("❌ Not submitted")
                
                with col2:
                    if pd.notna(assignment['marks_obtained']):
                        percentage = (assignment['marks_obtained'] / assignment['max_marks']) * 100
                        st.write(f"📊 Score: {assignment['marks_obtained']}/{assignment['max_marks']} ({percentage:.1f}%)")
                    else:
                        st.write(f"📊 Max Marks: {assignment['max_marks']}")
                
                with col3:
                    if pd.notna(assignment['feedback']) and assignment['feedback']:
                        st.write(f"💬 Feedback: {assignment['feedback']}")
                    else:
                        st.write("💬 No feedback yet")
                
                st.markdown("---")

def show_student_ai_insights(student_id, student_name):
    """Show AI insights for a specific student"""
    st.subheader(f"🤖 AI Insights: {student_name}")
    
    if st.button("🔍 Generate AI Analysis"):
        with st.spinner("Analyzing student performance..."):
            # Get AI analysis
            performance_analysis = analyze_student_performance(student_id)
            recommendations = generate_personalized_recommendations(student_id)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📊 Performance Analysis")
                st.write(performance_analysis)
            
            with col2:
                st.markdown("### 💡 Recommendations")
                st.write(recommendations)

def show_send_message_form(student_id, student_name):
    """Show form to send message to student"""
    st.subheader(f"💬 Send Message to {student_name}")
    
    with st.form(f"message_form_{student_id}"):
        message_title = st.text_input("Message Title")
        message_content = st.text_area("Message Content", height=100)
        message_type = st.selectbox("Message Type", ["info", "warning", "success"])
        
        if st.form_submit_button("📤 Send Message"):
            if message_title and message_content:
                create_notification(student_id, message_title, message_content, message_type)
                st.success("✅ Message sent successfully!")
            else:
                st.error("⚠️ Please fill in all fields")

def show_assignment_management():
    """Assignment management for teachers"""
    st.header("📝 Assignment Management")
    
    assignment_tabs = st.tabs(["📋 View Assignments", "➕ Create Assignment", "✏️ Grade Submissions"])
    
    with assignment_tabs[0]:
        show_assignments_list()
    
    with assignment_tabs[1]:
        create_new_assignment()
    
    with assignment_tabs[2]:
        grade_assignment_submissions()

def show_assignments_list():
    """Show all assignments created by teacher"""
    st.subheader("📋 My Assignments")
    
    conn = get_db_connection()
    
    query = '''
        SELECT 
            a.id,
            a.title,
            s.name as subject,
            a.due_date,
            a.max_marks,
            a.is_active,
            COUNT(asub.id) as submissions,
            COUNT(CASE WHEN asub.marks_obtained IS NOT NULL THEN 1 END) as graded
        FROM assignments a
        JOIN subjects s ON a.subject_id = s.id
        LEFT JOIN assignment_submissions asub ON a.id = asub.assignment_id
        WHERE a.teacher_id = ?
        GROUP BY a.id
        ORDER BY a.created_at DESC
    '''
    
    df = pd.read_sql_query(query, conn, params=(st.session_state.user_id,))
    conn.close()
    
    if not df.empty:
        for _, assignment in df.iterrows():
            with st.expander(f"📝 {assignment['title']} - {assignment['subject']}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Due Date:** {format_date(assignment['due_date'])}")
                    st.write(f"**Max Marks:** {assignment['max_marks']}")
                
                with col2:
                    st.write(f"**Submissions:** {assignment['submissions']}")
                    st.write(f"**Graded:** {assignment['graded']}")
                
                with col3:
                    status = "🟢 Active" if assignment['is_active'] else "🔴 Inactive"
                    st.write(f"**Status:** {status}")
                
                # Action buttons
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    if st.button(f"👀 View Submissions", key=f"view_{assignment['id']}"):
                        show_assignment_submissions(assignment['id'], assignment['title'])
                
                with col_b:
                    if st.button(f"✏️ Edit", key=f"edit_{assignment['id']}"):
                        edit_assignment(assignment['id'])
                
                with col_c:
                    action_text = "Deactivate" if assignment['is_active'] else "Activate"
                    if st.button(f"{action_text}", key=f"toggle_{assignment['id']}"):
                        toggle_assignment_status(assignment['id'], not assignment['is_active'])
                        st.rerun()
    else:
        st.info("No assignments created yet.")

def create_new_assignment():
    """Create new assignment"""
    st.subheader("➕ Create New Assignment")
    
    # Get teacher's subjects
    conn = get_db_connection()
    subjects_query = "SELECT id, name FROM subjects WHERE teacher_id = ? ORDER BY name"
    subjects_df = pd.read_sql_query(subjects_query, conn, params=(st.session_state.user_id,))
    conn.close()
    
    if subjects_df.empty:
        st.warning("No subjects assigned to you. Please contact admin to assign subjects.")
        return
    
    with st.form("create_assignment_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Assignment Title*")
            subject_options = {row['name']: row['id'] for _, row in subjects_df.iterrows()}
            selected_subject = st.selectbox("Subject*", list(subject_options.keys()))
            subject_id = subject_options[selected_subject]
        
        with col2:
            due_date = st.date_input("Due Date*", min_value=date.today())
            max_marks = st.number_input("Maximum Marks*", min_value=1, max_value=1000, value=100)
        
        description = st.text_area("Assignment Description", height=100)
        
        # File upload for assignment materials
        st.write("📎 **Assignment Materials (Optional)**")
        uploaded_file = st.file_uploader(
            "Upload assignment files/instructions",
            type=['pdf', 'doc', 'docx', 'txt', 'ppt', 'pptx'],
            help="Upload any supporting materials for the assignment"
        )
        
        submit_button = st.form_submit_button("📝 Create Assignment")
        
        if submit_button:
            if title and selected_subject and due_date:
                file_path = None
                if uploaded_file:
                    # Validate and save file
                    is_valid, message = validate_file_upload(
                        uploaded_file, 
                        ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                         'text/plain', 'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation'],
                        max_size_mb=10
                    )
                    
                    if is_valid:
                        file_path = save_uploaded_file(uploaded_file, "assignment_materials")
                    else:
                        st.error(f"File upload error: {message}")
                        return
                
                if create_assignment(title, description, subject_id, st.session_state.user_id, 
                                   due_date, max_marks, file_path):
                    st.success("✅ Assignment created successfully!")
                    
                    # Send notifications to enrolled students
                    send_assignment_notifications(subject_id, title, due_date)
                else:
                    st.error("❌ Failed to create assignment.")
            else:
                st.error("⚠️ Please fill in all required fields marked with *")

def show_assignment_submissions(assignment_id, assignment_title):
    """Show submissions for specific assignment"""
    st.subheader(f"📝 Submissions: {assignment_title}")
    
    conn = get_db_connection()
    
    query = '''
        SELECT 
            u.full_name as student_name,
            asub.submission_text,
            asub.file_name,
            asub.submitted_at,
            asub.marks_obtained,
            asub.feedback,
            asub.graded_at,
            asub.id as submission_id,
            u.id as student_id
        FROM assignment_submissions asub
        JOIN users u ON asub.student_id = u.id
        WHERE asub.assignment_id = ?
        ORDER BY asub.submitted_at DESC
    '''
    
    df = pd.read_sql_query(query, conn, params=(assignment_id,))
    conn.close()
    
    if not df.empty:
        for _, submission in df.iterrows():
            with st.expander(f"👨‍🎓 {submission['student_name']} - {'✅ Graded' if pd.notna(submission['marks_obtained']) else '⏳ Pending'}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Submitted:** {format_date(submission['submitted_at'])}")
                    if submission['submission_text']:
                        st.write("**Text Submission:**")
                        st.write(submission['submission_text'])
                    if submission['file_name']:
                        st.write(f"**File:** {submission['file_name']}")
                
                with col2:
                    if pd.notna(submission['marks_obtained']):
                        st.write(f"**Marks:** {submission['marks_obtained']}")
                        st.write(f"**Graded:** {format_date(submission['graded_at'])}")
                        if submission['feedback']:
                            st.write(f"**Feedback:** {submission['feedback']}")
                    else:
                        st.write("**Status:** Not graded yet")
                
                # Grading form for ungraded submissions
                if pd.isna(submission['marks_obtained']):
                    with st.form(f"grade_form_{submission['submission_id']}"):
                        col_a, col_b = st.columns(2)
                        with col_a:
                            marks = st.number_input("Marks", min_value=0, max_value=1000, key=f"marks_{submission['submission_id']}")
                        with col_b:
                            feedback = st.text_area("Feedback", key=f"feedback_{submission['submission_id']}")
                        
                        if st.form_submit_button("💾 Save Grade"):
                            if grade_submission(submission['submission_id'], marks, feedback, st.session_state.user_id):
                                st.success("✅ Grade saved successfully!")
                                
                                # Send notification to student
                                create_notification(
                                    submission['student_id'],
                                    f"Assignment Graded: {assignment_title}",
                                    f"Your assignment has been graded. Marks: {marks}",
                                    "success"
                                )
                                st.rerun()
                            else:
                                st.error("❌ Failed to save grade.")
    else:
        st.info("No submissions received yet.")

def edit_assignment(assignment_id):
    """Edit existing assignment"""
    st.subheader("✏️ Edit Assignment")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT a.*, s.name as subject_name 
        FROM assignments a 
        JOIN subjects s ON a.subject_id = s.id 
        WHERE a.id = ? AND a.teacher_id = ?
    ''', (assignment_id, st.session_state.user_id))
    
    assignment = cursor.fetchone()
    conn.close()
    
    if assignment:
        with st.form(f"edit_assignment_form_{assignment_id}"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_title = st.text_input("Title", value=assignment['title'])
                new_max_marks = st.number_input("Max Marks", value=assignment['max_marks'], min_value=1)
            
            with col2:
                new_due_date = st.date_input("Due Date", value=datetime.strptime(assignment['due_date'], '%Y-%m-%d').date())
                is_active = st.checkbox("Active", value=bool(assignment['is_active']))
            
            new_description = st.text_area("Description", value=assignment['description'] or "")
            
            if st.form_submit_button("💾 Update Assignment"):
                if update_assignment(assignment_id, new_title, new_description, new_due_date, new_max_marks, is_active):
                    st.success("✅ Assignment updated successfully!")
                else:
                    st.error("❌ Failed to update assignment.")

def grade_assignment_submissions():
    """Grade assignment submissions"""
    st.subheader("✏️ Grade Submissions")
    
    # Get pending submissions
    conn = get_db_connection()
    
    query = '''
        SELECT 
            a.title as assignment_title,
            a.id as assignment_id,
            COUNT(asub.id) as pending_submissions
        FROM assignments a
        LEFT JOIN assignment_submissions asub ON a.id = asub.assignment_id AND asub.marks_obtained IS NULL
        WHERE a.teacher_id = ? AND a.is_active = 1
        GROUP BY a.id
        HAVING pending_submissions > 0
        ORDER BY a.due_date
    '''
    
    df = pd.read_sql_query(query, conn, params=(st.session_state.user_id,))
    conn.close()
    
    if not df.empty:
        st.write("### ⏳ Assignments with Pending Grading")
        
        for _, assignment in df.iterrows():
            if st.button(f"📝 {assignment['assignment_title']} ({assignment['pending_submissions']} pending)", 
                        key=f"grade_btn_{assignment['assignment_id']}"):
                show_assignment_submissions(assignment['assignment_id'], assignment['assignment_title'])
    else:
        st.info("✅ All assignments are graded!")

def show_project_management():
    """Project management for teachers"""
    st.header("🔬 Project Management")
    
    project_tabs = st.tabs(["📋 View Projects", "➕ Create Project", "✏️ Grade Projects"])
    
    with project_tabs[0]:
        show_projects_list()
    
    with project_tabs[1]:
        create_new_project()
    
    with project_tabs[2]:
        grade_project_submissions()

def show_projects_list():
    """Show all projects created by teacher"""
    st.subheader("📋 My Projects")
    
    conn = get_db_connection()
    
    query = '''
        SELECT 
            p.id,
            p.title,
            s.name as subject,
            p.start_date,
            p.end_date,
            p.max_marks,
            p.status,
            COUNT(psub.id) as submissions,
            COUNT(CASE WHEN psub.marks_obtained IS NOT NULL THEN 1 END) as graded
        FROM projects p
        JOIN subjects s ON p.subject_id = s.id
        LEFT JOIN project_submissions psub ON p.id = psub.project_id
        WHERE p.teacher_id = ?
        GROUP BY p.id
        ORDER BY p.created_at DESC
    '''
    
    df = pd.read_sql_query(query, conn, params=(st.session_state.user_id,))
    conn.close()
    
    if not df.empty:
        for _, project in df.iterrows():
            with st.expander(f"🔬 {project['title']} - {project['subject']}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Start Date:** {format_date(project['start_date'])}")
                    st.write(f"**End Date:** {format_date(project['end_date'])}")
                
                with col2:
                    st.write(f"**Max Marks:** {project['max_marks']}")
                    st.write(f"**Status:** {project['status'].title()}")
                
                with col3:
                    st.write(f"**Submissions:** {project['submissions']}")
                    st.write(f"**Graded:** {project['graded']}")
                
                # Action buttons
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    if st.button(f"👀 View Submissions", key=f"view_proj_{project['id']}"):
                        show_project_submissions(project['id'], project['title'])
                
                with col_b:
                    if st.button(f"✏️ Edit", key=f"edit_proj_{project['id']}"):
                        edit_project(project['id'])
                
                with col_c:
                    new_status = "inactive" if project['status'] == "active" else "active"
                    action_text = "Deactivate" if project['status'] == "active" else "Activate"
                    if st.button(f"{action_text}", key=f"toggle_proj_{project['id']}"):
                        toggle_project_status(project['id'], new_status)
                        st.rerun()
    else:
        st.info("No projects created yet.")

def create_new_project():
    """Create new project"""
    st.subheader("➕ Create New Project")
    
    # Get teacher's subjects
    conn = get_db_connection()
    subjects_query = "SELECT id, name FROM subjects WHERE teacher_id = ? ORDER BY name"
    subjects_df = pd.read_sql_query(subjects_query, conn, params=(st.session_state.user_id,))
    conn.close()
    
    if subjects_df.empty:
        st.warning("No subjects assigned to you. Please contact admin to assign subjects.")
        return
    
    with st.form("create_project_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Project Title*")
            subject_options = {row['name']: row['id'] for _, row in subjects_df.iterrows()}
            selected_subject = st.selectbox("Subject*", list(subject_options.keys()))
            subject_id = subject_options[selected_subject]
        
        with col2:
            start_date = st.date_input("Start Date*", value=date.today())
            end_date = st.date_input("End Date*", min_value=date.today())
        
        max_marks = st.number_input("Maximum Marks*", min_value=1, max_value=1000, value=100)
        description = st.text_area("Project Description", height=150)
        
        submit_button = st.form_submit_button("🔬 Create Project")
        
        if submit_button:
            if title and selected_subject and start_date and end_date:
                if end_date >= start_date:
                    if create_project(title, description, subject_id, st.session_state.user_id, 
                                    start_date, end_date, max_marks):
                        st.success("✅ Project created successfully!")
                        
                        # Send notifications to enrolled students
                        send_project_notifications(subject_id, title, end_date)
                    else:
                        st.error("❌ Failed to create project.")
                else:
                    st.error("⚠️ End date must be after start date.")
            else:
                st.error("⚠️ Please fill in all required fields marked with *")

def show_project_submissions(project_id, project_title):
    """Show submissions for specific project"""
    st.subheader(f"🔬 Project Submissions: {project_title}")
    
    conn = get_db_connection()
    
    query = '''
        SELECT 
            u.full_name as student_name,
            psub.title as submission_title,
            psub.description,
            psub.file_name,
            psub.github_url,
            psub.submitted_at,
            psub.marks_obtained,
            psub.feedback,
            psub.graded_at,
            psub.id as submission_id,
            u.id as student_id
        FROM project_submissions psub
        JOIN users u ON psub.student_id = u.id
        WHERE psub.project_id = ?
        ORDER BY psub.submitted_at DESC
    '''
    
    df = pd.read_sql_query(query, conn, params=(project_id,))
    conn.close()
    
    if not df.empty:
        for _, submission in df.iterrows():
            with st.expander(f"👨‍🎓 {submission['student_name']} - {'✅ Graded' if pd.notna(submission['marks_obtained']) else '⏳ Pending'}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Project Title:** {submission['submission_title']}")
                    st.write(f"**Submitted:** {format_date(submission['submitted_at'])}")
                    if submission['description']:
                        st.write("**Description:**")
                        st.write(submission['description'])
                
                with col2:
                    if submission['file_name']:
                        st.write(f"**File:** {submission['file_name']}")
                    if submission['github_url']:
                        st.write(f"**GitHub:** [View Repository]({submission['github_url']})")
                    
                    if pd.notna(submission['marks_obtained']):
                        st.write(f"**Marks:** {submission['marks_obtained']}")
                        st.write(f"**Graded:** {format_date(submission['graded_at'])}")
                        if submission['feedback']:
                            st.write(f"**Feedback:** {submission['feedback']}")
                
                # Grading form for ungraded submissions
                if pd.isna(submission['marks_obtained']):
                    with st.form(f"grade_project_form_{submission['submission_id']}"):
                        col_a, col_b = st.columns(2)
                        with col_a:
                            marks = st.number_input("Marks", min_value=0, max_value=1000, key=f"proj_marks_{submission['submission_id']}")
                        with col_b:
                            feedback = st.text_area("Feedback", key=f"proj_feedback_{submission['submission_id']}")
                        
                        if st.form_submit_button("💾 Save Grade"):
                            if grade_project_submission(submission['submission_id'], marks, feedback, st.session_state.user_id):
                                st.success("✅ Grade saved successfully!")
                                
                                # Send notification to student
                                create_notification(
                                    submission['student_id'],
                                    f"Project Graded: {project_title}",
                                    f"Your project has been graded. Marks: {marks}",
                                    "success"
                                )
                                st.rerun()
                            else:
                                st.error("❌ Failed to save grade.")
    else:
        st.info("No project submissions received yet.")

def edit_project(project_id):
    """Edit existing project"""
    st.subheader("✏️ Edit Project")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.*, s.name as subject_name 
        FROM projects p 
        JOIN subjects s ON p.subject_id = s.id 
        WHERE p.id = ? AND p.teacher_id = ?
    ''', (project_id, st.session_state.user_id))
    
    project = cursor.fetchone()
    conn.close()
    
    if project:
        with st.form(f"edit_project_form_{project_id}"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_title = st.text_input("Title", value=project['title'])
                new_start_date = st.date_input("Start Date", value=datetime.strptime(project['start_date'], '%Y-%m-%d').date())
            
            with col2:
                new_end_date = st.date_input("End Date", value=datetime.strptime(project['end_date'], '%Y-%m-%d').date())
                new_max_marks = st.number_input("Max Marks", value=project['max_marks'], min_value=1)
            
            new_description = st.text_area("Description", value=project['description'] or "")
            status = st.selectbox("Status", ["active", "inactive"], index=0 if project['status'] == 'active' else 1)
            
            if st.form_submit_button("💾 Update Project"):
                if update_project(project_id, new_title, new_description, new_start_date, new_end_date, new_max_marks, status):
                    st.success("✅ Project updated successfully!")
                else:
                    st.error("❌ Failed to update project.")

def grade_project_submissions():
    """Grade project submissions"""
    st.subheader("✏️ Grade Project Submissions")
    
    # Get pending project submissions
    conn = get_db_connection()
    
    query = '''
        SELECT 
            p.title as project_title,
            p.id as project_id,
            COUNT(psub.id) as pending_submissions
        FROM projects p
        LEFT JOIN project_submissions psub ON p.id = psub.project_id AND psub.marks_obtained IS NULL
        WHERE p.teacher_id = ? AND p.status = 'active'
        GROUP BY p.id
        HAVING pending_submissions > 0
        ORDER BY p.end_date
    '''
    
    df = pd.read_sql_query(query, conn, params=(st.session_state.user_id,))
    conn.close()
    
    if not df.empty:
        st.write("### ⏳ Projects with Pending Grading")
        
        for _, project in df.iterrows():
            if st.button(f"🔬 {project['project_title']} ({project['pending_submissions']} pending)", 
                        key=f"grade_proj_btn_{project['project_id']}"):
                show_project_submissions(project['project_id'], project['project_title'])
    else:
        st.info("✅ All project submissions are graded!")

def show_attendance_management():
    """Attendance management for teachers"""
    st.header("📋 Attendance Management")
    
    attendance_tabs = st.tabs(["📊 View Attendance", "✅ Mark Attendance", "📈 Attendance Reports"])
    
    with attendance_tabs[0]:
        show_attendance_overview()
    
    with attendance_tabs[1]:
        mark_attendance()
    
    with attendance_tabs[2]:
        show_attendance_reports()

def show_attendance_overview():
    """Show attendance overview"""
    st.subheader("📊 Attendance Overview")
    
    # Get teacher's subjects
    conn = get_db_connection()
    subjects_query = "SELECT id, name FROM subjects WHERE teacher_id = ? ORDER BY name"
    subjects_df = pd.read_sql_query(subjects_query, conn, params=(st.session_state.user_id,))
    
    if subjects_df.empty:
        st.info("No subjects assigned to you.")
        conn.close()
        return
    
    # Subject filter
    subject_options = {row['name']: row['id'] for _, row in subjects_df.iterrows()}
    selected_subject = st.selectbox("Select Subject", list(subject_options.keys()))
    subject_id = subject_options[selected_subject]
    
    # Get attendance data
    query = '''
        SELECT 
            u.full_name as student_name,
            COUNT(CASE WHEN a.status = 'present' THEN 1 END) as present_count,
            COUNT(CASE WHEN a.status = 'absent' THEN 1 END) as absent_count,
            COUNT(CASE WHEN a.status = 'late' THEN 1 END) as late_count,
            COUNT(*) as total_classes,
            ROUND((COUNT(CASE WHEN a.status = 'present' THEN 1 END) * 100.0 / COUNT(*)), 2) as attendance_percentage
        FROM users u
        JOIN enrollments e ON u.id = e.student_id
        LEFT JOIN attendance a ON u.id = a.student_id AND e.subject_id = a.subject_id
        WHERE u.role = 'student' AND e.subject_id = ?
        GROUP BY u.id
        ORDER BY attendance_percentage DESC
    '''
    
    df = pd.read_sql_query(query, conn, params=(subject_id,))
    conn.close()
    
    if not df.empty:
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_attendance = df['attendance_percentage'].mean()
            st.metric("📊 Class Average", f"{avg_attendance:.1f}%")
        
        with col2:
            total_students = len(df)
            st.metric("👥 Total Students", total_students)
        
        with col3:
            low_attendance = len(df[df['attendance_percentage'] < 75])
            st.metric("⚠️ Low Attendance (<75%)", low_attendance)
        
        # Attendance chart
        fig = px.bar(df, x='student_name', y='attendance_percentage',
                    title=f'Attendance Percentage - {selected_subject}',
                    color='attendance_percentage',
                    color_continuous_scale='RdYlGn')
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed table
        st.subheader("📋 Detailed Attendance")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No attendance data available for this subject.")

def mark_attendance():
    """Mark attendance for students"""
    st.subheader("✅ Mark Attendance")
    
    # Get teacher's subjects
    conn = get_db_connection()
    subjects_query = "SELECT id, name FROM subjects WHERE teacher_id = ? ORDER BY name"
    subjects_df = pd.read_sql_query(subjects_query, conn, params=(st.session_state.user_id,))
    
    if subjects_df.empty:
        st.info("No subjects assigned to you.")
        conn.close()
        return
    
    # Subject and date selection
    col1, col2 = st.columns(2)
    
    with col1:
        subject_options = {row['name']: row['id'] for _, row in subjects_df.iterrows()}
        selected_subject = st.selectbox("Select Subject", list(subject_options.keys()), key="mark_attendance_subject")
        subject_id = subject_options[selected_subject]
    
    with col2:
        attendance_date = st.date_input("Attendance Date", value=date.today(), max_value=date.today(), key="attendance_date_input")
    
    # Get enrolled students
    students_query = '''
        SELECT u.id, u.full_name
        FROM users u
        JOIN enrollments e ON u.id = e.student_id
        WHERE u.role = 'student' AND e.subject_id = ?
        ORDER BY u.full_name
    '''
    
    students_df = pd.read_sql_query(students_query, conn, params=(subject_id,))
    
    # Check if attendance already marked for this date
    existing_query = '''
        SELECT student_id, status 
        FROM attendance 
        WHERE subject_id = ? AND date = ?
    '''
    
    existing_df = pd.read_sql_query(existing_query, conn, params=(subject_id, attendance_date))
    existing_attendance = {row['student_id']: row['status'] for _, row in existing_df.iterrows()}
    
    conn.close()
    
    if not students_df.empty:
        with st.form("attendance_form"):
            st.write(f"**Subject:** {selected_subject}")
            st.write(f"**Date:** {attendance_date}")
            
            if existing_attendance:
                st.warning("⚠️ Attendance already marked for this date. You can update it below.")
            
            attendance_data = {}
            
            for _, student in students_df.iterrows():
                col_name, col_status = st.columns([2, 1])
                
                with col_name:
                    st.write(f"👨‍🎓 {student['full_name']}")
                
                with col_status:
                    current_status = existing_attendance.get(student['id'], 'present')
                    status_options = ['present', 'absent', 'late']
                    default_index = status_options.index(current_status)
                    
                    attendance_data[student['id']] = st.selectbox(
                        "Status",
                        options=status_options,
                        index=default_index,
                        key=f"attendance_{student['id']}",
                        label_visibility="collapsed"
                    )
            
            if st.form_submit_button("💾 Save Attendance"):
                success_count = 0
                for student_id, status in attendance_data.items():
                    if save_attendance(student_id, subject_id, attendance_date, status, st.session_state.user_id):
                        success_count += 1
                
                if success_count == len(attendance_data):
                    st.success("✅ Attendance saved successfully!")
                    
                    # Send notifications to absent students
                    absent_students = [sid for sid, status in attendance_data.items() if status == 'absent']
                    for student_id in absent_students:
                        create_notification(
                            student_id,
                            "Attendance Alert",
                            f"You were marked absent in {selected_subject} on {attendance_date}",
                            "warning"
                        )
                else:
                    st.error("❌ Some attendance records failed to save.")
    else:
        st.info("No students enrolled in this subject.")

def show_attendance_reports():
    """Show attendance reports"""
    st.subheader("📈 Attendance Reports")
    
    # Get teacher's subjects
    conn = get_db_connection()
    subjects_query = "SELECT id, name FROM subjects WHERE teacher_id = ? ORDER BY name"
    subjects_df = pd.read_sql_query(subjects_query, conn, params=(st.session_state.user_id,))
    
    if subjects_df.empty:
        st.info("No subjects assigned to you.")
        conn.close()
        return
    
    # Subject filter
    subject_options = {"All Subjects": None}
    subject_options.update({row['name']: row['id'] for _, row in subjects_df.iterrows()})
    selected_subject = st.selectbox("Select Subject", list(subject_options.keys()))
    subject_id = subject_options[selected_subject]
    
    # Date range filter
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=date.today() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", value=date.today())
    
    # Generate report
    if st.button("📊 Generate Report"):
        if subject_id:
            # Single subject report
            query = '''
                SELECT 
                    u.full_name as student_name,
                    a.date,
                    a.status
                FROM attendance a
                JOIN users u ON a.student_id = u.id
                WHERE a.subject_id = ? AND a.date BETWEEN ? AND ?
                ORDER BY u.full_name, a.date
            '''
            df = pd.read_sql_query(query, conn, params=(subject_id, start_date, end_date))
            
            # Summary statistics
            summary_query = '''
                SELECT 
                    u.full_name as student_name,
                    COUNT(CASE WHEN a.status = 'present' THEN 1 END) as present,
                    COUNT(CASE WHEN a.status = 'absent' THEN 1 END) as absent,
                    COUNT(CASE WHEN a.status = 'late' THEN 1 END) as late,
                    COUNT(*) as total,
                    ROUND((COUNT(CASE WHEN a.status = 'present' THEN 1 END) * 100.0 / COUNT(*)), 2) as percentage
                FROM attendance a
                JOIN users u ON a.student_id = u.id
                WHERE a.subject_id = ? AND a.date BETWEEN ? AND ?
                GROUP BY u.id
                ORDER BY percentage DESC
            '''
            summary_df = pd.read_sql_query(summary_query, conn, params=(subject_id, start_date, end_date))
            
        else:
            # All subjects report
            query = '''
                SELECT 
                    s.name as subject,
                    u.full_name as student_name,
                    a.date,
                    a.status
                FROM attendance a
                JOIN users u ON a.student_id = u.id
                JOIN subjects s ON a.subject_id = s.id
                WHERE s.teacher_id = ? AND a.date BETWEEN ? AND ?
                ORDER BY s.name, u.full_name, a.date
            '''
            df = pd.read_sql_query(query, conn, params=(st.session_state.user_id, start_date, end_date))
            
            # Summary by subject
            summary_query = '''
                SELECT 
                    s.name as subject,
                    COUNT(CASE WHEN a.status = 'present' THEN 1 END) as present,
                    COUNT(CASE WHEN a.status = 'absent' THEN 1 END) as absent,
                    COUNT(CASE WHEN a.status = 'late' THEN 1 END) as late,
                    COUNT(*) as total,
                    ROUND((COUNT(CASE WHEN a.status = 'present' THEN 1 END) * 100.0 / COUNT(*)), 2) as percentage
                FROM attendance a
                JOIN subjects s ON a.subject_id = s.id
                WHERE s.teacher_id = ? AND a.date BETWEEN ? AND ?
                GROUP BY s.id
                ORDER BY percentage DESC
            '''
            summary_df = pd.read_sql_query(summary_query, conn, params=(st.session_state.user_id, start_date, end_date))
        
        if not summary_df.empty:
            st.subheader("📊 Attendance Summary")
            st.dataframe(summary_df, use_container_width=True)
            
            # Visualization
            if subject_id:
                fig = px.bar(summary_df, x='student_name', y='percentage',
                           title='Student Attendance Percentage',
                           color='percentage',
                           color_continuous_scale='RdYlGn')
            else:
                fig = px.bar(summary_df, x='subject', y='percentage',
                           title='Subject-wise Attendance Percentage',
                           color='percentage',
                           color_continuous_scale='RdYlGn')
            
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            
            # Export option
            csv = summary_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Report CSV",
                data=csv,
                file_name=f"attendance_report_{start_date}_{end_date}.csv",
                mime="text/csv"
            )
        else:
            st.info("No attendance data found for the selected criteria.")
    
    conn.close()

def show_teacher_analytics():
    """Show teacher analytics and AI insights"""
    st.header("📈 Analytics & Reports")
    
    analytics_tabs = st.tabs(["📊 Performance Analytics", "🤖 AI Insights", "📋 Custom Reports"])
    
    with analytics_tabs[0]:
        show_teacher_performance_analytics()
    
    with analytics_tabs[1]:
        show_teacher_ai_insights()
    
    with analytics_tabs[2]:
        show_custom_reports()

def show_teacher_performance_analytics():
    """Show teacher performance analytics"""
    st.subheader("📊 Teaching Performance Analytics")
    
    conn = get_db_connection()
    
    # Overall teaching statistics
    stats_query = '''
        SELECT 
            COUNT(DISTINCT s.id) as total_subjects,
            COUNT(DISTINCT e.student_id) as total_students,
            COUNT(DISTINCT a.id) as total_assignments,
            COUNT(DISTINCT p.id) as total_projects,
            AVG(r.total_marks) as avg_student_performance,
            AVG(r.attendance_percentage) as avg_attendance
        FROM subjects s
        LEFT JOIN enrollments e ON s.id = e.subject_id
        LEFT JOIN assignments a ON s.id = a.subject_id
        LEFT JOIN projects p ON s.id = p.subject_id
        LEFT JOIN results r ON s.id = r.subject_id
        WHERE s.teacher_id = ?
    '''
    
    stats_df = pd.read_sql_query(stats_query, conn, params=(st.session_state.user_id,))
    
    if not stats_df.empty and not stats_df.iloc[0].isna().all():
        stats = stats_df.iloc[0]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📚 Subjects", int(stats['total_subjects']) if pd.notna(stats['total_subjects']) else 0)
            st.metric("📝 Assignments", int(stats['total_assignments']) if pd.notna(stats['total_assignments']) else 0)
        
        with col2:
            st.metric("👥 Students", int(stats['total_students']) if pd.notna(stats['total_students']) else 0)
            st.metric("🔬 Projects", int(stats['total_projects']) if pd.notna(stats['total_projects']) else 0)
        
        with col3:
            avg_perf = stats['avg_student_performance']
            st.metric("📊 Avg Performance", f"{avg_perf:.1f}%" if pd.notna(avg_perf) else "N/A")
        
        with col4:
            avg_att = stats['avg_attendance']
            st.metric("📋 Avg Attendance", f"{avg_att:.1f}%" if pd.notna(avg_att) else "N/A")
    
    st.markdown("---")
    
    # Subject-wise performance comparison
    subject_perf_query = '''
        SELECT 
            s.name as subject,
            COUNT(DISTINCT e.student_id) as enrolled_students,
            AVG(r.total_marks) as avg_marks,
            AVG(r.attendance_percentage) as avg_attendance,
            COUNT(a.id) as assignment_count,
            COUNT(p.id) as project_count
        FROM subjects s
        LEFT JOIN enrollments e ON s.id = e.subject_id
        LEFT JOIN results r ON s.id = r.subject_id
        LEFT JOIN assignments a ON s.id = a.subject_id
        LEFT JOIN projects p ON s.id = p.subject_id
        WHERE s.teacher_id = ?
        GROUP BY s.id
        ORDER BY avg_marks DESC
    '''
    
    subject_df = pd.read_sql_query(subject_perf_query, conn, params=(st.session_state.user_id,))
    
    if not subject_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Subject Performance Comparison")
            fig1 = px.bar(subject_df, x='subject', y='avg_marks',
                         title='Average Marks by Subject',
                         color='avg_marks',
                         color_continuous_scale='viridis')
            fig1.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            st.subheader("📋 Subject Attendance Comparison")
            fig2 = px.bar(subject_df, x='subject', y='avg_attendance',
                         title='Average Attendance by Subject',
                         color='avg_attendance',
                         color_continuous_scale='blues')
            fig2.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig2, use_container_width=True)
        
        # Detailed subject table
        st.subheader("📋 Detailed Subject Statistics")
        st.dataframe(subject_df, use_container_width=True)
    
    # Monthly performance trend
    monthly_query = '''
        SELECT 
            strftime('%Y-%m', r.created_at) as month,
            AVG(r.total_marks) as avg_marks,
            AVG(r.attendance_percentage) as avg_attendance,
            COUNT(DISTINCT r.student_id) as student_count
        FROM results r
        JOIN subjects s ON r.subject_id = s.id
        WHERE s.teacher_id = ? AND r.created_at >= date('now', '-12 months')
        GROUP BY strftime('%Y-%m', r.created_at)
        ORDER BY month
    '''
    
    monthly_df = pd.read_sql_query(monthly_query, conn, params=(st.session_state.user_id,))
    
    if not monthly_df.empty:
        st.subheader("📈 Monthly Performance Trend")
        
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=monthly_df['month'], y=monthly_df['avg_marks'],
                                 mode='lines+markers', name='Average Marks',
                                 line=dict(color='blue')))
        fig3.add_trace(go.Scatter(x=monthly_df['month'], y=monthly_df['avg_attendance'],
                                 mode='lines+markers', name='Average Attendance',
                                 line=dict(color='green')))
        
        fig3.update_layout(title='Monthly Performance and Attendance Trend',
                          xaxis_title='Month',
                          yaxis_title='Percentage')
        st.plotly_chart(fig3, use_container_width=True)
    
    conn.close()

def show_teacher_ai_insights():
    """Show AI-powered teaching insights"""
    st.subheader("🤖 AI-Powered Teaching Insights")
    
    if st.button("🔍 Generate Teaching Insights"):
        with st.spinner("Analyzing your teaching performance..."):
            insights = generate_teaching_insights(st.session_state.user_id)
            
            st.markdown("### 📚 Teaching Performance Analysis")
            st.write(insights)
    
    st.markdown("---")
    
    # Subject-specific AI analysis
    st.subheader("📊 Subject-Specific Analysis")
    
    conn = get_db_connection()
    subjects_query = "SELECT id, name FROM subjects WHERE teacher_id = ? ORDER BY name"
    subjects_df = pd.read_sql_query(subjects_query, conn, params=(st.session_state.user_id,))
    conn.close()
    
    if not subjects_df.empty:
        subject_options = {row['name']: row['id'] for _, row in subjects_df.iterrows()}
        selected_subject = st.selectbox("Select Subject for Analysis", list(subject_options.keys()), key="ai_analysis_subject")
        
        if st.button("🤖 Analyze Subject Performance"):
            subject_id = subject_options[selected_subject]
            
            with st.spinner(f"Analyzing {selected_subject} performance..."):
                # Get subject-specific student data
                conn = get_db_connection()
                
                students_query = '''
                    SELECT u.id
                    FROM users u
                    JOIN enrollments e ON u.id = e.student_id
                    WHERE u.role = 'student' AND e.subject_id = ?
                '''
                
                students_df = pd.read_sql_query(students_query, conn, params=(subject_id,))
                student_ids = students_df['id'].tolist()
                conn.close()
                
                if student_ids:
                    # Get AI insights for these students
                    insights = predict_student_outcomes(student_ids)
                    
                    st.markdown(f"### 📊 AI Analysis for {selected_subject}")
                    st.write(insights)
                else:
                    st.info("No students enrolled in this subject.")

def show_custom_reports():
    """Show custom report generation"""
    st.subheader("📋 Custom Report Generation")
    
    report_type = st.selectbox(
        "Select Report Type",
        ["Student Performance Report", "Attendance Summary Report", "Assignment Analysis Report", "Subject Comparison Report"],
        key="custom_report_type"
    )
    
    # Date range selection
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=date.today() - timedelta(days=90), key="report_start_date")
    with col2:
        end_date = st.date_input("End Date", value=date.today(), key="report_end_date")
    
    if st.button("📊 Generate Custom Report"):
        conn = get_db_connection()
        
        if report_type == "Student Performance Report":
            generate_student_performance_report(conn, start_date, end_date)
        elif report_type == "Attendance Summary Report":
            generate_attendance_summary_report(conn, start_date, end_date)
        elif report_type == "Assignment Analysis Report":
            generate_assignment_analysis_report(conn, start_date, end_date)
        elif report_type == "Subject Comparison Report":
            generate_subject_comparison_report(conn, start_date, end_date)
        
        conn.close()

# Helper functions for teacher module

def create_assignment(title, description, subject_id, teacher_id, due_date, max_marks, file_path=None):
    """Create new assignment"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO assignments (title, description, subject_id, teacher_id, due_date, max_marks)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, description, subject_id, teacher_id, due_date, max_marks))
        
        conn.commit()
        conn.close()
        return True
    except:
        return False

def send_assignment_notifications(subject_id, title, due_date):
    """Send notifications to students about new assignment"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT u.id FROM users u
        JOIN enrollments e ON u.id = e.student_id
        WHERE u.role = 'student' AND e.subject_id = ?
    ''', (subject_id,))
    
    students = cursor.fetchall()
    
    for student in students:
        create_notification(
            student[0],
            f"New Assignment: {title}",
            f"A new assignment has been posted. Due date: {due_date}",
            "info"
        )
    
    conn.close()

def grade_submission(submission_id, marks, feedback, graded_by):
    """Grade assignment submission"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE assignment_submissions 
            SET marks_obtained = ?, feedback = ?, graded_by = ?, graded_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (marks, feedback, graded_by, submission_id))
        
        conn.commit()
        conn.close()
        return True
    except:
        return False

def toggle_assignment_status(assignment_id, new_status):
    """Toggle assignment active status"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE assignments SET is_active = ? WHERE id = ?", (new_status, assignment_id))
    
    conn.commit()
    conn.close()

def update_assignment(assignment_id, title, description, due_date, max_marks, is_active):
    """Update assignment"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE assignments 
            SET title = ?, description = ?, due_date = ?, max_marks = ?, is_active = ?
            WHERE id = ?
        ''', (title, description, due_date, max_marks, is_active, assignment_id))
        
        conn.commit()
        conn.close()
        return True
    except:
        return False

def create_project(title, description, subject_id, teacher_id, start_date, end_date, max_marks):
    """Create new project"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO projects (title, description, subject_id, teacher_id, start_date, end_date, max_marks)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (title, description, subject_id, teacher_id, start_date, end_date, max_marks))
        
        conn.commit()
        conn.close()
        return True
    except:
        return False

def send_project_notifications(subject_id, title, end_date):
    """Send notifications to students about new project"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT u.id FROM users u
        JOIN enrollments e ON u.id = e.student_id
        WHERE u.role = 'student' AND e.subject_id = ?
    ''', (subject_id,))
    
    students = cursor.fetchall()
    
    for student in students:
        create_notification(
            student[0],
            f"New Project: {title}",
            f"A new project has been assigned. End date: {end_date}",
            "info"
        )
    
    conn.close()

def grade_project_submission(submission_id, marks, feedback, graded_by):
    """Grade project submission"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE project_submissions 
            SET marks_obtained = ?, feedback = ?, graded_by = ?, graded_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (marks, feedback, graded_by, submission_id))
        
        conn.commit()
        conn.close()
        return True
    except:
        return False

def toggle_project_status(project_id, new_status):
    """Toggle project status"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE projects SET status = ? WHERE id = ?", (new_status, project_id))
    
    conn.commit()
    conn.close()

def update_project(project_id, title, description, start_date, end_date, max_marks, status):
    """Update project"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE projects 
            SET title = ?, description = ?, start_date = ?, end_date = ?, max_marks = ?, status = ?
            WHERE id = ?
        ''', (title, description, start_date, end_date, max_marks, status, project_id))
        
        conn.commit()
        conn.close()
        return True
    except:
        return False

def save_attendance(student_id, subject_id, date, status, marked_by):
    """Save attendance record"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO attendance (student_id, subject_id, date, status, marked_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (student_id, subject_id, date, status, marked_by))
        
        conn.commit()
        conn.close()
        return True
    except:
        return False

def generate_student_performance_report(conn, start_date, end_date):
    """Generate student performance report"""
    query = '''
        SELECT 
            u.full_name as student_name,
            s.name as subject,
            r.total_marks,
            r.attendance_percentage,
            r.grade,
            r.created_at
        FROM results r
        JOIN users u ON r.student_id = u.id
        JOIN subjects s ON r.subject_id = s.id
        WHERE s.teacher_id = ? AND DATE(r.created_at) BETWEEN ? AND ?
        ORDER BY u.full_name, s.name
    '''
    
    df = pd.read_sql_query(query, conn, params=(st.session_state.user_id, start_date, end_date))
    
    if not df.empty:
        st.subheader("📊 Student Performance Report")
        st.dataframe(df, use_container_width=True)
        
        # Summary statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_marks = df['total_marks'].mean()
            st.metric("Average Marks", f"{avg_marks:.1f}%")
        
        with col2:
            avg_attendance = df['attendance_percentage'].mean()
            st.metric("Average Attendance", f"{avg_attendance:.1f}%")
        
        with col3:
            total_students = df['student_name'].nunique()
            st.metric("Total Students", total_students)
        
        # Export option
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Report",
            data=csv,
            file_name=f"student_performance_report_{start_date}_{end_date}.csv",
            mime="text/csv"
        )
    else:
        st.info("No performance data found for the selected period.")

def generate_attendance_summary_report(conn, start_date, end_date):
    """Generate attendance summary report"""
    query = '''
        SELECT 
            s.name as subject,
            u.full_name as student_name,
            COUNT(CASE WHEN a.status = 'present' THEN 1 END) as present_days,
            COUNT(CASE WHEN a.status = 'absent' THEN 1 END) as absent_days,
            COUNT(CASE WHEN a.status = 'late' THEN 1 END) as late_days,
            COUNT(*) as total_days,
            ROUND((COUNT(CASE WHEN a.status = 'present' THEN 1 END) * 100.0 / COUNT(*)), 2) as attendance_percentage
        FROM attendance a
        JOIN users u ON a.student_id = u.id
        JOIN subjects s ON a.subject_id = s.id
        WHERE s.teacher_id = ? AND a.date BETWEEN ? AND ?
        GROUP BY s.id, u.id
        ORDER BY s.name, attendance_percentage DESC
    '''
    
    df = pd.read_sql_query(query, conn, params=(st.session_state.user_id, start_date, end_date))
    
    if not df.empty:
        st.subheader("📋 Attendance Summary Report")
        st.dataframe(df, use_container_width=True)
        
        # Visualization
        fig = px.histogram(df, x='attendance_percentage', nbins=10,
                          title='Attendance Distribution')
        st.plotly_chart(fig, use_container_width=True)
        
        # Export option
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Report",
            data=csv,
            file_name=f"attendance_summary_report_{start_date}_{end_date}.csv",
            mime="text/csv"
        )
    else:
        st.info("No attendance data found for the selected period.")

def generate_assignment_analysis_report(conn, start_date, end_date):
    """Generate assignment analysis report"""
    query = '''
        SELECT 
            a.title as assignment_title,
            s.name as subject,
            a.max_marks,
            COUNT(asub.id) as total_submissions,
            COUNT(CASE WHEN asub.marks_obtained IS NOT NULL THEN 1 END) as graded_submissions,
            AVG(asub.marks_obtained) as avg_marks,
            MIN(asub.marks_obtained) as min_marks,
            MAX(asub.marks_obtained) as max_marks,
            a.due_date
        FROM assignments a
        JOIN subjects s ON a.subject_id = s.id
        LEFT JOIN assignment_submissions asub ON a.id = asub.assignment_id
        WHERE a.teacher_id = ? AND a.created_at BETWEEN ? AND ?
        GROUP BY a.id
        ORDER BY a.due_date DESC
    '''
    
    df = pd.read_sql_query(query, conn, params=(st.session_state.user_id, start_date, end_date))
    
    if not df.empty:
        st.subheader("📝 Assignment Analysis Report")
        st.dataframe(df, use_container_width=True)
        
        # Performance visualization
        fig = px.bar(df, x='assignment_title', y='avg_marks',
                    title='Average Assignment Performance',
                    color='avg_marks',
                    color_continuous_scale='viridis')
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
        
        # Export option
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Report",
            data=csv,
            file_name=f"assignment_analysis_report_{start_date}_{end_date}.csv",
            mime="text/csv"
        )
    else:
        st.info("No assignment data found for the selected period.")

def generate_subject_comparison_report(conn, start_date, end_date):
    """Generate subject comparison report"""
    query = '''
        SELECT 
            s.name as subject,
            COUNT(DISTINCT e.student_id) as enrolled_students,
            AVG(r.total_marks) as avg_marks,
            AVG(r.attendance_percentage) as avg_attendance,
            COUNT(DISTINCT a.id) as total_assignments,
            COUNT(DISTINCT p.id) as total_projects
        FROM subjects s
        LEFT JOIN enrollments e ON s.id = e.subject_id
        LEFT JOIN results r ON s.id = r.subject_id
        LEFT JOIN assignments a ON s.id = a.subject_id
        LEFT JOIN projects p ON s.id = p.subject_id
        WHERE s.teacher_id = ?
        GROUP BY s.id
        ORDER BY avg_marks DESC
    '''
    
    df = pd.read_sql_query(query, conn, params=(st.session_state.user_id,))
    
    if not df.empty:
        st.subheader("📚 Subject Comparison Report")
        st.dataframe(df, use_container_width=True)
        
        # Comparison charts
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = px.bar(df, x='subject', y='avg_marks',
                         title='Average Marks by Subject')
            fig1.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            fig2 = px.bar(df, x='subject', y='enrolled_students',
                         title='Student Enrollment by Subject')
            fig2.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig2, use_container_width=True)
        
        # Export option
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Report",
            data=csv,
            file_name=f"subject_comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No subject data found.")

