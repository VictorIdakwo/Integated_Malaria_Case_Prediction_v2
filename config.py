"""
Configuration file for Malaria Prediction System
Centralizes all configuration parameters
"""

import os
from typing import List, Dict

# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

class Config:
    """Central configuration for the application"""
    
    # Application Info
    APP_NAME = "Clinical Malaria Prediction System"
    APP_VERSION = "2.0.0"
    ORG_NAME = "eHealth Africa"
    
    # File Paths
    MODEL_PATH = 'models/ppo_malaria'
    MODEL_PATH_ALT = 'models/ppo_malaria2'
    SCALER_PATH = 'models/scaler.pkl'
    SCALER_PATH_ALT = 'models/scaler2.pkl'
    DATA_PATH = 'test_records.csv'
    BACKUP_DIR = 'backups'
    LOGO_PATH = "images/eHA-logo-blue_320x132.png"
    
    # Feature Definitions
    FEATURES: List[str] = [
        'chill_cold', 
        'headache', 
        'fever', 
        'generalized body pain',
        'abdominal pain', 
        'Loss of appetite', 
        'joint pain', 
        'vomiting',
        'nausea', 
        'diarrhea'
    ]
    
    # Feature Display Names (prettier names for UI)
    FEATURE_DISPLAY_NAMES: Dict[str, str] = {
        'chill_cold': 'Chills or Cold Feeling',
        'headache': 'Headache',
        'fever': 'Fever',
        'generalized body pain': 'General Body Pain',
        'abdominal pain': 'Abdominal Pain',
        'Loss of appetite': 'Loss of Appetite',
        'joint pain': 'Joint Pain',
        'vomiting': 'Vomiting',
        'nausea': 'Nausea',
        'diarrhea': 'Diarrhea'
    }
    
    # Model Training Configuration
    ENABLE_RETRAINING = os.getenv('ENABLE_RETRAINING', 'False').lower() == 'true'
    RETRAIN_INTERVAL = 5  # Retrain after every N samples
    TRAINING_TIMESTEPS = 200  # Reduced for cloud stability
    MIN_SAMPLES_FOR_RETRAINING = 5
    
    # Data Validation
    PATIENT_ID_MIN_LENGTH = 3
    PATIENT_ID_MAX_LENGTH = 50
    PATIENT_ID_PATTERN = r'^[A-Za-z0-9_-]+$'  # Alphanumeric, underscore, hyphen only
    
    # UI Configuration
    PAGE_ICON = "🏥"
    LAYOUT = "wide"
    SIDEBAR_STATE = "expanded"
    
    # Data Export Configuration
    CSV_ENCODING = 'utf-8'
    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    DATE_FORMAT = '%Y-%m-%d'
    
    # Prediction Labels
    POSITIVE_LABEL = "Positive (1)"
    NEGATIVE_LABEL = "Negative (0)"
    
    # Warning Messages
    WARNING_RETRAINING_ENABLED = "🚨 WARNING: Online retraining ENABLED - WILL CRASH on Streamlit Cloud!"
    SUCCESS_STABLE_MODE = "✅ Stable mode - Data collection enabled. Model retraining available offline."
    
    # CSV Columns
    CSV_COLUMNS = ['Date', 'Patient ID', 'Symptoms', 'Predicted Case', 'Actual Case']
    
    @classmethod
    def get_feature_count(cls) -> int:
        """Get the number of features"""
        return len(cls.FEATURES)
    
    @classmethod
    def validate_patient_id(cls, patient_id: str) -> tuple[bool, str]:
        """
        Validate patient ID format
        Returns: (is_valid, error_message)
        """
        import re
        
        if not patient_id:
            return False, "Patient ID cannot be empty"
        
        if len(patient_id) < cls.PATIENT_ID_MIN_LENGTH:
            return False, f"Patient ID must be at least {cls.PATIENT_ID_MIN_LENGTH} characters"
        
        if len(patient_id) > cls.PATIENT_ID_MAX_LENGTH:
            return False, f"Patient ID cannot exceed {cls.PATIENT_ID_MAX_LENGTH} characters"
        
        if not re.match(cls.PATIENT_ID_PATTERN, patient_id):
            return False, "Patient ID can only contain letters, numbers, underscores, and hyphens"
        
        return True, ""
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories if they don't exist"""
        os.makedirs(cls.BACKUP_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(cls.MODEL_PATH), exist_ok=True)
