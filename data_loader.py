# data_loader.py
import geopandas as gpd
from decimal import Decimal
import streamlit as st

@st.cache_data
def load_vector_data():
    """
    Load GeoDataFrames and convert all Decimal types to float.
    """
    # Load Parquet files
    zones = gpd.read_parquet('flood_risk_zones.parquet').to_crs(epsg=4326)
    roads = gpd.read_parquet('danger_road_segments.parquet').to_crs(epsg=4326)
    moosi_sim = gpd.read_parquet('flood_buffers.parquet').to_crs(epsg=4326)

    # Convert Decimal to float
    zones = decimals_to_float(zones)
    roads = decimals_to_float(roads)
    moosi_sim = decimals_to_float(moosi_sim)

    return zones, roads, moosi_sim

def decimals_to_float(gdf):
    """
    Convert all Decimal columns to float for JSON serialization.
    """
    gdf = gdf.copy()
    for col in gdf.columns:
        # Apply conversion for Decimal type
        gdf[col] = gdf[col].apply(lambda x: float(x) if isinstance(x, Decimal) else x)
    return gdf