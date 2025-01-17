import dynamic from 'next/dynamic';
import { useRouter } from 'next/router';
import { useState, useEffect } from 'react';
import axios from 'axios';

// 用 dynamic 来在前端渲染 MapWithDraw
const MapWithDraw = dynamic(() => import('../components/MapWithDraw'), {
  ssr: false,
});

export default function SelectRegionPage() {
  const router = useRouter();
  const [projectId, setProjectId] = useState('');
  const [bounds, setBounds] = useState(null);
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (router.query.projectId) {
      setProjectId(router.query.projectId);
    }
  }, [router.query.projectId]);

  const handleFetchData = async () => {
    if (!bounds) {
      alert('请先在地图上画一个矩形区域');
      return;
    }
    const { minx, miny, maxx, maxy } = bounds;
    try {
      const res = await axios.post('http://localhost:5000/spatial/fetch', {
        minx,
        miny,
        maxx,
        maxy,
      });
      setResult(res.data);
    } catch (err) {
      console.error(err);
      alert('Error: ' + err.message);
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>选择区域: 获取 OSM + Census数据 (ProjectID: {projectId})</h2>

      <div style={{ width: '100%', height: '500px', marginBottom: '20px' }}>
        <MapWithDraw onBoundsChange={(b) => setBounds(b)} />
      </div>

      <button onClick={handleFetchData}>获取数据</button>

      {bounds && (
        <div style={{ marginTop: 10 }}>
          <strong>选取区域 Bounds:</strong>
          <p>
            Min X: {bounds.minx}, Max X: {bounds.maxx}
          </p>
          <p>
            Min Y: {bounds.miny}, Max Y: {bounds.maxy}
          </p>
        </div>
      )}

      {result && (
        <div style={{ marginTop: 20 }}>
          <h3>后端返回:</h3>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
