import geopandas as gpd
import os

# 读取 shp
file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'tl_2024_us_county', 'tl_2024_us_county.shp')
counties_gdf = gpd.read_file(file_path)