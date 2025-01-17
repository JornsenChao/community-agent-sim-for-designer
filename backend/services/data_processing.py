# 这里模拟存储和检索数据，可用全局字典替代数据库 (Demo用)
db_projects = {}
db_demographic = {}

def store_project_info(name, refined_desc, location):
    # 生成一个简单ID
    project_id = f"proj_{len(db_projects)+1}"
    db_projects[project_id] = {
        "id": project_id,
        "name": name,
        "description": refined_desc,
        "location": location
    }
    return project_id

def get_project_info(project_id):
    return db_projects.get(project_id, {})

def store_demographic_info(project_id, demographic_data):
    db_demographic[project_id] = demographic_data

def get_demographic_info(project_id):
    return db_demographic.get(project_id, {})

def process_design_data(design_info):
    # 这里就是做一个演示
    summary = f"设计描述: {design_info.get('description', '')}, 主要功能: {design_info.get('mainFeature', '')}"
    return {
        "summary": summary,
        "rawData": design_info
    }
