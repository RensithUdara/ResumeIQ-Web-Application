# Troubleshooting Guide for ResumeIQ Web Application

## Common Issues and Solutions

### Lottie Animation Error

**Error Message:**
```
Animation data must be one of Lottie URL or loaded JSON represented by dict or string/bytes UTF-8 JSON representative. Given type is: <class 'NoneType'>
```

**Solution:**
This error occurs when the application cannot load the Lottie animations from the internet. To fix this issue:

1. Make sure you have internet access to load the animations
2. Install the required dependencies:
   ```
   pip install streamlit-lottie requests
   ```
3. If the issue persists, the application will now automatically use fallback animations

### Missing Package Error

**Error Message:**
```
Required packages are missing...
```

**Solution:**
Some required packages are not installed. Install them using:

```
pip install -r requirements.txt
```

Or install the specific packages mentioned in the error message:

```
pip install streamlit-option-menu streamlit-lottie
```

### Database Connection Error

**Error Message:**
```
Failed to set up database...
```

**Solution:**
This error can occur if:
1. The database directory does not exist
2. You don't have write permissions for the database directory

To fix this issue:
1. Make sure the `database` directory exists
2. Run the application with appropriate permissions
3. Manually run the database setup script:
   ```
   python database/db_setup.py
   ```

### CSS File Not Found

**Error Message:**
```
CSS file not found. Using default styling.
```

**Solution:**
The application cannot find the CSS file. Make sure:
1. The `static/css/` directory exists
2. The `static/css/style.css` file exists
3. You are running the application from the project root directory

## Running the Application

To run the application correctly:

1. Make sure all dependencies are installed:
   ```
   pip install -r requirements.txt
   ```

2. Download the spaCy model:
   ```
   python -m spacy download en_core_web_sm
   ```

3. Initialize the database:
   ```
   python database/db_setup.py
   ```

4. Start the application:
   ```
   streamlit run app.py
   ```

## Contact for Support

If you continue to experience issues, please open an issue on the GitHub repository.
