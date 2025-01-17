import { useRouter } from 'next/router';
import { useState, useEffect } from 'react';
import axios from 'axios';
import AgentCard from '../components/AgentCard';

export default function AgentPreviewPage() {
  const router = useRouter();
  const [projectId, setProjectId] = useState('');
  const [agents, setAgents] = useState([]);
  const [agentCount, setAgentCount] = useState(3);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (router.query.projectId) {
      setProjectId(router.query.projectId);
    }
  }, [router.query.projectId]);

  const handleGenerateAgents = async () => {
    setLoading(true);
    try {
      const res = await axios.post('http://localhost:5000/agents/generate', {
        projectId,
        agentCount: Number(agentCount),
      });
      setAgents(res.data.agents);
    } catch (err) {
      alert('生成Agent失败:' + err.message);
    }
    setLoading(false);
  };

  const goToSelectRegion = () => {
    router.push({
      pathname: '/selectRegion',
      query: { projectId },
    });
  };

  const handlePreviewUpdate = async (agentId) => {
    // 演示：假设要把某agent的age改为 40
    const res = await axios.post('http://localhost:5000/agents/preview', {
      agentId,
      updatedProps: { age: 40 },
    });
    console.log('Preview update result:', res.data);
    // 你可以在这里刷新Agent列表、或做更多逻辑
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>Agent 预览与微调 (ProjectID: {projectId})</h2>

      <div>
        <label>生成Agent数量: </label>
        <input
          type="number"
          value={agentCount}
          onChange={(e) => setAgentCount(Number(e.target.value))}
          style={{ width: 60, marginRight: 10 }}
        />
        <button onClick={handleGenerateAgents}>
          {loading ? '生成中...' : '生成Agent'}
        </button>
      </div>

      <div style={{ marginTop: 20 }}>
        {agents.map((agent) => (
          <AgentCard
            key={agent.id}
            agent={agent}
            onUpdate={() => handlePreviewUpdate(agent.id)}
          />
        ))}
      </div>

      <div style={{ marginTop: 40 }}>
        <button onClick={goToSelectRegion}>
          下一步: 选择区域并获取 OSM 数据
        </button>
      </div>
    </div>
  );
}
