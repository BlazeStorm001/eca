import streamlit as st
import requests
import geopandas as gpd
import pandas as pd

# Define constants
STATIONS_API = "https://api.energyandcleanair.org/stations?country=GB,US,TR,PH,IN,TH&format=geojson"
COUNTRIES_GEOJSON_URL = "https://r2.datahub.io/clvyjaryy0000la0cxieg4o8o/main/raw/data/countries.geojson"
COUNTRY_CODES = {'US': 'United States', 'GB': 'United Kingdom', 'TR': 'Turkey', 'PH': 'Philippines', 'IN': 'India', 'TH': 'Thailand'}
# Hardcoded areas for countries in square kilometers
COUNTRY_AREAS = {
    'GB': 243610,  
    'US': 9833517, 
    'TR': 783562,  
    'PH': 300000, 
    'IN': 3287263,
    'TH': 513120  
}

@st.cache_data
def load_country_boundaries():
    try:
        with open("countries.geojson", "r") as file:
            countries_geojson = gpd.read_file(file)
    except FileNotFoundError:
        # If not present, download and save locally
        response = requests.get(COUNTRIES_GEOJSON_URL)
        with open("countries.geojson", "wb") as file:
            file.write(response.content)
        countries_geojson = gpd.read_file("countries.geojson")
    return countries_geojson

@st.cache_data
def load_pm10_stations():
    response = requests.get(STATIONS_API)
    stations_geojson = gpd.GeoDataFrame.from_features(response.json()["features"])
    return stations_geojson

def calculate_density(countries_gdf, stations_gdf):
    results = []
    # Group stations by 'country_id' (instead of spatial filtering)
    country_station_counts = stations_gdf.groupby('country_id').size()
    for code, name in COUNTRY_CODES.items():
        # Check if the country exists in the stations GeoJSON
        if code in country_station_counts:
            station_count = country_station_counts[code]
        else:
            station_count = 0
        
        # Use the hardcoded area values instead of the geometry
        country_area = COUNTRY_AREAS.get(code, 0)
        
        if country_area == 0:
            continue
        
        density = station_count / country_area * 1_000
        results.append({
            "Country Name": name,
            "Number of PM10 Stations": station_count,
            "Area (sq. km)": round(country_area, 2),
            "Density (per 1,000 sq. km)": round(density, 2)
        })
    
    return pd.DataFrame(results).sort_values(by="Density (per 1,000 sq. km)", ascending=False)

# Streamlit UI
st.title("PM10 Monitoring Station Density")
st.write("This application calculates and displays the density of PM10 monitoring stations for selected countries.")

if st.button("Show Data"):
    with st.spinner("Loading data..."):
        countries_gdf = load_country_boundaries()
        stations_gdf = load_pm10_stations()
        results_df = calculate_density(countries_gdf, stations_gdf)
    st.success("Data Loaded!")
    st.write("### Density of PM10 Monitoring Stations")
    st.table(results_df)
    # st.table(stations_gdf)
