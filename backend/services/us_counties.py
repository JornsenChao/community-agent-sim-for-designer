import geopandas as gpd
import os

# 读取 shp
file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'tl_2024_us_county', 'tl_2024_us_county.shp')
counties_gdf = gpd.read_file(file_path)

# 确保坐标系是 WGS84 (EPSG:4326)，根据你的 shapefile 实际情况
if counties_gdf.crs is None or counties_gdf.crs.to_epsg() != 4326:
    counties_gdf = counties_gdf.to_crs(epsg=4326)