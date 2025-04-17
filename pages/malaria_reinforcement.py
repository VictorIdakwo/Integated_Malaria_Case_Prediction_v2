import os
import sys
import streamlit as st
import pandas as pd
import torch
import uuid
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env

# Patch torch to prevent Streamlit path inspection crash
if 'torch' in sys.modules:
    torch.__path__ = []

# Prevent event loop issue (Streamlit + asyncio + Python 3.12)
import asyncio
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

# Set paths
MODEL_PATH = "ppo_malaria_model"
CSV_PATH = "malaria_prediction_results.csv"

# Dummy symptoms and environment setup
SYMPTOMS = ['fever', 'chills', 'headache', 'nausea', 'vomiting', 'diarrhea']
NUM_FEATURES = len(SYMPTOMS)

# Create a dummy environment for PPO
from gymnasium import spaces
import numpy as np
import gymnasium as gym

class MalariaEnv(gym.Env):
    def __init__(self):
        super().__init__()
        self.observation_space = spaces.Box(low=0, high=1, shape=(NUM_FEATURES,), dtype=np.float32)
        self.action_space = spaces.Discrete(2)  # 0: no malaria, 1: malaria
        self.state = np.zeros(NUM_FEATURES)
        self.current_label = 0

    def reset(self, *, seed=None, options=None):
        self.state = np.random.randint(0, 2, size=NUM_FEATURES).astype(np.float32)
        self.current_label = np.random.randint(0, 2)
        return self.state, {}

    def step(self, action):
        reward = 1 if action == self.current_label else -1
        done = True
        return self.state, reward, done, False, {}

# Load or train PPO model
def load_or_train_model():
    if os.path.exists(f"{MODEL_PATH}/success_model.zip"):
        return PPO.load(f"{MODEL_PATH}/success_model", env=make_vec_env(MalariaEnv, n_envs=1))
    else:
        env = make_vec_env(MalariaEnv, n_envs=1)
        model = PPO("MlpPolicy", env, verbose=0)
        model.learn(total_timesteps=2000)
        model.save(f"{MODEL_PATH}/success_model")
        return model

model = load_or_train_model()

# Load previous results
def load_results():
    if os.path.exists(CSV_PATH):
        return pd.read_csv(CSV_PATH)
    else:
        return pd.DataFrame(columns=["Patient ID", "Date", *SYMPTOMS, "Predicted", "Actual"])

results_df = load_results()

# --- Streamlit UI ---
st.title("🦟 Clinical Malaria Prediction (Reinforcement Learning)")

st.subheader("Enter Symptoms for a New Patient")
patient_id = st.text_input("Patient ID", str(uuid.uuid4())[:8])
selected_symptoms = st.multiselect("Select observed symptoms", SYMPTOMS)
actual_case = st.selectbox("Clinically confirmed?", ["Yes", "No"])
submit = st.button("Predict and Save")

if submit:
    # Convert input
    obs = np.array([1 if symptom in selected_symptoms else 0 for symptom in SYMPTOMS], dtype=np.float32)
    
    # Predict
    predicted_action, _ = model.predict(obs)
    predicted = "Yes" if predicted_action == 1 else "No"

    # Save record
    new_row = {
        "Patient ID": patient_id,
        "Date": pd.Timestamp.now().strftime("%Y-%m-%d"),
        **{symptom: 1 if symptom in selected_symptoms else 0 for symptom in SYMPTOMS},
        "Predicted": predicted,
        "Actual": actual_case
    }
    results_df = pd.concat([results_df, pd.DataFrame([new_row])], ignore_index=True)
    results_df.to_csv(CSV_PATH, index=False)

    st.success(f"Prediction saved: **{predicted}**")

    # Optional: model retraining
    try:
        model.set_env(make_vec_env(MalariaEnv, n_envs=1))
        model.learn(total_timesteps=500)
        model.save(f"{MODEL_PATH}/success_model")
        st.info("Model retrained with new experience.")
    except Exception as e:
        st.error(f"Retraining failed: {e}")

# --- Results Section ---
st.subheader("📊 Daily Prediction Records")
date_filter = st.date_input("Filter by Date", value=None)
id_filter = st.text_input("Filter by Patient ID")

filtered_df = results_df.copy()
if date_filter:
    filtered_df = filtered_df[filtered_df["Date"] == pd.to_datetime(date_filter).strftime("%Y-%m-%d")]
if id_filter:
    filtered_df = filtered_df[filtered_df["Patient ID"].str.contains(id_filter)]

st.dataframe(filtered_df)

# Download option
csv = filtered_df.to_csv(index=False).encode()
st.download_button("Download CSV", csv, "malaria_predictions_filtered.csv", "text/csv")
