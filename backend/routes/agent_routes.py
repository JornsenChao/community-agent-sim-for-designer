from flask import Blueprint, request, jsonify
from services.agent_generation import generate_agents
from services.data_processing import get_project_info, get_demographic_info

agent_bp = Blueprint('agent_bp', __name__)

@agent_bp.route('/generate', methods=['POST'])
def generate():
    """
    根据projectId, 调用已存的项目信息 & demographic，
    利用 LLM 生成若干 Agent
    """
    data = request.json
    project_id = data.get('projectId', '')
    agent_count = data.get('agentCount', 3)  # 用户可自定义想要生成几个Agent
    agent_count = int(agent_count)  # 转成int
    
    # 取到项目基础信息 & 人口信息
    project_info = get_project_info(project_id)
    demographic = get_demographic_info(project_id)

    # 调用Service生成Agent
    agents = generate_agents(project_info, demographic, agent_count)
    
    return jsonify({"agents": agents})

@agent_bp.route('/preview', methods=['POST'])
def preview():
    """
    用户可在此微调Agent属性
    比如前端传 { agentId, newAge, newIncome... }
    然后更新后再返回最新的agent数据
    这里只做示例
    """
    data = request.json
    agent_id = data.get('agentId', '')
    updated_props = data.get('updatedProps', {})
    
    # 此处仅演示, 实际你可能在数据库/内存中更新
    # ...
    return jsonify({"status": "ok", "updatedAgentId": agent_id, "newProps": updated_props})
