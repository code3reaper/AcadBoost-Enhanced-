import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import sqlite3
from database import get_db_connection
from io import BytesIO
import base64
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
import uuid

def create_notification(user_id, title, message, type_='info'):
    """Create a notification for a user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO notifications (user_id, title, message, type)
        VALUES (?, ?, ?, ?)
    ''', (user_id, title, message, type_))
    
    conn.commit()
    conn.close()

def get_user_notifications(user_id, limit=10):
    """Get notifications for a user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM notifications 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT ?
    ''', (user_id, limit))
    
    notifications = cursor.fetchall()
    conn.close()
    return notifications

def mark_notification_read(notification_id):
    """Mark a notification as read"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE notifications 
        SET is_read = 1 
        WHERE id = ?
    ''', (notification_id,))
    
    conn.commit()
    conn.close()

def create_performance_chart(data, title, x_col, y_col, chart_type='bar'):
    """Create performance charts using Plotly"""
    if data.empty:
        st.warning("No data available for chart")
        return None
    
    fig = None
    
    if chart_type == 'bar':
        fig = px.bar(data, x=x_col, y=y_col, title=title)
    elif chart_type == 'line':
        fig = px.line(data, x=x_col, y=y_col, title=title)
    elif chart_type == 'pie':
        fig = px.pie(data, values=y_col, names=x_col, title=title)
    elif chart_type == 'scatter':
        fig = px.scatter(data, x=x_col, y=y_col, title=title)
    else:
        # Default to bar chart
        fig = px.bar(data, x=x_col, y=y_col, title=title)
    
    if fig:
        fig.update_layout(
            showlegend=True,
            height=400,
            margin=dict(l=0, r=0, t=50, b=0)
        )
    
    return fig

def calculate_grade(marks):
    """Calculate grade based on marks"""
    if marks >= 90:
        return 'A+'
    elif marks >= 80:
        return 'A'
    elif marks >= 70:
        return 'B+'
    elif marks >= 60:
        return 'B'
    elif marks >= 50:
        return 'C'
    elif marks >= 40:
        return 'D'
    else:
        return 'F'

def get_grade_color(grade):
    """Get color for grade display"""
    colors = {
        'A+': '#28a745',
        'A': '#28a745', 
        'B+': '#ffc107',
        'B': '#ffc107',
        'C': '#fd7e14',
        'D': '#dc3545',
        'F': '#dc3545'
    }
    return colors.get(grade, '#6c757d')

def format_date(date_str):
    """Format date string for display"""
    if not date_str:
        return 'N/A'
    try:
        if isinstance(date_str, str):
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        else:
            date_obj = date_str
        return date_obj.strftime('%B %d, %Y')
    except:
        return str(date_str)

def create_attendance_chart(student_id, subject_id=None):
    """Create attendance visualization"""
    conn = get_db_connection()
    
    if subject_id:
        query = '''
            SELECT date, status, s.name as subject
            FROM attendance a
            JOIN subjects s ON a.subject_id = s.id
            WHERE a.student_id = ? AND a.subject_id = ?
            ORDER BY date DESC
            LIMIT 30
        '''
        df = pd.read_sql_query(query, conn, params=(student_id, subject_id))
    else:
        query = '''
            SELECT date, status, s.name as subject
            FROM attendance a
            JOIN subjects s ON a.subject_id = s.id
            WHERE a.student_id = ?
            ORDER BY date DESC
            LIMIT 30
        '''
        df = pd.read_sql_query(query, conn, params=(student_id,))
    
    conn.close()
    
    if df.empty:
        return None
    
    # Calculate attendance percentage
    attendance_counts = df['status'].value_counts()
    present_count = attendance_counts.get('present', 0)
    total_count = len(df)
    attendance_percentage = (present_count / total_count) * 100 if total_count > 0 else 0
    
    # Create pie chart
    fig = px.pie(
        values=[attendance_counts.get('present', 0), 
                attendance_counts.get('absent', 0), 
                attendance_counts.get('late', 0)],
        names=['Present', 'Absent', 'Late'],
        title=f'Attendance Distribution ({attendance_percentage:.1f}% Present)',
        color_discrete_map={
            'Present': '#28a745',
            'Absent': '#dc3545', 
            'Late': '#ffc107'
        }
    )
    
    return fig

def export_to_csv(data, filename):
    """Export data to CSV"""
    csv = data.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}.csv">Download CSV</a>'
    return href

def generate_certificate_pdf(student_name, certificate_type, course_name, issue_date, certificate_id):
    """Generate PDF certificate"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1,  # Center alignment
        textColor=colors.darkblue
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=18,
        spaceAfter=20,
        alignment=1,
        textColor=colors.darkgreen
    )
    
    content_style = ParagraphStyle(
        'Content',
        parent=styles['Normal'],
        fontSize=14,
        spaceAfter=12,
        alignment=1
    )
    
    # Certificate content
    story = []
    
    # Header
    story.append(Paragraph("🎓 AcadBoost Academic Management System", title_style))
    story.append(Spacer(1, 20))
    
    # Certificate title
    story.append(Paragraph(f"Certificate of {certificate_type}", subtitle_style))
    story.append(Spacer(1, 30))
    
    # Main content
    story.append(Paragraph("This is to certify that", content_style))
    story.append(Spacer(1, 10))
    
    name_style = ParagraphStyle(
        'StudentName',
        parent=styles['Normal'],
        fontSize=20,
        spaceAfter=20,
        alignment=1,
        textColor=colors.darkblue,
        fontName='Helvetica-Bold'
    )
    story.append(Paragraph(student_name, name_style))
    
    story.append(Paragraph(f"has successfully completed the course", content_style))
    story.append(Spacer(1, 10))
    
    course_style = ParagraphStyle(
        'CourseName',
        parent=styles['Normal'],
        fontSize=16,
        spaceAfter=30,
        alignment=1,
        textColor=colors.darkgreen,
        fontName='Helvetica-Bold'
    )
    story.append(Paragraph(course_name, course_style))
    
    story.append(Paragraph(f"Issue Date: {issue_date}", content_style))
    story.append(Paragraph(f"Certificate ID: {certificate_id}", content_style))
    story.append(Spacer(1, 40))
    
    # Footer
    story.append(Paragraph("AcadBoost Administration", content_style))
    story.append(Paragraph("Digitally Generated Certificate", content_style))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

def validate_file_upload(uploaded_file, allowed_types, max_size_mb=10):
    """Validate uploaded file"""
    if uploaded_file is None:
        return False, "No file uploaded"
    
    # Check file type
    file_type = uploaded_file.type
    if file_type not in allowed_types:
        return False, f"File type {file_type} not allowed. Allowed types: {', '.join(allowed_types)}"
    
    # Check file size
    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        return False, f"File size {file_size_mb:.1f}MB exceeds maximum allowed size of {max_size_mb}MB"
    
    return True, "File validation passed"

def save_uploaded_file(uploaded_file, folder="uploads"):
    """Save uploaded file and return file path"""
    import os
    
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    file_path = os.path.join(folder, f"{uuid.uuid4()}_{uploaded_file.name}")
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return file_path

def get_dashboard_stats(user_role, user_id):
    """Get dashboard statistics based on user role"""
    conn = get_db_connection()
    stats = {}
    
    if user_role == 'admin':
        # Admin stats
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
        stats['total_students'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'teacher'")
        stats['total_teachers'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM departments")
        stats['total_departments'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM subjects")
        stats['total_subjects'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM assignments WHERE is_active = 1")
        stats['active_assignments'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM projects WHERE status = 'active'")
        stats['active_projects'] = cursor.fetchone()[0]
        
    elif user_role == 'teacher':
        # Teacher stats
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM subjects WHERE teacher_id = ?", (user_id,))
        stats['my_subjects'] = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(DISTINCT e.student_id) 
            FROM enrollments e 
            JOIN subjects s ON e.subject_id = s.id 
            WHERE s.teacher_id = ?
        ''', (user_id,))
        stats['my_students'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM assignments WHERE teacher_id = ? AND is_active = 1", (user_id,))
        stats['my_assignments'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM projects WHERE teacher_id = ? AND status = 'active'", (user_id,))
        stats['my_projects'] = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM assignment_submissions asub
            JOIN assignments a ON asub.assignment_id = a.id
            WHERE a.teacher_id = ? AND asub.marks_obtained IS NULL
        ''', (user_id,))
        stats['pending_grading'] = cursor.fetchone()[0]
        
    elif user_role == 'student':
        # Student stats
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM enrollments WHERE student_id = ?", (user_id,))
        stats['enrolled_subjects'] = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM assignment_submissions 
            WHERE student_id = ?
        ''', (user_id,))
        stats['submitted_assignments'] = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM project_submissions 
            WHERE student_id = ?
        ''', (user_id,))
        stats['submitted_projects'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM certificates WHERE student_id = ?", (user_id,))
        stats['certificates_earned'] = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT AVG(attendance_percentage) FROM results 
            WHERE student_id = ?
        ''', (user_id,))
        result = cursor.fetchone()[0]
        stats['avg_attendance'] = round(result if result else 0, 1)
        
        cursor.execute('''
            SELECT AVG(total_marks) FROM results 
            WHERE student_id = ?
        ''', (user_id,))
        result = cursor.fetchone()[0]
        stats['avg_marks'] = round(result if result else 0, 1)
    
    conn.close()
    return stats

def show_notifications_sidebar():
    """Show notifications in sidebar"""
    with st.sidebar:
        st.markdown("### 🔔 Notifications")
        
        notifications = get_user_notifications(st.session_state.user_id, limit=5)
        
        if notifications:
            for notif in notifications:
                with st.container():
                    status_icon = "🔴" if not notif['is_read'] else "✅"
                    st.markdown(f"{status_icon} **{notif['title']}**")
                    st.caption(notif['message'])
                    
                    if not notif['is_read']:
                        if st.button(f"Mark Read", key=f"read_{notif['id']}", type="secondary"):
                            mark_notification_read(notif['id'])
                            st.rerun()
                    
                    st.markdown("---")
        else:
            st.info("No new notifications")
