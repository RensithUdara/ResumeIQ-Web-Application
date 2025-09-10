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
    page_title="Smart Resume Analyzer",
    page_icon="📑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
db = DatabaseManager()

# Function to load custom CSS
def load_css():
    with open('static/css/style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

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
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_type = None
    st.session_state.username = None
    st.experimental_rerun()

# Main App UI
def main():
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/000000/resume.png", width=80)
        st.title("Smart Resume Analyzer")
        
        if st.session_state.logged_in:
            st.write(f"Welcome, **{st.session_state.username}**!")
            
            if st.session_state.user_type == "job_seeker":
                menu = option_menu(
                    "Main Menu",
                    ["Resume Upload", "My Resumes", "Job Matching", "About"],
                    icons=["cloud-upload", "file-earmark-text", "briefcase", "info-circle"],
                    menu_icon="list",
                    default_index=0,
                )
            else:  # recruiter
                menu = option_menu(
                    "Main Menu",
                    ["Post Job", "My Postings", "Resume Matching", "About"],
                    icons=["pencil-square", "clipboard-check", "people", "info-circle"],
                    menu_icon="list",
                    default_index=0,
                )
                
            st.button("Logout", on_click=logout)
        else:
            auth_option = option_menu(
                "Authentication",
                ["Login", "Signup"],
                icons=["box-arrow-in-right", "person-plus"],
                menu_icon="lock",
                default_index=0,
            )
    
    # Main content
    if not st.session_state.logged_in:
        if 'auth_option' in locals() and auth_option == "Login":
            login_form()
        else:
            signup_form()
    else:
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

# Page content functions
def resume_upload_page():
    st.markdown("""
    <div class="custom-card">
        <h1 style="color: #4F46E5; text-align: center;">Upload Your Resume</h1>
        <p style="text-align: center;">Upload your resume to get detailed analysis and improvement suggestions</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Upload animation with fallback
    upload_animation = load_lottie_url("https://assets9.lottiefiles.com/packages/lf20_nw19osms.json")
    if upload_animation is None:
        upload_animation = load_lottie_fallback()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        display_lottie(upload_animation, height=250)
    
    with col2:
        uploaded_file = st.file_uploader("Upload Your Resume (PDF or DOCX)", type=['pdf', 'docx'])
        
        if uploaded_file is not None:
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
    # Display score
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
        st.plotly_chart(create_score_gauge(analysis["score"]), use_container_width=True)
        st.markdown(f"<div style='text-align: center;'><h3>Overall Score</h3></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
        st.metric("Skills Detected", len(analysis["skills"]))
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
        st.metric("Content Length", analysis["text_length"], "characters")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Display tabs with detailed information
    tab1, tab2, tab3, tab4 = st.tabs(["Skills", "Education", "Experience", "Suggestions"])
    
    with tab1:
        st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
        st.markdown("### Detected Skills")
        if analysis["skills"]:
            skills_html = ""
            for skill in analysis["skills"]:
                skills_html += f"<span class='skill-tag'>{skill}</span>"
            st.markdown(f"<div style='line-height: 2.5;'>{skills_html}</div>", unsafe_allow_html=True)
        else:
            st.warning("No skills detected. Consider adding more technical skills to your resume.")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab2:
        st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
        st.markdown("### Education Details")
        if analysis["education"]:
            for edu in analysis["education"]:
                st.markdown(f"• {edu}")
        else:
            st.warning("No education details detected. Make sure your education section is clearly formatted.")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab3:
        st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
        st.markdown("### Experience Details")
        if analysis["experience"]:
            for exp in analysis["experience"]:
                st.markdown(f"• {exp}")
        else:
            st.warning("No work experience detected. Make sure your work experience section is clearly formatted.")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab4:
        st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
        st.markdown("### Improvement Suggestions")
        for suggestion in analysis["suggestions"]:
            st.markdown(f"• {suggestion}")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Display word cloud
    if "wordcloud_path" in analysis and analysis["wordcloud_path"]:
        st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
        st.markdown("### Resume Word Cloud")
        st.image(analysis["wordcloud_path"])
        st.markdown("</div>", unsafe_allow_html=True)

def my_resumes_page():
    st.markdown("""
    <div class="custom-card">
        <h1 style="color: #4F46E5; text-align: center;">My Resumes</h1>
        <p style="text-align: center;">View and manage all your uploaded resumes</p>
    </div>
    """, unsafe_allow_html=True)
    
    resumes = db.get_user_resumes(st.session_state.user_id)
    
    if not resumes:
        st.markdown("""
        <div class="custom-card">
            <p style="text-align: center;">You haven't uploaded any resumes yet.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # No resumes animation with fallback
        empty_animation = load_lottie_url("https://assets5.lottiefiles.com/packages/lf20_ydo1amjm.json")
        if empty_animation is None:
            empty_animation = load_lottie_fallback()
        display_lottie(empty_animation)
        
        st.markdown("""
        <div class="custom-card">
            <p style="text-align: center;">Head over to the Resume Upload section to analyze your first resume!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Display resumes in cards
        for resume in resumes:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                <div class="custom-card">
                    <h3>{resume['filename']}</h3>
                    <p>Uploaded on: {resume['uploaded_at']}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if st.button(f"View Analysis", key=f"view_{resume['id']}"):
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
                
                if st.button(f"Delete", key=f"delete_{resume['id']}"):
                    # Implement delete functionality
                    # This would need additional DB methods
                    st.error("Delete functionality not yet implemented")

def job_matching_page():
    st.markdown("""
    <div class="custom-card">
        <h1 style="color: #4F46E5; text-align: center;">Job Matching</h1>
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
