# A tool to create local context based contextual agents and simulate conversations to give design feedback

## Agent generation

### related code

#### models.py:

'''
name, age, occupation, background_story, home_tract, work_tract
'''

#### routes/agent_routes.py:

'''
/agents/locate：前端点击地图传 {home, work}, 后端根据坐标获取 tract，新建 Agent 记录。
/agents/list：返回当前项目下全部 Agent；
/agents/generateDetailed：对数据库里的 Agent 调用 generate_agent_desc_with_demo(ag) ，将结果写回 DB。
'''

#### services/agent_generation.py

'''
generate_single_agent_desc(home_tract, work_tract)
generate_agent_desc_with_demo(agent)：结合 Census data 做详细背景故事。
'''

#### services/llm_service.py

generate_agent_with_llm(prompt_text)
