// pages/createProject.js
import { useState } from 'react';
import axios from 'axios';
import { apiClient } from '../utils/api';
import { useRouter } from 'next/router';

export default function CreateProjectPage() {
  const router = useRouter();
  const [projectName, setProjectName] = useState('');
  const [projectDesc, setProjectDesc] = useState('');
  const [projectLocation, setProjectLocation] = useState('');

  const handleCreate = async () => {
    try {
      const res = await apiClient.post('/project/create', {
        projectName,
        projectDesc,
        projectLocation,
      });
      const pid = res.data.projectId;
      router.push({
        pathname: '/selectRegion',
        query: { projectId: pid },
      });
    } catch (err) {
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
        <label>场地位置(可选): </label>
        <input
          value={projectLocation}
          onChange={(e) => setProjectLocation(e.target.value)}
          style={{ marginBottom: 10 }}
        />
      </div>
      <button onClick={handleCreate}>下一步: 选择区域</button>
    </div>
  );
}
