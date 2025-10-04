"""
Clinical Malaria Prediction System - Improved Version
======================================================
Enhanced with better error handling, validation, and UX

Version: 2.0.0
Organization: eHealth Africa
"""

import streamlit as st
import numpy as np
import pandas as pd
import joblib
import os
import gc
from datetime import datetime
from typing import Optional

# Import configuration and utilities
from config import Config
from utils import (
    DataManager, 
    SymptomProcessor,
    ValidationHelper,
    UIHelper,
    format_datetime
)

# Lazy imports for optional dependencies
try:
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv
    import gymnasium as gym
    from gymnasium import spaces
    PPO_AVAILABLE = True
except ImportError:
    PPO_AVAILABLE = False

try:
    import torch
except ImportError:
    torch = None

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title=Config.APP_NAME,
    page_icon=Config.PAGE_ICON,
    layout=Config.LAYOUT,
    initial_sidebar_state=Config.SIDEBAR_STATE
)

# ============================================================
# MODEL LOADING WITH ERROR HANDLING
# ============================================================

@st.cache_resource(show_spinner="Loading AI model...")
def load_model_and_scaler():
    """
    Load the trained PPO model and scaler with error handling
    Returns: (model, scaler, error_message)
    """
    try:
        if not PPO_AVAILABLE:
            return None, None, "PPO library not available"
        
        # Check if model files exist
        model_file = f"{Config.MODEL_PATH}.zip"
        if not os.path.exists(model_file):
            return None, None, f"Model file not found: {model_file}"
        
        if not os.path.exists(Config.SCALER_PATH):
            return None, None, f"Scaler file not found: {Config.SCALER_PATH}"
        
        # Load model and scaler
        model = PPO.load(Config.MODEL_PATH)
        scaler = joblib.load(Config.SCALER_PATH)
        
        return model, scaler, None
        
    except Exception as e:
        return None, None, f"Error loading model: {str(e)}"


# Load model
model, scaler, model_error = load_model_and_scaler()

# ============================================================
# HEADER AND STATUS
# ============================================================

st.title(f"🏥 {Config.APP_NAME}")
st.caption(f"Version {Config.APP_VERSION} | {Config.ORG_NAME}")

# Check for errors
if model_error:
    st.error(f"❌ {model_error}")
    st.stop()

# Display deployment status
if Config.ENABLE_RETRAINING:
    st.error(Config.WARNING_RETRAINING_ENABLED)
    st.error("💥 Expect segmentation faults. Set ENABLE_RETRAINING=false")
else:
    st.success(Config.SUCCESS_STABLE_MODE)

# Display info expander
UIHelper.create_info_expander()

# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================

def init_session_state():
    """Initialize session state variables"""
    defaults = {
        'patient_id': None,
        'features': None,
        'predicted_case': None,
        'prediction_time': None,
        'symptom_count': 0
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()

# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

st.sidebar.title("📋 Navigation")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Select Page:",
    ["🩺 Symptom Assessment", "📊 Test Results & Data"],
    label_visibility="collapsed"
)

# Display quick stats in sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("📈 Quick Statistics")
stats = DataManager.get_statistics()
st.sidebar.metric("Total Records", stats['total'])
st.sidebar.metric("Model Accuracy", f"{stats['accuracy']}%")

# ============================================================
# PAGE 1: SYMPTOM ASSESSMENT
# ============================================================

if page == "🩺 Symptom Assessment":
    st.header("🩺 Patient Symptom Assessment")
    st.markdown("Complete the form below to get a malaria prediction based on symptoms.")
    
    # Patient Information Section
    with st.container():
        st.subheader("1️⃣ Patient Information")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            patient_id_input = st.text_input(
                "Patient ID *",
                value="",
                max_chars=Config.PATIENT_ID_MAX_LENGTH,
                help=f"Enter a unique ID ({Config.PATIENT_ID_MIN_LENGTH}-{Config.PATIENT_ID_MAX_LENGTH} characters, alphanumeric only)",
                placeholder="e.g., TRIAL001, PAT_2024_001"
            )
        
        with col2:
            # Check for duplicate
            if patient_id_input:
                is_duplicate, last_date = DataManager.check_duplicate_patient(patient_id_input)
                if is_duplicate:
                    st.warning(f"⚠️ Existing record from {last_date}")
    
    st.markdown("---")
    
    # Symptom Selection Section
    st.subheader("2️⃣ Symptom Checklist")
    st.markdown("*Select all symptoms that the patient is experiencing:*")
    
    selected_features = {}
    symptom_count = 0
    
    # Display symptoms in a 2-column layout
    col1, col2 = st.columns(2)
    
    for idx, feature in enumerate(Config.FEATURES):
        display_name = Config.FEATURE_DISPLAY_NAMES.get(feature, feature.replace('_', ' ').title())
        
        # Alternate between columns
        with col1 if idx % 2 == 0 else col2:
            response = st.checkbox(
                display_name,
                key=f"symptom_{feature}"
            )
            selected_features[feature] = 1 if response else 0
            if response:
                symptom_count += 1
    
    # Display symptom count
    st.info(f"✓ {symptom_count} symptom(s) selected")
    
    st.markdown("---")
    
    # Prediction Section
    st.subheader("3️⃣ Get Prediction")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        predict_button = st.button(
            "🔍 Predict Malaria Risk",
            type="primary",
            use_container_width=True,
            disabled=(symptom_count == 0 or not patient_id_input)
        )
    
    # Handle prediction
    if predict_button:
        # Sanitize and validate inputs
        patient_id = ValidationHelper.sanitize_patient_id(patient_id_input)
        
        is_valid, error_msg = ValidationHelper.validate_prediction_inputs(patient_id, selected_features)
        
        if not is_valid:
            st.error(f"❌ {error_msg}")
        else:
            try:
                with UIHelper.show_progress_indicator("🤖 Analyzing symptoms..."):
                    # Create feature vector
                    feature_values = SymptomProcessor.create_feature_vector(selected_features)
                    
                    # Scale features
                    feature_df = pd.DataFrame(feature_values, columns=Config.FEATURES)
                    scaled_values = scaler.transform(feature_df)
                    
                    # Get prediction
                    action, _ = model.predict(scaled_values, deterministic=True)
                    predicted_case = Config.POSITIVE_LABEL if action[0] == 1 else Config.NEGATIVE_LABEL
                    
                    # Store in session state
                    st.session_state['patient_id'] = patient_id
                    st.session_state['features'] = feature_values.tolist()
                    st.session_state['predicted_case'] = predicted_case
                    st.session_state['prediction_time'] = datetime.now()
                    st.session_state['symptom_count'] = symptom_count
                
                # Display result
                st.markdown("---")
                st.subheader("🎯 Prediction Result")
                UIHelper.display_prediction_result(predicted_case)
                
                # Next steps
                st.info("👉 **Next Step**: Navigate to 'Test Results & Data' to enter the laboratory test result.")
                
            except Exception as e:
                st.error(f"❌ Prediction error: {str(e)}")
                st.exception(e)

# ============================================================
# PAGE 2: TEST RESULTS & DATA MANAGEMENT
# ============================================================

elif page == "📊 Test Results & Data":
    st.header("📊 Test Results & Data Management")
    
    # Test Result Entry Section
    st.subheader("1️⃣ Enter Laboratory Test Result")
    
    if st.session_state['patient_id'] is None:
        st.warning("⚠️ No pending prediction. Please complete symptom assessment first.")
        st.info("👈 Go to 'Symptom Assessment' page to start.")
    else:
        # Display prediction summary
        with st.container():
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Patient ID", st.session_state['patient_id'])
            
            with col2:
                st.metric("Predicted Result", st.session_state['predicted_case'])
            
            with col3:
                if st.session_state['prediction_time']:
                    time_diff = (datetime.now() - st.session_state['prediction_time']).seconds // 60
                    st.metric("Time Elapsed", f"{time_diff} min ago")
        
        st.markdown("---")
        
        # Actual test result input
        st.markdown("**Enter the laboratory test result:**")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            actual_result = st.radio(
                "Laboratory Test Result",
                [Config.POSITIVE_LABEL, Config.NEGATIVE_LABEL],
                horizontal=True,
                label_visibility="collapsed"
            )
        
        # Submit button
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            submit_button = st.button(
                "💾 Submit & Save Record",
                type="primary",
                use_container_width=True
            )
        
        if submit_button:
            try:
                with UIHelper.show_progress_indicator("💾 Saving record..."):
                    # Create new entry
                    new_entry = pd.DataFrame({
                        'Date': [format_datetime(datetime.now())],
                        'Patient ID': [st.session_state['patient_id']],
                        'Symptoms': [str(st.session_state['features'])],
                        'Predicted Case': [st.session_state['predicted_case']],
                        'Actual Case': [actual_result]
                    })
                    
                    # Save data
                    success, total_records, message = DataManager.save_data(new_entry)
                    
                    if success:
                        st.success(f"✅ {message} (Total records: {total_records})")
                        
                        # Check prediction accuracy
                        predicted_label = "1" if "Positive" in st.session_state['predicted_case'] else "0"
                        actual_label = "1" if "Positive" in actual_result else "0"
                        is_correct = (predicted_label == actual_label)
                        
                        UIHelper.display_accuracy_feedback(is_correct)
                        
                        # Check for retraining notification
                        if not Config.ENABLE_RETRAINING and total_records >= Config.RETRAIN_INTERVAL and total_records % Config.RETRAIN_INTERVAL == 0:
                            st.info(f"📊 {total_records} samples collected. Data ready for offline model retraining.")
                            st.info("💡 See RETRAINING_GUIDE.md for instructions.")
                        
                        # Reset session state
                        st.session_state['patient_id'] = None
                        st.session_state['features'] = None
                        st.session_state['predicted_case'] = None
                        st.session_state['prediction_time'] = None
                        
                        st.info("✓ Ready for next patient assessment.")
                    else:
                        st.error(f"❌ {message}")
                        
            except Exception as e:
                st.error(f"❌ Error saving record: {str(e)}")
    
    st.markdown("---")
    
    # Data Visualization and Export Section
    st.subheader("2️⃣ Trial Data & Analytics")
    
    df = DataManager.load_data()
    
    if df.empty:
        st.info("📝 No records yet. Start by completing symptom assessments.")
    else:
        # Display statistics
        stats = DataManager.get_statistics()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Records", stats['total'], delta=None)
        
        with col2:
            st.metric("Positive Cases", stats['positive'], 
                     delta=f"{stats['positive']/stats['total']*100:.1f}%" if stats['total'] > 0 else "0%")
        
        with col3:
            st.metric("Negative Cases", stats['negative'],
                     delta=f"{stats['negative']/stats['total']*100:.1f}%" if stats['total'] > 0 else "0%")
        
        with col4:
            st.metric("Model Accuracy", f"{stats['accuracy']}%")
        
        st.markdown("---")
        
        # Data filtering
        st.subheader("3️⃣ Filter & Export Data")
        
        filter_option = st.radio(
            "Filter By:",
            ["📋 All Data", "📅 Date Range", "👤 Patient ID"],
            horizontal=True
        )
        
        filtered_df = df.copy()
        
        if filter_option == "📅 Date Range":
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date")
            with col2:
                end_date = st.date_input("End Date")
            
            # Filter by date range
            try:
                filtered_df['Date_parsed'] = pd.to_datetime(filtered_df['Date'], errors='coerce')
                filtered_df = filtered_df[
                    (filtered_df['Date_parsed'].dt.date >= start_date) &
                    (filtered_df['Date_parsed'].dt.date <= end_date)
                ]
                filtered_df = filtered_df.drop('Date_parsed', axis=1)
            except:
                st.warning("Error filtering by date")
                
        elif filter_option == "👤 Patient ID":
            patient_filter = st.text_input("Enter Patient ID:")
            if patient_filter:
                filtered_df = df[df['Patient ID'].str.contains(patient_filter, case=False, na=False)]
        
        # Display filtered data
        if not filtered_df.empty:
            st.dataframe(
                filtered_df,
                use_container_width=True,
                height=400
            )
            
            st.caption(f"Showing {len(filtered_df)} of {len(df)} records")
            
            # Download buttons
            st.markdown("---")
            st.subheader("💾 Download Options")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                csv_data = filtered_df.to_csv(index=False).encode(Config.CSV_ENCODING)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_data,
                    file_name=f"malaria_trial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                tsv_data = filtered_df.to_csv(index=False, sep='\\t').encode(Config.CSV_ENCODING)
                st.download_button(
                    label="📊 Download TSV (Excel)",
                    data=tsv_data,
                    file_name=f"malaria_trial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tsv",
                    mime="text/tab-separated-values",
                    use_container_width=True
                )
            
            with col3:
                # JSON export for API integration
                json_data = filtered_df.to_json(orient='records', date_format='iso')
                st.download_button(
                    label="📄 Download JSON",
                    data=json_data,
                    file_name=f"malaria_trial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
        else:
            st.warning("No records match the selected filter.")

# ============================================================
# FOOTER
# ============================================================

st.markdown("---")
st.caption(f"© 2025 {Config.ORG_NAME} | {Config.APP_NAME} v{Config.APP_VERSION}")
st.caption("⚠️ This is a clinical decision support tool. Always confirm with laboratory testing.")
