# routes/spatial_routes.py

from flask import Blueprint, request, jsonify
import osmnx as ox
import geopandas as gpd
from shapely.geometry import box
from services.census_service import get_demographic_for_bbox

spatial_bp = Blueprint('spatial_bp', __name__)

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
        # 1) OSM data
        region_polygon = box(minx, miny, maxx, maxy)
        # roads
        G = ox.graph_from_polygon(region_polygon, network_type='drive')
        # buildings
        tags = {"building": True}
        buildings_gdf = ox.geometries_from_polygon(region_polygon, tags)

        # summarize
        building_count = len(buildings_gdf)
        road_nodes_count = len(G.nodes)
        road_edges_count = len(G.edges)

        # 2) Census
        # let's do "weighted" approach
        demographic_info = get_demographic_for_bbox(minx, miny, maxx, maxy, method="weighted")

        # 3) combine results
        combined = {
            "boundingBox": [minx, miny, maxx, maxy],
            "osmData": {
                "buildingCount": building_count,
                "roadNodes": road_nodes_count,
                "roadEdges": road_edges_count
            },
            "demographic": demographic_info
        }
        return jsonify(combined)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
