# routes/geo_routes.py
from flask import Blueprint, request, jsonify
from models import db, GeoFeature
from shapely.geometry import shape
from geoalchemy2.shape import from_shape, to_shape

geo_bp = Blueprint('geo_bp', __name__)

@geo_bp.route('/features', methods=['POST'])
def create_feature():
    """
    前端发送:
    {
      "name": "test feature",
      "geometry": {
        "type": "Point",
        "coordinates": [-122.084, 37.421]
      }
    }
    """
    data = request.json
    name = data.get('name', '')
    geometry_data = data.get('geometry')

    if not geometry_data:
        return jsonify({"error": "No geometry"}), 400

    # 用 shapely 的 shape() 将GeoJSON -> shapely geom
    shp = shape(geometry_data)
    geom_wkb = from_shape(shp, srid=4326)

    feature = GeoFeature(name=name, geom=geom_wkb)
    db.session.add(feature)
    db.session.commit()
    return jsonify({"message": "Created", "id": feature.id})

@geo_bp.route('/features', methods=['GET'])
def list_features():
    """
    简单返回所有Feature的 name, geometry(GeoJSON)
    """
    feats = GeoFeature.query.all()
    results = []
    for f in feats:
        geom_shp = to_shape(f.geom)  # shapely geometry
        results.append({
            "id": f.id,
            "name": f.name,
            "geometry": shapely_to_geojson(geom_shp)
        })
    return jsonify(results)

def shapely_to_geojson(shp):
    # from shapely.geometry import mapping
    from shapely.geometry import mapping
    return mapping(shp)
