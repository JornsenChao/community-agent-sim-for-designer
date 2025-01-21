from flask import Blueprint, request, jsonify
from models import db, Agent
# from services.agent_generation import generate_agents
from services.data_processing import get_project_info, get_demographic_info
from services.agent_generation import  generate_agent_desc_with_demo
from services.census_service import get_tract_for_point
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy import update

agent_bp = Blueprint('agent_bp', __name__)

# @agent_bp.route('/generate', methods=['POST'])
# def generate():
#     """
#     批量对数据库里那些Agent补充信息
#     POST { projectId } 
#     后端:
#      1) 查projectId下所有agent (home_tract, work_tract)
#      2) 调LLM, 结合这些 tract info 生成 name/age/desc
#      3) 更新DB
#      4) 返回agent列表
#     """
#     data = request.json
#     project_id = data.get('projectId')
#     if not project_id:
#         return jsonify({"error": "no projectId"}), 400

#     from models import Agent
#     agents = Agent.query.filter_by(project_id=project_id).all()
#     if not agents:
#         return jsonify({"agents": [], "message": "No Agents found"}), 200

#     # 调用你原services.agent_generation里的一些逻辑:
#     from services.agent_generation import generate_single_agent_desc
#     updated_list = []
#     for ag in agents:
#         # 这里仅示例, 你可以写更完整Prompt:
#         llm_result = generate_single_agent_desc(
#             home_tract=ag.home_tract,
#             work_tract=ag.work_tract
#         )
#         # 假设返回一个dict:
#         ag.name = llm_result.get('name')
#         ag.age = llm_result.get('age')
#         ag.occupation = llm_result.get('occupation')
#         ag.background_story = llm_result.get('background_story')
#         db.session.add(ag)
#         updated_list.append({
#             "id": ag.id,
#             "name": ag.name,
#             "age": ag.age,
#             "occupation": ag.occupation,
#             "background_story": ag.background_story
#         })
#     db.session.commit()

#     return jsonify({"agents": updated_list})

# @agent_bp.route('/preview', methods=['POST'])
# def preview():
#     """
#     用户可在此微调Agent属性
#     比如前端传 { agentId, newAge, newIncome... }
#     然后更新后再返回最新的agent数据
#     这里只做示例
#     """
#     data = request.json
#     agent_id = data.get('agentId', '')
#     updated_props = data.get('updatedProps', {})
    
#     # 此处仅演示, 实际你可能在数据库/内存中更新
#     # ...
#     return jsonify({"status": "ok", "updatedAgentId": agent_id, "newProps": updated_props})

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

    from models import Agent
    agents = Agent.query.filter_by(project_id=project_id).all()
    results = []
    from shapely.geometry import mapping
    from geoalchemy2.shape import to_shape
    for ag in agents:
        # 把 geom 转成geojson
        home_geom = None
        if ag.home_geom:
            shp = to_shape(ag.home_geom)
            home_geom = mapping(shp)
        work_geom = None
        if ag.work_geom:
            shp2 = to_shape(ag.work_geom)
            work_geom = mapping(shp2)
        work_tract = None
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
    """
    POST /agents/generateDetailed
    body: { "projectId": X }

    - 查询该projectId下全部 Agent
    - 对每个Agent调用 generate_agent_desc_with_demo
    - 将结果存DB
    - 返回更新后的 agent列表
    """
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

    # 重新获取更新后对象 (或直接组装)
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