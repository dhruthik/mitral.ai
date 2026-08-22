export default function Avatar({ agent, compact = false, speaking = false, selected = false, onSelect }) {
  return (
    <button
      type="button"
      className={`avatar ${compact ? 'compact' : ''} ${speaking ? 'speaking' : ''} ${selected ? 'selected' : ''}`}
      style={{ '--agent': agent.color }}
      onClick={() => onSelect?.(agent)}
      aria-pressed={selected}
      title={`Read ${agent.name}'s profile`}
    >
      <div className="sprite" aria-hidden="true"><span>{agent.glyph}</span></div>
      <strong>{agent.name}</strong>
      <small>{agent.role}</small>
    </button>
  );
}
