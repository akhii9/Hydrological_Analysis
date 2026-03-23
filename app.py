import streamlit as st
import folium
import geopandas as gpd
import branca.colormap as cm
from streamlit_folium import folium_static
from decimal import Decimal
from shapely.geometry import Point
import os
from PIL import Image


def get_dashboard_images():
    """Pulls project images. Automatically checks for .png and .tif extensions."""
    image_files = {
        "Flood Hazard": "img_fhs",
        "LULC": "img_lulc",
        "NDWI": "img_ndwi",
        "Population": "img_pop",
        "Rainfall": "img_rainfall",
        "Streams": "img_streams",
        "Digital Elevation Model": "img_dem" 
    }
    
    loaded_images = {}
    extensions = [".png", ".tif", ".jpg", ".jpeg"]
    
    for label, base_name in image_files.items():
        found_img = None
        for ext in extensions:
            full_path = base_name + ext
            if os.path.exists(full_path):
                try:
                    img = Image.open(full_path)
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    found_img = img
                    break 
                except:
                    continue
        loaded_images[label] = found_img
                
    return loaded_images


# 2. PAGE CONFIGURATION
st.set_page_config(page_title="Hyderabad Flood Dashboard", layout="wide")


# 3. DATA LOADING & PREPARATION (SPEED OPTIMIZED)

@st.cache_data
def load_data():
    try:
        # Vector Data
        zones = gpd.read_parquet('flood_risk_zones.parquet')
        roads = gpd.read_parquet('danger_road_segments.parquet')
        
        # GeoJSON Data
        rainfall = gpd.read_file('Rainfall_data.geojson')
        moosi_flood = gpd.read_file('Moosi_flood_extent.geojson')

        # --- SPEED OPTIMIZATION: Geometry Simplification ---
        # 0.0001 is approx 11-meter precision. This significantly reduces lag.
        zones['geometry'] = zones['geometry'].simplify(0.0001, preserve_topology=True)
        rainfall['geometry'] = rainfall['geometry'].simplify(0.0001, preserve_topology=True)
        moosi_flood['geometry'] = moosi_flood['geometry'].simplify(0.0001, preserve_topology=True)
        
        # Mapping Ranks to Strings
        zones['DN'] = zones['DN'].astype(int)
        if 'DN' in rainfall.columns:
            rainfall['DN'] = rainfall['DN'].astype(int)
            
        rank_to_text = {1: "Very Low", 2: "Low", 3: "Moderate", 4: "High", 5: "Very High"}
        
        # Apply mapping
        zones['Risk_Level'] = zones['DN'].map(rank_to_text)
        rainfall['Rain_Level'] = rainfall['DN'].map(rank_to_text)
        
        # Decimal to Float conversion
        for gdf in [zones, roads, rainfall, moosi_flood]:
            for col in gdf.columns:
                gdf[col] = gdf[col].apply(lambda x: float(x) if isinstance(x, Decimal) else x)
        
        return (zones.to_crs(epsg=4326), 
                roads.to_crs(epsg=4326), 
                rainfall.to_crs(epsg=4326), 
                moosi_flood.to_crs(epsg=4326))
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()

# Initialize Header and Data
st.title("🌊 Hydrology of Hyderabad")
st.write("Analysis  -  Realtime Case Study  -  Preparedness")
flood_zones, roads, rainfall_data, moosi_extent = load_data()
images = get_dashboard_images()


# 4. SIDEBAR: LOCATION RISK LOOKUP

st.sidebar.title("📍 Location Risk Lookup")
user_lat = st.sidebar.number_input("Enter Latitude", value=17.385044, format="%.6f")
user_lon = st.sidebar.number_input("Enter Longitude", value=78.486671, format="%.6f")

user_point = Point(user_lon, user_lat)
matching_zone = flood_zones[flood_zones.contains(user_point)]

if not matching_zone.empty:
    risk_text = matching_zone.iloc[0]['Risk_Level']
    risk_rank = matching_zone.iloc[0]['DN']
    if risk_rank >= 4:
        st.sidebar.error(f"### ⚠️ {risk_text} Risk")
    elif risk_rank == 3:
        st.sidebar.warning(f"### 🟠 {risk_text} Risk")
    else:
        st.sidebar.success(f"### ✅ {risk_text} Risk")
else:
    st.sidebar.info("Location is outside high-susceptibility zones.")

st.sidebar.markdown("---")
st.sidebar.title("🗺️ Map Layer Toggles")
show_zones = st.sidebar.checkbox("Show Flood Susceptibility Zones", value=True)
show_rainfall = st.sidebar.checkbox("Show Rainfall Intensity Overlay", value=False)
show_moosi = st.sidebar.checkbox("Show Moosi Flood Extent", value=False)
show_roads = st.sidebar.checkbox("Show Critical Road Blockages", value=True)


# 5. MAIN CONTENT - TABS

tab1, tab2 = st.tabs(["🗺️ Interactive Dashboard", "🖼️ Map Gallery"])

with tab1:
    m = folium.Map(
        location=[user_lat, user_lon], 
        zoom_start=13, 
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri Satellite'
    )
    
    folium.TileLayer(
        'https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{y}/{x}{r}.png',
        attr='CartoDB', name="Street Labels", overlay=True
    ).add_to(m)

    hazard_cm = cm.LinearColormap(["#2BFF00", '#FF8C00', '#FF0000', '#8B0000'], vmin=1, vmax=5, caption="Flood Hazard")
    rain_cm = cm.LinearColormap(['#DEEBF7', '#9ECAE1', '#4292C6', '#084594'], vmin=1, vmax=5, caption="Rainfall (1-5)")

    # 1. Rainfall Layer
    if show_rainfall:
        folium.GeoJson(
            rainfall_data,
            style_function=lambda x: {'fillColor': rain_cm(x['properties']['DN']), 'color': 'white', 'weight': 0.5, 'fillOpacity': 0.6},
            tooltip=folium.GeoJsonTooltip(fields=['Rain_Level'], aliases=['Rainfall Intensity: ']),
            name="Rainfall Intensity"
        ).add_to(m)

    # 2. Susceptibility Zones
    if show_zones:
        folium.GeoJson(
            flood_zones,
            style_function=lambda x: {'fillColor': hazard_cm(x['properties']['DN']), 'color': 'black', 'weight': 0.1, 'fillOpacity': 0.5},
            tooltip=folium.GeoJsonTooltip(fields=['Risk_Level'], aliases=['Risk: ']),
            name="Flood Susceptibility"
        ).add_to(m)

    # 3. Moosi Extent
    if show_moosi:
        folium.GeoJson(
            moosi_extent,
            style_function=lambda x: {'fillColor': '#000080', 'color': '#00FFFF', 'weight': 1.5, 'fillOpacity': 0.4},
            tooltip='Flooded Region 2025 Moosi River',
            name="Moosi Flood Extent"
        ).add_to(m)

    # 4. Roads
    if show_roads:
        folium.GeoJson(
            roads,
            style_function=lambda x: {'color': '#00FFFF', 'weight': 5, 'opacity': 1.0},
            tooltip='⚠️ Water Logging Risk',
            name="Critical Infrastructure"
        ).add_to(m)

    folium.Marker([user_lat, user_lon], icon=folium.Icon(color='red', icon='info-sign')).add_to(m)
    hazard_cm.add_to(m)
    folium.LayerControl().add_to(m)
    folium_static(m, width=1200, height=750)

with tab2:
    st.header("Spatial Analysis Maps")
    st.write("Analytical maps processed via GEE & QGIS/ArcGIS for the Hyderabad region.")
    
    col1, col2 = st.columns(2)
    display_list = ["Flood Hazard", "NDWI", "Rainfall", "Digital Elevation Model", "LULC", "Population", "Streams"]
    
    for i, key in enumerate(display_list):
        target_col = col1 if i % 2 == 0 else col2
        with target_col:
            if key in images and images[key]:
                st.subheader(key)
                st.image(images[key], use_container_width=True)
            else:
                st.warning(f"Map file for '{key}' not found in directory.")

st.sidebar.info("Project: **Hydrology of Hyderabad** - GEO INFORMATICS")
