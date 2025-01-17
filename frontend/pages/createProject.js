import { useState } from 'react';
import axios from 'axios';
import { useRouter } from 'next/router';

export default function CreateProjectPage() {
  const router = useRouter();

  const [projectName, setProjectName] = useState('');
  const [projectDesc, setProjectDesc] = useState('');
  const [projectLocation, setProjectLocation] = useState('');
  const [result, setResult] = useState(null);

  const handleCreate = async () => {
    try {
      const res = await axios.post('http://localhost:5000/project/create', {
        projectName,
        projectDesc,
        projectLocation,
      });
      setResult(res.data);

      // 跳转到下一步(人口信息页面)时，把projectId传过去
      router.push({
        pathname: '/demographic',
        query: { projectId: res.data.projectId },
      });
    } catch (err) {
      console.error(err);
      alert('创建项目失败:' + err.message);
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>创建新项目</h2>
      <div>
        <label>项目名称: </label>
        <input
          value={projectName}
          onChange={(e) => setProjectName(e.target.value)}
          style={{ marginBottom: 10 }}
        />
      </div>
      <div>
        <label>项目简介: </label>
        <textarea
          value={projectDesc}
          onChange={(e) => setProjectDesc(e.target.value)}
          rows={3}
          style={{ marginBottom: 10, width: 300 }}
        />
      </div>
      <div>
        <label>场地位置: </label>
        <input
          value={projectLocation}
          onChange={(e) => setProjectLocation(e.target.value)}
          style={{ marginBottom: 10 }}
        />
      </div>
      <button onClick={handleCreate}>创建并进入下一步</button>

      {result && (
        <div style={{ marginTop: 20 }}>
          <h4>后端返回信息:</h4>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
