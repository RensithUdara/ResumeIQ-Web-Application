# ResumeIQ Web Application

An AI-driven web application designed to automate and enhance the resume screening process for both job seekers and recruiters. By leveraging Natural Language Processing (NLP) and structured rule-based evaluation, it provides transparent, actionable feedback, helping candidates optimize their resumes for modern recruitment systems and enabling recruiters to efficiently identify the best-fit candidates.

![ResumeIQ Web Application](https://img.icons8.com/fluency/96/000000/resume.png)

## Status

This project is currently in active development. If you encounter any issues, please check the [troubleshooting guide](TROUBLESHOOTING.md) or report them in the GitHub issues section.

## Features

- **Resume Analysis**: Extract key information from resumes including skills, education, and work experience
- **Resume Scoring**: Evaluate resumes based on content quality and completeness
- **Visual Insights**: Generate visual representations of resume content (word clouds, skills graphs)
- **Job-Resume Matching**: Match resumes to job postings based on skills and requirements
- **Improvement Suggestions**: Get actionable feedback to improve your resume
- **Dual Interface**: Separate interfaces for job seekers and recruiters
- **Modern UI**: Clean, responsive design with animations and intuitive navigation

## Technologies Used

- **Frontend & Backend**: Streamlit (Python-based web framework)
- **NLP**: spaCy for natural language processing
- **Database**: SQLite3 for storing resumes, analysis results, and user feedback
- **Document Processing**: PyPDF2 and python-docx for extracting text from resumes
- **Data Visualization**: Matplotlib and Plotly for visualizing resume data
- **UI Enhancements**: Streamlit-Lottie for animations, custom CSS for modern styling

## Getting Started

### Prerequisites

- Python 3.8+
- pip package manager

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/smart-resume-analyzer.git
   cd smart-resume-analyzer
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Download the spaCy model:
   ```
   python -m spacy download en_core_web_sm
   ```

4. Initialize the database:
   ```
   python database/db_setup.py
   ```

### Running the Application

Run the Streamlit app:
```
streamlit run app.py
```

The application will be accessible at http://localhost:8501 in your web browser.

## Usage

### For Job Seekers

1. Create an account as a job seeker
2. Upload your resume in PDF or DOCX format
3. View detailed analysis including skills detection, education verification, and experience extraction
4. Get a score and improvement suggestions for your resume
5. Match your resume with available job postings

### For Recruiters

1. Create an account as a recruiter
2. Post job openings with required skills, education, and experience
3. Upload candidate resumes to match with your job postings
4. View detailed match scores and insights
5. Manage all your job postings and view candidate matches

## Project Structure

```
smart-resume-analyzer/
│
├── app.py                  # Main Streamlit application
├── requirements.txt        # Project dependencies
│
├── database/               # Database related files
│   ├── db_setup.py         # Database initialization script
│   ├── db_manager.py       # Database operations manager
│   └── resume_analyzer.db  # SQLite database file
│
├── utils/                  # Utility functions
│   ├── resume_parser.py    # Resume parsing and analysis logic
│   └── ...
│
├── static/                 # Static files
│   ├── css/                # Custom CSS styles
│   │   └── style.css       # Main stylesheet
│   └── images/             # Generated images and icons
│
├── uploads/                # Directory for uploaded resumes
│   └── ...
│
└── models/                 # Custom models (if any)
    └── ...
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Icon8 for the resume icon
- LottieFiles for the animations used in the application

## Troubleshooting

If you encounter any issues while setting up or running the application, please refer to the [troubleshooting guide](TROUBLESHOOTING.md) for common problems and solutions.
