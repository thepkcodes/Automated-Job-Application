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
        "CA", "NY", "WA", "TX", "CT", "MA", "GA", "FL", "OR", "CO", "IL", "AZ", "MO", "NJ", "NC"
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
    
def save_user_profile(profile_data):
    """Save user profile to database"""
    conn = sqlite3.connect('job_applications.db')
    c = conn.cursor()

    c.execute('''
    INSERT INTO user_profile (full_name, email, phone, resume_path, skills, experience, education, preference)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        profile_data["full_name"], profile_data["email"], profile_data["phone"],
        profile_data["resume_path"], profile_data["skills"], profile_data["experience"],
        profile_data["education"], profile_data["performance"]
    ))

    conn.commit()
    conn.close()

def get_applied_jobs():
    """Get list of jobs the user has applied to"""
    conn = sqlite3.connect('job_applications.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute('SELECT * FROM jobs ORDER BY date_applied DESC')
    results = [dict(row) for row in c.fetchall()]

    conn.close()
    return results

def update_job_status(job_id, new_status, notes = None):
    """Update the status of a job application"""
    conn = sqlite3.connect('job_applications.db')
    c = conn.cursor()

    if notes:
        c.execute('UPDATE jobs SET status = ?, notes = ? WHERE id = ?',
                  (new_status, notes, job_id))
    else:
        c.execute('SELECT notes FROM jobs WHERE id = ?', (job_id))
        current_notes = c.fetchone()[0]
        c.execute('UPDATE jobs SET STATUS = ?', notes = ? WHERE id = ?',
                  (new_status, current_notes, job_id))
        
    conn.commit()
    conn.close()

if page == "Dashboard":
    st.markdown("<h1 class = 'main-header'>Job Application Agent Dashboard</h1>", unsafe_allow_html = True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class = 'card'>", unsafe_allow_html = True)
        st.markdown("h3>Quick Stats</h3>", unsafe_allow_html = True)

        applied_jobs = get_applied_jobs()
        total_applications = len(applied_jobs)

        statuses = {}
        platforms = {}
        recent_activity = []

        for job in applied_jobs:
            status = job["status"]
            platform = job["platform"]

            if status in statuses:
                statuses[status] += 1
            else:
                statuses[status] = 1

            if platform in platforms:
                platforms[platform] += 1
            else:
                platforms[platform] = 1

            date_applied = datetime.strptime(job["date_applied"], "%Y-%m-%d").date()
            days_ago = (datetime.now().date() - date_applied).days
            if days_ago <= 7:
                recent_activity.append(job)

        st.metric("Total Applications", total_applications)

        status_cols = st.columns(4)
        with status_cols[0]:
            applied_count = statuses.get("Applied", 0)
            st.metric("Applied", applied_count)

        with status_cols[1]:
            interview_count = statuses.get("Interview", 0)
            st.metric("Interviews", interview_count)

        with status_cols[2]:
            offer_count = statuses.get("Offer", 0)
            st.metric("Offers", offer_count)

        with status_cols[3]:
            rejected_count = statuses.get("Rejected", 0)
            st.metric("Rejected", rejected_count)

        if applied_jobs:
            st.markdown("<h4>Weekly Applications Activity</h4>", unsafe_allow_html = True)

            today = datetime.now().date()
            date_range = [(today - pd.Timedelta(days = i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]

            daily_counts = {date: 0 for date in date_range}

            for job in applied_jobs:
                if job["date_applied"] in daily_counts:
                    daily_counts[job["date_applied"]] += 1

            activity_df = pd.DataFrame({
                "Date": list(daily_counts.values())
            })

            st.bar_chart(activity_df.set_index("Date"))

        st.markdown("</div>", unsafe_allow_html = True)

    with col2:
        st.markdown("<div class = 'card'>", unsafe_allow_html = True)
        st.markdown("<h3>Recent Activity</h3", unsafe_allow_html = True)

        if recent_activity:
            for job in recent_activity[:5]:
                status_class = f"status-{job['status'].lower()}"

                st.markdown(f"""
                <div style = "margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px soldi #eee;">
                    <strong>{job['job_title']}</strong> at {job['company']}
                    <br>
                    <span class = "{status_class}">{job['status']}</span • {job['date_applied']} • {job['platform']}
                </div>
                """, unsafe_allow_html = True)
        else:
            st.info("No recent application activity to display")

        st.markdown("<div>", unsafe_allow_html = True)

        st.markdown("<div class = 'card'>", unsafe_allow_html = True)
        st.markdown("h3>Profile Summary</h3>", unsafe_allow_html = True)

        user_profile = get_user_profile()
        if user_profile:
            st.markdown(f"""
            <p><strong>Name:</strong> {user_profile['full_name']}</p>
            <p><strong>Top Skills:</strong> {', '.join(user_profile['skills'].split(',')[:5])}...</p>
            <p><strong>Experience:</strong> {user_profile['experience'][:100]}...</p>
            """, unsafe_allow_html = True)

            st.button("Edit Profile", key = "edit_profile_dashboard",
                    on_click = lambda: st.session_state.update({"page": "Profile Setup"}))
        else:
            st.markdown("Profile not set up yet. Please go to Profile Setup!")
            st.button("Set Up Profile", key = "setup_profile_dashboard",
                    on_click = lambda: st.session_state.update({"page": "Profile Setup"}))
            
        st.markdown("</div>", unsafe_allow_html = True)

    st.markdown("<div class = 'card'>", unsafe_allow_html = True)
    st.markdown("<h3>Recommended Actions</h3>", unsafe_allow_html = True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style = "text-align: center;">
            <h4>🔍 Find Jobs</h4>
            <p>Search for new job opportunities based on your profile</p>
        </div>
        """, unsafe_allow_html = True)
        st.button("Search Jobs", key = "search_jobs_dashboard",
                on_click = lambda: st.session_state.update({"page": "Job Search"}))
        
    with col2:
        st.markdown("""
        <div style = "text-align: center;">
            <h4>📊 View Analytics</h4>
            <p>Analyze your application performance and insights</p>
        </div>
        """, unsafe_allow_html = True)
        st.button("View Analytics", key = "view_analytics_dashboard",
                on_click = lambda: st.session_state.update({"page": "Analytics"}))
        
    with col3:
        st.markdown("""
        <div style = "text-align: center;">
            <h4>📋 Track Application</h4>
            <p>Update and manage your job applications</p>
        </div>
        """, unsafe_allow_html = True)
        st.button("Track Jobs", key = "track_jobs_dashboard",
                on_click = lambda: st.session_state.update({"page": "Job Tracker"}))
        
    st.markdown("</div>", unsafe_allow_html = True)

elif page == "Job Search":
    st.markdown("<h1 class = 'main-header'>Job Search & Auto-Apply</h1>", unsafe_allow_html = True)

    user_profile = get_user_profile()
    if not user_profile:
        st.warning("Please set up your profile before searching for jobs")
        if st.button("Go to Profile Setup"):
            st.session_state.page = "Profile Setup"
        st.stop()

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("<div class = 'card'>", unsafe_allow_html = True)
        st.markdown("<h3>Search Parameters</h3>", unsafe_allow_html = True)

        with st.form("job_search_form"):
            default_keywords = ", ".join(user_profile["skills"].split(",")[:3])
            keywords = st.text_input("Keywords (skills, job titles)", values = default_keywords)

            default_location = ""
            if user_profile["preferences"]:
                location_match = re.search(r'location[:\s]+([\w\s,]+)', user_profile["preferences"], re.IGNORECASE)
                if location_match:
                    default_keywords = location_match.group(1).strip()

                location = st.text_input("Location", value = default_location)

                platforms = st.multiselect(
                    "Job Platforms",
                    ["LinkedIn", "Indedd", "Glassdoor", "Welcome to the Jungle", "Handshake", "Built In", "Google Jobs", "ZipRecruiter", "Monster"],
                    default = ["LinkedIn", "Indeed", "Glassdoor", "Google Jobs"]
                )

                num_results = st.slider("Maximum Results", min_value = 10, max_value = 100, value = 20, step = 10)

                search_button = st.form_submit_button("Search Jobs")

            # Auto-apply settings
            st.markdown("<h3> Auto-Apply Settings</h3>", unsafe_allow_html=True)
            
            min_match_score = st.slider("Minimum Match Score (%)", 0, 100, 70)

            auto_apply_all = st.checkbox("Apply to All Matching Jobs Automatically", value=False)

            if auto_apply_all:
                max_daily_applications = st.number_input("Maximum Daily Applications", min_value=1, max_value=50, value=10)

            st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3>Search Results</h3>", unsafe_allow_html=True)

        if "job_results" not in st.session_state:
            st.session_state.job_results = []

        if search_button:
            with st.spinner("Searching for jobs across platforms..."):
                time.sleep(2)

                jobs = scrape_jobs(keywords, location, platforms, num_results)

                for job in jobs:
                    job["matching_score"] = calculate_matching_score(
                        job["job_description"],
                        user_profile["skills"],
                        user_profile["experience"]
                    )

                jobs.sort(key=lambda x: x["matching_score"], reverse=True)

                st.session_state.job_results = jobs
                st.success(f"Found {len(jobs)} matching jobs!")

                if auto_apply_all:
                    matching_jobs = [job for job in jobs if job["matching_score"] >= min_match_score]
                    jobs_to_apply = matching_jobs[:max_daily_applications] if auto_apply_all else[]

                    if jobs_to_apply:
                        applied_count = 0
                        with st.spinner(f"Auto-applying to {len(jobs_to_apply)} jobs..."):
                            for job in jobs_to_apply:
                                success = apply_to_job(job, user_profile)
                                if success:
                                    applied_count += 1

                                time.sleep(0.5)

                        st.success(f"Successfully applied to {applied_count} jobs!")

        if st.session_state.job_results:
            for i, job in enumerate(st.session_state.job_results):
                if job["matching_score"] >= 80:
                    score_class = "match-score-high"
                elif job["matching_score"] >= 60:
                    score_class = "match-score-medium"
                else:
                    score_class = "match-score-low"

                st.markdown(f"""
                <div style="margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #eee;">
                    <h4>{job["job_title"]} at {job["company"]}</h4>
                    <p>📍 {job["location"]} • 💰 {job["salary"]} • 🔗 {job["platform"]}</p>
                    <p><span class="{score_class}">Match Score: {job["matching_score"]}%</span></p>
                </div>
                """, unsafe_allow_html=True)

                col1, col2 = st.columns([3, 1])

                with col1:
                    if st.button(f"View Details #{i}", key = f"view_{i}"):
                        st.session_state[f"show_details_{i}"] = not st.session_state.get(f"show_details_{i}", False)

                with col2:
                    conn = sqlite3.connect("job_application.db")
                    c = conn.cursor()
                    c.execute('SELECT COUNT(*) FROM jobs WHERE job_url = ?', (job["job_url"],))
                    already_applied = c.fetchone()[0] > 0
                    conn.close()

                    if already_applied:
                        st.button("Already Applied", key=f"applied_{i}", disabled=True)
                    else:
                        if st.button(f"Apply Now #{i}", key=f"apply_{i}"):
                            with st.spinner("Applying to job..."):
                                time.sleep(2)
                                success = apply_to_job(job, user_profile)

                                if success:
                                    st.success("Successfully applied!")
                                else:
                                    st.error("Application failed. Please try again or apply manually.")

                if st.session_state.get(f"show_details_{i}", False):
                    st.markdown(f"""
                    <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin-top: 10px;">
                        <h5>Job Description</h5>
                        <p>{job["job_description"]}</p>
                        <p><strong>URL:</strong> <a href="{job["job_url"]} target="_blank">{job["job_url"]}</a></p>
                        <p><strong>Date Posted:</strong> {job["date_posted"]}</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Search for jobs to see results here")

        st.markdown("</div>", unsafe_allow_html=True)

elif page == "Profile Setup":
    st.markdown("<h1 class='main-header'>Profile Setup</h1>", unsafe_allow_html=True)

    existing_profile = get_user_profile()

    with st.form("profile_setup_form"):
        st.markdown("<h3>Personal Information</h3>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col2:
            full_name = st.text_input("Full Name", value=existing_profile["full_name"] if existing_profile else "")
            email = st.text_input("Email", value=existing_profile["email"] if existing_profile else "")

        with col2:
            phone = st.text_input("Phone Number", value=existing_profile["phone"] if existing_profile else "")
            resume_path = st.text_input("Resume File Path (optional)",
                                value=existing_profile["resume_path"] if existing_profile else "")
            
        st.markdown("<h3>Skills & Experience</h3>", unsafe_allow_html=True)

        skills = st.text_area("Skills (comma separated)",
                    value=existing_profile["skills"] if existing_profile else "",
                    height = 100,
                    help="Enter your skills separated by commas")
        
        experience = st.text_area("Professional Experience",
                        value=existing_profile["experience"] if existing_profile else "",
                        height=150,
                        help="Enter your work experience, including years of experience in relevant roles")
        
        education = st.text_area("Education",
                        value=existing_profile["education"] if existing_profile else "",
                        height=100)
        
        st.markdown("<h3>Job Preferences</h3>", unsafe_allow_html=True)

        preferences = st.text_area("Job Preferences",
                        value=existing_profile["preferences"] if existing_profile else "",
                        height=100,
                        help="Enter your job preferences such as: location, remote/hybrid/in-office, salary range, etc.")
        
        submitted = st.form_submit_button("Save Profile")

    if submitted:
        profile_data = {
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "resume_path": resume_path,
            "skills": skills,
            "experience": experience,
            "education": education,
            "preferences": preferences
        }

        save_user_profile(profile_data)
        st.success("Profile saved successfully!")

elif page == "Application Settings":
    st.markdown("<h1 class='main-header'>Application Settings</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class ='card'>", unsafe_allow_html=True)
        st.markdown("<h3>Auto-Apply Settings</h3>", unsafe_allow_html=True)

        with st.form("auto_apply_settings"):
            st.checkbox("Enable Auto-Apply Feature", value=True, key="enable_auto_apply")
            
            st.number_input("Maximum Application Per Day", min_value=1, max_value=50, value=10, key="max_applications")

            st.slider("Minimum Match Score for Auto-Apply (%)", min_value=0, max_value=100, value=75, key="min_match_score")

            st.multiselect(
                "Preferred Job Platforms",
                ["LinkedIn", "Indeed", "Glassdoor", "Welcome to the Jungle", "Handshake", "Built In", "Google Jobs", "ZipRecruiter",
                 "Monster"],
                 default=["LinkedIn", "Indeed", "Glassdoor"],
                 key="preferred_platforms"
            )

            st.text_area("Auto-Apply Message Template",
                         value="Dear Hiring Manager, \n\nI am writing to express my interest in the [JOB_TITLE] position at [COMPANY]. With my experience in [SKILLS], I believe I would be a great fit for this role. \n\nThank you for your consideration. \n\nBest regards, \n[FULL_NAME]",
                         height=150,
                         help="Customize the message template for auto-applications. Use [JOB_TITLE], [COMPANY], [SKILLS, [FULL_NAME] as placeholders.",
                         key="message_template")
            
            st.form_submit_button("Save Auto-Apply Settings")

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3>Job Filter Settings</h3>", unsafe_allow_html=True)

        with st.form("job_filter_settings"):
            st.multiselect(
                "Job Types",
                ["Full-time", "Part-time", "Contract", "Temporary", "Internship", "Remote"],
                default=["Full-time", "Remote"],
                key="job_types"
            )

            col1, col2 = st.columns(2)

            with col1:
                st.number_input("Minimum Salary ($K)", min_value=0, max_value=500, value=50, key="min_salary")

            with col2:
                st.number_input("Maximum Salary ($K)", min_value=0, max_value=500, value=200, key="max_salary")

            st.multiselect(
                "Industry Preferences",
                ["Technology", "Healthcare", "Finance", "Education", "Retail", "Manufacturing", "Media", "Consulting", "Non-profit",
                 "Government"],
                 default=["Technology", "Finance", "Consulting"],
                 key="industries"
            )

            st.text_input("Location Preferences", value="Remote, New York, San Francisco, Boston", key="locations")

            st.form_submit_button("Save Job Filter Settings")

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("</div class= 'card'>", unsafe_allow_html=True)
        st.markdown("<h3>Notfication Settings</h3>", unsafe_allow_html=True)

        with st.form("notification_settings"):
            st.checkbox("Email Notifications", value=True, key="email_notifications")

            st.text_input("Notification Email", value="", key="notification_email",
                          help="Email address to receive job application notifications")
            
            st.multiselect(
                "Notify Me About",
                ["New matching jobs", "Successful applications", "Application status changes",
                 "Interview invitations", "Job offers", "Daily Summary"],
                 default=["Successful applications", "Interview invitations", "Job offers"],
                 key="notification_types"
            )

            st.select_slider(
                "Notification Frequency",
                options=["Immediately", "Hourly", "Daily", "Weekly"],
                value="Daily"
                key="notification_frequency"
            )

            st.form_submit_button("Save Notification Settings")
    
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class = 'card'>", unsafe_allow_html=True)
        st.markdown("<h3>Data Management</h3>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Export All Data (CSV)"):
                st.info("Feature would export all job application data as CSV")

        with col2:
            if st.button("Delete All Data (CSV)", key="delete_data_button"):
                st.session_state.confirm_delete = True
        
        if st.session_state.get("confirm_delete", False):
            st.warning("Are you sure you want to delete all application data? This cannot be undone.")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Yes, Delete Everything"):
                    st.success("All data has been deleted!")
                    st.session_state.confirm_delete = False

            with col2:
                if st.button("Cancel"):
                    st.session_state.confirm_delete = False

        st.markdown("<h3>API Credentials</h3>", unsafe_allow_html=True)

        with st.expander("LinkedIn API"):
            st.text_input("LinkedIn API Key", type="password")
            
    






 


