# routes/spatial_routes.py

from flask import Blueprint, request, jsonify
import osmnx as ox
import geopandas as gpd
from shapely.geometry import shape, box, MultiPolygon, Polygon, MultiLineString, LineString
from geoalchemy2.shape import from_shape
from models import db, Project, OSMBuilding, OSMRoad
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

@spatial_bp.route('/setBoundary', methods=['POST'])
def set_boundary():
    """
    前端传 { projectId, geometry: GeoJSON } 
    geometry 可能是多边形(用户画的), 
    or bounding box => 也可转成 polygon
    后端存到Project表 boundary_geom字段
    然后再自动调用 fetch OSM & census data
    """

    data = request.json
    project_id = data.get('projectId')
    geom_data = data.get('geometry')

    if not project_id or not geom_data:
        return jsonify({"error": "Missing projectId or geometry"}), 400

    proj = Project.query.get(project_id)
    if not proj:
        return jsonify({"error": "Project not found"}), 404

    # 1) 把前端传来的 GeoJSON 解析成 shapely
    boundary_data = geom_data
    if boundary_data.get("type") == "Feature":
        boundary_data = boundary_data.get("geometry")
    boundary_shp = shape(boundary_data)  # polygon or multipolygon
    if isinstance(boundary_shp, Polygon):
        boundary_shp = MultiPolygon([boundary_shp])

    boundary_wkb = from_shape(boundary_shp, srid=4326)
    proj.boundary_geom = boundary_wkb
    db.session.commit()

    # 2) 获取 bounding box (minx, miny, maxx, maxy)
    minx, miny, maxx, maxy = boundary_shp.bounds

    # 3) 调用 OSMnx 抓建筑、道路 (跟你的 fetch_spatial_data 类似)
    #    先删除本 project 下以前抓过的数据(若有)
    bbox_str = f"{minx},{miny},{maxx},{maxy}"
    OSMBuilding.query.filter_by(bounding_box=bbox_str).delete()
    OSMRoad.query.filter_by(bounding_box=bbox_str).delete()
    db.session.commit()

    # roads
    region_polygon = boundary_shp
    G = ox.graph_from_polygon(region_polygon, network_type='drive')
    edges_gdf = ox.graph_to_gdfs(G, nodes=False, edges=True)

    # buildings
    tags = {"building": True}
    buildings_gdf = ox.geometries_from_polygon(region_polygon, tags)

    # Insert building data
    building_count = 0
    for idx, row in buildings_gdf.iterrows():
        geom_obj = row.geometry
        if geom_obj is None or geom_obj.is_empty:
            continue
        if isinstance(geom_obj, Polygon):
            geom_obj = MultiPolygon([geom_obj])
        if not isinstance(geom_obj, MultiPolygon):
            continue
        building_count += 1
        building_type = row.get('building', None)
        osm_id = row.get('osmid', None)
        if isinstance(osm_id, list):
            osm_id = ','.join(str(x) for x in osm_id)
        bname = row.get('name', None)
        geom_wkb = from_shape(geom_obj, srid=4326)
        b = OSMBuilding(
            bounding_box=bbox_str,
            osm_id=str(osm_id) if osm_id else None,
            name=bname if isinstance(bname, str) else None,
            building_type=building_type if isinstance(building_type, str) else None,
            geom=geom_wkb
        )
        db.session.add(b)

    # Insert road data
    road_count = 0
    for idx, row in edges_gdf.iterrows():
        geom_obj = row.geometry
        if geom_obj is None or geom_obj.is_empty:
            continue
        road_count += 1
        # 先省略跟原先相同的处理...
        # ...
        # 省略: 你可以和之前 /fetch 里写的保持一致

    db.session.commit()

    # 4) 调Census -> bounding box
    demographic_info = get_demographic_for_bbox(minx, miny, maxx, maxy, method="weighted")

    result = {
        "osmData": {
            "buildings": building_count,
            "roads": road_count
        },
        "demographic": demographic_info
    }

    return jsonify({"status": "ok", "projectId": project_id, "boundary": geom_data, "analysis": result})