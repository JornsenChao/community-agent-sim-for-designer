export default function AgentCard({ agent, onUpdate }) {
  return (
    <div
      style={{
        border: '1px solid #ccc',
        padding: '10px',
        margin: '10px 0',
        borderRadius: 4,
      }}
    >
      <h3>{agent.id}</h3>
      <p>{agent.desc}</p>
      {onUpdate && <button onClick={onUpdate}>微调一下 (age=40 仅示例)</button>}
    </div>
  );
}
