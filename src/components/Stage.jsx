import Avatar from './Avatar';

export default function Stage({ crew, activeSpeaker }) {
  return <section className="stage card" aria-label="Brainstorm stage">
    <div className="stage-heading">
      <span className="stage-light" />
      <h2>Live brainstorm</h2>
      <small>Dream · Plan · Test · Decide</small>
    </div>
    <div className="stage-cast">
      {crew.map(agent => <Avatar key={agent.id} agent={agent} speaking={activeSpeaker === agent.id} />)}
    </div>
    <div className="you">YOU</div>
  </section>;
}
