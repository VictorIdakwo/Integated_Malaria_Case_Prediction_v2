import streamlit as st
import os
import subprocess
import threading
import sys  # Import sys module to fix the error

# Function to run a Streamlit app in a new thread
def run_streamlit_app(script_name):
    subprocess.run([sys.executable, "-m", "streamlit", "run", script_name])

# Function to show the main landing page
def main_landing_page():
    # Title of the landing page
    st.title("Malaria Prediction Portal")
    
    # Logo (Replace with your own logo)
    st.image("images/eHA-logo-blue_320x132.png", width=320)
    
    # Introduction Text
    st.markdown("""
    This portal provides insights into **malaria prediction** using advanced Machine Learning models.  
    Choose an option below to explore predictions for clinical or non-clinical malaria cases.
    """)

    # Buttons to navigate to the specific prediction apps
    if st.button("Clinical Malaria Prediction"):
        st.write("Navigating to Clinical Malaria Prediction...")
        threading.Thread(target=run_streamlit_app, args=("malaria_reinforcement.py",)).start()
        
    if st.button("Non-Clinical Malaria Prediction"):
        st.write("Navigating to Non-Clinical Malaria Prediction...")
        threading.Thread(target=run_streamlit_app, args=("non_clinical_malaria_streamlit.py",)).start()

    # Features Section
    st.subheader("Prediction Features")
    st.markdown("""
    - **Clinical Malaria Prediction**: Uses symptoms such as chill/cold, headache, fever, generalized body pain, 
      abdominal pain, loss of appetite, joint pain, vomiting, nausea, and diarrhea for predictions.
    - **Non-Clinical Malaria Prediction**: Utilizes environmental factors like Rainfall, Land Surface Temperature (LST), 
      and Relative Humidity for predictions.
    """)

if __name__ == "__main__":
    # Show the landing page
    main_landing_page()
