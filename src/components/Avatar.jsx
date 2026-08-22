export default function Avatar({ agent, compact = false, speaking = false }) {
  return (
    <div className={`avatar ${compact ? 'compact' : ''} ${speaking ? 'speaking' : ''}`} style={{ '--agent': agent.color }}>
      <div className="sprite" aria-hidden="true"><span>{agent.glyph}</span></div>
      <strong>{agent.name}</strong>
      <small>{agent.role}</small>
    </div>
  );
}
