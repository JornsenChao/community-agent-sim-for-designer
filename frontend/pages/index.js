import Link from 'next/link';

export default function HomePage() {
  return (
    <div style={{ padding: 20 }}>
      <h1>多角色社区模拟 Demo (新流程)</h1>
      <ul>
        <li>
          <Link href="/createProject">1) 创建项目</Link>
        </li>
      </ul>
    </div>
  );
}
