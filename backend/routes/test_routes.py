# routes/test_routes.py
from flask import Blueprint, request, jsonify
from services.census_service import get_tract_for_point
from services.agent_generation import generate_single_agent_desc, generate_agent_desc_with_demo
from models import Agent

test_bp = Blueprint('test_bp', __name__)

@test_bp.route('/tract', methods=['GET'])
def test_tract():
    '''
    http://localhost:5000/test/tract?lat=37.7334258&lng=-122.413123122
    '''
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    if not lat or not lng:
        return jsonify({"error":"missing lat or lng"}), 400
    
    lat = float(lat)
    lng = float(lng)
    tract_id = get_tract_for_point(lat, lng)
    return jsonify({"tract_id": tract_id})

@test_bp.route('/agentDebug', methods=['GET'])
def debug_agent_generation():
    """
    use this to test
    http://localhost:5000/test/agentDebug?homeLat=37.710125697908786&homeLng=-122.44228363037111&workLat=37.7940050122603&workLng=-122.41550445556642&detailed=true

    {
        "age": 35,
        "background_story": "Lindsay Tran is a dedicated school counselor at a local elementary school in Census Tract 263.03, San Francisco County. With a passion for supporting and guiding young minds, Lindsay plays a crucial role in shaping the educational and emotional development of the children in the neighborhood. Despite the challenges of navigating the busy city environment, Lindsay finds solace in the community's emphasis on alternative modes of transportation, promoting a healthier and more sustainable lifestyle.",
        "homeTract": "06-075-026303",
        "name": "Lindsay Tran",
        "occupation": "School Counselor",
        "workTract": "06-075-010800"
    }
    
    http://localhost:5000/test/agentDebug?homeLat=37.710125697908786&homeLng=-122.44228363037111&workLat=37.7940050122603&workLng=-122.41550445556642

    {
        "age": 35,
        "background_story": "Alicia, a software engineer, commutes daily from the residential area of 06-075-026303 to her workplace in the downtown district of 06-075-010800. She navigates through bustling streets, hopping on the subway for a brief ride before finally arriving at her office building, ready to start her day.",
        "homeTract": "06-075-026303",
        "name": "Alicia",
        "occupation": "Software Engineer",
        "workTract": "06-075-010800"
    }
    """
    from services.census_service import get_tract_for_point
    from services.agent_generation import generate_single_agent_desc, generate_agent_desc_with_demo
    from models import Agent

    homeLat = request.args.get('homeLat')
    homeLng = request.args.get('homeLng')
    workLat = request.args.get('workLat')
    workLng = request.args.get('workLng')
    do_detailed_str = request.args.get('detailed', 'false')  # "true" or "false"
    do_detailed = (do_detailed_str.lower() == 'true')

    if not all([homeLat, homeLng, workLat, workLng]):
        return jsonify({"error": "Missing lat/lng for home or work"}), 400

    try:
        homeLat = float(homeLat)
        homeLng = float(homeLng)
        workLat = float(workLat)
        workLng = float(workLng)
    except ValueError:
        return jsonify({"error": "lat/lng must be numeric"}), 400

    home_tract = get_tract_for_point(homeLat, homeLng)
    work_tract = get_tract_for_point(workLat, workLng)

    agent = Agent(
        home_tract=home_tract,
        work_tract=work_tract
    )

    # 第一步：用 generate_single_agent_desc() 生成基本信息
    single_desc = generate_single_agent_desc(agent.home_tract, agent.work_tract)
    agent.name = single_desc.get('name')
    agent.age = single_desc.get('age')
    agent.occupation = single_desc.get('occupation')
    agent.background_story = single_desc.get('background_story')

    # 如果指定了 "detailed=true"，则使用更深入的Census info
    if do_detailed:
        agent = generate_agent_desc_with_demo(agent)

    return jsonify({
        "homeTract": agent.home_tract,
        "workTract": agent.work_tract,
        "name": agent.name,
        "age": agent.age,
        "occupation": agent.occupation,
        "background_story": agent.background_story
    })


