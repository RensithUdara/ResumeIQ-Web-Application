import streamlit as st
import os
import base64
import time
from datetime import datetime
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from PIL import Image
import requests
import sys

# Handle potential missing packages
try:
    from streamlit_option_menu import option_menu
except ImportError:
    st.error("Missing package: streamlit-option-menu. Please install using: pip install streamlit-option-menu")
    option_menu = None

try:
    from streamlit_lottie import st_lottie
except ImportError:
    st.error("Missing package: streamlit-lottie. Please install using: pip install streamlit-lottie")
    st_lottie = None

# Import custom modules
from database.db_manager import DatabaseManager
from utils.resume_parser import analyze_resume, match_resume_to_job

# Set page configuration
st.set_page_config(
    page_title="ResumeIQ Web Application",
    page_icon="�",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "# ResumeIQ Web Application\nAn AI-driven tool for resume analysis and job matching.",
        'Report a bug': "https://github.com/RensithUdara/ResumeIQ-Web-Application/issues",
        'Get help': "https://github.com/RensithUdara/ResumeIQ-Web-Application/blob/main/TROUBLESHOOTING.md"
    }
)

# Initialize database
db = DatabaseManager()

# Function to load custom CSS
def load_css():
    try:
        with open('static/css/style.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("CSS file not found. Using default styling.")
        # Apply some minimal default styling
        st.markdown("""
        <style>
        .custom-card {
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            padding: 1.5rem;
            margin-bottom: 1rem;
        }
        </style>
        """, unsafe_allow_html=True)

# Function to load Lottie animations
def load_lottie_url(url: str):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception as e:
        st.error(f"Error loading animation: {str(e)}")
        return None
        
# Function to load local Lottie files as fallback
def load_lottie_fallback():
    # Simple JSON for a basic loading animation as fallback
    return {
        "v": "5.7.8",
        "fr": 30,
        "ip": 0,
        "op": 60,
        "w": 400,
        "h": 400,
        "nm": "Loading Animation",
        "ddd": 0,
        "assets": [],
        "layers": [{
            "ddd": 0,
            "ind": 1,
            "ty": 4,
            "nm": "Circle",
            "sr": 1,
            "ks": {
                "o": {"a": 0, "k": 100},
                "r": {"a": 1, "k": [{"t": 0, "s": [0], "e": [360]}, {"t": 60, "s": [360]}]},
                "p": {"a": 0, "k": [200, 200]},
                "a": {"a": 0, "k": [0, 0]},
                "s": {"a": 0, "k": [100, 100]}
            },
            "shapes": [{
                "ty": "el",
                "p": {"a": 0, "k": [0, 0]},
                "s": {"a": 0, "k": [100, 100]},
                "d": [],
                "nm": "Ellipse Path 1"
            }, {
                "ty": "st",
                "c": {"a": 0, "k": [0.31, 0.27, 0.9]},
                "o": {"a": 0, "k": 100},
                "w": {"a": 0, "k": 10},
                "lc": 2,
                "lj": 1,
                "ml": 4,
                "nm": "Stroke 1"
            }, {
                "ty": "tr",
                "p": {"a": 0, "k": [0, 0]},
                "a": {"a": 0, "k": [0, 0]},
                "s": {"a": 0, "k": [80, 80]},
                "r": {"a": 0, "k": 0},
                "o": {"a": 0, "k": 100}
            }]
        }]
    }

# Function to display animated icons
def display_lottie(animation, height=300, width=300):
    if animation is not None:
        st_lottie(animation, height=height, width=width, key=f"lottie_{int(time.time())}")
    else:
        # Fallback when animation fails to load
        st.info("Animation could not be loaded. Continuing without animation.")

# Function to save uploaded resume
def save_uploaded_resume(uploaded_file, user_id):
    if uploaded_file is not None:
        # Create directory if it doesn't exist
        save_dir = os.path.join("uploads", str(user_id))
        os.makedirs(save_dir, exist_ok=True)
        
        # Save file to directory
        file_path = os.path.join(save_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Save file info to database
        resume_id = db.save_resume(user_id, uploaded_file.name, file_path)
        
        return resume_id, file_path
    return None, None

# Function to create a gauge chart for resume score
def create_score_gauge(score):
    fig = px.pie(
        values=[score, 100-score],
        names=["Score", ""],
        hole=0.7,
        color_discrete_sequence=["#4F46E5", "#F3F4F6"]
    )
    fig.update_layout(
        showlegend=False,
        margin=dict(t=0, b=0, l=0, r=0),
        height=200,
        annotations=[dict(text=f"{score}%", x=0.5, y=0.5, font_size=40, showarrow=False)]
    )
    return fig

# Create session states
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'user_id' not in st.session_state:
    st.session_state.user_id = None

if 'user_type' not in st.session_state:
    st.session_state.user_type = None

if 'username' not in st.session_state:
    st.session_state.username = None
    
if 'guest_mode' not in st.session_state:
    st.session_state.guest_mode = False
    
if 'temp_resume_path' not in st.session_state:
    st.session_state.temp_resume_path = None
    
if 'current_analysis' not in st.session_state:
    st.session_state.current_analysis = None
    
if 'current_step' not in st.session_state:
    st.session_state.current_step = 1
    
if 'resume_history' not in st.session_state:
    st.session_state.resume_history = []

# Load custom CSS
load_css()

# Authentication functions
def login_form():
    st.markdown("""
    <div class="custom-card">
        <h2 style="text-align: center; color: #4F46E5;">Login</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Load animation with fallback
    login_animation = load_lottie_url("https://assets3.lottiefiles.com/packages/lf20_q7hibrh9.json")
    if login_animation is None:
        login_animation = load_lottie_fallback()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        display_lottie(login_animation)
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                if username and password:
                    result = db.authenticate_user(username, password)
                    if result["status"] == "success":
                        st.session_state.logged_in = True
                        st.session_state.user_id = result["user_id"]
                        st.session_state.user_type = result["user_type"]
                        st.session_state.username = result["username"]
                        st.experimental_rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.error("Please enter both username and password")

def signup_form():
    st.markdown("""
    <div class="custom-card">
        <h2 style="text-align: center; color: #4F46E5;">Create Account</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Load animation with fallback
    signup_animation = load_lottie_url("https://assets5.lottiefiles.com/packages/lf20_q5pk6p1k.json")
    if signup_animation is None:
        signup_animation = load_lottie_fallback()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        display_lottie(signup_animation)
    
    with col2:
        with st.form("signup_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            password_confirm = st.text_input("Confirm Password", type="password")
            user_type = st.selectbox("Account Type", ["job_seeker", "recruiter"])
            submitted = st.form_submit_button("Create Account")
            
            if submitted:
                if username and password and password_confirm:
                    if password == password_confirm:
                        result = db.create_user(username, password, user_type)
                        if result["status"] == "success":
                            st.success("Account created successfully! You can now log in.")
                            time.sleep(1)
                            st.session_state.logged_in = True
                            st.session_state.user_id = result["user_id"]
                            st.session_state.user_type = user_type
                            st.session_state.username = username
                            st.experimental_rerun()
                        else:
                            st.error(result["message"])
                    else:
                        st.error("Passwords do not match")
                else:
                    st.error("Please fill all fields")

def logout():
    """Function to log out the user"""
    # Clean up any temporary files
    if st.session_state.get('temp_resume_path') and os.path.exists(st.session_state.temp_resume_path):
        try:
            os.remove(st.session_state.temp_resume_path)
        except Exception as e:
            print(f"Error removing temporary file: {e}")
    
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_type = None
    st.session_state.username = None
    st.session_state.guest_mode = False
    st.session_state.temp_resume_path = None
    st.experimental_rerun()

def enable_guest_mode():
    """Enable guest mode for users without accounts"""
    # Clean up any previous guest session
    if st.session_state.get('temp_resume_path') and os.path.exists(st.session_state.temp_resume_path):
        try:
            os.remove(st.session_state.temp_resume_path)
        except Exception as e:
            print(f"Error removing temporary file: {e}")
    
    st.session_state.guest_mode = True
    st.session_state.user_type = "job_seeker"
    st.experimental_rerun()
    
def disable_guest_mode():
    """Disable guest mode and return to login/signup"""
    # Clean up any temporary files
    if st.session_state.get('temp_resume_path') and os.path.exists(st.session_state.temp_resume_path):
        try:
            os.remove(st.session_state.temp_resume_path)
        except Exception as e:
            print(f"Error removing temporary file: {e}")
    
    st.session_state.guest_mode = False
    st.session_state.temp_resume_path = None
    st.experimental_rerun()

# Main App UI
def cleanup_temp_files():
    """Clean up old temporary files to prevent disk space issues"""
    temp_dir = "temp"
    if not os.path.exists(temp_dir):
        return
        
    try:
        # Get all files in the temp directory
        files = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir)]
        files = [(f, os.path.getmtime(f)) for f in files if os.path.isfile(f)]
        
        # Sort by modification time (oldest first)
        files.sort(key=lambda x: x[1])
        
        # Keep only the 10 most recent files, delete the rest
        if len(files) > 10:
            for file_path, _ in files[:-10]:
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error removing old temporary file {file_path}: {e}")
    except Exception as e:
        print(f"Error during temp file cleanup: {e}")

def main():
    # Clean up old temporary files
    cleanup_temp_files()
    
    # Check if required packages are available
    if option_menu is None or st_lottie is None:
        st.error("Required packages are missing. Please install them using the following command:")
        st.code("pip install streamlit-option-menu streamlit-lottie")
        st.warning("After installing the required packages, please restart the application.")
        return
    
    # Sidebar
    with st.sidebar:
        try:
            st.image("https://img.icons8.com/fluency/96/000000/resume.png", width=80)
        except:
            st.write("�") # Fallback icon
            
        st.title("ResumeIQ Web Application")
        
        if st.session_state.logged_in:
            st.write(f"Welcome, **{st.session_state.username}**!")
            
            if st.session_state.user_type == "job_seeker":
                try:
                    menu = option_menu(
                        "Main Menu",
                        ["Resume Upload", "My Resumes", "Job Matching", "About"],
                        icons=["cloud-upload", "file-earmark-text", "briefcase", "info-circle"],
                        menu_icon="list",
                        default_index=0,
                    )
                except Exception as e:
                    st.error(f"Error displaying menu: {str(e)}")
                    menu = st.radio(
                        "Main Menu",
                        ["Resume Upload", "My Resumes", "Job Matching", "About"]
                    )
            else:  # recruiter
                try:
                    menu = option_menu(
                        "Main Menu",
                        ["Post Job", "My Postings", "Resume Matching", "About"],
                        icons=["pencil-square", "clipboard-check", "people", "info-circle"],
                        menu_icon="list",
                        default_index=0,
                    )
                except Exception as e:
                    st.error(f"Error displaying menu: {str(e)}")
                    menu = st.radio(
                        "Main Menu",
                        ["Post Job", "My Postings", "Resume Matching", "About"]
                    )
                
            st.button("Logout", on_click=logout)
        elif st.session_state.guest_mode:
            st.markdown("""<div class="guest-banner">Guest Mode</div>""", unsafe_allow_html=True)
            
            try:
                menu = option_menu(
                    "Menu",
                    ["Analyze Resume", "About"],
                    icons=["file-earmark-text", "info-circle"],
                    menu_icon="list",
                    default_index=0,
                )
            except Exception as e:
                st.error(f"Error displaying menu: {str(e)}")
                menu = st.radio(
                    "Menu",
                    ["Analyze Resume", "About"]
                )
            
            with st.expander("Want to save your results?"):
                st.write("Create an account to save your resume analysis history and match with job opportunities.")
                col1, col2 = st.columns(2)
                with col1:
                    st.button("Sign Up", on_click=disable_guest_mode, key="signup_from_guest")
                with col2:
                    st.button("Login", on_click=disable_guest_mode, key="login_from_guest")
                
        else:
            try:
                auth_option = option_menu(
                    "Authentication",
                    ["Login", "Signup", "Guest Mode"],
                    icons=["box-arrow-in-right", "person-plus", "person-incognito"],
                    menu_icon="lock",
                    default_index=0,
                )
            except Exception as e:
                st.error(f"Error displaying authentication menu: {str(e)}")
                auth_option = st.radio(
                    "Authentication",
                    ["Login", "Signup", "Guest Mode"]
                )
    
    # Main content
    if st.session_state.logged_in:
        # Job Seeker Interface
        if st.session_state.user_type == "job_seeker":
            if menu == "Resume Upload":
                resume_upload_page()
            elif menu == "My Resumes":
                my_resumes_page()
            elif menu == "Job Matching":
                job_matching_page()
            else:
                about_page()
        
        # Recruiter Interface
        else:
            if menu == "Post Job":
                post_job_page()
            elif menu == "My Postings":
                my_postings_page()
            elif menu == "Resume Matching":
                resume_matching_page()
            else:
                about_page()
    
    elif st.session_state.guest_mode:
        # Guest Mode Interface
        if menu == "Analyze Resume":
            resume_upload_page(guest_mode=True)
        else:
            about_page()
            
    else:
        # Authentication pages
        if 'auth_option' in locals():
            if auth_option == "Login":
                login_form()
            elif auth_option == "Signup":
                signup_form()
            elif auth_option == "Guest Mode":
                enable_guest_mode()
        else:
            signup_form()

# Page content functions
def resume_upload_page(guest_mode=False):
    if guest_mode:
        title_text = "Analyze Your Resume"
    else:
        title_text = "Upload Your Resume"
        
    st.markdown(f"""
    <div class="custom-card">
        <h1 style="color: #0071e3; text-align: center;">{title_text}</h1>
        <p style="text-align: center;">Upload your resume to get detailed analysis and improvement suggestions</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Upload animation with fallback
    upload_animation = load_lottie_url("https://assets9.lottiefiles.com/packages/lf20_nw19osms.json")
    if upload_animation is None:
        upload_animation = load_lottie_fallback()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("""
        <div style="background-color: #f0f7ff; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
            <h3 style="color: #0071e3; margin-bottom: 15px;">How It Works</h3>
            <ol style="margin-left: 20px; color: #343a40;">
                <li style="margin-bottom: 8px;"><strong>Upload</strong> your resume (PDF or DOCX)</li>
                <li style="margin-bottom: 8px;"><strong>Analyze</strong> skills, education & experience</li>
                <li style="margin-bottom: 8px;"><strong>Get</strong> personalized improvement suggestions</li>
                <li style="margin-bottom: 8px;"><strong>Improve</strong> your resume with AI-powered insights</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        display_lottie(upload_animation, height=200)
    
    with col2:
        st.markdown("""
        <div style="background-color: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
            <h3 style="color: #0071e3; margin-bottom: 15px;">Resume Upload</h3>
        </div>
        """, unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Drag and drop your resume here", type=['pdf', 'docx'])
        
        if uploaded_file is not None:
            if guest_mode:
                # For guest users, use a temporary ID and don't save to database
                resume_id = f"temp_{int(time.time())}"
                file_extension = uploaded_file.name.split('.')[-1].lower()
                temp_dir = "temp"
                
                # Create temp directory if it doesn't exist
                os.makedirs(temp_dir, exist_ok=True)
                
                file_path = os.path.join(temp_dir, f"{resume_id}.{file_extension}")
                
                # Save the file temporarily
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                st.session_state.temp_resume_path = file_path
            else:
                resume_id, file_path = save_uploaded_resume(uploaded_file, st.session_state.user_id)
            
            if resume_id and file_path:
                st.success(f"Resume '{uploaded_file.name}' uploaded successfully!")
                
                with st.spinner("Analyzing resume..."):
                    # Analyze the resume
                    analysis_result = analyze_resume(file_path, resume_id)
                    
                    if analysis_result["status"] == "success":
                        st.session_state.current_analysis = analysis_result
                        st.session_state.current_resume_id = resume_id
                        
                        # Display analysis in an expandable section
                        with st.expander("Show Analysis Results", expanded=True):
                            display_resume_analysis(analysis_result)
                    else:
                        st.error(analysis_result["message"])

def display_resume_analysis(analysis):
    # Header section
    st.markdown("""
    <div class="custom-card">
        <h2 style="color: #0071e3; margin-bottom: 15px;">Resume Analysis Results</h2>
        <p style="color: #6c757d;">Detailed insights and improvement recommendations for your resume</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display metrics in a modern layout
    st.markdown("""
    <style>
    .metric-container {
        display: flex;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 16px;
        margin-bottom: 24px;
    }
    .metric-card {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        flex: 1;
        min-width: 180px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        text-align: center;
    }
    .metric-value {
        font-size: 36px;
        font-weight: 700;
        color: #0071e3;
        margin: 10px 0;
    }
    .metric-label {
        font-size: 14px;
        color: #6c757d;
        font-weight: 500;
    }
    </style>
    
    <div class="metric-container">
        <div class="metric-card">
            <div class="metric-label">OVERALL SCORE</div>
            <div class="metric-value">{analysis["score"]}%</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">SKILLS DETECTED</div>
            <div class="metric-value">{len(analysis["skills"])}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">CONTENT LENGTH</div>
            <div class="metric-value">{analysis["text_length"]}</div>
            <div class="metric-label">CHARACTERS</div>
        </div>
    </div>
    """.format(
        score=analysis["score"],
        skills_count=len(analysis["skills"]),
        text_length=analysis["text_length"]
    ), unsafe_allow_html=True)
    
    # Display tabs with detailed information
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Skills", "🎓 Education", "💼 Experience", "💡 Suggestions"])
    
    with tab1:
        st.markdown("""
        <div class="custom-card">
            <h3 style="color: #0071e3; margin-bottom: 15px;">Detected Skills</h3>
        """, unsafe_allow_html=True)
        
        if analysis["skills"]:
            # Group skills by categories if possible
            skill_categories = {
                "Programming": [],
                "Database": [],
                "Web": [],
                "Cloud": [],
                "Soft Skills": [],
                "Other": []
            }
            
            # Simple categorization logic - can be enhanced with more sophisticated categorization
            for skill in analysis["skills"]:
                skill_lower = skill.lower()
                if skill_lower in ["python", "java", "javascript", "c++", "c#", "typescript", "ruby", "php", "go"]:
                    skill_categories["Programming"].append(skill)
                elif skill_lower in ["sql", "mysql", "postgresql", "mongodb", "oracle", "database"]:
                    skill_categories["Database"].append(skill)
                elif skill_lower in ["html", "css", "react", "angular", "vue", "django", "flask", "node"]:
                    skill_categories["Web"].append(skill)
                elif skill_lower in ["aws", "azure", "gcp", "docker", "kubernetes", "cloud"]:
                    skill_categories["Cloud"].append(skill)
                elif skill_lower in ["leadership", "communication", "teamwork", "problem solving", "management"]:
                    skill_categories["Soft Skills"].append(skill)
                else:
                    skill_categories["Other"].append(skill)
            
            # Display skills by category
            for category, skills in skill_categories.items():
                if skills:
                    st.markdown(f"<h4 style='margin-top: 15px; margin-bottom: 10px; color: #495057;'>{category}</h4>", unsafe_allow_html=True)
                    skills_html = ""
                    for skill in skills:
                        skills_html += f"<span class='skill-tag'>{skill}</span>"
                    st.markdown(f"<div style='line-height: 2.8;'>{skills_html}</div>", unsafe_allow_html=True)
        else:
            st.warning("No skills detected. Consider adding more technical skills to your resume.")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab2:
        st.markdown("""
        <div class="custom-card">
            <h3 style="color: #0071e3; margin-bottom: 15px;">Education Details</h3>
        """, unsafe_allow_html=True)
        
        if analysis["education"]:
            for edu in analysis["education"]:
                st.markdown("""
                <div style="background-color: #f8f9fa; border-left: 3px solid #0071e3; padding: 12px; margin-bottom: 10px; border-radius: 4px;">
                    <p style="margin: 0;">{}</p>
                </div>
                """.format(edu), unsafe_allow_html=True)
        else:
            st.warning("No education details detected. Make sure your education section is clearly formatted.")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab3:
        st.markdown("""
        <div class="custom-card">
            <h3 style="color: #0071e3; margin-bottom: 15px;">Experience Details</h3>
        """, unsafe_allow_html=True)
        
        if analysis["experience"]:
            for exp in analysis["experience"]:
                st.markdown("""
                <div style="background-color: #f8f9fa; border-left: 3px solid #0071e3; padding: 12px; margin-bottom: 10px; border-radius: 4px;">
                    <p style="margin: 0;">{}</p>
                </div>
                """.format(exp), unsafe_allow_html=True)
        else:
            st.warning("No work experience detected. Make sure your work experience section is clearly formatted.")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab4:
        st.markdown("""
        <div class="custom-card">
            <h3 style="color: #0071e3; margin-bottom: 15px;">Improvement Suggestions</h3>
        """, unsafe_allow_html=True)
        
        if analysis["suggestions"]:
            for i, suggestion in enumerate(analysis["suggestions"]):
                st.markdown(f"""
                <div style="background-color: #fff8f0; border-left: 3px solid #ff9500; padding: 12px; margin-bottom: 10px; border-radius: 4px;">
                    <p style="margin: 0; color: #495057;"><strong>Suggestion {i+1}:</strong> {suggestion}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No specific suggestions available for this resume.")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Display word cloud
    if "wordcloud_path" in analysis and analysis["wordcloud_path"]:
        st.markdown("""
        <div class="custom-card">
            <h3 style="color: #0071e3; margin-bottom: 15px;">Resume Word Cloud</h3>
            <div style="text-align: center;">
        """, unsafe_allow_html=True)
        st.image(analysis["wordcloud_path"])
        st.markdown("""
            </div>
        </div>
        """, unsafe_allow_html=True)

def my_resumes_page():
    st.markdown("""
    <div class="custom-card">
        <h1 style="color: #0071e3; text-align: center;">My Resumes</h1>
        <p style="text-align: center;">View and manage all your uploaded resumes</p>
    </div>
    """, unsafe_allow_html=True)
    
    resumes = db.get_user_resumes(st.session_state.user_id)
    
    if not resumes:
        st.markdown("""
        <div style="text-align: center; padding: 40px 20px; background-color: white; border-radius: 12px; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
            <img src="https://img.icons8.com/fluency/96/000000/empty-box.png" width="80">
            <h3 style="color: #0071e3; margin-top: 20px;">No Resumes Yet</h3>
            <p style="color: #6c757d; margin-bottom: 20px;">You haven't uploaded any resumes yet.</p>
            <a href="#" style="background-color: #0071e3; color: white; text-decoration: none; padding: 10px 20px; border-radius: 8px; font-weight: 500;">Upload Your First Resume</a>
        </div>
        """, unsafe_allow_html=True)
        
        # No resumes animation with fallback
        empty_animation = load_lottie_url("https://assets5.lottiefiles.com/packages/lf20_ydo1amjm.json")
        if empty_animation is None:
            empty_animation = load_lottie_fallback()
        display_lottie(empty_animation, height=200)
    else:
        # Display header
        st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <h2 style="color: #0071e3; margin: 0;">My Resume Collection</h2>
            <span style="background-color: #e1f0ff; color: #0071e3; padding: 4px 12px; border-radius: 20px; font-size: 14px; font-weight: 500;">
                {} Resumes
            </span>
        </div>
        """.format(len(resumes)), unsafe_allow_html=True)
        
        # Display resumes in cards with modern styling
        st.markdown("""
        <style>
        .resume-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .resume-card {
            background-color: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            transition: all 0.2s ease;
        }
        .resume-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.08);
        }
        .resume-header {
            background-color: #0071e3;
            color: white;
            padding: 12px 16px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .resume-content {
            padding: 16px;
        }
        .resume-footer {
            border-top: 1px solid #f1f3f5;
            padding: 12px 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .resume-date {
            color: #6c757d;
            font-size: 13px;
        }
        .resume-score {
            background-color: #e1f0ff;
            color: #0071e3;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 13px;
            font-weight: 600;
        }
        </style>
        
        <div class="resume-grid">
        """, unsafe_allow_html=True)
        
        # Create cards for each resume
        for resume in resumes:
            score = db.get_resume_score(resume['id'])
            
            st.markdown(f"""
            <div class="resume-card" id="resume-{resume['id']}">
                <div class="resume-header">
                    <h4 style="margin: 0; font-weight: 500;">{resume['filename']}</h4>
                </div>
                <div class="resume-content">
                    <div style="display: flex; align-items: center; margin-bottom: 12px;">
                        <img src="https://img.icons8.com/fluency/48/000000/document.png" width="36" style="margin-right: 12px;">
                        <div>
                            <div style="font-weight: 500; color: #212529;">{os.path.splitext(resume['filename'])[0]}</div>
                            <div class="resume-date">Uploaded on {resume['uploaded_at']}</div>
                        </div>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="resume-score">Score: {score}%</span>
                    </div>
                </div>
                <div class="resume-footer">
                    <button onclick="document.getElementById('view-btn-{resume['id']}').click()" 
                            style="background-color: #0071e3; color: white; border: none; border-radius: 6px; padding: 6px 12px; cursor: pointer; font-size: 13px; font-weight: 500;">
                        View Analysis
                    </button>
                    <button onclick="document.getElementById('delete-btn-{resume['id']}').click()" 
                            style="background-color: rgba(255,59,48,0.1); color: #ff3b30; border: none; border-radius: 6px; padding: 6px 12px; cursor: pointer; font-size: 13px; font-weight: 500;">
                        Delete
                    </button>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Hidden buttons that will be clicked by the JavaScript in the HTML
            if st.button("View", key=f"view-btn-{resume['id']}", help="View resume analysis", style="visibility: hidden;"):
                # Get analysis results
                analysis = db.get_resume_analysis(resume['id'])
                
                if analysis:
                    # Convert string data back to lists
                    skills = analysis['skills'].split(", ") if analysis['skills'] else []
                    education = analysis['education'].split(", ") if analysis['education'] else []
                    experience = analysis['experience'].split(", ") if analysis['experience'] else []
                    suggestions = analysis['feedback'].split(", ") if analysis['feedback'] else []
                    
                    # Create analysis dict
                    analysis_result = {
                        "status": "success",
                        "skills": skills,
                        "education": education,
                        "experience": experience,
                        "score": analysis['score'],
                        "suggestions": suggestions,
                        "text_length": 0  # Not stored in DB
                    }
                    
                    # Display analysis
                    display_resume_analysis(analysis_result)
                else:
                    st.warning("No analysis found for this resume. Try re-uploading it.")
            
            if st.button("Delete", key=f"delete-btn-{resume['id']}", help="Delete this resume", style="visibility: hidden;"):
                # Implement delete functionality
                st.error("Delete functionality not yet implemented")

def job_matching_page():
    st.markdown("""
    <div class="custom-card">
        <h1 style="color: #0071e3; text-align: center;">Job Matching</h1>
        <p style="text-align: center;">Find jobs that match your resume</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get user's resumes
    resumes = db.get_user_resumes(st.session_state.user_id)
    
    if not resumes:
        st.markdown("""
        <div class="warning-box">
            <p>You haven't uploaded any resumes yet. Please upload a resume first to match with jobs.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Select resume to match
    resume_options = {resume['id']: resume['filename'] for resume in resumes}
    selected_resume_id = st.selectbox("Select Resume to Match", options=list(resume_options.keys()), 
                                     format_func=lambda x: resume_options[x])
    
    if selected_resume_id:
        # Get available jobs
        jobs = db.get_all_jobs()
        
        if not jobs:
            st.markdown("""
            <div class="warning-box">
                <p>There are no job postings available yet. Please check back later.</p>
            </div>
            """, unsafe_allow_html=True)
            return
        
        # Get selected resume analysis
        resume_analysis = db.get_resume_analysis(selected_resume_id)
        
        if not resume_analysis:
            st.warning("No analysis found for this resume. Please re-upload it.")
            return
        
        # Convert analysis data for matching
        analysis_data = {
            "skills": resume_analysis['skills'].split(", ") if resume_analysis['skills'] else [],
            "education": resume_analysis['education'].split(", ") if resume_analysis['education'] else [],
            "experience": resume_analysis['experience'].split(", ") if resume_analysis['experience'] else [],
        }
        
        # Match with jobs
        st.markdown("### Job Matches")
        
        for job in jobs:
            # Match resume to job
            match_result = match_resume_to_job(analysis_data, job)
            
            # Save match to database
            db.save_resume_job_match(selected_resume_id, job['id'], 
                                   match_result['match_score'],
                                   match_result['match_details'])
            
            # Determine match color class
            if match_result['match_score'] >= 75:
                match_class = "match-high"
            elif match_result['match_score'] >= 50:
                match_class = "match-medium"
            else:
                match_class = "match-low"
            
            # Display job card with match score
            st.markdown(f"""
            <div class="custom-card job-card">
                <h3>{job['title']}</h3>
                <p>{job['description'][:150]}...</p>
                <p><strong>Skills Required:</strong> {job['required_skills']}</p>
                <p><strong>Match Score:</strong> <span class="{match_class}">{match_result['match_score']}%</span></p>
            </div>
            """, unsafe_allow_html=True)
            
            # Show match details in expander
            with st.expander("Match Details"):
                for detail in match_result['match_details']:
                    st.write(detail)

def post_job_page():
    st.markdown("""
    <div class="custom-card">
        <h1 style="color: #4F46E5; text-align: center;">Post a Job</h1>
        <p style="text-align: center;">Create a new job posting to find matching candidates</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Job posting form
    with st.form("job_posting_form"):
        job_title = st.text_input("Job Title")
        job_description = st.text_area("Job Description", height=150)
        required_skills = st.text_input("Required Skills (comma-separated)")
        required_education = st.text_input("Required Education")
        required_experience = st.text_input("Required Experience")
        
        submitted = st.form_submit_button("Post Job")
        
        if submitted:
            if job_title and job_description and required_skills:
                # Save job posting to database
                job_id = db.create_job_posting(
                    st.session_state.user_id,
                    job_title,
                    job_description,
                    required_skills,
                    required_education,
                    required_experience
                )
                
                if job_id:
                    st.success("Job posted successfully!")
                    # Show success animation with fallback
                    success_animation = load_lottie_url("https://assets6.lottiefiles.com/packages/lf20_swnc1xqy.json")
                    if success_animation is None:
                        success_animation = load_lottie_fallback()
                    display_lottie(success_animation, height=150)
                else:
                    st.error("Error posting job. Please try again.")
            else:
                st.warning("Please fill in all required fields (title, description, and skills).")

def my_postings_page():
    st.markdown("""
    <div class="custom-card">
        <h1 style="color: #4F46E5; text-align: center;">My Job Postings</h1>
        <p style="text-align: center;">View and manage your job postings</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get recruiter's job postings
    jobs = db.get_recruiter_jobs(st.session_state.user_id)
    
    if not jobs:
        st.markdown("""
        <div class="custom-card">
            <p style="text-align: center;">You haven't posted any jobs yet.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # No jobs animation with fallback
        empty_animation = load_lottie_url("https://assets5.lottiefiles.com/packages/lf20_ydo1amjm.json")
        if empty_animation is None:
            empty_animation = load_lottie_fallback()
        display_lottie(empty_animation)
        
        st.markdown("""
        <div class="custom-card">
            <p style="text-align: center;">Head over to the Post Job section to create your first job posting!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Display job postings in cards
        for job in jobs:
            st.markdown(f"""
            <div class="custom-card job-card">
                <h3>{job['title']}</h3>
                <p><strong>Posted on:</strong> {job['posted_at']}</p>
                <p>{job['description'][:200]}...</p>
                <p><strong>Required Skills:</strong> {job['required_skills']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # View matches for this job posting
            if st.button(f"View Matches", key=f"matches_{job['id']}"):
                matches = db.get_resume_job_matches(job_id=job['id'])
                
                if matches:
                    st.markdown("### Candidate Matches")
                    
                    # Sort matches by score (highest first)
                    matches.sort(key=lambda x: x['match_score'], reverse=True)
                    
                    for match in matches:
                        # Determine match color class
                        if match['match_score'] >= 75:
                            match_class = "match-high"
                        elif match['match_score'] >= 50:
                            match_class = "match-medium"
                        else:
                            match_class = "match-low"
                        
                        # Display match card
                        st.markdown(f"""
                        <div class="custom-card">
                            <h4>{match['filename']}</h4>
                            <p><strong>Match Score:</strong> <span class="{match_class}">{match['match_score']}%</span></p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Show match details in expander
                        with st.expander("Match Details"):
                            st.write(match['match_details'])
                else:
                    st.info("No candidate matches found for this job posting yet.")

def resume_matching_page():
    st.markdown("""
    <div class="custom-card">
        <h1 style="color: #4F46E5; text-align: center;">Resume Matching</h1>
        <p style="text-align: center;">Match resumes to your job postings</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get recruiter's job postings
    jobs = db.get_recruiter_jobs(st.session_state.user_id)
    
    if not jobs:
        st.markdown("""
        <div class="warning-box">
            <p>You haven't posted any jobs yet. Please create a job posting first.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Select job to match
    job_options = {job['id']: job['title'] for job in jobs}
    selected_job_id = st.selectbox("Select Job Posting", options=list(job_options.keys()), 
                                  format_func=lambda x: job_options[x])
    
    if selected_job_id:
        # Get the selected job details
        selected_job = None
        for job in jobs:
            if job['id'] == selected_job_id:
                selected_job = job
                break
        
        if not selected_job:
            st.error("Job not found")
            return
        
        # Allow resume upload for matching
        st.markdown("### Upload Resume to Match")
        uploaded_file = st.file_uploader("Upload Resume (PDF or DOCX)", type=['pdf', 'docx'])
        
        if uploaded_file is not None:
            # Temporarily save the file
            temp_dir = os.path.join("uploads", "temp")
            os.makedirs(temp_dir, exist_ok=True)
            file_path = os.path.join(temp_dir, uploaded_file.name)
            
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            with st.spinner("Analyzing resume..."):
                # Analyze the resume (without saving to DB)
                analysis_result = analyze_resume(file_path)
                
                if analysis_result["status"] == "success":
                    # Match with selected job
                    match_result = match_resume_to_job(analysis_result, selected_job)
                    
                    # Determine match color class
                    if match_result['match_score'] >= 75:
                        match_class = "match-high"
                    elif match_result['match_score'] >= 50:
                        match_class = "match-medium"
                    else:
                        match_class = "match-low"
                    
                    # Display match result
                    st.markdown(f"""
                    <div class="custom-card">
                        <h3>Match Result</h3>
                        <p><strong>Resume:</strong> {uploaded_file.name}</p>
                        <p><strong>Job:</strong> {selected_job['title']}</p>
                        <p><strong>Match Score:</strong> <span class="{match_class}">{match_result['match_score']}%</span></p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show match details
                    st.markdown("### Match Details")
                    for detail in match_result['match_details']:
                        st.write(detail)
                    
                    # Show resume analysis
                    with st.expander("View Resume Analysis"):
                        display_resume_analysis(analysis_result)
                else:
                    st.error(analysis_result["message"])

def about_page():
    st.markdown("""
    <div class="custom-card">
        <h1 style="color: #4F46E5; text-align: center;">About Smart Resume Analyzer</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # About animation with fallback
    about_animation = load_lottie_url("https://assets1.lottiefiles.com/packages/lf20_v4isjbj5.json")
    if about_animation is None:
        about_animation = load_lottie_fallback()
    display_lottie(about_animation, height=300)
    
    st.markdown("""
    <div class="custom-card">
        <h3>What is Smart Resume Analyzer?</h3>
        <p>
        The Smart Resume Analyzer is an AI-driven web application designed to automate and enhance the
        resume screening process for both job seekers and recruiters. By leveraging Natural Language Processing
        (NLP) and structured rule-based evaluation, it provides transparent, actionable feedback, helping
        candidates optimize their resumes for modern recruitment systems and enabling recruiters to efficiently
        identify the best-fit candidates.
        </p>
        
        <h3>Features</h3>
        <ul>
            <li>Resume parsing and analysis using NLP</li>
            <li>Skills extraction and matching</li>
            <li>Resume scoring and feedback</li>
            <li>Job-Resume matching</li>
            <li>Visual representations of resume content</li>
            <li>User accounts for both job seekers and recruiters</li>
        </ul>
        
        <h3>Technologies Used</h3>
        <ul>
            <li>Frontend & Backend: Streamlit (Python-based web framework)</li>
            <li>NLP: spaCy</li>
            <li>Database: SQLite3</li>
            <li>Document Processing: PyPDF2 and python-docx</li>
            <li>Data Visualization: Matplotlib, Plotly</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Run the app
if __name__ == "__main__":
    main()
