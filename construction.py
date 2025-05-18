import cv2
import numpy as np
import streamlit as st
import tempfile
import os
import pandas as pd
from streamlit_lottie import st_lottie
import json

# ------------------------- BACKEND CONFIG -------------------------
DIFF_THRESHOLD = 50  # Set threshold value in backend
ANIMATION_FPS = 3   # Set FPS in backend
FRAMES = 30          # Number of animation frames

# ------------------------- CSS Styling -------------------------
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style.css")

# ------------------------- Helper Functions -------------------------
def create_animation_video(image1, image2, diff_thresh, output_path):
    height, width = image1.shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(output_path, fourcc, ANIMATION_FPS, (width, height))

    alpha_values = np.linspace(0, 1, num=FRAMES)
    
    for alpha in alpha_values:
        blended = cv2.addWeighted(image1, 1 - alpha, image2, alpha, 0)
        mask = cv2.merge([diff_thresh*0, diff_thresh*0, diff_thresh])
        highlighted = cv2.addWeighted(blended, 1, mask, 0.5, 0)
        highlighted_rgb = cv2.cvtColor(highlighted, cv2.COLOR_BGR2RGB)
        video_writer.write(highlighted_rgb)
    
    video_writer.release()
    return highlighted_rgb

# ------------------------- Main App -------------------------
def main():
    # Header Section
    st.markdown("""
    <div class="header">
        <h1>Admin Dashboard – Progress Mapping</h1>
    </div>
    """, unsafe_allow_html=True)

    # Create tabs
    tab_progress, tab_plot = st.tabs(["Progress", "Progress Plot"])

    with tab_progress:
        # Project Selection
        st.markdown("""
        <div class="card">
            <h3>Project Selection</h3>
        """, unsafe_allow_html=True)
        
        projects = {
            "P1 BUILDINGS": "🏗️",
            "P2 BRIDGES": "🌉",
            "P3 DAMS": "💧", 
            "P4 ROADS": "🛣️"
        }
        
        selected_project = st.selectbox(
            "Select Project ID",
            options=list(projects.keys()),
            format_func=lambda x: f"{projects[x]} {x}",
            key="project_select"
        )
        st.markdown("</div>", unsafe_allow_html=True)

        # Image Comparison
        st.markdown("""
        <div class="card">
            <h3>Image Comparison</h3>
        """, unsafe_allow_html=True)
        
        df = pd.read_csv("projects.csv")
        project_id = selected_project.split()[0]
        project_images = df[df['Project_ID'] == project_id]
        
        days = st.multiselect(
            "Select two images to compare (by Day No)",
            options=sorted(project_images['Day_No'].unique()),
            format_func=lambda x: f"Day {x}",
            help="Select exactly two days for comparison",
            key="day_select"
        )
        
        st.markdown("</div>", unsafe_allow_html=True)

        # Processing Section
        if len(days) == 2:
            try:
                # Image processing code...
                img_paths = []
                for day in days:
                    path = project_images[project_images['Day_No'] == day]['Image_Path'].values[0]
                    img_paths.append(path)
                
                images = []
                for path in img_paths:
                    img = cv2.imread(path)
                    if img is None:
                        raise FileNotFoundError(f"Image not found at {path}")
                    images.append(img)
                
                gray_images = [cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) for img in images]
                image2 = cv2.resize(images[1], (images[0].shape[1], images[0].shape[0]))
                gray2 = cv2.resize(gray_images[1], (gray_images[0].shape[1], gray_images[0].shape[0]))
                
                # Compute differences with backend threshold
                _, diff_thresh = cv2.threshold(
                    cv2.absdiff(gray_images[0], gray2), DIFF_THRESHOLD, 255, cv2.THRESH_BINARY
                )

                # Create animation with backend FPS
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmpfile:
                    last_frame = create_animation_video(images[0], image2, diff_thresh, tmpfile.name)
                    
                    # Read video bytes for download
                    video_bytes = open(tmpfile.name, 'rb').read()
                    
                    # Download button - NOW PROPERLY INCLUDED
                    st.download_button(
                        label="📥 Download Progress",
                        data=video_bytes,
                        file_name=f"{project_id}_comparison.mp4",
                        mime="video/mp4",
                        use_container_width=True
                    )

                # Display results
                st.markdown("""
                <div class="card">
                    <h3>Comparison Results</h3>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.image(images[0], caption=f"Day {days[0]}", use_container_width=True)
                with col2:
                    st.image(last_frame, caption="Comparison Result", use_container_width=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
                os.unlink(tmpfile.name)
                # Rest of your image processing logic...
                # ...

            except Exception as e:
                st.error(f"🚨 Error processing images: {str(e)}")
        elif len(days) > 0:
            st.warning("⚠️ Please select exactly two days for comparison")

    with tab_plot:
        st.markdown("""
        <div class="card">
            <h3>Progress Visualization</h3>
        """, unsafe_allow_html=True)
        
        # Example progress data (replace with actual project data)
        progress_data = {
            "Day 1": 10,
            "Day 5": 25,
            "Day 10": 40,
            "Day 15": 60,
            "Day 25": 85
        }
        
        progress_df = pd.DataFrame(
            list(progress_data.items()),
            columns=["Day", "Progress (%)"]
        ).set_index("Day")
        
        st.line_chart(progress_df)
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()