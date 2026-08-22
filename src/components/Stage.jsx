import Avatar from './Avatar';

const ROOMS = [
  ['plenary', 'Plenary'],
  ['room-a', 'Room A'],
  ['room-b', 'Room B'],
  ['room-c', 'Room C'],
];

export default function Stage({ crew, activeSpeaker, bubble }) {
  return <section className="stage card" aria-label="Brainstorm stage">
    <div className="stage-heading">
      <span className="stage-light" />
      <h2>Live brainstorm</h2>
      <small>Speak · Propose · Split off · Vote</small>
    </div>
    <div className="rooms">
      {ROOMS.map(([roomId, label]) => {
        const here = crew.filter(agent => agent.room === roomId);
        return <div key={roomId} className={`room ${roomId} ${here.length ? '' : 'empty'}`}>
          <h3>{label}</h3>
          <div className="room-cast">
            {here.map(agent => <Avatar key={agent.id} agent={agent} speaking={activeSpeaker === agent.id} bubble={bubble?.agent === agent.id ? bubble : null} />)}
          </div>
        </div>;
      })}
    </div>
    <div className="you">YOU</div>
  </section>;
}
