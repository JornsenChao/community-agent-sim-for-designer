def handle_chat(agent_id, user_message):
    """
    对某个agent进行对话的逻辑。
    这里暂时不用LLM，只返回mock回复
    你可以将agent_id, user_message 拼到prompt 调OpenAI
    """
    # 示例，仅返回固定文本:
    return f"Agent {agent_id} 回应: 我已收到你的信息({user_message})，你好。"
