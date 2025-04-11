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