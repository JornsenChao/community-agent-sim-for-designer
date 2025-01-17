from flask import Blueprint, request, jsonify
import osmnx as ox
import geopandas as gpd
from shapely.geometry import box
from services.census_service import get_county_population
from services.us_counties import counties_gdf
from services.census_service import get_county_population

spatial_bp = Blueprint('spatial_bp', __name__)

counties_gdf = counties_gdf.to_crs(epsg=4326)  # 确保是 WGS84 经纬度

@spatial_bp.route('/fetch', methods=['POST'])
def fetch_spatial_data():
    data = request.json
    minx = data.get("minx")
    miny = data.get("miny")
    maxx = data.get("maxx")
    maxy = data.get("maxy")

    if None in [minx, miny, maxx, maxy]:
        return jsonify({"error": "bounding box params missing"}), 400

    try:
        # Step 1: 构建 shapely Polygon
        region_polygon = box(minx, miny, maxx, maxy)

        # Step 2: 用 osmnx 获取 OSM 数据
        # roads
        G = ox.graph_from_polygon(region_polygon, network_type='drive')
        # buildings
        tags = {"building": True}
        buildings_gdf = ox.geometries_from_polygon(region_polygon, tags)

        # 统计
        building_count = len(buildings_gdf)
        road_nodes_count = len(G.nodes)
        road_edges_count = len(G.edges)

        # Step 3: 找到用户选区落在哪个 county
        #   3.1 构建一个 GeoDataFrame 只包含 region_polygon
        import geopandas as gpd
        region_gdf = gpd.GeoDataFrame(
            {'id':[1]}, 
            geometry=[region_polygon], 
            crs="EPSG:4326"
        )

        #   3.2 做空间交集(overlay)或 sjoin
        #       sjoin requires polygon type in counties_gdf
        #       We'll do intersection area, pick county with max intersection
        intersected = gpd.overlay(counties_gdf, region_gdf, how='intersection')
        if len(intersected) == 0:
            # 选区不在任何县? or 可能在海外
            demographic_info = {"warning": "No county found for this bounding box."}
        else:
            # 可能落在多个县, 取覆盖面积最大者
            intersected["area"] = intersected.geometry.area
            max_area_row = intersected.loc[intersected["area"].idxmax()]

            state_fips = max_area_row["STATEFP"]  # e.g. '06'
            county_fips = max_area_row["COUNTYFP"]  # e.g. '001'
            # 你也可从 max_area_row["NAME"] 取 county name

            # Step 4: 调 census_service
            demographic_info = get_county_population(state_fips, county_fips)

        # Step 5: 组合并返回
        combined_result = {
            "boundingBox": [minx, miny, maxx, maxy],
            "osmData": {
                "buildingCount": building_count,
                "roadNodes": road_nodes_count,
                "roadEdges": road_edges_count
            },
            "demographic": demographic_info
        }
        return jsonify(combined_result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
