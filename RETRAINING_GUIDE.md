# Model Retraining Guide

## Overview

Online retraining has been **disabled by default** to prevent segmentation faults and memory crashes in Streamlit Cloud deployment. Patient data is automatically saved to `test_records.csv` for offline retraining.

## Why Online Retraining is Disabled

The application was crashing after multiple entries due to:
- **Memory exhaustion**: PyTorch + stable-baselines3 requires significant RAM
- **Multiprocessing conflicts**: RL training conflicts with Streamlit's event loop
- **Cloud resource limits**: Streamlit Cloud has limited CPU/memory allocation

## Offline Retraining (Recommended)

### Step 1: Download Patient Data
1. Navigate to "Test Result & Download Data" page
2. Filter data if needed (by date or patient ID)
3. Click "Download Data" to get `filtered_data.csv` or download the full `test_records.csv`

### Step 2: Retrain Model Locally
Run the retraining script on a machine with sufficient resources:

```python
# retrain_offline.py
import pandas as pd
import numpy as np
import joblib
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
import gymnasium as gym
from gymnasium import spaces

# Load data
df = pd.read_csv('test_records.csv')

# Define features
features = ['chill_cold', 'headache', 'fever', 'generalized body pain',
            'abdominal pain', 'Loss of appetite', 'joint pain', 'vomiting',
            'nausea', 'diarrhea']

scaler = joblib.load('models/scaler.pkl')

# Prepare data
X = np.array([eval(symptoms) for symptoms in df['Symptoms']])
X = np.squeeze(X)
if len(df) >= 5:  # Retrain after every 5 samples
    X = X.reshape(1, -1)

X_df = pd.DataFrame(X, columns=features)
X_scaled = scaler.transform(X_df)

# Define environment
{{ ... }}

### Monitoring Data Collection

The app will display informative messages:
- **At 5, 10, 15, 20 samples**: "📊 X samples collected. Data saved for offline model retraining."
- This ensures you know when enough data is available for retraining

## Best Practices

1. **Collect data regularly**: Download `test_records.csv` weekly or monthly
{{ ... }}
3. **Test locally first**: Validate retrained model before deployment
4. **Monitor performance**: Track prediction accuracy over time
5. **Version control**: Use git tags for model versions

## Troubleshooting

**Q: Why is my model not improving?**
- Ensure you have diverse patient cases (both positive and negative)
- Check data quality in `test_records.csv`
- Increase `total_timesteps` during retraining

**Q: Can I retrain with a subset of data?**
- Yes, filter the CSV file before retraining
- Use recent data for better relevance

**Q: What if the app still crashes?**
- Verify `ENABLE_RETRAINING=false` (default)
- Check Streamlit Cloud logs for torch warnings
- Contact support if model loading fails
