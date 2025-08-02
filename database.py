import sqlite3
import hashlib
from datetime import datetime, date
import os

DB_NAME = "acadboost.db"

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_database():
    """Initialize database with all required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT,
            department TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Departments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            code TEXT UNIQUE NOT NULL,
            head_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (head_id) REFERENCES users (id)
        )
    ''')
    
    # Subjects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT UNIQUE NOT NULL,
            department_id INTEGER,
            teacher_id INTEGER,
            credits INTEGER DEFAULT 3,
            semester INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (department_id) REFERENCES departments (id),
            FOREIGN KEY (teacher_id) REFERENCES users (id)
        )
    ''')
    
    # Student enrollments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject_id INTEGER,
            enrollment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (student_id) REFERENCES users (id),
            FOREIGN KEY (subject_id) REFERENCES subjects (id),
            UNIQUE(student_id, subject_id)
        )
    ''')
    
    # Attendance table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject_id INTEGER,
            date DATE,
            status TEXT CHECK(status IN ('present', 'absent', 'late')),
            marked_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users (id),
            FOREIGN KEY (subject_id) REFERENCES subjects (id),
            FOREIGN KEY (marked_by) REFERENCES users (id),
            UNIQUE(student_id, subject_id, date)
        )
    ''')
    
    # Assignments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            subject_id INTEGER,
            teacher_id INTEGER,
            due_date DATE,
            max_marks INTEGER DEFAULT 100,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (subject_id) REFERENCES subjects (id),
            FOREIGN KEY (teacher_id) REFERENCES users (id)
        )
    ''')
    
    # Assignment submissions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assignment_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assignment_id INTEGER,
            student_id INTEGER,
            submission_text TEXT,
            file_name TEXT,
            file_path TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            marks_obtained INTEGER,
            feedback TEXT,
            graded_by INTEGER,
            graded_at TIMESTAMP,
            FOREIGN KEY (assignment_id) REFERENCES assignments (id),
            FOREIGN KEY (student_id) REFERENCES users (id),
            FOREIGN KEY (graded_by) REFERENCES users (id),
            UNIQUE(assignment_id, student_id)
        )
    ''')
    
    # Projects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            subject_id INTEGER,
            teacher_id INTEGER,
            start_date DATE,
            end_date DATE,
            max_marks INTEGER DEFAULT 100,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subjects (id),
            FOREIGN KEY (teacher_id) REFERENCES users (id)
        )
    ''')
    
    # Project submissions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            student_id INTEGER,
            title TEXT,
            description TEXT,
            file_name TEXT,
            file_path TEXT,
            github_url TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            marks_obtained INTEGER,
            feedback TEXT,
            graded_by INTEGER,
            graded_at TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (id),
            FOREIGN KEY (student_id) REFERENCES users (id),
            FOREIGN KEY (graded_by) REFERENCES users (id),
            UNIQUE(project_id, student_id)
        )
    ''')
    
    # Results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject_id INTEGER,
            semester INTEGER,
            assignment_marks REAL DEFAULT 0,
            project_marks REAL DEFAULT 0,
            attendance_percentage REAL DEFAULT 0,
            exam_marks REAL DEFAULT 0,
            total_marks REAL DEFAULT 0,
            grade TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users (id),
            FOREIGN KEY (subject_id) REFERENCES subjects (id),
            UNIQUE(student_id, subject_id, semester)
        )
    ''')
    
    # Certificates table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            certificate_type TEXT,
            title TEXT NOT NULL,
            description TEXT,
            issue_date DATE,
            certificate_id TEXT UNIQUE,
            file_path TEXT,
            issued_by INTEGER,
            is_verified BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users (id),
            FOREIGN KEY (issued_by) REFERENCES users (id)
        )
    ''')
    
    # Announcements table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            posted_by INTEGER,
            target_role TEXT,
            department_id INTEGER,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (posted_by) REFERENCES users (id),
            FOREIGN KEY (department_id) REFERENCES departments (id)
        )
    ''')
    
    # Notifications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            type TEXT DEFAULT 'info',
            is_read BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Resumes table for resume management
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            title TEXT,
            resume_type TEXT NOT NULL CHECK (resume_type IN ('generated', 'uploaded')),
            resume_data TEXT,
            file_path TEXT,
            ai_analysis TEXT,
            analysis_score REAL,
            ats_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            analyzed_at TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def create_sample_users():
    """Create sample users for testing"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Sample departments
    departments = [
        ('Computer Science & Engineering', 'CSE'),
        ('Information Technology', 'IT'),
        ('Electronics & Communication', 'ECE'),
        ('Mechanical Engineering', 'ME')
    ]
    
    for dept_name, dept_code in departments:
        cursor.execute('''
            INSERT OR IGNORE INTO departments (name, code) VALUES (?, ?)
        ''', (dept_name, dept_code))
    
    # Sample users
    users = [
        # Admin
        ('admin', hash_password('admin123'), 'admin', 'System Administrator', 'admin@acadboost.com', 'Administration'),
        
        # Teachers
        ('teacher1', hash_password('teacher123'), 'teacher', 'Dr. Arvind Upadhyay', 'arvind@acadboost.com', 'Computer Science & Engineering'),
        ('teacher2', hash_password('teacher123'), 'teacher', 'Prof. Sarah Johnson', 'sarah@acadboost.com', 'Information Technology'),
        
        # Students
        ('student1', hash_password('student123'), 'student', 'Pratham Joshi', 'pratham@student.acadboost.com', 'Computer Science & Engineering'),
        ('student2', hash_password('student123'), 'student', 'Prakhar Agrawal', 'prakhar@student.acadboost.com', 'Computer Science & Engineering'),
        ('student3', hash_password('student123'), 'student', 'Alice Smith', 'alice@student.acadboost.com', 'Information Technology'),
    ]
    
    for username, password, role, full_name, email, department in users:
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, password, role, full_name, email, department)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, password, role, full_name, email, department))
    
    # Get department and user IDs
    cursor.execute('SELECT id FROM departments WHERE code = "CSE"')
    cse_dept_id = cursor.fetchone()[0]
    
    cursor.execute('SELECT id FROM departments WHERE code = "IT"')
    it_dept_id = cursor.fetchone()[0]
    
    cursor.execute('SELECT id FROM users WHERE username = "teacher1"')
    teacher1_id = cursor.fetchone()[0]
    
    cursor.execute('SELECT id FROM users WHERE username = "teacher2"')
    teacher2_id = cursor.fetchone()[0]
    
    # Sample subjects
    subjects = [
        ('Data Structures', 'CS201', cse_dept_id, teacher1_id, 4, 3),
        ('Algorithms', 'CS202', cse_dept_id, teacher1_id, 4, 4),
        ('Database Management', 'CS301', cse_dept_id, teacher1_id, 3, 5),
        ('Web Development', 'IT201', it_dept_id, teacher2_id, 3, 3),
        ('Software Engineering', 'IT301', it_dept_id, teacher2_id, 4, 5),
    ]
    
    for name, code, dept_id, teacher_id, credits, semester in subjects:
        cursor.execute('''
            INSERT OR IGNORE INTO subjects (name, code, department_id, teacher_id, credits, semester)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, code, dept_id, teacher_id, credits, semester))
    
    # Sample enrollments
    cursor.execute('SELECT id FROM users WHERE role = "student"')
    student_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute('SELECT id FROM subjects')
    subject_ids = [row[0] for row in cursor.fetchall()]
    
    for student_id in student_ids:
        for subject_id in subject_ids[:3]:  # Enroll each student in first 3 subjects
            cursor.execute('''
                INSERT OR IGNORE INTO enrollments (student_id, subject_id)
                VALUES (?, ?)
            ''', (student_id, subject_id))
    
    # Create sample assignments
    assignments = [
        ('Data Structure Implementation', 'Implement a binary search tree with all operations', 1, teacher1_id, '2024-08-15', 100),
        ('Algorithm Analysis', 'Analyze time complexity of sorting algorithms', 2, teacher1_id, '2024-08-20', 100),
        ('Database Design Project', 'Design a complete database for library management', 3, teacher1_id, '2024-08-25', 150),
        ('Web Development Portfolio', 'Create a responsive portfolio website', 4, teacher2_id, '2024-08-30', 100),
        ('Software Engineering Documentation', 'Complete SRS document for a mobile app', 5, teacher2_id, '2024-09-05', 100),
    ]
    
    for title, desc, subject_id, teacher_id, due_date, max_marks in assignments:
        cursor.execute('''
            INSERT OR IGNORE INTO assignments (title, description, subject_id, teacher_id, due_date, max_marks)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, desc, subject_id, teacher_id, due_date, max_marks))
    
    # Create sample projects
    projects = [
        ('AI Chatbot Development', 'Build an AI-powered chatbot using NLP', 1, teacher1_id, '2024-09-01', '2024-10-15', 200),
        ('Mobile App Development', 'Create a mobile app for student management', 4, teacher2_id, '2024-09-10', '2024-11-01', 250),
        ('Machine Learning Model', 'Train a model for academic performance prediction', 2, teacher1_id, '2024-09-15', '2024-10-30', 300),
    ]
    
    for title, desc, subject_id, teacher_id, start_date, end_date, max_marks in projects:
        cursor.execute('''
            INSERT OR IGNORE INTO projects (title, description, subject_id, teacher_id, start_date, end_date, max_marks)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (title, desc, subject_id, teacher_id, start_date, end_date, max_marks))
    
    # Create sample results
    results = [
        # Student 1 results
        (student_ids[0], 1, 5, 85, 90, 88, 80, 86, 'A'),
        (student_ids[0], 2, 5, 78, 85, 82, 75, 80, 'A'),
        (student_ids[0], 3, 5, 92, 88, 90, 85, 89, 'A'),
        
        # Student 2 results  
        (student_ids[1], 1, 5, 88, 92, 90, 85, 89, 'A'),
        (student_ids[1], 2, 5, 82, 87, 85, 80, 84, 'A'),
        (student_ids[1], 3, 5, 90, 85, 88, 82, 86, 'A'),
        
        # Student 3 results
        (student_ids[2], 4, 5, 87, 89, 88, 84, 87, 'A'),
        (student_ids[2], 5, 5, 85, 91, 88, 86, 88, 'A'),
    ]
    
    for student_id, subject_id, semester, assignment_marks, project_marks, attendance_percentage, exam_marks, total_marks, grade in results:
        cursor.execute('''
            INSERT OR IGNORE INTO results (student_id, subject_id, semester, assignment_marks, project_marks, attendance_percentage, exam_marks, total_marks, grade)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (student_id, subject_id, semester, assignment_marks, project_marks, attendance_percentage, exam_marks, total_marks, grade))
    
    # Create sample attendance records
    from datetime import datetime, timedelta
    base_date = datetime.now() - timedelta(days=30)
    
    for i in range(20):  # 20 days of attendance
        current_date = (base_date + timedelta(days=i)).strftime('%Y-%m-%d')
        
        for student_id in student_ids:
            for subject_id in subject_ids[:3]:
                # 85% attendance rate
                status = 'present' if (i + student_id) % 7 != 0 else 'absent'
                cursor.execute('''
                    INSERT OR IGNORE INTO attendance (student_id, subject_id, date, status, marked_by)
                    VALUES (?, ?, ?, ?, ?)
                ''', (student_id, subject_id, current_date, status, teacher1_id))
    
    # Create sample announcements
    announcements = [
        ('Mid-term Examination Schedule', 'Mid-term exams will be conducted from September 15-25, 2024. Please check your subject-wise schedule on the notice board.', 1, 'student', None),
        ('Faculty Meeting', 'All faculty members are requested to attend the monthly meeting on August 20, 2024, at 2:00 PM in the conference room.', 1, 'teacher', None),
        ('New Course Registration', 'Registration for the next semester courses will begin on August 25, 2024. Students can register through the portal.', 1, 'student', None),
    ]
    
    for title, content, posted_by, target_role, dept_id in announcements:
        cursor.execute('''
            INSERT OR IGNORE INTO announcements (title, content, posted_by, target_role, department_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, content, posted_by, target_role, dept_id))
    
    # Create sample certificates
    certificates = [
        (student_ids[0], 'Achievement', 'Excellence in Data Structures', 'Awarded for outstanding performance in Data Structures course', '2024-07-30', 'CERT-2024-001', 1),
        (student_ids[1], 'Participation', 'Web Development Workshop', 'Successfully completed 40-hour Web Development workshop', '2024-07-29', 'CERT-2024-002', 1),
    ]
    
    for student_id, cert_type, title, description, issue_date, cert_id, issued_by in certificates:
        cursor.execute('''
            INSERT OR IGNORE INTO certificates (student_id, certificate_type, title, description, issue_date, certificate_id, issued_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (student_id, cert_type, title, description, issue_date, cert_id, issued_by))
    
    conn.commit()
    conn.close()

def get_user_by_credentials(username, password, role):
    """Get user by credentials"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    hashed_password = hash_password(password)
    cursor.execute('''
        SELECT * FROM users 
        WHERE username = ? AND password = ? AND role = ? AND is_active = 1
    ''', (username, hashed_password, role))
    
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    """Get user by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user
