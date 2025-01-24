# ========= 这是修改后的 agent_routes.py 全部内容示例 =========
from flask import Blueprint, request, jsonify
from models import db, Agent
from services.data_processing import get_project_info, get_demographic_info
from services.agent_generation import generate_agent_desc_with_demo
from services.census_service import get_tract_for_point
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

agent_bp = Blueprint('agent_bp', __name__)

@agent_bp.route('/locate', methods=['POST'])
def locate_agent():
    """
    前端传 { projectId, home: {lat, lng}, work: {lat, lng} }
    后端:
    1) 根据 home 位置 -> census tract
    2) 根据 work 位置 -> census tract
    3) 在 Agent表插入1条记录 (无LLM信息)
    4) 返回 agentId
    """
    data = request.json
    project_id = data.get('projectId')
    home = data.get('home', {})
    work = data.get('work', {})

    if not project_id or not home or not work:
        return jsonify({"error": "Missing data"}), 400

    # 注意: lat/lng -> shapely 的 Point 要用 (lng, lat)
    home_geom = from_shape(Point(home['lng'], home['lat']), srid=4326)
    work_geom = from_shape(Point(work['lng'], work['lat']), srid=4326)

    # 调用 census_service 获取 tract
    home_tract = get_tract_for_point(home['lat'], home['lng'])
    work_tract = get_tract_for_point(work['lat'], work['lng'])

    new_agent = Agent(
        project_id = project_id,
        home_geom = home_geom,
        work_geom = work_geom,
        home_tract = home_tract,
        work_tract = work_tract
    )
    db.session.add(new_agent)
    db.session.commit()

    return jsonify({
        "status": "ok",
        "agentId": new_agent.id,
        "homeTract": home_tract,
        "workTract": work_tract
    })

@agent_bp.route('/list', methods=['GET'])
def list_agents():
    """
    GET /agents/list?projectId=xxx
    返回该项目所有Agent
    """
    project_id = request.args.get('projectId')
    if not project_id:
        return jsonify({"error":"no projectId"}), 400

    agents = Agent.query.filter_by(project_id=project_id).all()
    results = []
    from shapely.geometry import mapping
    from geoalchemy2.shape import to_shape
    for ag in agents:
        # 把 geom 转成 geojson 以便前端使用
        home_geom = None
        if ag.home_geom:
            shp = to_shape(ag.home_geom)
            home_geom = mapping(shp)
        work_geom = None
        if ag.work_geom:
            shp2 = to_shape(ag.work_geom)
            work_geom = mapping(shp2)

        results.append({
            "id": ag.id,
            "projectId": ag.project_id,
            "name": ag.name,
            "age": ag.age,
            "occupation": ag.occupation,
            "background_story": ag.background_story,
            "home_geom": home_geom,
            "work_geom": work_geom,
            "home_tract":ag.home_tract,
            "work_tract":ag.work_tract
        })
    return jsonify({"agents": results})


@agent_bp.route('/generateDetailed', methods=['POST'])
def generate_detailed():
    data = request.json
    project_id = data.get("projectId")
    if not project_id:
        return jsonify({"error":"missing projectId"}), 400

    agents = Agent.query.filter_by(project_id=project_id).all()
    if not agents:
        return jsonify({"agents": [], "message": "No Agents in this project"}), 200

    updated_results = []
    for ag in agents:
        ag = generate_agent_desc_with_demo(ag)
        db.session.add(ag)  # agent updated in memory

    db.session.commit()

    for ag in agents:
        updated_results.append({
            "id": ag.id,
            "name": ag.name,
            "age": ag.age,
            "home_tract": ag.home_tract,
            "occupation": ag.occupation,
            "background_story": ag.background_story
        })

    return jsonify({"agents": updated_results})


# ============== 新增这个 /agents/preview 路由 ==============
@agent_bp.route('/preview', methods=['POST'])
def preview_update():
    """
    让前端可以发送:
      { 
        "agentId": XXX,
        "updatedProps": { "age": 40, ... }
      }
    来做一个简单的 Agent 局部更新。
    """
    data = request.json or {}
    agent_id = data.get("agentId")
    updated_props = data.get("updatedProps", {})

    if not agent_id:
        return jsonify({"error": "no agentId"}), 400

    agent = Agent.query.get(agent_id)
    if not agent:
        return jsonify({"error": "agent not found"}), 404

    # 根据前端传入的字段，更新agent
    if "age" in updated_props:
        agent.age = updated_props["age"]
    if "occupation" in updated_props:
        agent.occupation = updated_props["occupation"]
    if "name" in updated_props:
        agent.name = updated_props["name"]

    db.session.commit()

    return jsonify({
        "status": "ok",
        "updatedAgent": {
            "id": agent.id,
            "name": agent.name,
            "age": agent.age,
            "occupation": agent.occupation,
            "background_story": agent.background_story
        }
    })
