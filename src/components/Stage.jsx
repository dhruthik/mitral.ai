import Avatar from './Avatar';
import Profile from './Profile';

export default function Stage({ crew, activeSpeaker, selected, onSelect, onAdd, adding }) {
  const shown = crew.find(agent => agent.id === selected);
  return <section className="stage card" aria-label="Brainstorm stage">
    <div className="stage-heading">
      <span className="stage-light" />
      <h2>Live brainstorm</h2>
      <small>Dream · Plan · Test · Decide</small>
      <p className="stage-hint">Click anyone to read who they are · jump in at the bottom · call the quorum when you've heard enough</p>
    </div>
    <div className="stage-cast">
      {crew.map(agent => <Avatar
        key={agent.id}
        agent={agent}
        speaking={activeSpeaker === agent.id}
        selected={selected === agent.id}
        onSelect={() => onSelect(selected === agent.id ? null : agent.id)}
      />)}
      <button type="button" className="avatar add" onClick={onAdd} disabled={adding} title="Add another panellist">
        <div className="sprite" aria-hidden="true"><span>{adding ? '…' : '+'}</span></div>
        <strong>{adding ? 'Casting…' : 'Add someone'}</strong>
        <small>{adding ? 'Mistral is writing them' : 'A new way of thinking'}</small>
      </button>
    </div>
    {shown && <Profile agent={shown} onClose={() => onSelect(null)} />}
    {!shown && <div className="you">YOU</div>}
  </section>;
}
