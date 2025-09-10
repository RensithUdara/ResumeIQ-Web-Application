# Smart Resume Analyzer - Setup and Run Script

Write-Host "Smart Resume Analyzer - Setup and Run Script" -ForegroundColor Cyan

# Check Python installation
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host $pythonVersion -ForegroundColor Green
} 
catch {
    Write-Host "Python is not installed or not in PATH. Please install Python 3.8+ and try again." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit
}

# Set up virtual environment
Write-Host "Setting up virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path -Path "venv")) {
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
try {
    pip install -r requirements.txt
    Write-Host "Dependencies installed successfully." -ForegroundColor Green
} 
catch {
    Write-Host "Failed to install dependencies. Please check your internet connection and try again." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit
}

# Download spaCy model
Write-Host "Downloading spaCy model..." -ForegroundColor Yellow
try {
    python -m spacy download en_core_web_sm
    Write-Host "SpaCy model downloaded successfully." -ForegroundColor Green
} 
catch {
    Write-Host "Failed to download spaCy model. Please check your internet connection and try again." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit
}

# Set up database
Write-Host "Setting up database..." -ForegroundColor Yellow
try {
    python .\database\db_setup.py
    Write-Host "Database setup completed successfully." -ForegroundColor Green
} 
catch {
    Write-Host "Failed to set up database. Please check file permissions and try again." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit
}

# Create required directories
Write-Host "Creating required directories..." -ForegroundColor Yellow
if (-not (Test-Path -Path "uploads")) {
    New-Item -Path "uploads" -ItemType Directory | Out-Null
}
if (-not (Test-Path -Path "static\images")) {
    New-Item -Path "static\images" -ItemType Directory -Force | Out-Null
}
Write-Host "Directories created successfully." -ForegroundColor Green

# Start the application
Write-Host "Starting the application..." -ForegroundColor Cyan
Write-Host "The application will open in your web browser shortly..." -ForegroundColor Green
streamlit run app.py
