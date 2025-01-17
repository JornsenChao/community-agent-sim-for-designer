import random
from services.llm_service import generate_agent_with_llm

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
