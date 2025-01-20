# routes/test_routes.py
from flask import Blueprint, request, jsonify
from services.census_service import get_tract_for_point

test_bp = Blueprint('test_bp', __name__)

@test_bp.route('/tract', methods=['GET'])
def test_tract():
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    if not lat or not lng:
        return jsonify({"error":"missing lat or lng"}), 400
    
    lat = float(lat)
    lng = float(lng)
    tract_id = get_tract_for_point(lat, lng)
    return jsonify({"tract_id": tract_id})

