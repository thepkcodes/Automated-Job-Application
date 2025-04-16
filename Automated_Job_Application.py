import streamlit as st
import pandas as pd
import random
import time
from datetime import datetime
import sqlite3
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
import re
import json

# Set up the Streamlit page configuration
st.set_page_config(
    page_title = "Job Application Agent",
    page_icon = "💼",
    layout = "wide",
    initial_sidebar_state = "expanded"
)

# Database setup
def init_db():
    conn = sqlite3.connect('job_applications.db')
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY,
        job_title TEXT,
        company TEXT,
        location TEXT,
        job_description TEXT,
        salary TEXT,
        job_url TEXT,
        platform TEXT,
        date_applied TEXT,
        status TEXT,
        matching_score REAL,
        notes TEXT
    )          
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS user_profile (
        id INTEGER PRIMARY KEY,
        full_name TEXT,
        email TEXT,
        phone TEXT,
        resume_path TEXT,
        skills TEXT,
        experience TEXT,
        education TEXT,
        preference TEXT
    )
    ''')

    conn.commit()
    conn.close()

init_db()

# CSS styling
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    color: #2E86C1;
    text-align: center;
    margin-bottom: 1rem;
}
.sub-header {
    font-size: 1.8rem;
    color: #3498DB;
    margin-top: 2rem;
    margin-bottom: 1rem;
}
.card {
    background-color: #f8f9fa;
    border-radius: 10px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 0 10px rgba(0,0,0,0.1):
}
.info-text {
    color: #5D6D7E;
    font-size: 1rem;
}
.highlight {
    background-color: #E8F8F5;
    padding: 0.5rem;
    border-radius: 5px;
    font-weight: bold;
}
.status-applied {
    color: #27AE60;
    font-weight: bold;
}
.status-pending {
    color: #F39C12;
    font-weight: bold;
}
.status-rejected {
    color: #E74C3C;
    font-weight: bold;
}
.status-interview {
    color: #3498DB;
    font-weight: bold;
}
.match-score-high {
    color: #27AE60;
}
.match-score-medium {
    color: #F39C12;
}
.match-score-low {
    color: #E74C3C;
}
.sidebar .sidebar-content {
    background-color: #F8F9F9;
}
</style>
""", unsafe_allow_html = True)

# Sidebar navigation
st.sidebar.markdown("# 💼 Job Application Agent")
page = st.sidebar.radio("Navigation", ["Dashboard", "Job Search", "Profile Setup", "Application Settings", "Job Tracker", "Analytics"])

# Helper functions for job search and application
def scrape_jobs(keywords, location, platforms, num_results = 20):
    """Simulate scraping jobs from various platforms"""
    all_jobs = []

    job_titles = [
        "Data Scientist", "Software Engineer", "Product Manager", "UX Desginer", "Marketing Specialist", "DevOps Engineer",
        "Full Stack Developer", "Machine Learning Engineer", "Frontend Developer", "Backend Developer", "Project Manager",
        "Business Analyst", "Data Analyst", "UI Designer", "Content Writer", "Sales Representative", "Customer Success Manager"
    ]

    companies = [
        "Google", "Microsoft", "Amazon", "Apple", "Meta", "Netflix", "Spotify", "Salesforce", "Adobe", "IBM", "Orcale", "Cisco",
        "Intel", "Uber", "Airbnb", "X", "LinkedIn", "Slack", "Zoom", "PayPal", "Square", "Shopify", "Nvidia", "Tesla"
    ] 

    locations = [
        "CA", "NY", "WA", "TX", "CT", "MA", "GA", "FL", "OR", "CO", "IL", "AZ"
    ]

    # For each selected platform, generate simulated job listings
    for platform in platforms:
        platform_jobs = []
        for _ in range(num_results // len(platforms) + 1):
            # Generate a job that has higher chance of matching keywords
            if random.random() < 0.7 and keywords:
                # Use one of the keywords in the job title
                keyword = random.choice(keywords.split())
                job_title = random.choice([
                    f"Senior {keyword} Developer",
                    f"{keyword} Engineer",
                    f"{keyword} Specialist",
                    f"Lead {keyword} Architect"
                ])
            else:
                job_title = random.choice(job_titles)

            if location and random.random() < 0.8:
                job_location = location
            else:
                job_location = random.choice(locations)

            company = random.choice(companies)

            # Create a realistic job description based on the title
            skills_required = random.sample([
                "Python", "JavaScript", "SQL", "React", "Node.js", "AWS", "Docker", "Kubernetes", "TensorFlow",
                "PyTorch", "Excel", "Tableau", "PowerBI", "Figma", "Sketch", "JIRA", "Git", "SnowFlake", "Artificial Intelligence",
                "Machine Learning", "Deep Learning", "NLP"
            ], k = random.randit(3, 7))

            experience = f"{random.randint(1, 8)}+ years"

            job_description = f"""
            {company} is seeking a {job_title} to join our growing team in {job_location}.

            Responsibilities:
            - Design, develop, and maintain {job_title.lower()} solutions
            - Collaborate with cross-functional teams to define requirements
            - Implement best practices and standards
            - Troubleshoot and resolve technical issues

            Requirements:
            - {experience} of experience in {job_title}
            - Proficiency in: {', '.join(skills_required)}
            - Bachelor's degree in Computer Science or related field
            - Strong communication and teamwork skills
            """

            # Generate a realistic salary range
            base = random.randint(70, 180)
            salary = f"${base}K - ${base + random.randint(15, 40)}K"

            job_url = f"https://{platform.lower().replace(' ', '')}.com/jobs/{company.lower()}-{job_title.lower().replace(' ','-')}-{random.randint(10000, 99999)}"

            job = {
                "job_title": job_title,
                "company": company,
                "location": job_location,
                "job_description": job_description,
                "salary": salary,
                "job_url": job_url,
                "platform": platform,
                "date_posted": (datetime.now().date() - pd.Timedelta(days=random.randint(0, 14))).strftime("%Y-%m-%d")
            }

            platform_jobs.append(job)
        
        all_jobs.extend(platform_jobs)

    # Shuffle to mix platforms
    random.shuffle(all_jobs)

    # Return the specified number of results
    return all_jobs[:num_results]

def calculate_matching_score(job_desc, user_skills, user_experience):
    """Calculate a matching score between job and user profile"""
    
    # Convert inputs to lowercase for case-insensitive matching
    job_desc_lower = job_desc_lower()

    # Extract user skills and convert to lowercase
    user_skills_list = [skill.strip().lower() for skill in user_skills.split(',')]

    # Count how many user skills appear in the job description
    matched_skills = sum(1 for skill in user_skills_list if skill in job_desc_lower)

    # Calculate basic matching score based on skills match ratio
    skill_match_ratio = matched_skills / len(user_skills_list) if user_skills_list else 0

    # Extract years of experience from user profile
    experience_years = 0
    experience_match = re.search(r'(\d+)\s*(?:years|yrs)', user_experience.lower())
    if experience_match:
        experience_years = int(experience_match.group(1))

    # Check if job description has experience requirements
    job_req_years = 0
    job_exp_match = re.search(r'(\d+)\+?\s*(?:years|yrs)', job_desc_lower)
    if job_exp_match:
        job_req_years = int(job_exp_match.group(1))
    
    # Experience matching component (1.0 if user has >= required experience)
    exp_match = min(1.0, experience_years / job_req_years) if job_req_years > 0 else 0.5

    # Combine skill and experience components (weighted)
    matching_score = (skill_match_ratio * 0.7) + (exp_match * 0.3)

    # Scale to 0-100%
    return round(matching_score * 100, 1)

def apply_to_job(job, user_profile):
    """Simulate applying to a job"""

    success = random.random() < 0.9

    if success:
        conn = sqlite3.connect('job_applications.db')
        c = conn.cursor()

        matching_score = calculate_matching_score(
            job["job_description"],
            user_profile["skilles"],
            user_profile["experience"]
        )

        c.execute('''
        INSERT INTO JOBS (job_title, company, location, job_description, salary,
                  job_url, platform, date_applied, status, matching_score, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            job["job_title"], job["company"], job["location"], job["job_description"],
            job["salary"], job["job_url"], job["platform"], datetime.now().strftime(%Y-%m-%d),
            "Applied", matching_score, "Auto-applied bu job Application Agent"
        ))

        conn.connect()
        conn.close()

    return success

def get_user_profile():
    """Get user profile from database"""
    conn = sqlite3.connect('job_applications.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute('SELECT * FROM user_profile ORDER By id DESC LIMIT 1')
    result = c.fetchone()

    conn.close()

    if result:
        return dict(result)
    else:
        return None
    
def 
 


