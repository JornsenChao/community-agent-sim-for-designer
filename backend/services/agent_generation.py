import random
import json
from models import db, Agent
from services.llm_service import generate_agent_with_llm
from services.census_service import get_tract_demographics
# 
'''
generate_agents(project_info, demographic, agent_count):    很少被用到
    批量生成“基础版”Agent描述（带随机年龄、简单背景），但不直接存进数据库，返回一个 临时列表 agents 

generate_single_agent_desc(home_tract, work_tract):
    为某个 Agent 生成简洁描述（姓名、年龄、职业、背景故事）
    作用：
        拼出 Prompt：
            You are generating a fictional resident in the US. 
            This person's home is in CensusTract {home_tract}, 
            They work/study in CensusTract {work_tract}.
        调用 generate_agent_with_llm(...)，返回一段 JSON 文本。
        try: json.loads(...)，若成功则从中取出 name, age, occupation, background_story 组成 dict 返回。
    被谁调用：
        在 agent_routes.py 里 /generate 路由。
        它从数据库里遍历所有 Agent（这时Agent只存了 home_tract, work_tract），对每个Agent调用 generate_single_agent_desc()，然后把解析到的 name, age, occupation 等写回数据库。
    
generate_agent_desc_with_demo(agent):
        在已有Agent上，结合真实人口/通勤/收入等统计信息（从 Census 获取）进行“更深入”背景故事补充。
    作用：
        从 agent.home_tract 提取 state_fips, county_fips, tract_fips；
        调用 get_tract_demographics(...) 来查真实的 Census 人口和经济数据；
        用这些统计信息拼接成 Prompt，调用 generate_agent_with_llm(...)，得到更丰富的背景描述；
        写进 agent.background_story 并返回更新后的 agent。
    被谁调用：
        在 agent_routes.py 中 /generateDetailed 路由。
        路由里针对同一个project的全部Agent执行 generate_agent_desc_with_demo(ag)，然后db.session.commit()保存结果。    
    
    '''

# def pick_category_from_distribution(demographic):
#     distribution = []
#     elderly_p = demographic.get('elderlyPercent', 0)
#     worker_p = demographic.get('workerPercent', 0)
#     # assisted_mobility_p = demographic.get('assistedMobilityPercent', 0)
#     # 也可加 studentPercent, childPercent...
    
#     distribution.append(('elderly', elderly_p))
#     distribution.append(('worker', worker_p))
#     # distribution.append(('assistedMobility', assisted_mobility_p))

#     total = sum([item[1] for item in distribution]) or 1
#     r = random.random()
#     cumulative = 0.0
#     for cat, pct in distribution:
#         portion = pct / total
#         cumulative += portion
#         if r <= cumulative:
#             return cat
#     return 'other'

# def generate_agents(project_info, demographic, agent_count):
#     project_name = project_info.get("name", "Unnamed")
#     location = project_info.get("location", "Unknown")
#     demo_str = str(demographic)  # 只是把dict转字符串当做简易输入
#     notes = demographic.get('notes', '')

#     agents = []
#     previous_agent_descriptions = []
    
#     for i in range(agent_count):
#         cat = pick_category_from_distribution(demographic)
#         if cat == 'elderly':
#             age = random.randint(65, 90)
#         elif cat == 'worker':
#             age = random.randint(18, 70)
#         # elif cat == 'assistedMobility':
#         #     age = random.randint(10, 80)
#         else:
#             age = random.randint(10, 80)
#         prompt_text = f"""
# System context: You are a generator of social characters in an architectural or urban project. 
# We have a project named '{project_name}' located at '{location}'. 
# User notes: {notes}

# We want a unique character for category: '{cat}' (meaning age group or social role). 
# Their approximate age is {age}. 
# Previously generated agents: {previous_agent_descriptions}

# Please output:
# 1) Name (English)
# 2) Exact age
# 3) Occupation or identity 
# 4) Main focus or concern
# 5) Brief background story
# 6) A day in their life

# Be sure to make this character distinct from the previously generated ones.
# """
#         agent_desc = generate_agent_with_llm(prompt_text)
        
#         # 这里你可以再解析agent_desc，变成结构化数据
#         # 暂时仅示例:
#         agents.append({
#             "id": f"agent_{i+1}",
#             "desc": agent_desc
#         })
        
#     return agents

def generate_single_agent_desc(home_tract, work_tract):
    """
    给定 home_tract, work_tract, 用LLM生成一个Agent信息
    返回 dict, e.g. {name, age, occupation, background_story}
    """

    prompt_text = f"""
You are generating a fictional resident in the US. 
We only want these fields in valid JSON:
{{
  "name": "...",
  "age": 30,
  "occupation": "...",
  "background_story": "A short paragraph summarizing daily commute from {home_tract} to {work_tract}."
}}

Constraints:
- 'name' can be a random first name, last name optional
- 'age' must be an integer between 18 and 80
- 'occupation' can be anything, do NOT default to 'urban planner' or 'landscape architect'
- 'background_story' references traveling from {home_tract} to {work_tract}

Output JSON only, no extra text.
"""
    raw_response = generate_agent_with_llm(prompt_text).strip()
    # 可能带有多余字符，用 try parse
    try:
        agent_obj = json.loads(raw_response)
    except:
        agent_obj = {
            "name": "Unknown",
            "age": 30,
            "occupation": "Unknown",
            "background_story": raw_response
        }
    return agent_obj


def generate_agent_desc_with_demo(agent):
    """
    给定一个Agent, 根据其 home_tract 调用 census_service 获取
    相关人口/年龄/收入/通勤等信息, 并把这些信息写进Prompt,
    让LLM 生成更贴近现实的背景故事.
    
    最终更新 agent.background_story 等字段, 并返回更新后的 agent.
    """
    # 如果 agent.home_tract 是 None 或空, 就跳过
    if not agent.home_tract:
        agent.background_story = "(No tract info, skipping demographics-based story.)"
        return agent

    # 拆分 "06-081-610202"
    parts = agent.home_tract.split("-")
    if len(parts) != 3:
        agent.background_story = f"(Invalid home_tract: {agent.home_tract})"
        return agent

    state_fips, county_fips, tract_fips = parts

    # 1) 拉取真实统计信息
    demo_info = get_tract_demographics(state_fips, county_fips, tract_fips)
    if "error" in demo_info:
        # 出错时, 可以记一条, 也可以抛异常
        agent.background_story = f"(Error calling census: {demo_info['error']})"
        return agent

    # demo_info 样例:
    # {
    #   "tract_name": "Census Tract 610202, ...",
    #   "total_pop": 7890,
    #   "median_age": 34.2,
    #   "pct_children": 15.3,
    #   "pct_seniors": 12.7,
    #   "median_income": 65000,
    #   "commute": {...},
    #   "education_levels": {...}
    # }

    # 2) 构造Prompt: 让LLM把这些统计信息纳入 "Agent背景描述"
    tract_prompt = f"""
You are generating a fictional resident who lives in a neighborhood with these Census Tract satistics:
 - Census tract name: {demo_info.get('tract_name')}
 - Total population: {demo_info.get('total_pop')}
 - Median age: {demo_info.get('median_age')}
 - Children (0-14): {demo_info.get('pct_children')}%
 - Seniors (65+): {demo_info.get('pct_seniors')}%
 - Median household income: {demo_info.get('median_income')}
 - Commute: 
     Walk/Bike = {demo_info['commute'].get('pct_walk_bike',0)}%, 
     PublicTransit = {demo_info['commute'].get('pct_public_transit',0)}%,
     DriveAlone = {demo_info['commute'].get('pct_drive_alone',0)}%
 - Education:
     HS or lower = {demo_info['education_levels'].get('pct_hs_or_lower',0)}%,
     Bachelor+ = {demo_info['education_levels'].get('pct_bach_or_higher',0)}%

We currently have partial agent data: 
NAME: {agent.name or "unknown"}
AGE: {agent.age or "30"}
OCCUPATION: {agent.occupation or "unemployed"}

Now, refine the agent's background_story to incorporate at least 8 relevant data points from above, within which all the communting information must be included. 
Explain how these local demographics or commute patterns affect daily routines or personal perspective. 
Output only valid JSON in the format:
{{
  "name": "...",
  "age": 25,
  "occupation": "...",
  "background_story": "...",
}}
All fields are mandatory. 
Make sure 'occupation' is consistent with the local context, but do not lock it to 'urban planner' or 'landscape architect'. 
Generate a unique name if none was specified. 
Return JSON only, no extra text.
"""

    # 3) 让LLM生成
    raw_story = generate_agent_with_llm(tract_prompt)
    try:
        story_obj = json.loads(raw_story)
        # story_obj: { "name": "...", "age":..., "occupation":"...", "background_story":"..." }
        agent.name = story_obj.get("name")
        agent.age = story_obj.get("age")
        agent.occupation = story_obj.get("occupation")
        agent.background_story = story_obj.get("background_story")
    except:
        # 如果解析失败, 就用 fallback
        agent.background_story = raw_story

    return agent