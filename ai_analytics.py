import os
import json
try:
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
except ImportError:
    genai = None
    types = None
    client = None
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
from database import get_db_connection

# Client initialized above with error handling

def analyze_student_performance(student_id):
    """Analyze individual student performance using AI"""
    try:
        conn = get_db_connection()
        
        # Get student data
        query = '''
            SELECT 
                u.full_name,
                s.name as subject,
                r.total_marks,
                r.attendance_percentage,
                r.grade,
                COUNT(asub.id) as assignments_submitted,
                AVG(asub.marks_obtained) as avg_assignment_marks
            FROM users u
            LEFT JOIN results r ON u.id = r.student_id
            LEFT JOIN subjects s ON r.subject_id = s.id
            LEFT JOIN assignment_submissions asub ON u.id = asub.student_id
            WHERE u.id = ? AND u.role = 'student'
            GROUP BY u.id, s.id
        '''
        
        df = pd.read_sql_query(query, conn, params=(student_id,))
        conn.close()
        
        if df.empty:
            return "No performance data available for analysis."
        
        # Prepare data for AI analysis
        performance_data = df.to_dict('records')
        
        prompt = f"""
        Analyze the following student performance data and provide insights:
        
        Student Data: {json.dumps(performance_data, default=str)}
        
        Please provide:
        1. Overall performance assessment
        2. Strengths and weaknesses
        3. Specific recommendations for improvement
        4. Risk factors (if any)
        5. Predicted performance trends
        
        Format the response in a clear, structured manner.
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        return response.text if response.text else "Unable to generate analysis."
        
    except Exception as e:
        return f"Error analyzing performance: {str(e)}"

def predict_student_outcomes(student_ids=None):
    """Predict student outcomes based on current performance"""
    try:
        conn = get_db_connection()
        
        if student_ids:
            placeholders = ','.join(['?' for _ in student_ids])
            query = f'''
                SELECT 
                    u.id,
                    u.full_name,
                    AVG(r.total_marks) as avg_marks,
                    AVG(r.attendance_percentage) as avg_attendance,
                    COUNT(DISTINCT r.subject_id) as subjects_enrolled,
                    COUNT(asub.id) as total_assignments
                FROM users u
                LEFT JOIN results r ON u.id = r.student_id
                LEFT JOIN assignment_submissions asub ON u.id = asub.student_id
                WHERE u.id IN ({placeholders}) AND u.role = 'student'
                GROUP BY u.id
            '''
            df = pd.read_sql_query(query, conn, params=student_ids)
        else:
            query = '''
                SELECT 
                    u.id,
                    u.full_name,
                    AVG(r.total_marks) as avg_marks,
                    AVG(r.attendance_percentage) as avg_attendance,
                    COUNT(DISTINCT r.subject_id) as subjects_enrolled,
                    COUNT(asub.id) as total_assignments
                FROM users u
                LEFT JOIN results r ON u.id = r.student_id
                LEFT JOIN assignment_submissions asub ON u.id = asub.student_id
                WHERE u.role = 'student'
                GROUP BY u.id
            '''
            df = pd.read_sql_query(query, conn)
        
        conn.close()
        
        if df.empty:
            return "No student data available for prediction."
        
        # Prepare data for AI analysis
        students_data = df.to_dict('records')
        
        prompt = f"""
        Based on the following student performance data, predict outcomes and identify at-risk students:
        
        Students Data: {json.dumps(students_data, default=str)}
        
        For each student, provide:
        1. Risk level (Low/Medium/High)
        2. Predicted final performance
        3. Key factors affecting performance
        4. Recommended interventions
        
        Also provide overall class insights and recommendations.
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        return response.text if response.text else "Unable to generate predictions."
        
    except Exception as e:
        return f"Error predicting outcomes: {str(e)}"

def generate_teaching_insights(teacher_id):
    """Generate insights for teachers about their classes"""
    try:
        conn = get_db_connection()
        
        query = '''
            SELECT 
                s.name as subject,
                COUNT(DISTINCT e.student_id) as total_students,
                AVG(r.total_marks) as avg_marks,
                AVG(r.attendance_percentage) as avg_attendance,
                COUNT(a.id) as total_assignments,
                COUNT(asub.id) as submitted_assignments
            FROM subjects s
            LEFT JOIN enrollments e ON s.id = e.subject_id
            LEFT JOIN results r ON s.id = r.subject_id
            LEFT JOIN assignments a ON s.id = a.subject_id
            LEFT JOIN assignment_submissions asub ON a.id = asub.assignment_id
            WHERE s.teacher_id = ?
            GROUP BY s.id
        '''
        
        df = pd.read_sql_query(query, conn, params=(teacher_id,))
        conn.close()
        
        if df.empty:
            return "No teaching data available for analysis."
        
        teaching_data = df.to_dict('records')
        
        prompt = f"""
        Analyze the following teaching performance data and provide insights:
        
        Teaching Data: {json.dumps(teaching_data, default=str)}
        
        Please provide:
        1. Overall class performance analysis
        2. Subject-wise insights
        3. Student engagement metrics
        4. Areas for improvement in teaching methods
        5. Recommendations for better student outcomes
        
        Format the response professionally for an educator.
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        return response.text if response.text else "Unable to generate teaching insights."
        
    except Exception as e:
        return f"Error generating insights: {str(e)}"

def analyze_department_performance(department_name=None):
    """Analyze department-wide performance"""
    try:
        conn = get_db_connection()
        
        if department_name:
            query = '''
                SELECT 
                    d.name as department,
                    COUNT(DISTINCT u.id) as total_students,
                    AVG(r.total_marks) as avg_marks,
                    AVG(r.attendance_percentage) as avg_attendance,
                    COUNT(DISTINCT s.id) as total_subjects,
                    COUNT(DISTINCT t.id) as total_teachers
                FROM departments d
                LEFT JOIN users u ON d.name = u.department AND u.role = 'student'
                LEFT JOIN results r ON u.id = r.student_id
                LEFT JOIN subjects s ON d.id = s.department_id
                LEFT JOIN users t ON d.name = t.department AND t.role = 'teacher'
                WHERE d.name = ?
                GROUP BY d.id
            '''
            df = pd.read_sql_query(query, conn, params=(department_name,))
        else:
            query = '''
                SELECT 
                    d.name as department,
                    COUNT(DISTINCT u.id) as total_students,
                    AVG(r.total_marks) as avg_marks,
                    AVG(r.attendance_percentage) as avg_attendance,
                    COUNT(DISTINCT s.id) as total_subjects,
                    COUNT(DISTINCT t.id) as total_teachers
                FROM departments d
                LEFT JOIN users u ON d.name = u.department AND u.role = 'student'
                LEFT JOIN results r ON u.id = r.student_id
                LEFT JOIN subjects s ON d.id = s.department_id
                LEFT JOIN users t ON d.name = t.department AND t.role = 'teacher'
                GROUP BY d.id
            '''
            df = pd.read_sql_query(query, conn)
        
        conn.close()
        
        if df.empty:
            return "No department data available for analysis."
        
        dept_data = df.to_dict('records')
        
        prompt = f"""
        Analyze the following department performance data:
        
        Department Data: {json.dumps(dept_data, default=str)}
        
        Provide:
        1. Department performance overview
        2. Comparative analysis between departments (if multiple)
        3. Resource utilization insights
        4. Strategic recommendations for department improvement
        5. Faculty and student performance trends
        
        Format as an executive summary for department heads.
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        return response.text if response.text else "Unable to generate department analysis."
        
    except Exception as e:
        return f"Error analyzing department: {str(e)}"

def generate_personalized_recommendations(student_id):
    """Generate personalized learning recommendations"""
    try:
        conn = get_db_connection()
        
        query = '''
            SELECT 
                u.full_name,
                s.name as subject,
                r.total_marks,
                r.attendance_percentage,
                r.grade,
                asub.marks_obtained as assignment_marks,
                a.title as assignment_title
            FROM users u
            LEFT JOIN results r ON u.id = r.student_id
            LEFT JOIN subjects s ON r.subject_id = s.id
            LEFT JOIN assignment_submissions asub ON u.id = asub.student_id
            LEFT JOIN assignments a ON asub.assignment_id = a.id
            WHERE u.id = ? AND u.role = 'student'
        '''
        
        df = pd.read_sql_query(query, conn, params=(student_id,))
        conn.close()
        
        if df.empty:
            return "No data available for generating recommendations."
        
        student_data = df.to_dict('records')
        
        prompt = f"""
        Based on the following student data, generate personalized learning recommendations:
        
        Student Performance Data: {json.dumps(student_data, default=str)}
        
        Provide specific, actionable recommendations including:
        1. Study strategies for weak subjects
        2. Time management suggestions
        3. Resource recommendations (books, online courses, etc.)
        4. Practice exercises and activities
        5. Goal-setting advice
        6. Motivational strategies
        
        Make the recommendations practical and achievable.
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt
        )
        
        return response.text if response.text else "Unable to generate recommendations."
        
    except Exception as e:
        return f"Error generating recommendations: {str(e)}"

def analyze_resume(resume_text):
    """Analyze resume using AI"""
    try:
        prompt = f"""
        As an AI career advisor and resume expert, analyze this resume and provide comprehensive feedback:

        Resume Content:
        {resume_text}

        Please provide detailed analysis covering:

        1. **Overall Assessment (Score out of 10)**
        2. **ATS Optimization (Percentage score)**
        3. **Strengths** - What works well
        4. **Areas for Improvement** - Specific suggestions
        5. **Keyword Analysis** - Missing industry keywords
        6. **Format and Structure** - ATS-friendly recommendations
        7. **Content Quality** - Impact statements and quantifiable achievements
        8. **Professional Recommendations** - Next steps for improvement

        Keep the feedback constructive, specific, and actionable.
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        return response.text or "Unable to analyze resume at this time."
        
    except Exception as e:
        return f"Error analyzing resume: {str(e)}"
