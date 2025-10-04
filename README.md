# Integrated Malaria Case Prediction v2.0

**Production-ready malaria prediction system optimized for Streamlit Cloud deployment and clinical trials.**

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)

## 🚀 Features

- **Clinical Symptom-Based Prediction**: AI-powered malaria diagnosis using patient symptoms
- **Reinforcement Learning Model**: PPO (Proximal Policy Optimization) for adaptive predictions
- **Real-Time Data Collection**: Automated trial data capture with timestamps
- **Trial-Ready Dashboard**: Metrics, filtering, and export functionality
- **Cloud-Optimized**: No crashes, stable performance on Streamlit Cloud
- **Multiple Export Formats**: CSV and TSV (Excel-compatible) downloads

## 📊 Live Demo

> Deploy to Streamlit Cloud in seconds! See `CLINICAL_TRIAL_GUIDE.md` for instructions.

## 🏥 Clinical Trial Use

This application is specifically designed for:
- ✅ Healthcare facilities conducting malaria prediction trials
- ✅ Research institutions collecting patient symptom data
- ✅ Clinical decision support systems
- ✅ Medical training and education

### Trial Workflow:
1. **Patient Registration** → Enter symptoms → Get prediction
2. **Laboratory Testing** → Confirm with actual test
3. **Result Entry** → Record actual diagnosis
4. **Data Collection** → Export for analysis

See **[CLINICAL_TRIAL_GUIDE.md](CLINICAL_TRIAL_GUIDE.md)** for complete deployment instructions.

## 🛠️ Installation

### For Streamlit Cloud (Recommended):
1. Fork/clone this repository
2. Deploy on [share.streamlit.io](https://share.streamlit.io)
3. Set main file: `Home.py`
4. App deploys automatically

### For Local Development:
```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/Integated_Malaria_Case_Prediction_v2.git
cd Integated_Malaria_Case_Prediction_v2

# Install dependencies
pip install -r requirements.txt

# Run application
streamlit run Home.py
```

## 📁 Project Structure

```
├── Home.py                          # Main landing page
├── pages/
│   ├── malaria_reinforcement.py     # Clinical prediction (main)
│   └── non_clinical_malaria_streamlit.py
├── models/
│   ├── ppo_malaria.zip              # Trained RL model
│   ├── ppo_malaria2.zip             # Alternative model
│   ├── scaler.pkl                   # Feature scaler
│   └── scaler2.pkl
├── test_records.csv                 # Trial data (auto-generated)
├── requirements.txt                 # Python dependencies
├── CLINICAL_TRIAL_GUIDE.md          # Trial deployment guide
└── RETRAINING_GUIDE.md              # Offline retraining instructions
```

## 🧠 Model Information

- **Algorithm**: Proximal Policy Optimization (PPO)
- **Framework**: Stable-Baselines3 + PyTorch
- **Features**: 10 clinical symptoms
- **Output**: Binary classification (Positive/Negative)

### Symptoms Used:
- Chill/Cold
- Headache
- Fever
- Generalized body pain
- Abdominal pain
- Loss of appetite
- Joint pain
- Vomiting
- Nausea
- Diarrhea

## 🔒 Online Retraining: Streamlit Cloud Limitation

**❌ Online retraining is NOT compatible with Streamlit Cloud** due to PyTorch/asyncio conflicts.

### Current Status
- 🚫 **Online retraining DISABLED by default** (causes segmentation faults)
- ✅ **Data collection ENABLED** - All patient data saved automatically
- ✅ **Offline retraining RECOMMENDED** - Stable and reliable

### Why Online Retraining Fails
The error `torch.classes RuntimeError` and subsequent segmentation faults occur because:
- PyTorch's RL training uses multiprocessing
- Streamlit Cloud's file watcher conflicts with PyTorch modules
- `model.learn()` triggers segmentation faults even with optimizations
- No amount of memory cleanup prevents this fundamental incompatibility

### Recommended Workflow (Stable)
1. ✅ **Deploy with retraining disabled** (default)
2. ✅ **Collect patient data** - Saves to `test_records.csv`
3. ✅ **Download data every 20-50 patients**
4. ✅ **Retrain offline** using local machine
5. ✅ **Deploy updated model** to Streamlit Cloud

### Offline Retraining (RECOMMENDED)
See **[RETRAINING_GUIDE.md](RETRAINING_GUIDE.md)** for step-by-step instructions on:
- Downloading trial data
- Retraining model locally
- Deploying updated model

### For Advanced Users: Local Development Only
Online retraining works on **local machines** with adequate resources:
```bash
# Windows PowerShell
$env:ENABLE_RETRAINING="true"
streamlit run Home.py

# Linux/Mac
export ENABLE_RETRAINING=true
streamlit run Home.py
```
⚠️ **DO NOT enable on Streamlit Cloud** - will crash immediately.

## 📈 Data Export

All patient data is saved to `test_records.csv` with:
- Timestamp
- Patient ID
- Symptoms array
- Predicted result
- Actual test result

Download options:
- **CSV**: For Python/R analysis
- **TSV**: For Excel analysis
- **Filters**: By date, patient ID, or all data

## 🐛 Troubleshooting

### App crashes after multiple entries
- ✅ **Optimized in v2.0** - Ultra-low timesteps + aggressive memory cleanup
- If crashes persist, disable retraining: `ENABLE_RETRAINING=false`
- Verify deployment shows warning banner if enabled

### Segmentation fault errors
- Now includes memory cleanup to prevent this
- If still occurring, set `ENABLE_RETRAINING=false`
- Consider offline retraining instead

### Data not saving
- Check internet connection
- Ensure Patient ID is entered
- Complete full workflow (symptoms → prediction → test result)

## 📝 Citation

If using this system in research, please cite:
```
eHealth Africa - Integrated Malaria Case Prediction System v2.0
URL: [Your Streamlit Cloud URL]
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/improvement`)
3. Commit changes (`git commit -am 'Add feature'`)
4. Push to branch (`git push origin feature/improvement`)
5. Open Pull Request

## 📄 License

[Specify your license]

## 🏢 Organization

**eHealth Africa**

## 📞 Support

For technical issues:
- Review `CLINICAL_TRIAL_GUIDE.md`
- Review `RETRAINING_GUIDE.md`
- Check Streamlit Cloud logs
- Open GitHub issue

## ⚠️ Medical Disclaimer

This system is a **clinical decision support tool** and should NOT replace:
- Professional medical diagnosis
- Laboratory testing
- Clinical judgment
- Standard medical protocols

Always confirm predictions with appropriate laboratory tests.

---

**Status**: ✅ Production Ready | **Version**: 2.0 | **Last Updated**: 2025-10-04