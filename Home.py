"""
Malaria Prediction Portal - Home Page
======================================
eHealth Africa
"""

import streamlit as st
import os
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Malaria Prediction Portal - eHealth Africa",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .feature-card {
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #e5e7eb;
        background: #f9fafb;
        margin: 1rem 0;
        transition: transform 0.2s;
    }
    .feature-card:hover {
        transform: translateY(-5px);
        border-color: #3b82f6;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    .stat-box {
        text-align: center;
        padding: 1rem;
        background: white;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header"><h1>🏥 Malaria Prediction Portal</h1><p>AI-Powered Clinical Decision Support System</p></div>', unsafe_allow_html=True)

# Logo and organization info
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if os.path.exists("images/eHA-logo-blue_320x132.png"):
        st.image("images/eHA-logo-blue_320x132.png", width=300)
    st.markdown("<p style='text-align: center; color: #6b7280;'>eHealth Africa | Transforming Healthcare with Technology</p>", unsafe_allow_html=True)

st.markdown("---")

# Introduction
st.markdown("""
### Welcome to the Malaria Prediction System

This portal provides **intelligent malaria prediction** using advanced Machine Learning and Reinforcement Learning models. 
Our system helps healthcare workers make informed decisions by analyzing patient symptoms and environmental data.

""")

# Feature cards
st.subheader("🎯 Available Prediction Models")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="feature-card">
        <h3>🩺 Clinical Malaria Prediction</h3>
        <p><strong>Symptom-Based Analysis</strong></p>
        <ul>
            <li>Uses patient clinical symptoms</li>
            <li>Reinforcement Learning (PPO Algorithm)</li>
            <li>Real-time prediction in seconds</li>
            <li>Ideal for clinical settings</li>
        </ul>
        <p><em>Analyzes: Fever, chills, headache, body pain, and 6 more symptoms</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    st.page_link("pages/malaria_reinforcement.py", label="🚀 Launch Clinical Predictor", use_container_width=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <h3>🌍 Non-Clinical Malaria Prediction</h3>
        <p><strong>Environmental Data Analysis</strong></p>
        <ul>
            <li>Uses climate and environmental data</li>
            <li>Machine Learning models</li>
            <li>Epidemic forecasting capabilities</li>
            <li>Ideal for public health planning</li>
        </ul>
        <p><em>Analyzes: Rainfall, temperature, humidity, and more</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    st.page_link("pages/non_clinical_malaria_streamlit.py", label="🚀 Launch Environmental Predictor", use_container_width=True)

st.markdown("---")

# Key features
st.subheader("✨ Key Features")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="stat-box">
        <h2>🤖</h2>
        <p><strong>AI-Powered</strong></p>
        <p style="font-size: 0.9rem; color: #6b7280;">Advanced ML algorithms</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="stat-box">
        <h2>⚡</h2>
        <p><strong>Real-Time</strong></p>
        <p style="font-size: 0.9rem; color: #6b7280;">Instant predictions</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="stat-box">
        <h2>📊</h2>
        <p><strong>Data-Driven</strong></p>
        <p style="font-size: 0.9rem; color: #6b7280;">Evidence-based decisions</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="stat-box">
        <h2>🔒</h2>
        <p><strong>Secure</strong></p>
        <p style="font-size: 0.9rem; color: #6b7280;">Privacy-focused design</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Important information
st.subheader("⚠️ Important Information")

col1, col2 = st.columns(2)

with col1:
    st.info("""
    **Clinical Use Guidelines**
    
    ✓ This is a **decision support tool**, not a diagnostic device
    
    ✓ Always confirm predictions with laboratory testing (microscopy or RDT)
    
    ✓ Follow your local clinical protocols and guidelines
    
    ✓ Use as part of comprehensive patient assessment
    """)

with col2:
    st.warning("""
    **Data Privacy & Security**
    
    🔒 Use anonymized patient IDs only
    
    🔒 Do not enter personally identifiable information
    
    🔒 Data is stored securely for model improvement
    
    🔒 Comply with HIPAA/GDPR regulations
    """)

# Getting started
st.markdown("---")
st.subheader("🚀 Getting Started")

with st.expander("📖 Quick Start Guide"):
    st.markdown("""
    ### For Clinical Malaria Prediction:
    
    1. **Click** on "Launch Clinical Predictor" above
    2. **Enter** a unique patient ID
    3. **Select** all relevant symptoms
    4. **Get** instant prediction
    5. **Record** laboratory test result
    6. **Download** data for analysis
    
    ### For Environmental Prediction:
    
    1. **Click** on "Launch Environmental Predictor"
    2. **Enter** environmental data (rainfall, temperature, etc.)
    3. **Get** malaria risk prediction
    4. **Use** for public health planning
    
    ### Need Help?
    
    - Check the **CLINICAL_TRIAL_GUIDE.md** for detailed instructions
    - Review **README.md** for technical documentation
    - Contact your system administrator for support
    """)

# Footer
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown(f"""
    <p style='text-align: center; color: #9ca3af; font-size: 0.9rem;'>
    © {datetime.now().year} eHealth Africa | Malaria Prediction System v2.0<br>
    <em>Empowering healthcare workers with AI-driven insights</em>
    </p>
    """, unsafe_allow_html=True)
