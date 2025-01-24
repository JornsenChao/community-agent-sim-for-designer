import { useRouter } from 'next/router';
import { useState, useEffect } from 'react';
import { apiClient } from '../utils/api'; // <-- 改用这个
import axios from 'axios';
import AgentCard from '../components/AgentCard';

export default function AgentPreviewPage() {
  const router = useRouter();
  const [projectId, setProjectId] = useState('');
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (router.query.projectId) {
      setProjectId(router.query.projectId);
      fetchAgents(router.query.projectId);
    }
  }, [router.query.projectId]);

  const fetchAgents = async (pid) => {
    setLoading(true);
    try {
      const res = await apiClient.get(`/agents/list?projectId=${pid}`);
      setAgents(res.data.agents);
    } catch (err) {
      alert('获取Agent失败:' + err.message);
    }
    setLoading(false);
  };

  const handlePreviewUpdate = async (agentId) => {
    // 你可以在这里调用 /agents/preview 之类路由更新Agent
    // 此处仅示例:
    const res = await apiClient.post('/agents/preview', {
      agentId,
      updatedProps: { age: 40 },
    });
    console.log('Preview update result:', res.data);
    // 刷新
    fetchAgents(projectId);
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>4) Agent 预览 (ProjectID: {projectId})</h2>
      {loading && <div>加载中...</div>}
      {agents.map((agent) => (
        <AgentCard
          key={agent.id}
          agent={{
            id: agent.id,
            // all: agent,
            // desc: `姓名: ${agent.name}\n年龄:${agent.age}\n职业:${agent.occupation}\n故事:${agent.background_story}`,
            name: agent.name,
            age: agent.age,
            occupation: agent.occupation,
            background_story: agent.background_story,
            home_tract: agent.home_tract,
            work_tract: agent.work_tract,
          }}
          onUpdate={() => handlePreviewUpdate(agent.id)}
        />
      ))}
    </div>
  );
}
