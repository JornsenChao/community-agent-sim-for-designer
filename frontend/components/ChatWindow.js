export default function ChatWindow({ response }) {
  return (
    <div style={{ border: '1px solid #ddd', padding: 10, marginTop: 20 }}>
      <h4>Agent 回复</h4>
      <div>{response}</div>
    </div>
  );
}
