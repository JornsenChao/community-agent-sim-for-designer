# routes/spatial_routes.py

from flask import Blueprint, request, jsonify
import osmnx as ox
import geopandas as gpd
from shapely.geometry import box, MultiPolygon, Polygon, MultiLineString, LineString
from geoalchemy2.shape import from_shape
from models import db, OSMBuilding, OSMRoad
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
    
    bbox_str = f"{minx},{miny},{maxx},{maxy}"

    try:
        # 1) OSM data
        region_polygon = box(minx, miny, maxx, maxy)
        # roads
        G = ox.graph_from_polygon(region_polygon, network_type='drive')
        edges_gdf = ox.graph_to_gdfs(G, nodes=False, edges=True)

        # buildings
        tags = {"building": True}
        buildings_gdf = ox.geometries_from_polygon(region_polygon, tags)

        # summarize
        building_count = len(buildings_gdf)
        road_nodes_count = len(G.nodes)
        road_edges_count = len(G.edges)

        # remove old data for this bounding box
        OSMBuilding.query.filter_by(bounding_box=bbox_str).delete()
        OSMRoad.query.filter_by(bounding_box=bbox_str).delete()
        db.session.commit()

        # Insert new building data
        for idx, row in buildings_gdf.iterrows():
            geom_obj = row.geometry
            if geom_obj is None or geom_obj.is_empty:
                continue
            # building_type = row.get('building', '') # optional
            # ensure polygon
            if isinstance(geom_obj, (Polygon, MultiPolygon)):
                geom_wkb = from_shape(geom_obj, srid=4326)  # 关键：geoalchemy2 from_shape
                building = OSMBuilding(
                    bounding_box=bbox_str,
                    # building_type=building_type,
                    geom=geom_wkb
                )
                db.session.add(building)

        # Insert new road data
        for idx, row in edges_gdf.iterrows():
            geom_obj = row.geometry
            if geom_obj is None or geom_obj.is_empty:
                continue
            if isinstance(geom_obj, (LineString, MultiLineString)):
                geom_wkb = from_shape(geom_obj, srid=4326)
                road = OSMRoad(
                    bounding_box=bbox_str,
                    geom=geom_wkb
                )
                db.session.add(road)

        db.session.commit()

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
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
