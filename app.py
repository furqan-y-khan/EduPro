import streamlit as st
import sqlite3
import pandas as pd
from PIL import Image
from datetime import datetime
import os
import secrets
from io import BytesIO
import random
import requests
from urllib.parse import urlparse, parse_qs, quote
import re
from bs4 import BeautifulSoup

# Admin credentials
ADMIN_EMAIL = "furqanthedeveloper@gmail.com"
ADMIN_PIN = "0000"

# Create necessary directories
if not os.path.exists("uploads"):
    os.makedirs("uploads")
if not os.path.exists("uploads/videos"):
    os.makedirs("uploads/videos")
if not os.path.exists("uploads/materials"):
    os.makedirs("uploads/materials")

def get_youtube_videos(query, max_results=10):
    """
    Get YouTube videos using web scraping
    """
    try:
        # Format search query
        search_query = quote(f"{query} tutorial")
        url = f"https://www.youtube.com/results?search_query={search_query}"
        
        # Add headers to mimic browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Make request
        response = requests.get(url, headers=headers)
        
        # Extract video IDs directly from the URL
        video_ids = re.findall(r"watch\?v=(\S{11})", response.text)
        
        # Get unique videos
        videos = []
        seen_ids = set()
        
        for vid_id in video_ids:
            if vid_id not in seen_ids and len(videos) < max_results:
                videos.append({
                    'id': vid_id,
                    'title': f"Tutorial {len(videos) + 1}"  # Simple numbered title
                })
                seen_ids.add(vid_id)
        
        return videos
    except Exception as e:
        st.error(f"Error fetching videos: {str(e)}")
        return []

def embed_youtube_video(video_id):
    """
    Create an embedded YouTube video player
    """
    return f'''
        <div style="position: relative; padding-bottom: 56.25%; height: 0; margin-bottom: 20px;">
            <iframe 
                style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"
                src="https://www.youtube.com/embed/{video_id}"
                frameborder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowfullscreen>
            </iframe>
        </div>
    '''

def is_admin(email, pin):
    return email == ADMIN_EMAIL and pin == ADMIN_PIN

def generate_pin():
    return ''.join(random.choices('0123456789', k=4))

# Initialize database
def init_db():
    conn = sqlite3.connect('courses.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS courses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  description TEXT,
                  instructor_email TEXT NOT NULL,
                  instructor_name TEXT,
                  deletion_pin TEXT,
                  donation_qr BLOB,
                  created_at TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS course_content
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  course_id INTEGER,
                  video_path TEXT,
                  material_path TEXT,
                  title TEXT,
                  FOREIGN KEY (course_id) REFERENCES courses(id))''')
    conn.commit()
    conn.close()

def delete_course_files(course_id):
    conn = sqlite3.connect('courses.db')
    content = pd.read_sql('SELECT video_path, material_path FROM course_content WHERE course_id = ?', 
                         conn, params=[course_id])
    conn.close()
    
    if not content.empty:
        # Delete video file
        if content.iloc[0]['video_path'] and os.path.exists(content.iloc[0]['video_path']):
            os.remove(content.iloc[0]['video_path'])
        
        # Delete material file
        if content.iloc[0]['material_path'] and os.path.exists(content.iloc[0]['material_path']):
            os.remove(content.iloc[0]['material_path'])

# Initialize the database
init_db()

# Set page config
st.set_page_config(page_title="EduPro - Course Marketplace", layout="wide")

# Main title with better proportions
st.markdown("""
    <h1 style='
        text-align: center; 
        padding: 1rem 0; 
        font-size: 2.5rem;
        color: #1e3c72;
        margin-bottom: 2rem;'>
        🎓 EduPro Course Marketplace
    </h1>
""", unsafe_allow_html=True)

# Add search bar with better styling
st.markdown("""
    <style>
        div[data-baseweb="input"] {
            margin-bottom: 2rem;
        }
    </style>
""", unsafe_allow_html=True)
search_query = st.text_input("🔍 Search for courses...")
search_type = st.radio("Search in:", ["Local Courses", "YouTube"], horizontal=True)

# Sidebar styling
st.sidebar.markdown("""
    <div style="
        padding: 1rem 0;
        margin-bottom: 1rem;
        border-bottom: 2px solid #1e3c72;">
        <h1 style="
            font-family: 'Trebuchet MS', sans-serif;
            background: linear-gradient(45deg, #1e3c72, #2a5298);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2rem;
            margin: 0;
            ">LastAppStanding</h1>
    </div>
""", unsafe_allow_html=True)

page = st.sidebar.selectbox("Choose a page", ["Browse Courses", "Add Course"])

if search_type == "Local Courses":
    if search_query:
        conn = sqlite3.connect('courses.db')
        courses = pd.read_sql('''
            SELECT * FROM courses 
            WHERE LOWER(title) LIKE ? OR LOWER(description) LIKE ?
        ''', conn, params=[f'%{search_query.lower()}%', f'%{search_query.lower()}%'])
        conn.close()
        
        if not courses.empty:
            st.subheader(f"Found {len(courses)} matching courses")
            for _, course in courses.iterrows():
                with st.container():
                    st.subheader(course['title'])
                    st.write(course['description'])
                    st.write(f"Instructor: {course['instructor_name']}")
                    st.divider()
        else:
            st.info("No matching courses found.")

else:  # YouTube search
    if search_query:
        st.subheader(f"📺 Tutorials for: {search_query}")
        
        # Show loading spinner while fetching videos
        with st.spinner("Loading videos..."):
            videos = get_youtube_videos(search_query)
        
        if videos:
            # Display videos in a clean layout
            for i, video in enumerate(videos, 1):
                st.markdown(f"### {i}.")  # Simple number
                st.markdown(embed_youtube_video(video['id']), unsafe_allow_html=True)
                st.divider()
        else:
            st.info("No videos found. Try a different search term.")
        
        # Simple link to more results
        youtube_search_url = f"https://www.youtube.com/results?search_query={quote(search_query + ' tutorial')}"
        st.markdown(f'''
            <div style="text-align: center;">
                <a href="{youtube_search_url}" target="_blank" style="
                    text-decoration: none;
                    background-color: #FF0000;
                    color: white;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-weight: bold;">
                    🎥 View More on YouTube
                </a>
            </div>
        ''', unsafe_allow_html=True)

if page == "Browse Courses":
    st.header("Available Courses")
    
    conn = sqlite3.connect('courses.db')
    courses = pd.read_sql('SELECT * FROM courses ORDER BY created_at DESC', conn)
    conn.close()
    
    if not courses.empty:
        for _, course in courses.iterrows():
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader(course['title'])
                    st.write(course['description'])
                    st.write(f"Instructor: {course['instructor_name']}")
                    
                    # Display course content
                    conn = sqlite3.connect('courses.db')
                    content = pd.read_sql('''
                        SELECT video_path, material_path, title
                        FROM course_content
                        WHERE course_id = ?
                    ''', conn, params=[course['id']])
                    conn.close()
                    
                    if not content.empty:
                        st.write(f"Content: {content.iloc[0]['title']}")
                        if os.path.exists(content.iloc[0]['video_path']):
                            with open(content.iloc[0]['video_path'], 'rb') as video_file:
                                st.video(video_file)
                        
                        if content.iloc[0]['material_path'] and os.path.exists(content.iloc[0]['material_path']):
                            with open(content.iloc[0]['material_path'], 'rb') as material_file:
                                st.download_button(
                                    label="📚 Download Materials",
                                    data=material_file,
                                    file_name=os.path.basename(content.iloc[0]['material_path'])
                                )
                
                with col2:
                    if course['donation_qr']:
                        st.write("💝 Support the creator:")
                        qr_image = Image.open(BytesIO(course['donation_qr']))
                        st.image(qr_image, caption="Donate", width=200)
                st.divider()
    else:
        st.info("No courses available yet. Be the first to add a course!")

elif page == "Add Course":
    st.header("Add a New Course")
    
    # Admin authentication
    with st.expander("👑 Admin Authentication", expanded=True):
        admin_email = st.text_input("Admin Email:")
        admin_pin = st.text_input("Admin PIN:", type="password")
        
        if admin_email and admin_pin:
            if not is_admin(admin_email, admin_pin):
                st.error("⚠️ Invalid admin credentials. Only admin can upload courses.")
                st.stop()
            else:
                st.success("✅ Admin authenticated successfully!")
    
    # Admin Course Management
    if is_admin(admin_email, admin_pin):
        st.subheader("🗑️ Admin Course Management")
        
        conn = sqlite3.connect('courses.db')
        all_courses = pd.read_sql('SELECT * FROM courses ORDER BY created_at DESC', conn)
        conn.close()
        
        if not all_courses.empty:
            for _, course in all_courses.iterrows():
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{course['title']}**")
                        st.write(f"Instructor: {course['instructor_name']}")
                        st.write(f"Email: {course['instructor_email']}")
                    with col2:
                        if st.button("🗑️ Delete Course", key=f"admin_delete_{course['id']}"):
                            delete_course_files(course['id'])
                            
                            conn = sqlite3.connect('courses.db')
                            c = conn.cursor()
                            c.execute('DELETE FROM course_content WHERE course_id = ?', (course['id'],))
                            c.execute('DELETE FROM courses WHERE id = ?', (course['id'],))
                            conn.commit()
                            conn.close()
                            st.success("Course deleted successfully!")
                            st.rerun()
                    st.divider()
        else:
            st.info("No courses available.")
        
        st.divider()
    
    # New course form
    st.subheader("📝 Add New Course")
    if not admin_email or not admin_pin or not is_admin(admin_email, admin_pin):
        st.warning("⚠️ Please authenticate as admin to add courses.")
    else:
        with st.form("add_course_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("Course Title")
                instructor_name = st.text_input("Instructor Name")
                instructor_email = st.text_input("Instructor Email")
            with col2:
                description = st.text_area("Course Description")
                donation_qr = st.file_uploader("💝 Donation QR Code (optional)", type=['png', 'jpg', 'jpeg'])
            
            st.subheader("Course Content")
            video_file = st.file_uploader("📹 Upload Course Video", type=['mp4', 'mov', 'avi'])
            material_file = st.file_uploader("📚 Upload Materials (optional)", type=['pdf', 'doc', 'docx'])
            content_title = st.text_input("Content Title")
            
            submit_button = st.form_submit_button("📤 Upload Course")
            
            if submit_button:
                if not all([title, description, instructor_name, instructor_email, video_file, content_title]):
                    st.error("Please fill in all required fields!")
                else:
                    try:
                        # Generate deletion PIN
                        deletion_pin = generate_pin()
                        
                        # Save course details
                        conn = sqlite3.connect('courses.db')
                        c = conn.cursor()
                        
                        # Check for existing course
                        existing = c.execute('''
                            SELECT 1 FROM courses 
                            WHERE title = ? AND instructor_email = ?
                        ''', (title, instructor_email)).fetchone()
                        
                        if existing:
                            st.error("A course with this title already exists!")
                        else:
                            # Save course
                            qr_bytes = donation_qr.getvalue() if donation_qr else None
                            c.execute('''
                                INSERT INTO courses 
                                (title, description, instructor_email, instructor_name, 
                                 deletion_pin, donation_qr, created_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''', (title, description, instructor_email, instructor_name,
                                 deletion_pin, qr_bytes, datetime.now()))
                            
                            course_id = c.lastrowid
                            
                            # Save video
                            video_path = f"uploads/videos/{course_id}_{video_file.name}"
                            with open(video_path, "wb") as f:
                                f.write(video_file.getvalue())
                            
                            # Save materials if provided
                            material_path = None
                            if material_file:
                                material_path = f"uploads/materials/{course_id}_{material_file.name}"
                                with open(material_path, "wb") as f:
                                    f.write(material_file.getvalue())
                            
                            # Save content info
                            c.execute('''
                                INSERT INTO course_content 
                                (course_id, video_path, material_path, title)
                                VALUES (?, ?, ?, ?)
                            ''', (course_id, video_path, material_path, content_title))
                            
                            conn.commit()
                            st.success(f"""
                            ✅ Course uploaded successfully!
                            Your course deletion PIN is: {deletion_pin}
                            Please save this PIN - you'll need it to delete the course later.
                            """)
                            
                    except Exception as e:
                        st.error(f"Error uploading course: {str(e)}")
                        # Cleanup any partial uploads
                        if 'video_path' in locals() and os.path.exists(video_path):
                            os.remove(video_path)
                        if 'material_path' in locals() and material_path and os.path.exists(material_path):
                            os.remove(material_path)
                    finally:
                        if 'conn' in locals():
                            conn.close() 