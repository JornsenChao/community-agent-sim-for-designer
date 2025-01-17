from flask import Blueprint, request, jsonify
from services.data_processing import process_design_data

design_data_bp = Blueprint('design_data_bp', __name__)

@design_data_bp.route('/upload', methods=['POST'])
def upload():
    design_info = request.json.get('designInfo', {})
    result = process_design_data(design_info)
    
    return jsonify({
        "status": "ok",
        "processedDesign": result
    })
