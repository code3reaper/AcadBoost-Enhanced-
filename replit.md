# AcadBoost - Academic Management System

## Overview

AcadBoost is a comprehensive academic management system built with Streamlit that serves three main user roles: administrators, teachers, and students. The application provides role-based dashboards with features for user management, academic tracking, AI-powered analytics, and certificate generation. The system uses SQLite for data persistence and integrates with Google's Gemini AI for intelligent insights and recommendations.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Updates (July 31, 2025)

✓ Enhanced login page with improved design and tabbed credential display
✓ Added quick login buttons for instant access to different user roles  
✓ Fixed authentication issues and ensured sample users are always available
✓ Added comprehensive sample data including assignments, projects, results, attendance, announcements, and certificates
✓ Implemented all functional features with no placeholder content
✓ Fixed LSP diagnostics and import issues
✓ Integrated Gemini AI analytics with user-provided API key
✓ Fixed duplicate selectbox errors in teacher portal for attendance marking
✓ Added comprehensive Resume Management System for students with:
  - ATS-friendly resume builder with professional templates
  - Resume upload functionality for existing resumes
  - AI-powered resume analysis and optimization suggestions
  - Resume storage and version history
✓ Created complete VS Code setup guide for local development
✓ Added database table for resume management

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web framework for rapid UI development
- **Multi-page Architecture**: Role-based dashboard modules (admin, teacher, student)
- **Component Structure**: Modular design with separate files for each user role
- **UI Components**: Tab-based navigation within dashboards, sidebar notifications, and interactive charts using Plotly

### Backend Architecture
- **Database Layer**: SQLite database with connection pooling via `database.py`
- **Authentication System**: Session-based authentication with role-based access control
- **Business Logic**: Separated into role-specific modules with shared utilities
- **File Upload Handling**: PDF generation capabilities using ReportLab for certificates and reports

### Data Storage Solutions
- **Primary Database**: SQLite (`acadboost.db`) for core application data
- **Database Schema**: Includes tables for users, departments, subjects, assignments, projects, attendance, results, notifications, and certificates
- **File Storage**: Local file system for uploaded documents and generated PDFs
- **Session Management**: Streamlit's built-in session state for user authentication and data persistence

### Authentication and Authorization
- **Password Security**: SHA-256 hashing for password storage
- **Role-Based Access**: Three-tier role system (admin, teacher, student)
- **Session Management**: Streamlit session state for maintaining user login status
- **Access Control**: Decorator-based role requirements for protected functions

### AI Integration Architecture
- **AI Provider**: Google Gemini API for intelligent analytics
- **Analytics Engine**: Student performance analysis, teaching insights, and personalized recommendations
- **Data Processing**: Conversion of database queries to AI-readable formats for analysis
- **Response Handling**: Structured AI responses integrated into dashboard visualizations

## External Dependencies

### Third-Party Services
- **Google Gemini AI**: API key-based integration for student performance analysis, teaching insights, and personalized recommendations
- **Plotly**: Interactive charting and visualization library for dashboard analytics
- **ReportLab**: PDF generation library for certificates and reports

### Python Libraries
- **Streamlit**: Primary web framework for the application interface
- **pandas**: Data manipulation and analysis for academic records
- **sqlite3**: Database connectivity and operations
- **hashlib**: Password hashing and security functions
- **datetime**: Date and time handling for academic scheduling

### Database Dependencies
- **SQLite**: Embedded database system requiring no external server setup
- **Row Factory**: Configured for dictionary-style database result access
- **Connection Pooling**: Manual connection management through utility functions

### File System Dependencies
- **Local Storage**: PDF generation and file uploads stored in application directory
- **Environment Variables**: Gemini API key configuration through environment variables
- **Static Assets**: CSS styling embedded within application modules