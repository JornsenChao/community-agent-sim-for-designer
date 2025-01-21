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
      {/* <h3>{agent.id}</h3> */}
      {/* <p>{agent.desc}</p> */}
      <h3>Agent #{agent.id}</h3>
      <p>Name: {agent.name}</p>
      <p>Age: {agent.age}</p>
      {/* <p>All: {agent.all}</p> */}
      <p>Occupation: {agent.occupation}</p>
      <p>Background Story: {agent.background_story}</p>
      <p>Home (census track): {agent.home_tract}</p>
      <p>Work/School (census track): {agent.work_tract}</p>
      {onUpdate && <button onClick={onUpdate}>微调一下 (age=40 仅示例)</button>}
    </div>
  );
}
