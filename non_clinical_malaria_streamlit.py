import streamlit as st
import geopandas as gpd
import requests
import pandas as pd
import folium
import io
import concurrent.futures
from streamlit_folium import folium_static
from datetime import datetime
from branca.colormap import LinearColormap
import joblib
from sklearn.preprocessing import StandardScaler

st.title("Non-Clinical Malaria Prediction")

# File paths
SHAPEFILE_PATH = "./ward/Wards.shp"
MODEL_PATH = "./Models/Non Clinical/models/random_forest.joblib"
SCALER_PATH = "./Models/Non Clinical/models/scaler_rf.joblib"

# Cached model and scaler loading
@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)

@st.cache_resource
def load_scaler():
    return joblib.load(SCALER_PATH)

trained_model = load_model()
scaler = load_scaler()

# Load and preprocess shapefile
st.title("🦟 Malaria Case Prediction & 🌍 Climate Data ")
gdf = gpd.read_file(SHAPEFILE_PATH).to_crs("EPSG:4326")
gdf["geometry"] = gdf["geometry"].simplify(0.001, preserve_topology=True)
gdf["lat"] = gdf.geometry.centroid.y
gdf["lon"] = gdf.geometry.centroid.x

# NASA POWER API Parameters
BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
PARAMETERS = "T2M,RH2M,PRECTOTCORR"
COMMUNITY = "RE"

date = st.sidebar.date_input("Select Date", datetime(2024, 1, 1))
selected_layer = st.sidebar.radio("Select Layer", ["Predicted Malaria Cases","Temperature", "Humidity", "Precipitation"])

# Function to fetch NASA POWER climate data
@st.cache_data(show_spinner="Fetching Climate Data...")
def fetch_nasa_data(locations, date):
    date_str = date.strftime("%Y%m%d")
    results = []
    
    def fetch(lat, lon):
        url = f"{BASE_URL}?parameters={PARAMETERS}&latitude={lat}&longitude={lon}&start={date_str}&end={date_str}&community={COMMUNITY}&format=CSV"
        response = requests.get(url)
        if response.status_code == 200:
            lines = response.text.splitlines()
            header_end = next(i for i, line in enumerate(lines) if "-END HEADER-" in line)
            df = pd.read_csv(io.StringIO("\n".join(lines[header_end + 1:])))
            df[["Latitude", "Longitude"]] = lat, lon
            return df
        return None
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch, lat, lon) for lat, lon in locations]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result is not None:
                results.append(result)
    
    return pd.concat(results, ignore_index=True) if results else None

# Fetch climate data
locations = list(gdf[["lat", "lon"]].drop_duplicates().itertuples(index=False, name=None))
df = fetch_nasa_data(locations, date)

if df is not None:
    gdf = gdf.merge(df, left_on=["lat", "lon"], right_on=["Latitude", "Longitude"], how="left")
    gdf.rename(columns={"PRECTOTCORR": "Rainfall", "T2M": "LST", "RH2M": "Relative_H"}, inplace=True)
    
    # Fill missing values with 0 instead of mean
    gdf[["Rainfall", "LST", "Relative_H"]] = gdf[["Rainfall", "LST", "Relative_H"]].fillna(0)

    # Ensure no duplicate column labels before reindexing
    gdf = gdf.loc[:, ~gdf.columns.duplicated()]

    # Feature selection and scaling
    feature_columns = ["Rainfall", "LST", "Relative_H"]
    X_pred = gdf[feature_columns].copy()

    # Ensure feature names match and avoid errors
    X_pred = X_pred.reindex(columns=scaler.feature_names_in_, fill_value=0)

    # Transform and predict malaria cases
    X_pred_scaled = scaler.transform(X_pred)
    gdf["pred_cases"] = trained_model.predict(X_pred_scaled).astype(int)
    
    # Assign climate values based on selection
    gdf["climate_value"] = (
        gdf["LST"] if selected_layer == "Temperature" else
        gdf["Relative_H"] if selected_layer == "Humidity" else
        gdf["Rainfall"] if selected_layer == "Precipitation" else
        gdf["pred_cases"]
    )

    # Define colormap
    colormap = LinearColormap(["blue", "cyan", "yellow", "orange", "red"], vmin=gdf["climate_value"].min(), vmax=gdf["climate_value"].max())

    # Folium Map
    m = folium.Map(location=[gdf["lat"].mean(), gdf["lon"].mean()], zoom_start=6)

    # Function to apply correct color mapping (Fix KeyError)
    def style_function(feature):
        # Extract value safely from feature properties, default to 0 if missing
        value = feature.get("properties", {}).get("climate_value", 0)
        return {"fillColor": colormap(value), "color": "black", "weight": 1, "fillOpacity": 0.7}

    # Convert GeoDataFrame to GeoJSON and add to map
    folium.GeoJson(
        gdf,
        name=selected_layer,
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(fields=["climate_value"], aliases=[f"{selected_layer}:"]),
    ).add_to(m)

    colormap.caption = f"{selected_layer} Scale"
    colormap.add_to(m)
    folium_static(m)

else:
    st.error("❌ Climate data retrieval failed. Please try again later.")
