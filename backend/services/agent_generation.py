import random
import json
from models import db, Agent
from services.llm_service import generate_agent_with_llm
from services.census_service import get_tract_demographics

def pick_category_from_distribution(demographic):
    distribution = []
    elderly_p = demographic.get('elderlyPercent', 0)
    worker_p = demographic.get('workerPercent', 0)
    # assisted_mobility_p = demographic.get('assistedMobilityPercent', 0)
    # 也可加 studentPercent, childPercent...
    
    distribution.append(('elderly', elderly_p))
    distribution.append(('worker', worker_p))
    # distribution.append(('assistedMobility', assisted_mobility_p))

    total = sum([item[1] for item in distribution]) or 1
    r = random.random()
    cumulative = 0.0
    for cat, pct in distribution:
        portion = pct / total
        cumulative += portion
        if r <= cumulative:
            return cat
    return 'other'
def generate_agents(project_info, demographic, agent_count):
    project_name = project_info.get("name", "Unnamed")
    location = project_info.get("location", "Unknown")
    demo_str = str(demographic)  # 只是把dict转字符串当做简易输入
    notes = demographic.get('notes', '')

    agents = []
    previous_agent_descriptions = []
    
    for i in range(agent_count):
        cat = pick_category_from_distribution(demographic)
        if cat == 'elderly':
            age = random.randint(65, 90)
        elif cat == 'worker':
            age = random.randint(18, 70)
        # elif cat == 'assistedMobility':
        #     age = random.randint(10, 80)
        else:
            age = random.randint(10, 80)
        prompt_text = f"""
System context: You are a generator of social characters in an architectural or urban project. 
We have a project named '{project_name}' located at '{location}'. 
User notes: {notes}

We want a unique character for category: '{cat}' (meaning age group or social role). 
Their approximate age is {age}. 
Previously generated agents: {previous_agent_descriptions}

Please output:
1) Name (English)
2) Exact age
3) Occupation or identity 
4) Main focus or concern
5) Brief background story
6) A day in their life

Be sure to make this character distinct from the previously generated ones.
"""
        agent_desc = generate_agent_with_llm(prompt_text)
        
        # 这里你可以再解析agent_desc，变成结构化数据
        # 暂时仅示例:
        agents.append({
            "id": f"agent_{i+1}",
            "desc": agent_desc
        })
        
    return agents

def generate_single_agent_desc(home_tract, work_tract):
    """
    给定 home_tract, work_tract, 用LLM生成一个Agent信息
    返回 dict, e.g. {name, age, occupation, background_story}
    """

    prompt_text = f"""
You are generating a fictional resident in the US. 
- This person's home is in CensusTract {home_tract}, 
- They work/study in CensusTract {work_tract}.

Create a short JSON with fields: name, age, occupation, background_story. 
The story should reflect commuting or daily life considerations traveling from {home_tract} to {work_tract}.
Output JSON only.
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
Neighborhood ACS data for your area:
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

Given this is the environment you live in, 
please expand or refine your background story to mention how your daily life 
might be influenced by these demographic/economic factors. 
Output in plain text, describing how you (the agent) typically experience 
the local neighborhood, commute, interactions with families, etc.
"""

    # 3) 让LLM生成
    raw_story = generate_agent_with_llm(tract_prompt)
    # 你可以直接把 raw_story 存 agent.background_story
    # 或者先做 json.loads, 这里示例就直接用文本
    agent.background_story = raw_story.strip()

    return agent