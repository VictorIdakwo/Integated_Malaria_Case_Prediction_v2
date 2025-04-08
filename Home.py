import streamlit as st

st.set_page_config(page_title="Malaria Prediction Portal")

st.title("Malaria Prediction Portal")

st.image("images/eHA-logo-blue_320x132.png", width=320)

st.markdown("""
This portal provides insights into **malaria prediction** using advanced Machine Learning models.

Use the sidebar or links below to explore:
""")

st.page_link("pages/malaria_reinforcement.py", label="Clinical Malaria Prediction")
st.page_link("pages/non_clinical_malaria_streamlit.py", label="Non-Clinical Malaria Prediction")

st.subheader("Prediction Features")
st.markdown("""
- **Clinical Malaria Prediction**: Uses symptoms like chills, fever, headache, vomiting, etc.
- **Non-Clinical Malaria Prediction**: Uses climate data like Rainfall, LST, and Humidity.
""")
