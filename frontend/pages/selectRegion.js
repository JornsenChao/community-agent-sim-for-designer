// pages/selectRegion.js
import dynamic from 'next/dynamic';
import { useRouter } from 'next/router';
import { useState, useEffect } from 'react';
import axios from 'axios';

// 这个组件是你已有的, 用来在地图上绘制多边形/矩形
const MapWithDraw = dynamic(() => import('../components/MapWithDraw'), {
  ssr: false,
});

export default function SelectRegionPage() {
  const router = useRouter();
  const [projectId, setProjectId] = useState('');
  const [geometry, setGeometry] = useState(null);
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (router.query.projectId) {
      setProjectId(router.query.projectId);
    }
  }, [router.query.projectId]);

  const handleSetBoundary = async () => {
    if (!geometry) {
      alert('请先在地图上画多边形/矩形');
      return;
    }
    try {
      const res = await axios.post(
        'http://localhost:5000/spatial/setBoundary',
        {
          projectId,
          geometry,
        }
      );
      setResult(res.data.analysis);

      // 接下来跳转到下一步
      router.push({
        pathname: '/markAgents',
        query: { projectId },
      });
    } catch (err) {
      alert('Error: ' + err.message);
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>2) 选择区域: (ProjectID: {projectId})</h2>
      <p>在地图上绘制你的Project Boundary, 然后点击 "确定区域"。</p>
      <div style={{ width: '100%', height: '500px', marginBottom: '20px' }}>
        <MapWithDraw onGeometryCreated={(geo) => setGeometry(geo)} />
      </div>
      <button onClick={handleSetBoundary}>确定区域</button>

      {result && (
        <div style={{ marginTop: 20 }}>
          <h3>后端返回:</h3>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
