from flask import Blueprint, request, jsonify
from services.data_processing import store_project_info, store_demographic_info
from services.llm_service import refine_project_description

project_bp = Blueprint('project_bp', __name__)

@project_bp.route('/create', methods=['POST'])
def create_project():
    """
    用户在前端 createProject.js 中输入项目名称、简介、场地位置信息
    后端可以调用LLM做一定处理，然后把结果存起来
    """
    data = request.json
    project_name = data.get('projectName', '')
    project_desc = data.get('projectDesc', '')
    project_location = data.get('projectLocation', '')

    # 调用LLM做些“自动润色”或“提取关键词”等 (此处示例简单)
    refined_text = refine_project_description(project_desc, project_location)

    # 存入数据库或内存(此处示例用 services.data_processing 里的一个函数)
    project_id = store_project_info(project_name, refined_text, project_location)

    return jsonify({
        "projectId": project_id,
        "projectName": project_name,
        "refinedDesc": refined_text
    })

@project_bp.route('/demographic', methods=['POST'])
def set_demographic():
    """
    用户填写/上传 Demographic 信息，后端暂存
    可能包含各种字段: 人口比例、年龄段、出行方式等
    """
    data = request.json
    project_id = data.get('projectId', '')
    demographic_data = data.get('demographic', {})

    # 存储到后端 (假装存进数据库)
    store_demographic_info(project_id, demographic_data)

    return jsonify({"status": "ok", "message": "Demographic info stored."})
