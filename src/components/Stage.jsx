import Avatar from './Avatar';
import StageDecor from './StageDecor';

const ROOMS = [
  ['plenary', 'Plenary'],
  ['room-a', 'Room A'],
  ['room-b', 'Room B'],
  ['room-c', 'Room C'],
];

export default function Stage({ crew, activeSpeaker, bubble, focusRoom, onFocusRoom }) {
  return <section className="stage card" aria-label="Brainstorm stage">
    <StageDecor />
    <div className="stage-heading">
      <span className="stage-light" />
      <h2>Live brainstorm</h2>
      <small>{focusRoom ? 'Reading one room — click it again for everything' : 'Click a room to read only what was said in it'}</small>
    </div>
    <div className="rooms">
      {ROOMS.map(([roomId, label]) => {
        const here = crew.filter(agent => agent.room === roomId);
        const focused = focusRoom === roomId;
        return <div
          key={roomId}
          role="button"
          tabIndex={0}
          aria-pressed={focused}
          aria-label={`Read the ${label} transcript`}
          onClick={() => onFocusRoom(focused ? null : roomId)}
          onKeyDown={event => {
            if (event.key !== 'Enter' && event.key !== ' ') return;
            event.preventDefault();
            onFocusRoom(focused ? null : roomId);
          }}
          className={`room ${roomId} ${here.length ? '' : 'empty'} ${focused ? 'focused' : ''} ${focusRoom && !focused ? 'dimmed' : ''}`}
        >
          <h3>{label}{focused && <span className="room-reading">reading</span>}</h3>
          <div className="table" aria-hidden="true" />
          <div className="room-cast">
            {here.map(agent => <Avatar key={agent.id} agent={agent} speaking={activeSpeaker === agent.id} bubble={bubble?.agent === agent.id ? bubble : null} />)}
          </div>
        </div>;
      })}
    </div>
  </section>;
}
