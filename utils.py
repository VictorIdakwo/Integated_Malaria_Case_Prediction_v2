"""
Utility functions for Malaria Prediction System
Provides data management, validation, and helper functions
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
from typing import Optional, Tuple, List, Dict
import streamlit as st
from config import Config


class DataManager:
    """Manages data loading, saving, and validation"""
    
    @staticmethod
    def load_data() -> pd.DataFrame:
        """
        Load patient data from CSV file
        Returns empty DataFrame with proper columns if file doesn't exist
        """
        if os.path.exists(Config.DATA_PATH):
            try:
                df = pd.read_csv(Config.DATA_PATH)
                return df
            except Exception as e:
                st.error(f"❌ Error loading data: {str(e)}")
                return pd.DataFrame(columns=Config.CSV_COLUMNS)
        else:
            return pd.DataFrame(columns=Config.CSV_COLUMNS)
    
    @staticmethod
    def save_data(new_entry: pd.DataFrame) -> Tuple[bool, int, str]:
        """
        Save patient data with backup and validation
        
        Args:
            new_entry: DataFrame with new patient record
            
        Returns:
            Tuple of (success, total_records, message)
        """
        try:
            df = DataManager.load_data()
            
            # Create backup before saving
            DataManager._create_backup(df)
            
            # Append new entry
            df = pd.concat([df, new_entry], ignore_index=True)
            
            # Save to CSV
            df.to_csv(Config.DATA_PATH, index=False, encoding=Config.CSV_ENCODING)
            
            return True, len(df), "Data saved successfully"
            
        except Exception as e:
            return False, 0, f"Error saving data: {str(e)}"
    
    @staticmethod
    def _create_backup(df: pd.DataFrame):
        """Create backup of current data"""
        try:
            Config.create_directories()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(Config.BACKUP_DIR, f'backup_{timestamp}.csv')
            
            # Only keep last 10 backups
            DataManager._cleanup_old_backups()
            
            if not df.empty:
                df.to_csv(backup_path, index=False, encoding=Config.CSV_ENCODING)
        except Exception:
            pass  # Silent fail for backups
    
    @staticmethod
    def _cleanup_old_backups(keep_last: int = 10):
        """Keep only the most recent N backups"""
        try:
            if not os.path.exists(Config.BACKUP_DIR):
                return
            
            backups = [f for f in os.listdir(Config.BACKUP_DIR) if f.startswith('backup_')]
            backups.sort(reverse=True)
            
            # Remove old backups
            for old_backup in backups[keep_last:]:
                os.remove(os.path.join(Config.BACKUP_DIR, old_backup))
        except Exception:
            pass
    
    @staticmethod
    def check_duplicate_patient(patient_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if patient ID already exists with pending test result
        
        Returns:
            Tuple of (is_duplicate, last_entry_date)
        """
        df = DataManager.load_data()
        
        if df.empty:
            return False, None
        
        # Check for exact patient ID match
        patient_records = df[df['Patient ID'] == patient_id]
        
        if not patient_records.empty:
            last_date = patient_records.iloc[-1]['Date']
            return True, last_date
        
        return False, None
    
    @staticmethod
    def get_statistics() -> Dict:
        """Get summary statistics from collected data"""
        df = DataManager.load_data()
        
        if df.empty:
            return {
                'total': 0,
                'positive': 0,
                'negative': 0,
                'accuracy': 0.0,
                'recent_entries': []
            }
        
        # Count positive and negative cases
        positive_count = df['Actual Case'].str.contains('Positive', na=False).sum()
        negative_count = df['Actual Case'].str.contains('Negative', na=False).sum()
        
        # Calculate accuracy
        correct_predictions = 0
        total_with_results = 0
        
        for _, row in df.iterrows():
            if pd.notna(row['Predicted Case']) and pd.notna(row['Actual Case']):
                total_with_results += 1
                pred = '1' if 'Positive' in str(row['Predicted Case']) else '0'
                actual = '1' if 'Positive' in str(row['Actual Case']) else '0'
                if pred == actual:
                    correct_predictions += 1
        
        accuracy = (correct_predictions / total_with_results * 100) if total_with_results > 0 else 0.0
        
        # Get recent entries
        recent = df.tail(5)[['Date', 'Patient ID', 'Predicted Case', 'Actual Case']].to_dict('records')
        
        return {
            'total': len(df),
            'positive': int(positive_count),
            'negative': int(negative_count),
            'accuracy': round(accuracy, 2),
            'recent_entries': recent
        }


class SymptomProcessor:
    """Processes symptom data for model prediction"""
    
    @staticmethod
    def parse_symptoms_from_string(symptoms_str: str) -> Optional[np.ndarray]:
        """
        Safely parse symptoms string to array (avoiding eval)
        
        Args:
            symptoms_str: String representation of symptoms array
            
        Returns:
            numpy array or None if parsing fails
        """
        try:
            # Use json.loads instead of eval for security
            # Clean up the string format
            symptoms_str = symptoms_str.strip()
            
            # Convert Python list format to JSON format
            symptoms_str = symptoms_str.replace("'", '"')
            
            # Parse JSON
            symptoms_list = json.loads(symptoms_str)
            
            # Handle nested list structure [[...]]
            if isinstance(symptoms_list, list) and len(symptoms_list) > 0:
                if isinstance(symptoms_list[0], list):
                    symptoms_list = symptoms_list[0]
            
            return np.array(symptoms_list, dtype=np.float32)
            
        except Exception as e:
            st.error(f"Error parsing symptoms: {str(e)}")
            return None
    
    @staticmethod
    def create_feature_vector(selected_features: Dict[str, int]) -> np.ndarray:
        """
        Create feature vector from selected symptoms
        
        Args:
            selected_features: Dictionary mapping feature names to values (0 or 1)
            
        Returns:
            numpy array of feature values
        """
        feature_values = np.array([selected_features[f] for f in Config.FEATURES])
        return feature_values.reshape(1, -1)


class ValidationHelper:
    """Input validation helper functions"""
    
    @staticmethod
    def validate_prediction_inputs(patient_id: str, selected_features: Dict) -> Tuple[bool, str]:
        """
        Validate all inputs before prediction
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate patient ID
        is_valid, error_msg = Config.validate_patient_id(patient_id)
        if not is_valid:
            return False, error_msg
        
        # Check if any symptoms selected
        if all(value == 0 for value in selected_features.values()):
            return False, "⚠️ Please select at least one symptom before predicting."
        
        return True, ""
    
    @staticmethod
    def sanitize_patient_id(patient_id: str) -> str:
        """Remove potentially harmful characters from patient ID"""
        # Remove leading/trailing whitespace
        patient_id = patient_id.strip()
        
        # Remove any control characters
        patient_id = ''.join(char for char in patient_id if char.isprintable())
        
        return patient_id


class UIHelper:
    """UI/UX helper functions"""
    
    @staticmethod
    def display_prediction_result(predicted_case: str, confidence: Optional[float] = None):
        """
        Display prediction result with appropriate styling
        
        Args:
            predicted_case: Prediction label
            confidence: Optional confidence score
        """
        if "Positive" in predicted_case:
            st.error(f"### 🦟 Prediction: {predicted_case}")
            st.warning("⚠️ **Action Required**: Patient should visit a clinic for laboratory testing.")
        else:
            st.success(f"### ✓ Prediction: {predicted_case}")
            st.info("💡 **Recommendation**: If symptoms persist or worsen, please seek medical attention.")
        
        if confidence is not None:
            st.progress(confidence, text=f"Confidence: {confidence*100:.1f}%")
    
    @staticmethod
    def display_accuracy_feedback(is_correct: bool):
        """Display whether prediction was correct"""
        if is_correct:
            st.balloons()
            st.success("🎯 **Model Prediction: CORRECT** - Model is learning!")
        else:
            st.warning("📊 **Model Prediction: INCORRECT** - This feedback helps improve the model.")
    
    @staticmethod
    def create_info_expander():
        """Create an expandable info section"""
        with st.expander("ℹ️ About This Prediction System"):
            st.markdown("""
            ### How It Works
            This system uses **Reinforcement Learning** (PPO algorithm) to predict malaria based on clinical symptoms.
            
            ### Important Notes
            - ⚠️ This is a **decision support tool**, not a replacement for medical diagnosis
            - 🔬 Always confirm with laboratory testing (microscopy or RDT)
            - 📊 The model improves as more data is collected
            - 🏥 Follow your local clinical protocols
            
            ### Symptoms Analyzed
            The model considers 10 key malaria symptoms to make predictions.
            
            ### Data Privacy
            - Patient IDs should be anonymized
            - No personally identifiable information should be entered
            - Data is stored securely for model improvement
            """)
    
    @staticmethod
    def show_progress_indicator(message: str):
        """Show a progress indicator for long operations"""
        return st.spinner(message)


def format_datetime(dt: datetime) -> str:
    """Format datetime for display"""
    return dt.strftime(Config.DATETIME_FORMAT)


def format_date(dt: datetime) -> str:
    """Format date for display"""
    return dt.strftime(Config.DATE_FORMAT)
