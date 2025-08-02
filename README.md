# 🎓 AcadBoost - Academic Management System

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Streamlit-1.47.1+-red.svg" alt="Streamlit">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/AI%20Powered-Gemini-purple.svg" alt="AI Powered">
</div>

<div align="center">
  <h3>🚀 A comprehensive, AI-powered academic management system built with Streamlit</h3>
  <p>Streamline education management with role-based dashboards, intelligent analytics, and automated workflows</p>
</div>

---

## 📋 Table of Contents

- [✨ Features](#-features)
- [🏗️ System Architecture](#️-system-architecture)
- [🚀 Quick Start](#-quick-start)
- [👥 User Roles & Dashboards](#-user-roles--dashboards)
- [🤖 AI-Powered Analytics](#-ai-powered-analytics)
- [📸 Screenshots](#-screenshots)
- [🛠️ Installation](#️-installation)
- [⚙️ Configuration](#️-configuration)
- [🔧 Usage](#-usage)
- [📊 Database Schema](#-database-schema)
- [🔒 Security](#-security)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

## ✨ Features

### 🎯 Core Functionality
- **Multi-Role Authentication** - Secure login system for Admin, Teacher, and Student roles
- **Role-Based Dashboards** - Customized interfaces for each user type
- **Real-time Notifications** - System-wide announcement and alert system
- **Comprehensive Analytics** - Performance tracking with interactive charts
- **AI-Powered Insights** - Intelligent recommendations and predictions

### 📚 Academic Management
- **Student Information System** - Complete student profile management
- **Assignment & Project Tracking** - End-to-end academic work management
- **Attendance Management** - Automated attendance tracking and reporting
- **Grade & Results Management** - Comprehensive grading system with analytics
- **Certificate Generation** - Automated PDF certificate creation
- **Resume Builder** - AI-assisted resume creation and management

### 🔧 Administrative Tools
- **User Management** - Complete CRUD operations for all user types
- **Department Management** - Organizational structure management
- **Bulk Operations** - Efficient mass data import/export
- **System Reports** - Comprehensive reporting and analytics
- **Data Visualization** - Interactive charts and dashboards

## 🏗️ System Architecture

```
AcadBoost/
├── 🎯 Core Application
│   ├── app.py                 # Main Streamlit application
│   ├── auth.py               # Authentication system
│   └── database.py           # Database operations
├── 👥 User Modules
│   ├── admin_module.py       # Administrator dashboard
│   ├── teacher_module.py     # Teacher dashboard
│   └── student_module.py     # Student dashboard
├── 🤖 AI & Analytics
│   ├── ai_analytics.py       # AI-powered insights
│   └── utils.py             # Utility functions
├── 📄 Specialized Features
│   └── resume_module.py      # Resume builder
└── 💾 Data Storage
    ├── acadboost.db         # SQLite database
    ├── uploaded_resumes/    # Resume storage
    └── generated_resumes/   # Generated resume PDFs
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Google Gemini API Key (for AI features)

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/portalsage.git
cd portalsage

# Create virtual environment
python -m venv acadboost_env

# Activate virtual environment
# Windows:
acadboost_env\Scripts\activate
# macOS/Linux:
source acadboost_env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Start the Streamlit application
streamlit run app.py

# Navigate to: http://localhost:8501
```

## 👥 User Roles & Dashboards

### 🏛️ Administrator Dashboard
- **System Overview** - Complete system statistics and health monitoring
- **User Management** - Add, edit, delete users across all roles
- **Department Management** - Organizational structure control
- **Announcements** - System-wide communication management
- **Reports & Analytics** - Comprehensive system reporting
- **Certificate Management** - Certificate template and generation control

**Default Login:** `admin` / `admin123`

### 👨‍🏫 Teacher Dashboard
- **Teaching Overview** - Personal teaching statistics and insights
- **Student Management** - View and manage assigned students
- **Assignment Management** - Create, manage, and grade assignments
- **Project Management** - Oversee student projects and milestones
- **Attendance Management** - Mark and track student attendance
- **Analytics & Reports** - Teaching performance and student insights

**Default Login:** `teacher1` / `teacher123`

### 👨‍🎓 Student Dashboard
- **Academic Overview** - Personal academic performance summary
- **Assignments** - View, submit, and track assignment progress
- **Projects** - Manage personal and group projects
- **Attendance** - View attendance records and patterns
- **Results & Analytics** - Academic performance analysis
- **Resume Builder** - AI-assisted resume creation and management
- **Certificates** - View and download earned certificates
- **Profile Management** - Personal information and preferences

**Default Login:** `student1` / `student123`

## 🤖 AI-Powered Analytics

### 🧠 Intelligent Features
- **Performance Prediction** - Predict student outcomes using historical data
- **Personalized Recommendations** - AI-generated study and improvement suggestions
- **Department Analytics** - AI-driven departmental performance analysis
- **Teaching Insights** - Intelligent teaching strategy recommendations
- **Automated Reporting** - AI-generated comprehensive reports

### 🔮 Predictive Analytics
- Student performance forecasting
- Attendance pattern analysis
- Risk identification and early warning systems
- Learning outcome predictions

## 📸 Screenshots

*Coming Soon - Application screenshots will be added here*

## 🛠️ Installation

### Option 1: Using uv (Recommended)
```bash
# Install uv package manager
pip install uv

# Create and activate virtual environment
uv venv acadboost_env
source acadboost_env/bin/activate  # Linux/macOS
# or
acadboost_env\Scripts\activate     # Windows

# Install dependencies
uv pip install -r requirements.txt
```

### Option 2: Traditional pip
```bash
# Create virtual environment
python -m venv acadboost_env
source acadboost_env/bin/activate  # Linux/macOS
# or
acadboost_env\Scripts\activate     # Windows

# Install dependencies
pip install streamlit pandas plotly reportlab google-genai
```

### Dependencies
- **streamlit** >= 1.47.1 - Web application framework
- **pandas** >= 2.3.1 - Data manipulation and analysis
- **plotly** >= 6.2.0 - Interactive data visualization
- **reportlab** >= 4.4.3 - PDF generation
- **google-genai** >= 1.28.0 - AI analytics integration

## ⚙️ Configuration

### Environment Setup
1. **Google Gemini API Key**: 
   - Obtain an API key from [Google AI Studio](https://aistudio.google.com/)
   - Set as environment variable (recommended):
   ```bash
   # Windows PowerShell
   $env:GEMINI_API_KEY="your_api_key_here"
   
   # Windows Command Prompt
   set GEMINI_API_KEY=your_api_key_here
   
   # macOS/Linux
   export GEMINI_API_KEY="your_api_key_here"
   ```
   - Alternatively, you can set it directly in the application interface

2. **Database Configuration**:
   - The application uses SQLite by default
   - Database file: `acadboost.db`
   - Automatically initialized on first run

### Sample Data
The application automatically creates sample users and data on first run:
- **Admin**: admin/admin123
- **Teacher**: teacher1/teacher123  
- **Student**: student1/student123

> ⚠️ **Security Note**: Change default passwords immediately in production environments. The sample credentials are for demonstration purposes only.

## 🔧 Usage

### Starting the Application
1. **Activate Virtual Environment**:
   ```bash
   acadboost_env\Scripts\activate  # Windows
   source acadboost_env/bin/activate  # Linux/macOS
   ```

2. **Run Application**:
   ```bash
   streamlit run app.py
   ```

3. **Access Application**:
   - Open browser to `http://localhost:8501`
   - Use sample credentials or create new accounts

### Key Workflows

#### For Administrators:
1. Login with admin credentials
2. Manage users and departments
3. Create system announcements
4. Monitor system analytics
5. Generate reports

#### For Teachers:
1. Login with teacher credentials
2. Manage assigned students
3. Create and grade assignments
4. Track attendance
5. View teaching analytics

#### For Students:
1. Login with student credentials
2. View and submit assignments
3. Track academic progress
4. Build and manage resume
5. View certificates and achievements

## 📊 Database Schema

The application uses SQLite with the following main tables:

- **users** - User authentication and basic information
- **students** - Student-specific data
- **teachers** - Teacher-specific data
- **departments** - Department/subject organization
- **assignments** - Assignment management
- **projects** - Project tracking
- **attendance** - Attendance records
- **results** - Academic results and grades
- **announcements** - System announcements
- **certificates** - Certificate management
- **notifications** - User notifications

## � Security

### Important Security Considerations

⚠️ **Before deploying to production:**

1. **Change Default Credentials**: 
   - Immediately change all default passwords
   - Use strong, unique passwords for each account
   - Consider implementing password complexity requirements

2. **API Key Security**:
   - Never commit API keys to version control
   - Use environment variables or secure key management systems
   - Rotate API keys regularly
   - Monitor API key usage and set appropriate limits

3. **Database Security**:
   - In production, consider using PostgreSQL or MySQL instead of SQLite
   - Implement proper database access controls
   - Regular database backups with encryption

4. **Network Security**:
   - Use HTTPS in production environments
   - Implement proper firewall rules
   - Consider using reverse proxy (nginx/Apache)

5. **Session Management**:
   - Configure secure session cookies
   - Implement session timeout mechanisms
   - Use secure session storage

### Environment Variables Template

Create a `.env` file (never commit this to git):
```bash
# API Keys
GEMINI_API_KEY=your_actual_api_key_here

# Database (for production)
DATABASE_URL=your_database_connection_string

# Security
SECRET_KEY=your_secret_key_for_sessions
```

## �🚦 System Requirements

### Minimum Requirements
- **OS**: Windows 10, macOS 10.14, or Linux
- **Python**: 3.11 or higher
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 500MB free space
- **Browser**: Chrome, Firefox, Safari, or Edge

### Recommended Setup
- **RAM**: 8GB or higher
- **Storage**: 1GB free space
- **Internet**: Stable connection for AI features

## 🔍 Troubleshooting

### Common Issues

1. **Port Already in Use**:
   ```bash
   streamlit run app.py --server.port 8502
   ```

2. **Database Locked Error**:
   - Close all application instances
   - Restart the application

3. **AI Features Not Working**:
   - Verify Gemini API key is set correctly
   - Check internet connection
   - Ensure API key has sufficient quota

4. **Module Import Errors**:
   ```bash
   pip install --upgrade streamlit pandas plotly reportlab google-genai
   ```

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Getting Started
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Contribution Guidelines
- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting

### Areas for Contribution
- 🐛 Bug fixes and improvements
- ✨ New features and enhancements
- 📚 Documentation improvements
- 🎨 UI/UX enhancements
- 🔧 Performance optimizations

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/portalsage/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/portalsage/discussions)
- **Documentation**: [Wiki](https://github.com/yourusername/portalsage/wiki)

## 🗺️ Roadmap

### Version 2.0 (Planned)
- [ ] Mobile responsive design
- [ ] Advanced reporting dashboard
- [ ] Email notification system
- [ ] Multi-language support
- [ ] Advanced AI recommendations

### Version 3.0 (Future)
- [ ] Real-time collaboration features
- [ ] Advanced analytics dashboard
- [ ] Integration with external LMS
- [ ] Mobile application
- [ ] Advanced security features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  <p>⭐ If you found this project helpful, please give it a star!</p>
  <p>Made with ❤️ and 🤖 AI</p>
</div>

---

## 🙏 Acknowledgments

- **Streamlit Team** - For the amazing web framework
- **Google AI** - For Gemini AI integration
- **Plotly** - For interactive visualizations
- **ReportLab** - For PDF generation capabilities
- **Open Source Community** - For continuous inspiration and support
