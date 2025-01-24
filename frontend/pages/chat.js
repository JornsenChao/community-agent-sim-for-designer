/*
让用户在下拉或选项中选择某个 Agent（如 Josh, Amy）
输入问题或点击「模拟对话」按钮
前端发送 agent_id + user_input 给后端 /api/agent_chat
后端返回 Agent/系统回复
显示在对话框中
*/
import { useState } from 'react';
import axios from 'axios';
import { apiClient } from '../utils/api';
import ChatWindow from '../components/ChatWindow';

export default function ChatPage() {
  const [agentId, setAgentId] = useState('agent_1');
  const [userMessage, setUserMessage] = useState('');
  const [chatResponse, setChatResponse] = useState('');

  const handleSend = async () => {
    try {
      const res = await apiClient.post('/chat/ask', {
        agentId,
        message: userMessage,
      });
      setChatResponse(res.data.response);
    } catch (err) {
      setChatResponse('Error: ' + err.message);
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>多角色对话</h2>
      <label>
        Agent ID:
        <input
          type="text"
          value={agentId}
          onChange={(e) => setAgentId(e.target.value)}
          style={{ marginLeft: 10 }}
        />
      </label>
      <br />
      <br />
      <label>
        你的消息:
        <input
          type="text"
          value={userMessage}
          onChange={(e) => setUserMessage(e.target.value)}
          style={{ marginLeft: 10, width: '300px' }}
        />
      </label>
      <button onClick={handleSend} style={{ marginLeft: 10 }}>
        发送
      </button>

      <ChatWindow response={chatResponse} />
    </div>
  );
}
