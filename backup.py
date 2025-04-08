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
st.title("Malaria Case Prediction")
gdf = gpd.read_file(SHAPEFILE_PATH).to_crs("EPSG:4326")
gdf["geometry"] = gdf["geometry"].simplify(0.001, preserve_topology=True)
gdf["lat"] = gdf.geometry.centroid.y
gdf["lon"] = gdf.geometry.centroid.x

# NASA POWER API Parameters
BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
PARAMETERS = "T2M,RH2M,PRECTOTCORR"
COMMUNITY = "RE"

date = st.sidebar.date_input("Select Date", datetime(2024, 1, 1))

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
    
    # Feature selection and scaling
    features = ["Rainfall", "LST", "Relative_H"]
    if all(f in gdf.columns for f in features):
        X_pred = gdf[features].fillna(gdf[features].mean())

        # Drop duplicate columns if they exist
        X_pred = X_pred.loc[:, ~X_pred.columns.duplicated()]

        # Ensure column order matches training
        X_pred = X_pred.reindex(columns=scaler.feature_names_in_, fill_value=0)

        # Debugging info (commented out)
        # print("Features used in training:", scaler.feature_names_in_)
        # print("Features in X_pred before scaling:", X_pred.columns.tolist())

        # Transform and predict
        X_pred_scaled = scaler.transform(X_pred)
        gdf["pred_cases"] = trained_model.predict(X_pred_scaled).astype(int)
    else:
        st.error("❌ Missing required climate features for prediction.")
        st.stop()
    
    # Folium Map
    m = folium.Map(location=[gdf["lat"].mean(), gdf["lon"].mean()], zoom_start=6)
    colormap = LinearColormap(["blue", "cyan", "yellow", "orange", "red"], vmin=gdf["pred_cases"].min(), vmax=gdf["pred_cases"].max())
    
    for _, row in gdf.iterrows():
        if "wardname" in gdf.columns and "lganame" in gdf.columns:
            tooltip_text = f"Predicted Cases: {row['pred_cases']}\nWard: {row['wardname']}\nLGA: {row['lganame']}"
        else:
            tooltip_text = f"Predicted Cases: {row['pred_cases']}"
        
        folium.GeoJson(
            row["geometry"],
            style_function=lambda x, val=row["pred_cases"]: {"fillColor": colormap(val), "color": "black", "weight": 1, "fillOpacity": 0.7},
            tooltip=tooltip_text
        ).add_to(m)
    
    colormap.caption = "Predicted Malaria Cases"
    colormap.add_to(m)
    folium_static(m)
else:
    st.error("❌ Climate data retrieval failed. Please try again later.")