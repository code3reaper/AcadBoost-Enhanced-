# AcadBoost - VS Code Setup Guide

## Prerequisites

Before running AcadBoost on your laptop, ensure you have the following installed:

### 1. Python 3.11+
- Download from [python.org](https://python.org)
- Verify installation: `python --version` or `python3 --version`

### 2. VS Code
- Download from [code.visualstudio.com](https://code.visualstudio.com)

### 3. Git (optional, for version control)
- Download from [git-scm.com](https://git-scm.com)

## Step-by-Step Setup Process

### Step 1: Download the Project Files

1. **Method 1: Download ZIP**
   - Download all project files as a ZIP from your Replit project
   - Extract to a folder like `C:\AcadBoost` (Windows) or `~/AcadBoost` (Mac/Linux)

2. **Method 2: Git Clone** (if using version control)
   ```bash
   git clone <your-repository-url>
   cd acadboost
   ```

### Step 2: Open Project in VS Code

1. Open VS Code
2. File → Open Folder
3. Select your AcadBoost project folder

### Step 3: Install Python Extensions

Install these VS Code extensions:
- **Python** (Microsoft)
- **Python Debugger** (Microsoft)
- **Pylance** (Microsoft) - Usually comes with Python extension

### Step 4: Set Up Virtual Environment

Open VS Code terminal (`Terminal → New Terminal`) and run:

**Windows:**
```bash
# Create virtual environment
python -m venv acadboost_env

# Activate virtual environment
acadboost_env\Scripts\activate

# Verify activation (should show (acadboost_env) in terminal)
```

**Mac/Linux:**
```bash
# Create virtual environment
python3 -m venv acadboost_env

# Activate virtual environment
source acadboost_env/bin/activate

# Verify activation (should show (acadboost_env) in terminal)
```

### Step 5: Install Required Packages

With the virtual environment activated, install all dependencies:

```bash
pip install streamlit pandas plotly reportlab google-genai
```

**Alternative:** If you have a requirements.txt file:
```bash
pip install -r requirements.txt
```

### Step 6: Set Up Environment Variables

Create a `.env` file in your project root folder with your API keys:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

**Important:** Never commit this file to version control. Add `.env` to your `.gitignore` file.

### Step 7: Database Setup

The SQLite database will be created automatically when you first run the application. No additional setup required.

### Step 8: Configure VS Code Python Interpreter

1. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
2. Type "Python: Select Interpreter"
3. Choose the interpreter from your virtual environment:
   - Windows: `acadboost_env\Scripts\python.exe`
   - Mac/Linux: `acadboost_env/bin/python`

## Running the Application

### Method 1: Using VS Code Terminal

1. Ensure virtual environment is activated
2. Run the application:
   ```bash
   streamlit run app.py --server.port 5000
   ```

### Method 2: Using VS Code Launch Configuration

Create `.vscode/launch.json` in your project:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Run AcadBoost",
            "type": "python",
            "request": "launch",
            "module": "streamlit",
            "args": [
                "run",
                "app.py",
                "--server.port",
                "5000"
            ],
            "console": "integratedTerminal",
            "env": {
                "GEMINI_API_KEY": "your_api_key_here"
            }
        }
    ]
}
```

Then press `F5` to run the application.

## Accessing the Application

1. After running the command, Streamlit will start the server
2. Open your web browser
3. Navigate to: `http://localhost:5000`
4. The AcadBoost login page should appear

## Default Login Credentials

**Admin Portal:**
- Username: `admin`
- Password: `admin123`

**Teacher Portal:**
- Username: `teacher1` or `teacher2`  
- Password: `teacher123`

**Student Portal:**
- Username: `student1`, `student2`, or `student3`
- Password: `student123`

## Project Structure

```
AcadBoost/
├── app.py                 # Main application entry point
├── auth.py               # Authentication functions
├── database.py           # Database operations
├── admin_module.py       # Admin dashboard
├── teacher_module.py     # Teacher dashboard
├── student_module.py     # Student dashboard
├── resume_module.py      # Resume management
├── ai_analytics.py       # AI-powered analytics
├── utils.py              # Utility functions
├── acadboost.db          # SQLite database (created automatically)
├── .env                  # Environment variables (create this)
├── requirements.txt      # Python dependencies (optional)
└── generated_resumes/    # Generated resume files (created automatically)
```

## Features Available

✅ **Multi-role Authentication System**
- Admin, Teacher, and Student portals
- Secure login with session management

✅ **Admin Dashboard**
- User management (add/edit/delete users)
- Department and subject management
- System-wide analytics and reports

✅ **Teacher Dashboard**
- Assignment and project management
- Attendance tracking and management
- Student performance analytics
- AI-powered teaching insights

✅ **Student Dashboard**
- Assignment submissions and tracking
- Project portfolio management
- Attendance and performance tracking
- **Resume Management System** (NEW!)
  - ATS-friendly resume builder
  - Resume upload and AI analysis
  - Professional templates

✅ **AI-Powered Features**
- Student performance analysis
- Personalized learning recommendations
- Resume optimization suggestions
- Teaching effectiveness insights

## Troubleshooting

### Common Issues and Solutions

**1. Import Errors**
```
ModuleNotFoundError: No module named 'streamlit'
```
**Solution:** Ensure virtual environment is activated and packages are installed

**2. Port Already in Use**
```
OSError: [Errno 48] Address already in use
```
**Solution:** Use a different port:
```bash
streamlit run app.py --server.port 5001
```

**3. Database Errors**
```
sqlite3.OperationalError: no such table
```
**Solution:** Delete `acadboost.db` file and restart the application to recreate tables

**4. AI Features Not Working**
- Ensure `GEMINI_API_KEY` is set correctly in your `.env` file
- Check if your API key has sufficient quota/credits

**5. File Upload Issues**
- Ensure the application has write permissions in the project directory
- Check if `generated_resumes/` and `uploaded_resumes/` folders exist

### Environment Variables

Make sure these environment variables are set:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### Performance Tips

- Use a fast SSD for better database performance
- Ensure adequate RAM (4GB minimum, 8GB recommended)
- Close unnecessary applications when running the system
- Use Chrome or Edge browsers for best Streamlit compatibility

## Development Tips

### VS Code Recommended Settings

Create `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "./acadboost_env/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "autopep8",
    "files.exclude": {
        "**/__pycache__": true,
        "**/.env": false,
        "**/acadboost.db": false
    }
}
```

### Debugging

1. Set breakpoints in VS Code by clicking on line numbers
2. Press `F5` to start debugging
3. Use the Debug Console to inspect variables

### Code Formatting

Install and configure:
```bash
pip install autopep8 pylint
```

## Support

If you encounter issues:

1. Check the VS Code terminal for error messages
2. Ensure all dependencies are installed correctly
3. Verify your Python version compatibility
4. Check file permissions in your project directory

## Next Steps

Once you have AcadBoost running locally:

1. **Customize the System:**
   - Add your own departments and subjects
   - Upload student and teacher data
   - Configure system settings

2. **Extend Functionality:**
   - Add new features using the existing architecture
   - Integrate with external systems (LMS, email, etc.)
   - Create custom reports and analytics

3. **Deploy to Production:**
   - Consider hosting options (AWS, Azure, Google Cloud)
   - Set up proper database backups
   - Configure SSL certificates for security

Enjoy using AcadBoost! 🚀