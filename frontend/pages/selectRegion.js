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
  // const [result, setResult] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

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
    setErrorMsg('');
    setAnalysis(null);
    try {
      const res = await apiClient.post('/spatial/setBoundary', {
        projectId,
        geometry,
      });
      if (res.data.analysis) {
        setAnalysis(res.data.analysis);
      } else {
        setErrorMsg('后端没有返回分析结果');
      }

      // 这里说明成功抓取了 OSMnx + Census
      // 可能会耗时，因此前端要给提示
      // router.push({
      //   pathname: '/markAgents',
      //   query: { projectId },
      // });
    } catch (err) {
      alert('Error: ' + err.message);
    }
    setLoading(false);
  };
  // 用户点击“下一步”按钮时，才进入 markAgents
  const goNextStep = () => {
    router.push({
      pathname: '/markAgents',
      query: { projectId },
    });
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

      {errorMsg && <p style={{ color: 'red' }}>{errorMsg}</p>}

      {/* 如果analysis有值，就显示分析结果 */}
      {analysis && (
        <div style={{ marginTop: 20, border: '1px solid #ccc', padding: 10 }}>
          <h3>分析结果</h3>
          {/* 这里按你的后端返回结构展示 */}
          <p>建筑数量: {analysis.osmData?.buildings}</p>
          <p>道路(Edge)数量: {analysis.osmData?.roads}</p>
          {/* 如果有人口统计 */}
          {analysis.demographic && (
            <pre>{JSON.stringify(analysis.demographic, null, 2)}</pre>
          )}

          {/* 给用户一个“下一步”按钮 */}
          <button onClick={goNextStep} style={{ marginTop: 10 }}>
            下一步: 标注 Agents
          </button>
        </div>
      )}
    </div>
  );
}
