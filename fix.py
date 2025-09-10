"""
ResumeIQ Web Application - Fix Script
This script helps fix common issues with the ResumeIQ Web Application.
"""

import os
import sys
import subprocess
import shutil

def check_python_version():
    """Check if Python version is compatible."""
    print("Checking Python version...")
    if sys.version_info < (3, 8):
        print("WARNING: This application requires Python 3.8 or higher.")
        print(f"Your Python version is {sys.version}")
        return False
    print(f"Python version {sys.version} is compatible.")
    return True

def install_dependencies():
    """Install required dependencies."""
    print("Installing required dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {str(e)}")
        print("Try running manually: pip install -r requirements.txt")
        return False

def download_spacy_model():
    """Download spaCy model."""
    print("Downloading spaCy model...")
    try:
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
        print("spaCy model downloaded successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error downloading spaCy model: {str(e)}")
        print("Try running manually: python -m spacy download en_core_web_sm")
        return False

def setup_database():
    """Set up the database."""
    print("Setting up database...")
    # Create database directory if it doesn't exist
    os.makedirs("database", exist_ok=True)
    
    try:
        # Run database setup script
        from database.db_setup import create_database
        create_database()
        print("Database setup successfully.")
        return True
    except Exception as e:
        print(f"Error setting up database: {str(e)}")
        print("Try running manually: python database/db_setup.py")
        return False

def create_directories():
    """Create required directories."""
    print("Creating required directories...")
    directories = [
        "uploads",
        "static/css",
        "static/images"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("Directories created successfully.")
    return True

def check_css_file():
    """Check if CSS file exists, create if not."""
    css_path = "static/css/style.css"
    if not os.path.exists(css_path):
        print(f"CSS file not found at {css_path}, creating it...")
        try:
            # Get the CSS file from the repository or create a minimal one
            with open(css_path, "w") as f:
                f.write("""/* Custom CSS for Resume Analyzer app */

/* Main theme colors */
:root {
    --primary-color: #4F46E5;
    --secondary-color: #818CF8;
    --accent-color: #3730A3;
    --light-bg: #F3F4F6;
    --dark-bg: #1F2937;
    --text-dark: #1F2937;
    --text-light: #F9FAFB;
    --success-color: #10B981;
    --warning-color: #F59E0B;
    --error-color: #EF4444;
}

/* Modifying Streamlit's default theme */
.stApp {
    background: linear-gradient(to bottom right, #ffffff, #f3f4f6);
}

/* Custom container for cards */
.custom-card {
    background-color: white;
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    padding: 1.5rem;
    margin-bottom: 1rem;
    border: 1px solid #F3F4F6;
}
""")
            print("Created a minimal CSS file.")
            return True
        except Exception as e:
            print(f"Error creating CSS file: {str(e)}")
            return False
    else:
        print("CSS file exists.")
        return True

def main():
    """Main function to fix common issues."""
    print("\nResumeIQ Web Application - Fix Script")
    print("=====================================\n")
    
    # Check if running from project root
    if not os.path.exists("app.py"):
        print("ERROR: This script must be run from the project root directory.")
        print("Please navigate to the directory containing app.py and run this script again.")
        return False
    
    # Run all checks
    checks = [
        check_python_version(),
        create_directories(),
        install_dependencies(),
        download_spacy_model(),
        setup_database(),
        check_css_file()
    ]
    
    if all(checks):
        print("\nAll issues have been fixed! You can now run the application:")
        print("streamlit run app.py")
        return True
    else:
        print("\nSome issues could not be fixed automatically.")
        print("Please check the output above and fix the remaining issues manually.")
        print("Once fixed, you can run the application: streamlit run app.py")
        return False

if __name__ == "__main__":
    main()
