// pages/markAgents.js
import dynamic from 'next/dynamic';
import { useRouter } from 'next/router';
import { useState, useEffect } from 'react';
import axios from 'axios';
import { apiClient } from '../utils/api';

// 改成一个叫 AgentMap 的组件, 我们会定义在 components/AgentMap.js
const AgentMap = dynamic(() => import('../components/AgentMap'), {
  ssr: false,
});

export default function MarkAgentsPage() {
  const router = useRouter();
  const [projectId, setProjectId] = useState('');
  const [step, setStep] = useState('home'); // 'home' or 'work'
  const [homeCoord, setHomeCoord] = useState(null);
  const [agents, setAgents] = useState([]); // 前端维护: { agentId, home, work }

  useEffect(() => {
    if (router.query.projectId) {
      setProjectId(router.query.projectId);
    }
  }, [router.query.projectId]);

  // 当用户在地图点击时
  const handleMapClick = async (lat, lng) => {
    if (step === 'home') {
      setHomeCoord({ lat, lng });
      setStep('work');
      alert(`已记录居住点: lat=${lat}, lng=${lng}，请再点地图选择工作地址`);
    } else {
      // step === 'work'
      if (!homeCoord) {
        alert('请先选择居住点');
        return;
      }
      const workCoord = { lat, lng };
      // 调用后端 /agents/locate
      try {
        const res = await apiClient.post('/agents/locate', {
          projectId,
          home: homeCoord,
          work: workCoord,
        });
        const newAgentId = res.data.agentId;
        alert(`成功创建Agent: id=${newAgentId}`);

        // 加入本地Agent数组
        setAgents((prev) => [
          ...prev,
          {
            agentId: newAgentId,
            home: homeCoord,
            work: workCoord,
          },
        ]);
        // 重置
        setHomeCoord(null);
        setStep('home');
      } catch (err) {
        alert('定位Agent失败:' + err.message);
      }
    }
  };

  // 让后端给这些Agent生成 LLM描述
  const handleGenerateAll = async () => {
    try {
      const res = await apiClient.post('/agents/generateDetailed', {
        projectId,
      });
      console.log('Generate result:', res.data);
      // 跳转到 agentPreview
      router.push({
        pathname: '/agentPreview',
        query: { projectId },
      });
    } catch (err) {
      alert('生成Agent失败:' + err.message);
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>3) 标注 Agent 居住地与工作地 (ProjectID: {projectId})</h2>
      <p>
        当前步骤: {step === 'home' ? '点击地图选择 Home' : '点击地图选择 Work'}
      </p>

      <div style={{ width: '100%', height: '500px' }}>
        <AgentMap agents={agents} onClickMap={handleMapClick} />
      </div>

      <div style={{ marginTop: 20 }}>
        <button onClick={handleGenerateAll}>生成全部Agent描述</button>
      </div>

      <div style={{ marginTop: 20 }}>
        <h3>已创建的Agent ({agents.length})</h3>
        <ul>
          {agents.map((a, idx) => (
            <li key={a.agentId}>
              Agent {a.agentId}: home=({a.home.lat},{a.home.lng}), work=(
              {a.work.lat},{a.work.lng})
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
