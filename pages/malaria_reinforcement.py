import streamlit as st
import numpy as np
import pandas as pd
import joblib
import os
import gc
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from datetime import datetime
import gymnasium as gym  # Updated to Gymnasium
from gymnasium import spaces
import torch

# CONFIGURATION: Online retraining ENABLED by default with memory optimizations
# To disable: Set ENABLE_RETRAINING=false in environment or secrets.toml
ENABLE_RETRAINING = os.getenv('ENABLE_RETRAINING', 'True').lower() == 'true'

st.title("Clinical Malaria Prediction - Trial Mode")

# Display deployment status
if ENABLE_RETRAINING:
    st.warning("⚠️ Online retraining is ENABLED - may be unstable in cloud deployment")
else:
    st.success("✅ Running in stable mode - Data collection enabled for clinical trials")

# File paths
MODEL_PATH = 'models/ppo_malaria2'  # Ensure it matches the training script
SCALER_PATH = 'models/scaler2.pkl'
DATA_PATH = 'test_records.csv'

# Load trained PPO model and scaler
model = PPO.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)

# Define symptom features
features = ['chill_cold', 'headache', 'fever', 'generalized body pain',
            'abdominal pain', 'Loss of appetite', 'joint pain', 'vomiting',
            'nausea', 'diarrhea']

# Load existing data or create an empty DataFrame
def load_data():
    if os.path.exists(DATA_PATH):
        return pd.read_csv(DATA_PATH)
    else:
        return pd.DataFrame(columns=['Date', 'Patient ID', 'Symptoms', 'Predicted Case', 'Actual Case'])

def save_data(new_entry):
    """Save patient data with validation for clinical trials"""
    df = load_data()
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(DATA_PATH, index=False)
    return len(df)  # Return total count

# Custom Gymnasium Environment for Malaria Prediction
class MalariaEnv(gym.Env):
    def __init__(self):
        super(MalariaEnv, self).__init__()
        self.observation_space = spaces.Box(low=-1, high=1, shape=(10,), dtype=np.float32)  # Match trained model
        self.action_space = spaces.Discrete(2)  # Binary classification (0=Negative, 1=Positive)
        self.state = np.zeros(10, dtype=np.float32)
        self.done = False

    def reset(self, seed=None, options=None):
        self.state = np.random.uniform(-1, 1, size=(10,)).astype(np.float32)  # Match trained model
        self.done = False
        return self.state, {}  # Gymnasium requires returning (obs, info)

    def step(self, action):
        reward = 1 if (action == 1 and np.sum(self.state) > 5) else -1  # Reward logic
        self.done = True
        return self.state, reward, self.done, False, {}  # Gymnasium requires (obs, reward, done, truncated, info)

    def render(self, mode='human'):
        pass

    def close(self):
        pass

# Function to retrain the model
def retrain_model():
    """Save data for offline retraining. Online retraining disabled to prevent crashes."""
    df = load_data()
    
    # Check if retraining is enabled
    if not ENABLE_RETRAINING:
        # Just save the data - retraining will be done offline
        if len(df) >= 5 and len(df) % 5 == 0:
            st.info(f"📊 {len(df)} samples collected. Data saved for offline model retraining.")
            st.info("💡 Online retraining is disabled to prevent memory issues in cloud deployment.")
        return
    
    # Only retrain at specific intervals (5, 10, 15, etc.) to prevent continuous retraining
    if len(df) >= 5 and len(df) % 5 == 0:  # Retrain every 5 samples
        try:
            st.warning("⚠️ Retraining enabled - this may cause crashes in cloud environments!")
            
            # Convert Symptoms column from string to list of numbers
            X = np.array([eval(symptoms) for symptoms in df['Symptoms']])  # Convert from string to list
            X = np.squeeze(X)  # Remove extra dimensions if present

            # Ensure X is 2D with shape (n_samples, n_features)
            if X.ndim == 1:
                X = X.reshape(1, -1)

            X_df = pd.DataFrame(X, columns=features)  # Convert to DataFrame
            X_scaled = scaler.transform(X_df)  # Scale features

            # Set up RL environment with minimal timesteps for cloud stability
            env = DummyVecEnv([lambda: MalariaEnv()])
            model.set_env(env)
            
            # Ultra-low timesteps for cloud deployment (200 instead of 500/1000)
            # This reduces memory pressure significantly
            model.learn(total_timesteps=200, progress_bar=False)

            model.save(MODEL_PATH)
            
            # Aggressive resource cleanup to prevent memory leaks
            env.close()
            del env
            
            # Clear PyTorch cache if using CUDA
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Force Python garbage collection
            gc.collect()
            
            st.success(f"✅ Model retrained successfully after {len(df)} samples!")
            st.info("💾 Memory cleaned up to prevent crashes.")
            
        except Exception as e:
            st.error(f"❌ Error during retraining: {str(e)}")
            st.warning("⚠️ Prediction will continue with the existing model.")
            
            # Clean up on error
            try:
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except:
                pass

# Initialize session state
if 'patient_id' not in st.session_state:
    st.session_state['patient_id'] = None
    st.session_state['features'] = None
    st.session_state['predicted_case'] = None
    st.session_state['last_retrain_count'] = 0  # Track last retrain to avoid duplicate retrains

# Streamlit Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Symptom Input", "Test Result & Download Data"])

# ---- PAGE 1: SYMPTOM INPUT ----
if page == "Symptom Input":
    st.title("Malaria Prediction - RL Model")
    st.write("Select your symptoms and get a prediction.")

    # Patient ID Input
    patient_id = st.text_input("Patient ID", "")

    # Symptom Selection using Yes/No Buttons
    selected_features = {}
    for feature in features:
        response = st.radio(f"Do you have {feature.replace('_', ' ')}?", ["No", "Yes"], horizontal=True)
        selected_features[feature] = 1 if response == "Yes" else 0

    if st.button("Predict Malaria"):
        if not patient_id:
            st.warning("Please enter a Patient ID.")
        else:
            # Convert selected symptoms to numeric array
            feature_values = np.array([selected_features[f] for f in features]).reshape(1, -1)
            feature_df = pd.DataFrame(feature_values, columns=features)  # Convert to DataFrame
            scaled_values = scaler.transform(feature_df)  # Ensure correct input format

            # RL Model Predicts Action
            action, _ = model.predict(scaled_values)
            predicted_case = "Positive (1)" if action[0] == 1 else "Negative (0)"

            # Store patient data in session state
            st.session_state['patient_id'] = patient_id
            st.session_state['features'] = feature_values.tolist()
            st.session_state['predicted_case'] = predicted_case

            st.write(f"### Predicted Case: {predicted_case}")
            st.info("Please proceed to a clinic for testing and enter your result on the next page.")

# ---- PAGE 2: TEST RESULT & DOWNLOAD DATA ----
if page == "Test Result & Download Data":
    st.title("Enter Actual Test Result & Download Data")

    if st.session_state['patient_id'] is None:
        st.warning("Please go to the first page and enter symptoms first.")
    else:
        st.write(f"Patient ID: {st.session_state['patient_id']}")
        st.write(f"Predicted Case: {st.session_state['predicted_case']}")

        # Actual result from clinic
        actual_cases = st.radio("Clinic Test Result", ["Positive (1)", "Negative (0)"])

        if st.button("Submit & Save Test Record"):
            new_entry = pd.DataFrame({
                'Date': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],  # Include timestamp
                'Patient ID': [st.session_state['patient_id']],
                'Symptoms': [str(st.session_state['features'])],
                'Predicted Case': [st.session_state['predicted_case']],
                'Actual Case': [actual_cases]
            })
            total_records = save_data(new_entry)
            st.success(f"✅ Test result saved successfully! (Total records: {total_records})")
            
            # Check prediction accuracy
            predicted_label = "1" if "Positive" in st.session_state['predicted_case'] else "0"
            actual_label = "1" if "Positive" in actual_cases else "0"
            
            if predicted_label == actual_label:
                st.success("✓ Prediction was CORRECT")
            else:
                st.warning("✗ Prediction was INCORRECT")
            
            retrain_model()
            
            # Reset session state for next patient
            st.session_state['patient_id'] = None
            st.session_state['features'] = None
            st.session_state['predicted_case'] = None

    # Data Filtering & Download
    st.subheader("Download Test Records for Clinical Trial")
    df = load_data()

    if df.empty:
        st.warning("No records found.")
    else:
        # Show summary statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Records", len(df))
        with col2:
            positive_count = df['Actual Case'].str.contains('Positive').sum() if 'Actual Case' in df.columns else 0
            st.metric("Positive Cases", positive_count)
        with col3:
            negative_count = df['Actual Case'].str.contains('Negative').sum() if 'Actual Case' in df.columns else 0
            st.metric("Negative Cases", negative_count)
        
        st.markdown("---")
        filter_option = st.radio("Filter By:", ["All Data", "Date", "Patient ID"], horizontal=True)

        if filter_option == "All Data":
            filtered_df = df
        elif filter_option == "Date":
            selected_date = st.date_input("Select Date")
            # Handle both date formats (with and without time)
            filtered_df = df[df['Date'].str.contains(selected_date.strftime('%Y-%m-%d'))]
        else:
            selected_patient = st.text_input("Enter Patient ID")
            filtered_df = df[df['Patient ID'] == selected_patient]

        if not filtered_df.empty:
            st.dataframe(filtered_df, use_container_width=True)
            
            # Multiple download formats
            col1, col2 = st.columns(2)
            with col1:
                csv = filtered_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Download as CSV", 
                    csv, 
                    f"malaria_trial_data_{datetime.now().strftime('%Y%m%d')}.csv", 
                    "text/csv",
                    use_container_width=True
                )
            with col2:
                # Download as Excel-compatible format
                excel_csv = filtered_df.to_csv(index=False, sep='\t').encode('utf-8')
                st.download_button(
                    "📊 Download as TSV (Excel)", 
                    excel_csv, 
                    f"malaria_trial_data_{datetime.now().strftime('%Y%m%d')}.tsv", 
                    "text/tab-separated-values",
                    use_container_width=True
                )
        else:
            st.warning("No matching records found.")
