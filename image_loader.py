#image_loader
import streamlit as st
import os
from PIL import Image

def get_dashboard_images():
    """
    Pulls all project images from the local directory.
    Returns a dictionary of Image objects.
    """
    # Define the filenames based on your screenshot
    image_files = {
        "Flood Hazard": "img_fhs.png",
        "LULC": "img_lulc.png",
        "NDWI": "img_ndwi.tif",
        "Population": "img_pop.png",
        "Rainfall": "img_rainfall.tif",
        "Streams": "img_streams.png",
        "Digital Elevation Model": "img_dem.tif"
    }
    
    loaded_images = {}
    
    for label, filename in image_files.items():
        # Check if file exists (handling both .png and .jpg if necessary)
        if os.path.exists(filename):
            loaded_images[label] = Image.open(filename)
        else:
            # Fallback for different extensions
            alt_filename = filename.replace(".png", ".jpg")
            if os.path.exists(alt_filename):
                loaded_images[label] = Image.open(alt_filename)
            else:
                loaded_images[label] = None
                
    return loaded_images