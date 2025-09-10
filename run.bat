@echo off
echo Smart Resume Analyzer - Setup and Run Script

echo Checking Python installation...
python --version
if %ERRORLEVEL% neq 0 (
    echo Python is not installed or not in PATH. Please install Python 3.8+ and try again.
    pause
    exit /b
)

echo Setting up virtual environment...
if not exist venv (
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo Failed to install dependencies. Please check your internet connection and try again.
    pause
    exit /b
)

echo Downloading spaCy model...
python -m spacy download en_core_web_sm
if %ERRORLEVEL% neq 0 (
    echo Failed to download spaCy model. Please check your internet connection and try again.
    pause
    exit /b
)

echo Setting up database...
python database\db_setup.py
if %ERRORLEVEL% neq 0 (
    echo Failed to set up database. Please check file permissions and try again.
    pause
    exit /b
)

echo Creating required directories...
if not exist uploads (
    mkdir uploads
)
if not exist static\images (
    mkdir static\images
)

echo Starting the application...
echo The application will open in your web browser shortly...
streamlit run app.py

pause
