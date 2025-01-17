/*
用户输入或粘贴设计方案文本（MVP）
或拖拽上传简易文件（再交给后端解析）
提交后 → POST /api/upload_design_info
*/
import { useState } from 'react';
import axios from 'axios';

export default function DesignInfoPage() {
  const [description, setDescription] = useState('');
  const [mainFeature, setMainFeature] = useState('');
  const [result, setResult] = useState('');

  const handleUpload = async () => {
    try {
      const designInfo = {
        description,
        mainFeature,
      };

      const res = await axios.post('http://localhost:5000/design/upload', {
        designInfo,
      });

      setResult(JSON.stringify(res.data.processedDesign, null, 2));
    } catch (err) {
      setResult('上传失败:' + err.message);
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>设计方案信息</h2>
      <label>
        方案描述:
        <input
          type="text"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          style={{ width: '300px', marginLeft: 10 }}
        />
      </label>
      <br />
      <br />
      <label>
        主要功能:
        <input
          type="text"
          value={mainFeature}
          onChange={(e) => setMainFeature(e.target.value)}
          style={{ width: '300px', marginLeft: 10 }}
        />
      </label>
      <br />
      <br />
      <button onClick={handleUpload}>上传方案</button>

      <pre>{result}</pre>
    </div>
  );
}
