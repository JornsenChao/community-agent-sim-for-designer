// pages/selectRegion.js
import dynamic from 'next/dynamic';
import { useRouter } from 'next/router';
import { useState, useEffect } from 'react';
import axios from 'axios';
import { apiClient } from '../utils/api';

// 这个组件是你已有的, 用来在地图上绘制多边形/矩形
const MapWithDraw = dynamic(() => import('../components/MapWithDraw'), {
  ssr: false,
});

export default function SelectRegionPage() {
  const router = useRouter();
  const [projectId, setProjectId] = useState('');
  const [geometry, setGeometry] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

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
    setLoading(true);
    try {
      const res = await apiClient.post('/spatial/setBoundary', {
        projectId,
        geometry,
      });
      setResult(res.data.analysis);

      // 这里说明成功抓取了 OSMnx + Census
      // 可能会耗时，因此前端要给提示
      router.push({
        pathname: '/markAgents',
        query: { projectId },
      });
    } catch (err) {
      alert('Error: ' + err.message);
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>2) 选择区域: (ProjectID: {projectId})</h2>
      <p>在地图上绘制你的Project Boundary, 然后点击 "确定区域"。</p>
      <div style={{ width: '100%', height: '500px', marginBottom: '20px' }}>
        <MapWithDraw onGeometryCreated={(geo) => setGeometry(geo)} />
      </div>
      <button onClick={handleSetBoundary} disabled={loading}>
        {loading ? '处理中...' : '确定区域'}
      </button>

      {result && (
        <div style={{ marginTop: 20 }}>
          <h3>后端返回:</h3>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
