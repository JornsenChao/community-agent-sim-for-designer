/*
用户输入社区信息：年龄段、需求点等
点击「提交」→ POST /api/upload_community_data
或直接生成 Agents → POST /api/generate_agents 并跳转到下一页
*/
import { useState } from 'react';
import axios from 'axios';

export default function CommunityDataPage() {
  const [population, setPopulation] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = async () => {
    try {
      // 示例: 构造提交的 JSON
      const communityData = {
        population: population,
      };

      // 调用后端 /agents/generate
      const res = await axios.post('http://localhost:5000/agents/generate', {
        communityData,
      });

      setMessage('社区数据提交成功，已生成 Agents!');
      console.log('Agents:', res.data.agents);
    } catch (err) {
      setMessage('提交失败:' + err.message);
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>社区数据填写</h2>
      <label>
        人口结构描述:
        <input
          type="text"
          value={population}
          onChange={(e) => setPopulation(e.target.value)}
          style={{ width: '300px', marginLeft: 10 }}
        />
      </label>
      <button onClick={handleSubmit} style={{ marginLeft: 10 }}>
        生成Agents
      </button>

      <p>{message}</p>
    </div>
  );
}
