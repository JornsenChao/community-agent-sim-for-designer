import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import axios from 'axios';

export default function DemographicPage() {
  const router = useRouter();
  const [projectId, setProjectId] = useState('');

  // 这里演示几种输入形式
  const [elderlyPercent, setElderlyPercent] = useState(0);
  const [workerPercent, setWorkerPercent] = useState(0);
  // const [assistedMobilityPercent, setAssistedMobilityPercent] = useState(0);
  const [notes, setNotes] = useState('');

  // 从URL参数里取projectId
  useEffect(() => {
    if (router.query.projectId) {
      setProjectId(router.query.projectId);
    }
  }, [router.query.projectId]);

  const handleSubmit = async () => {
    try {
      const demographicData = {
        elderlyPercent,
        workerPercent,
        // assistedMobilityPercent,
        notes,
      };
      const res = await axios.post(
        'http://localhost:5000/project/demographic',
        {
          projectId,
          demographic: demographicData,
        }
      );
      console.log('Demographic store result:', res.data);

      // 跳转到下一步: 生成 Agent
      router.push({
        pathname: '/agentPreview',
        query: { projectId },
      });
    } catch (err) {
      alert('提交失败:' + err.message);
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>人口信息填写 (ProjectID: {projectId})</h2>

      <div>
        <label>老年人占比: {elderlyPercent}%</label>
        <br />
        <input
          type="range"
          min={0}
          max={100}
          value={elderlyPercent}
          onChange={(e) => setElderlyPercent(e.target.value)}
          style={{ width: 300 }}
        />
      </div>
      <div style={{ marginTop: 20 }}>
        <label>上班族占比: {workerPercent}%</label>
        <br />
        <input
          type="range"
          min={0}
          max={100}
          value={workerPercent}
          onChange={(e) => setWorkerPercent(e.target.value)}
          style={{ width: 300 }}
        />
      </div>
      <div style={{ marginTop: 20 }}>
        <label>其它备注信息:</label>
        <br />
        <textarea
          rows={3}
          style={{ width: 300 }}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
      </div>

      <button style={{ marginTop: 20 }} onClick={handleSubmit}>
        提交并进入下一步
      </button>
    </div>
  );
}
