import os
import re
import spacy
import PyPDF2
import docx2txt
from wordcloud import WordCloud
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sqlite3

# Load spaCy NLP model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model...")
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    text = ""
    try:
        with open(pdf_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page_num in range(len(pdf_reader.pages)):
                text += pdf_reader.pages[page_num].extract_text()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
    return text

def extract_text_from_docx(docx_path):
    """Extract text from DOCX file"""
    try:
        text = docx2txt.process(docx_path)
        return text
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return ""

def extract_text(file_path):
    """Extract text from uploaded resume file"""
    file_extension = os.path.splitext(file_path)[1].lower()
    
    if file_extension == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_extension == '.docx':
        return extract_text_from_docx(file_path)
    else:
        return ""

def preprocess_text(text):
    """Clean and preprocess the extracted text"""
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters and numbers (but keep spaces between words)
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)
    
    return text.strip()

def extract_entities(text):
    """Extract entities (skills, education, experience, etc.) using spaCy NER"""
    doc = nlp(text)
    
    entities = {
        'PERSON': [],
        'ORG': [],
        'GPE': [],  # Geopolitical Entity (countries, cities, etc.)
        'DATE': [],
        'LANGUAGE': []
    }
    
    for ent in doc.ents:
        if ent.label_ in entities:
            entities[ent.label_].append(ent.text)
    
    return entities

def extract_skills(text):
    """Extract skills from resume text using a predefined skill list"""
    # Common technical skills list
    skills_list = [
        # Programming Languages
        "python", "java", "javascript", "c++", "c#", "ruby", "php", "swift", "kotlin", "golang",
        "typescript", "scala", "perl", "r", "matlab", "bash", "shell", "sql", "html", "css",
        
        # Frameworks & Libraries
        "react", "angular", "vue", "django", "flask", "spring", "express", "node.js", "tensorflow",
        "pytorch", "keras", "scikit-learn", "pandas", "numpy", "matplotlib", "bootstrap", "jquery",
        
        # Databases
        "mysql", "postgresql", "mongodb", "oracle", "sql server", "sqlite", "redis", "cassandra",
        "dynamodb", "firebase",
        
        # Cloud Platforms
        "aws", "azure", "google cloud", "gcp", "heroku", "digitalocean", "kubernetes", "docker",
        
        # Tools & Software
        "git", "jenkins", "jira", "confluence", "tableau", "power bi", "excel", "photoshop",
        "illustrator", "figma", "sketch", "invision",
        
        # Methodologies
        "agile", "scrum", "kanban", "waterfall", "devops", "ci/cd", "test-driven development", "tdd",
        
        # Soft Skills
        "communication", "teamwork", "leadership", "problem-solving", "critical thinking",
        "time management", "creativity", "adaptability", "emotional intelligence"
    ]
    
    found_skills = []
    processed_text = text.lower()
    
    for skill in skills_list:
        if re.search(r'\b' + re.escape(skill) + r'\b', processed_text):
            found_skills.append(skill)
    
    return found_skills

def extract_education(text):
    """Extract education information from resume"""
    education_keywords = [
        "bachelor", "master", "phd", "doctorate", "diploma", "certificate", 
        "degree", "b.tech", "m.tech", "b.e.", "m.e.", "b.sc", "m.sc",
        "b.a.", "m.a.", "mba", "bba", "college", "university", "institute",
        "school of", "academy"
    ]
    
    education_info = []
    lines = text.lower().split('\n')
    
    for i, line in enumerate(lines):
        if any(keyword in line for keyword in education_keywords):
            # Get the current line and potentially the next line for more context
            edu_text = line
            if i + 1 < len(lines):
                edu_text += " " + lines[i + 1]
            education_info.append(edu_text.strip())
    
    return education_info

def extract_experience(text):
    """Extract work experience from resume"""
    # Look for common experience section headers
    experience_sections = re.findall(
        r'(?:work|professional|employment)(?:\s+experience|\s+history)?.*?(?=\n\s*\n|$)', 
        text.lower(), 
        re.DOTALL
    )
    
    if not experience_sections:
        return []
    
    # Extract experience items (looking for dates, position titles, company names)
    experience_items = []
    
    for section in experience_sections:
        # Look for dates with various formats (MM/YYYY, Month YYYY, YYYY-YYYY)
        date_patterns = [
            r'\b\d{1,2}/\d{4}\b',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b',
            r'\b\d{4}\s*-\s*(?:\d{4}|present|current)\b',
            r'\b\d{4}\s*to\s*(?:\d{4}|present|current)\b'
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, section, re.IGNORECASE)
            for match in matches:
                start_pos = match.start()
                # Get context around the date (likely job details)
                context_start = max(0, start_pos - 100)
                context_end = min(len(section), start_pos + 200)
                context = section[context_start:context_end]
                experience_items.append(context.strip())
    
    return experience_items

def generate_wordcloud(text, file_name="wordcloud.png"):
    """Generate word cloud from resume text"""
    processed_text = preprocess_text(text)
    
    # Create and generate a word cloud image
    wordcloud = WordCloud(width=800, height=400, 
                         background_color='white',
                         min_font_size=10).generate(processed_text)
    
    # Save the image
    save_path = os.path.join('static/images', file_name)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    wordcloud.to_file(save_path)
    
    return save_path

def calculate_resume_score(skills, education, experience):
    """Calculate resume score based on extracted information"""
    score = 0
    
    # Score based on number of skills (max 40 points)
    skill_count = len(skills)
    skill_score = min(skill_count * 4, 40)
    score += skill_score
    
    # Score based on education (max 30 points)
    education_score = min(len(education) * 15, 30)
    score += education_score
    
    # Score based on experience (max 30 points)
    experience_score = min(len(experience) * 10, 30)
    score += experience_score
    
    return score

def get_improvement_suggestions(skills, education, experience, score):
    """Generate improvement suggestions based on analysis"""
    suggestions = []
    
    if score < 50:
        suggestions.append("Your resume needs significant improvement.")
    elif score < 70:
        suggestions.append("Your resume has a good foundation but needs enhancements.")
    else:
        suggestions.append("Your resume is strong, but minor improvements could make it excellent.")
    
    # Skill suggestions
    if len(skills) < 5:
        suggestions.append("Add more relevant technical and soft skills to your resume.")
    elif len(skills) < 10:
        suggestions.append("Consider adding more specialized skills that showcase your expertise.")
    
    # Education suggestions
    if not education:
        suggestions.append("Add your educational background, including degrees and certifications.")
    elif len(education) == 1:
        suggestions.append("Consider adding more educational details or relevant coursework.")
    
    # Experience suggestions
    if not experience:
        suggestions.append("Add work experience section with detailed responsibilities and achievements.")
    elif len(experience) < 2:
        suggestions.append("Expand your work experience with measurable achievements and results.")
    
    return suggestions

def save_analysis_to_db(resume_id, skills, education, experience, score, feedback):
    """Save analysis results to database"""
    conn = sqlite3.connect('database/resume_analyzer.db')
    cursor = conn.cursor()
    
    # Convert lists to strings for storage
    skills_str = ", ".join(skills)
    education_str = ", ".join(education)
    experience_str = ", ".join(experience)
    feedback_str = ", ".join(feedback)
    
    cursor.execute('''
    INSERT INTO analysis_results 
    (resume_id, skills, education, experience, score, feedback)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (resume_id, skills_str, education_str, experience_str, score, feedback_str))
    
    conn.commit()
    analysis_id = cursor.lastrowid
    conn.close()
    
    return analysis_id

def analyze_resume(file_path, resume_id=None):
    """Main function to analyze a resume file"""
    # Extract text from resume
    text = extract_text(file_path)
    if not text:
        return {
            "status": "error",
            "message": "Could not extract text from the file. Please check the file format."
        }
    
    # Extract information
    skills = extract_skills(text)
    education = extract_education(text)
    experience = extract_experience(text)
    
    # Calculate score
    score = calculate_resume_score(skills, education, experience)
    
    # Get improvement suggestions
    suggestions = get_improvement_suggestions(skills, education, experience, score)
    
    # Generate word cloud
    wordcloud_path = generate_wordcloud(text, f"wordcloud_{os.path.basename(file_path)}.png")
    
    # Save to database if resume_id provided
    if resume_id:
        save_analysis_to_db(resume_id, skills, education, experience, score, suggestions)
    
    # Return analysis results
    return {
        "status": "success",
        "text_length": len(text),
        "skills": skills,
        "education": education,
        "experience": experience,
        "score": score,
        "suggestions": suggestions,
        "wordcloud_path": wordcloud_path
    }

def match_resume_to_job(resume_analysis, job_posting):
    """Match a resume to a job posting and calculate match score"""
    match_score = 0
    match_details = []
    
    # Extract job requirements
    required_skills = job_posting["required_skills"].lower().split(",")
    required_skills = [skill.strip() for skill in required_skills]
    
    # Match skills (50% of match score)
    matching_skills = [skill for skill in resume_analysis["skills"] if skill.lower() in required_skills]
    skill_match_percentage = len(matching_skills) / len(required_skills) if required_skills else 0
    skill_score = skill_match_percentage * 50
    match_score += skill_score
    
    match_details.append(f"Skills match: {len(matching_skills)}/{len(required_skills)} ({skill_match_percentage:.0%})")
    
    # Match education (25% of match score)
    education_keywords = job_posting["required_education"].lower().split()
    education_match = any(any(keyword in edu.lower() for keyword in education_keywords) 
                         for edu in resume_analysis["education"]) if education_keywords else True
    
    education_score = 25 if education_match else 0
    match_score += education_score
    
    match_details.append(f"Education match: {'Yes' if education_match else 'No'}")
    
    # Match experience (25% of match score)
    experience_match = len(resume_analysis["experience"]) > 0
    experience_score = 25 if experience_match else 0
    match_score += experience_score
    
    match_details.append(f"Experience match: {'Yes' if experience_match else 'No'}")
    
    return {
        "match_score": match_score,
        "match_details": match_details
    }
