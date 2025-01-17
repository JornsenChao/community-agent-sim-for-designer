import Link from 'next/link';
import { useState, useEffect } from 'react';

export default function HomePage() {
  const [projects, setProjects] = useState([]);

  // 如果你想展示已有项目列表，可以在这里向后端拉取一下
  useEffect(() => {
    // 目前后端没写获取全部项目的接口，所以这里留空
  }, []);

  return (
    <div style={{ padding: 20 }}>
      <h1>多角色社区模拟 Demo</h1>
      <p>请选择操作：</p>
      <ul>
        <li>
          <Link href="/createProject">创建新项目</Link>
        </li>
        <li>
          <Link href="/demographic">填写人口信息</Link>
        </li>
        <li>
          <Link href="/agentPreview">预览 & 微调 Agent</Link>
        </li>
      </ul>
    </div>
  );
}
