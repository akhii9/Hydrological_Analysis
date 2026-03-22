import streamlit as st
import geopandas as gpd
import pandas as pd
import leafmap.foliumap as leafmap
import plotly.express as px
import streamlit.components.v1 as components  # <-- For stable map rendering

# -------------------------------
# 1. PAGE CONFIGURATION
# -------------------------------
st.set_page_config(
    page_title="Hyderabad Flood Resilience Dashboard",
    layout="wide"
)

st.title("🌊 Hyderabad Hydrological Resilience Dashboard")

# -------------------------------
# 2. DATA LOADING
# -------------------------------
@st.cache_data
def load_vector_data():
    # Read all Parquet files and convert to WGS84
    zones = gpd.read_parquet('flood_risk_zones.parquet').to_crs(epsg=4326)
    roads = gpd.read_parquet('danger_road_segments.parquet').to_crs(epsg=4326)
    moosi_sim = gpd.read_parquet('flood_buffers.parquet').to_crs(epsg=4326)
    return zones, roads, moosi_sim

# Sidebar Info
st.sidebar.title("🌍 Project Info")
st.sidebar.info(
"""
**Hydrological Resilience Platform**  
Developed by: **Akhil Kumar Myadarapu**  
JNTU Hyderabad | Geo-Informatics
"""
)

# Load Data
try:
    flood_zones, roads, moosi_sim = load_vector_data()
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
    st.stop()

# -------------------------------
# 3. TABS
# -------------------------------
tab1, tab2, tab3 = st.tabs([
    "📊 Part 1: Hydrology",
    "🌊 Part 2: Moosi Study",
    "🛡️ Part 3: Preparedness"
])

# =====================================================
# TAB 1 — HYDROLOGICAL BASELINE
# =====================================================
with tab1:
    st.header("Hydrological & Environmental Baseline")
    col1, col2 = st.columns([3, 1])

    with col1:
        m1 = leafmap.Map(center=[17.3850, 78.4867], zoom=11)
        m1.add_basemap("HYBRID")

        # Raster Layers
        m1.add_raster("dem.tif", layer_name="DEM (Topography)", cmap="terrain")
        m1.add_raster("ndwi.tif", layer_name="NDWI (Water Bodies)", cmap="Blues")
        m1.add_raster("lulc.tif", layer_name="LULC (Urban Sprawl)", cmap="viridis")

        # Stable Rendering (no temp file)
        components.html(m1._repr_html_(), height=600)

    with col2:
        st.subheader("📚 Layer Explanation")
        st.markdown("""
**DEM**
- Elevation surface
- Determines runoff direction

**NDWI**
- Detects surface water
- Highlights drainage patterns

**LULC**
- Shows urban expansion
- Identifies impervious surfaces
""")

# =====================================================
# TAB 2 — MOOSI FLOOD SIMULATION
# =====================================================
with tab2:
    st.header("Moosi River Flood Simulation")

    max_step = int(moosi_sim["step"].max())
    sim_step = st.slider("Flood Progression Step", 1, max_step, value=1)

    col_map, col_info = st.columns([3,1])

    with col_map:
        current_flood = moosi_sim[moosi_sim["step"] <= sim_step]

        m2 = leafmap.Map(center=[17.3850, 78.4867], zoom=13)
        m2.add_basemap("HYBRID")
        m2.add_gdf(current_flood, layer_name="Simulated Flood", fill_color="blue", fill_opacity=0.6)

        # Stable Rendering
        components.html(m2._repr_html_(), height=600)

    with col_info:
        st.subheader("Simulation Insights")
        st.info(f"Viewing Step **{sim_step}** of flood expansion.")
        st.markdown("""
The simulation visualizes potential inundation of the **Moosi River**.

Method used:
- Multi-ring buffer expansion
- Represents rising flood levels
- Helps identify vulnerable urban zones
""")

# =====================================================
# TAB 3 — RISK & PREPAREDNESS
# =====================================================
with tab3:
    st.header("Risk Assessment & Human Impact")

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Population at Risk", "539,770", delta="Rank 4 & 5")
    c2.metric("Critical Road Blockages", len(roads))
    c3.metric("Study Area Exposure", "20.3%")

    col_map_3, col_charts = st.columns([2,1])

    with col_map_3:
        m3 = leafmap.Map(center=[17.3850, 78.4867], zoom=12)
        m3.add_basemap("HYBRID")
        m3.add_gdf(flood_zones, layer_name="Flood Risk Zones", column="DN", cmap="YlOrRd")
        m3.add_gdf(roads, layer_name="Blocked Roads", fill_color="black")

        # Stable Rendering
        components.html(m3._repr_html_(), height=500)

    with col_charts:
        st.subheader("Demographic Split")
        df_gender = pd.DataFrame({"Gender":["Male","Female"],"Count":[273176,269536]})
        fig = px.pie(df_gender, values="Count", names="Gender", hole=0.55, color_discrete_sequence=["#3498db","#e74c3c"])
        st.plotly_chart(fig, use_container_width=True)

# -------------------------------
# SIDEBAR WARNING
# -------------------------------
st.sidebar.markdown("---")
st.sidebar.warning("⚠️ High Flood Risk detected in **20% of analyzed zones**.")