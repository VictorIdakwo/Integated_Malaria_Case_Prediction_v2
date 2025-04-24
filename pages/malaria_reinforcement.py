import streamlit as st
import numpy as np
import pandas as pd
import joblib
import os
import types
import torch
import asyncio

# Patch torch.classes for compatibility with Streamlit
if not hasattr(torch, 'classes'):
    torch.classes = types.SimpleNamespace()
elif not hasattr(torch.classes, '__path__'):
    torch.classes.__path__ = types.SimpleNamespace(_path=[])

# Fix asyncio crash
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from datetime import datetime
import gymnasium as gym
from gymnasium import spaces

st.title("Clinical Malaria Prediction")

# File paths
MODEL_PATH = 'models/ppo_malaria'
SCALER_PATH = 'models/scaler.pkl'
DATA_PATH = 'test_records.csv'

# Load trained PPO model and scaler
model = PPO.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)

# Symptom features
features = ['chill_cold', 'headache', 'fever', 'generalized body pain',
            'abdominal pain', 'Loss of appetite', 'joint pain', 'vomiting',
            'nausea', 'diarrhea']

# Load or create data
def load_data():
    if os.path.exists(DATA_PATH):
        return pd.read_csv(DATA_PATH)
    else:
        return pd.DataFrame(columns=['Date', 'Patient ID', 'Symptoms', 'Predicted Case', 'Actual Case'])

def save_data(new_entry):
    df = load_data()
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(DATA_PATH, index=False)

# Custom Environment
class MalariaEnv(gym.Env):
    def __init__(self):
        super(MalariaEnv, self).__init__()
        self.observation_space = spaces.Box(low=-1, high=1, shape=(10,), dtype=np.float32)
        self.action_space = spaces.Discrete(2)
        self.state = np.zeros(10, dtype=np.float32)
        self.done = False

    def reset(self, seed=None, options=None):
        self.state = np.random.uniform(-1, 1, size=(10,)).astype(np.float32)
        self.done = False
        return self.state, {}

    def step(self, action):
        reward = 1 if (action == 1 and np.sum(self.state) > 5) else -1
        self.done = True
        return self.state, reward, self.done, False, {}

    def render(self, mode='human'): pass
    def close(self): pass

# Retraining Logic
def retrain_model():
    df = load_data()
    if len(df) >= 10:
        X = np.array([eval(symptoms) for symptoms in df['Symptoms']])
        X = np.squeeze(X)
        if X.ndim == 1:
            X = X.reshape(1, -1)
        X_df = pd.DataFrame(X, columns=features)
        X_scaled = scaler.transform(X_df)
        env = DummyVecEnv([lambda: MalariaEnv()])
        model.set_env(env)
        model.learn(total_timesteps=1000)
        model.save(MODEL_PATH)
        st.success("Model retrained successfully!")

# Session state init
if 'patient_id' not in st.session_state:
    st.session_state['patient_id'] = None
    st.session_state['features'] = None
    st.session_state['predicted_case'] = None

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Symptom Input", "Test Result & Download Data"])

# Page 1
if page == "Symptom Input":
    st.title("Malaria Prediction - RL Model")
    st.write("Select your symptoms and get a prediction.")

    patient_id = st.text_input("Patient ID", "")
    selected_features = {}

    for feature in features:
        response = st.radio(f"Do you have {feature.replace('_', ' ')}?", ["No", "Yes"], horizontal=True)
        selected_features[feature] = 1 if response == "Yes" else 0

    if st.button("Predict Malaria"):
        if not patient_id:
            st.warning("Please enter a Patient ID.")
        else:
            feature_values = np.array([selected_features[f] for f in features]).reshape(1, -1)
            feature_df = pd.DataFrame(feature_values, columns=features)
            scaled_values = scaler.transform(feature_df)
            action, _ = model.predict(scaled_values)
            predicted_case = "Positive (1)" if action[0] == 1 else "Negative (0)"

            st.session_state['patient_id'] = patient_id
            st.session_state['features'] = feature_values.tolist()
            st.session_state['predicted_case'] = predicted_case

            st.write(f"### Predicted Case: {predicted_case}")
            st.info("Please proceed to a clinic for testing and enter your result on the next page.")

# Page 2
if page == "Test Result & Download Data":
    st.title("Enter Actual Test Result & Download Data")

    if st.session_state['patient_id'] is None:
        st.warning("Please go to the first page and enter symptoms first.")
    else:
        st.write(f"Patient ID: {st.session_state['patient_id']}")
        st.write(f"Predicted Case: {st.session_state['predicted_case']}")

        actual_cases = st.radio("Clinic Test Result", ["Positive (1)", "Negative (0)"])

        if st.button("Submit & Save Test Record"):
            new_entry = pd.DataFrame({
                'Date': [datetime.today().strftime('%Y-%m-%d')],
                'Patient ID': [st.session_state['patient_id']],
                'Symptoms': [str(st.session_state['features'])],
                'Predicted Case': [st.session_state['predicted_case']],
                'Actual Case': [actual_cases]
            })
            save_data(new_entry)
            retrain_model()
            st.success("Test result saved and model retrained successfully!")

    st.subheader("Download Test Records")
    df = load_data()

    if df.empty:
        st.warning("No records found.")
    else:
        filter_option = st.radio("Filter By:", ["Date", "Patient ID"], horizontal=True)

        if filter_option == "Date":
            selected_date = st.date_input("Select Date")
            filtered_df = df[df['Date'] == selected_date.strftime('%Y-%m-%d')]
        else:
            selected_patient = st.text_input("Enter Patient ID")
            filtered_df = df[df['Patient ID'] == selected_patient]

        if not filtered_df.empty:
            st.dataframe(filtered_df)
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Data", csv, "filtered_data.csv", "text/csv")
        else:
            st.warning("No matching records found.")
