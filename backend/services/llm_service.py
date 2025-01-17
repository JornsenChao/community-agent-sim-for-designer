import openai
import os
from openai import OpenAI
from config import config

# 这里是与真实LLM交互的工具函数
openai.api_key = config.OPENAI_API_KEY
client = OpenAI(
    api_key = config.OPENAI_API_KEY
    # api_key=os.environ.get("OPENAI_API_KEY"),  # This is the default and can be omitted
)

def refine_project_description(project_desc, location):

    prompt = f"""
    you are a professional writing assistant for building/park/infrastructure projects. There is a projectlocated at {location}. Here is the project description: {project_desc}. Please use simple language to extract project key points and slightly refine the project description.
"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  
            messages=[
                {"role": "system", "content": "You are a professional writing assistant for building/park/infrastructure projects。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=512
        )
        refined_text = response.choices[0].message.content.strip()
        return refined_text
    except Exception as e:
        print("OpenAI调用失败:", e)
        return project_desc  # 如果失败，就返回原文

def generate_agent_with_llm(prompt_text):
    """
    用LLM生成一个角色介绍
    prompt_text中包含：人口背景、需求点等
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  
            messages=[
                {"role": "system", "content": "You are a social character generator, and help architect, landscape architects, or urban planners to create a dynamic range of social characters that might use their projects."},
                {"role": "user", "content": prompt_text}
            ],
            max_tokens=512,
            temperature=0.9,   # 提高一点temperature，让模型输出更多样化
            top_p=0.9,         # 或者结合 top_p
        )
        agent_desc = response.choices[0].message.content.strip()
        return agent_desc
    except Exception as e:
        print("生成Agent时失败:", e)
        return "生成失败"
