# Virtual Environment Setup

## Overview
This project uses a Python virtual environment to manage dependencies. The virtual environment is located in the `venv` directory.

## Activation

### Windows
```bash
# Method 1: Using the batch file
run_app.bat

# Method 2: Manual activation
venv\Scripts\activate.bat
python app.py
```

### Using VS Code
1. Open the project in VS Code
2. The virtual environment should be automatically detected
3. If not, select the Python interpreter at `./venv/Scripts/python.exe`

## Dependencies
All required packages are listed in `requirements.txt`:
- Flask==3.1.2
- Flask-SQLAlchemy==3.1.1
- Flask-Login==0.6.3
- Flask-Migrate==4.1.0
- SQLAlchemy==2.0.44
- Alembic==1.17.2
- ReportLab==4.4.5
- openpyxl==3.1.5
- Pillow==12.0.0
- pandas==2.3.3
- numpy==2.3.5
- xlsxwriter==3.2.9
- pymysql==1.1.2

## Installation
```bash
# Create virtual environment (if not exists)
python -m venv venv

# Activate virtual environment
venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

## Running the Application
```bash
# Using the batch file (recommended)
run_app.bat

# Or manually
venv\Scripts\activate.bat
python app.py
```

The application will be available at http://localhost:5021

## Troubleshooting

### Pylance Errors in VS Code
If you're seeing "Import could not be resolved" errors in VS Code:
1. Make sure the virtual environment is activated
2. Check that VS Code is using the correct Python interpreter (`./venv/Scripts/python.exe`)
3. Restart VS Code after changing interpreter settings

### Module Not Found Errors
If you get "ModuleNotFoundError" when running the application:
1. Make sure the virtual environment is activated
2. Install missing packages with `pip install <package-name>`
3. Update requirements.txt if you add new dependencies

### Application Context Errors
If you see "Working outside of application context" errors:
1. This has been fixed by ensuring proper app context usage
2. The `initialize_ctp_machines()` function now uses `with app.app_context():`
3. Make sure you're using the latest version of the code