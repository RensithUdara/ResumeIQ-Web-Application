import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path='database/resume_analyzer.db'):
        """Initialize database connection"""
        self.db_path = db_path
        # Ensure database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database if it doesn't exist
        if not os.path.exists(db_path):
            from database.db_setup import create_database
            create_database()
    
    def _connect(self):
        """Create a connection to the database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    
    # User Management
    def create_user(self, username, password, user_type):
        """Create a new user"""
        conn = self._connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO users (username, password, user_type) VALUES (?, ?, ?)",
                (username, password, user_type)
            )
            conn.commit()
            user_id = cursor.lastrowid
            return {"status": "success", "user_id": user_id}
        except sqlite3.IntegrityError:
            return {"status": "error", "message": "Username already exists"}
        finally:
            conn.close()
    
    def authenticate_user(self, username, password):
        """Authenticate a user"""
        conn = self._connect()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, username, user_type FROM users WHERE username = ? AND password = ?",
            (username, password)
        )
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                "status": "success", 
                "user_id": user["id"], 
                "username": user["username"], 
                "user_type": user["user_type"]
            }
        else:
            return {"status": "error", "message": "Invalid username or password"}
    
    def get_user_by_id(self, user_id):
        """Get user info by ID"""
        conn = self._connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, username, user_type FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return dict(user)
        else:
            return None
    
    # Resume Management
    def save_resume(self, user_id, filename, file_path):
        """Save uploaded resume information"""
        conn = self._connect()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO resumes (user_id, filename, file_path) VALUES (?, ?, ?)",
            (user_id, filename, file_path)
        )
        conn.commit()
        resume_id = cursor.lastrowid
        conn.close()
        
        return resume_id
    
    def get_resume(self, resume_id):
        """Get resume information"""
        conn = self._connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,))
        resume = cursor.fetchone()
        conn.close()
        
        if resume:
            return dict(resume)
        else:
            return None
    
    def get_user_resumes(self, user_id):
        """Get all resumes for a user"""
        conn = self._connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM resumes WHERE user_id = ? ORDER BY uploaded_at DESC", (user_id,))
        resumes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return resumes
    
    # Analysis Management
    def get_analysis(self, analysis_id):
        """Get resume analysis result"""
        conn = self._connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM analysis_results WHERE id = ?", (analysis_id,))
        analysis = cursor.fetchone()
        conn.close()
        
        if analysis:
            return dict(analysis)
        else:
            return None
    
    def get_resume_analysis(self, resume_id):
        """Get analysis for a specific resume"""
        conn = self._connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM analysis_results WHERE resume_id = ? ORDER BY analyzed_at DESC", (resume_id,))
        analysis = cursor.fetchone()
        conn.close()
        
        if analysis:
            return dict(analysis)
        else:
            return None
            
    def get_resume_score(self, resume_id):
        """Get only the score for a specific resume (for display in cards)"""
        conn = self._connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT score FROM analysis_results WHERE resume_id = ? ORDER BY analyzed_at DESC", (resume_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result['score']
        else:
            return 0
    
    # Job Posting Management (for recruiters)
    def create_job_posting(self, user_id, title, description, required_skills, required_education, required_experience):
        """Create a new job posting"""
        conn = self._connect()
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO job_postings 
            (user_id, title, description, required_skills, required_education, required_experience) 
            VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, title, description, required_skills, required_education, required_experience)
        )
        conn.commit()
        job_id = cursor.lastrowid
        conn.close()
        
        return job_id
    
    def get_job_posting(self, job_id):
        """Get job posting information"""
        conn = self._connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM job_postings WHERE id = ?", (job_id,))
        job = cursor.fetchone()
        conn.close()
        
        if job:
            return dict(job)
        else:
            return None
    
    def get_recruiter_jobs(self, user_id):
        """Get all job postings for a recruiter"""
        conn = self._connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM job_postings WHERE user_id = ? ORDER BY posted_at DESC", (user_id,))
        jobs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jobs
    
    def get_all_jobs(self):
        """Get all job postings"""
        conn = self._connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM job_postings ORDER BY posted_at DESC")
        jobs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jobs
    
    # Resume-Job Matching
    def save_resume_job_match(self, resume_id, job_id, match_score, match_details):
        """Save a resume-job match result"""
        conn = self._connect()
        cursor = conn.cursor()
        
        # Convert match_details list to string
        if isinstance(match_details, list):
            match_details = "\n".join(match_details)
        
        cursor.execute(
            "INSERT INTO resume_job_matches (resume_id, job_id, match_score, match_details) VALUES (?, ?, ?, ?)",
            (resume_id, job_id, match_score, match_details)
        )
        conn.commit()
        match_id = cursor.lastrowid
        conn.close()
        
        return match_id
    
    def get_resume_job_matches(self, resume_id=None, job_id=None):
        """Get resume-job match results"""
        conn = self._connect()
        cursor = conn.cursor()
        
        if resume_id and job_id:
            cursor.execute(
                "SELECT * FROM resume_job_matches WHERE resume_id = ? AND job_id = ?", 
                (resume_id, job_id)
            )
        elif resume_id:
            cursor.execute(
                """SELECT m.*, j.title, j.description 
                FROM resume_job_matches m 
                JOIN job_postings j ON m.job_id = j.id 
                WHERE m.resume_id = ? 
                ORDER BY m.match_score DESC""", 
                (resume_id,)
            )
        elif job_id:
            cursor.execute(
                """SELECT m.*, r.filename 
                FROM resume_job_matches m 
                JOIN resumes r ON m.resume_id = r.id 
                WHERE m.job_id = ? 
                ORDER BY m.match_score DESC""", 
                (job_id,)
            )
        else:
            cursor.execute("SELECT * FROM resume_job_matches ORDER BY matched_at DESC")
        
        matches = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return matches
