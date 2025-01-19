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
        # print (edges_gdf.columns)
        # print("edges_gdf.columns: 'osmid', 'oneway', 'lanes', 'name', 'highway', 'maxspeed'")
        # print(edges_gdf[['osmid', 'oneway', 'lanes', 'name', 'highway', 'maxspeed']].head(50))
        # print(edges_gdf[['osmid', 'oneway', 'lanes', 'name', 'highway', 'maxspeed']].tail(50))
        # print("edges_gdf.columns: 'reversed','length', 'geometry', 'ref', 'access'")
        # print(edges_gdf[['reversed','length', 'geometry', 'ref', 'access']].head(50))
        # buildings
        tags = {"building": True}
        buildings_gdf = ox.geometries_from_polygon(region_polygon, tags)
        # print(list(buildings_gdf.columns))
        # print (buildings_gdf.columns[:20])
        # print (buildings_gdf.columns[21:40])
        # print (buildings_gdf.columns[41:60])
        # print (buildings_gdf.columns[61:80])
        # print (buildings_gdf.columns[81:100])
        # print (buildings_gdf.columns[101:120])
        # print(buildings_gdf.head(5))

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
            if not isinstance(geom_obj, (Polygon, MultiPolygon)):
                # 跳过非多边形
                continue

            # 如果是Polygon则转换成MultiPolygon
            if isinstance(geom_obj, Polygon):
                geom_obj = MultiPolygon([geom_obj])

            building_type = row.get('building', None)
            osm_id = row.get('osmid', None)
            if isinstance(osm_id, list):
                osm_id = ','.join(str(x) for x in osm_id)

            bname = row.get('name', None)

            geom_wkb = from_shape(geom_obj, srid=4326)
            building = OSMBuilding(
                bounding_box=bbox_str,
                osm_id=str(osm_id) if osm_id else None,
                name=bname if isinstance(bname, str) else None,
                building_type=building_type if isinstance(building_type, str) else None,
                geom=geom_wkb
            )
            db.session.add(building)

        # Insert new road data
        for idx, row in edges_gdf.iterrows():
            geom_obj = row.geometry
            if geom_obj is None or geom_obj.is_empty:
                continue

            # 如果是LineString则转换成MultiLineString
            if isinstance(geom_obj, LineString):
                geom_obj = MultiLineString([geom_obj])
            if not isinstance(geom_obj, (LineString, MultiLineString)):
                # 跳过非线要素
                continue

            osm_id = row.get('osmid', None)
            if isinstance(osm_id, list):
                osm_id = ','.join(str(x) for x in osm_id)

            rd_name = row.get('name', None)
            rd_type = row.get('highway', None)
            rd_oneway = row.get('oneway', False)

            lanes_val = row.get('lanes', None)
            rd_lanes = None
            if lanes_val is not None:
                if isinstance(lanes_val, list):
                    try:
                        rd_lanes = sum(map(float, lanes_val)) / len(lanes_val)
                    except:
                        rd_lanes = None
                else:
                    try:
                        rd_lanes = float(lanes_val)
                    except:
                        rd_lanes = None

            geom_wkb = from_shape(geom_obj, srid=4326)
            road = OSMRoad(
                bounding_box=bbox_str,
                osm_id=str(osm_id) if osm_id else None,
                name=rd_name if isinstance(rd_name, str) else None,
                road_type=rd_type if isinstance(rd_type, str) else None,
                oneway=bool(rd_oneway),
                lanes=rd_lanes,
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
        return jsonify(combined), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
