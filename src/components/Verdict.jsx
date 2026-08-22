import { useEffect, useRef } from 'react';
import Markdown from './Markdown';

// The panel's closing argument. Everything here is derived from events the
// client already replayed, so the modal costs no extra round trip.
export default function Verdict({ winner, milestones, ideas, topic, onClose }) {
  const closeButton = useRef(null);
  const votes = winner?.voters?.length ?? winner?.votes ?? 0;
  const ballots = milestones.filter(step => step.kind === 'vote').length;

  useEffect(() => {
    closeButton.current?.focus();
    const onKey = event => { if (event.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  return <div className="verdict-backdrop" onClick={event => { if (event.target === event.currentTarget) onClose(); }}>
    <div className="verdict card" role="dialog" aria-modal="true" aria-labelledby="verdict-title">
      <button className="verdict-close" onClick={onClose} ref={closeButton} aria-label="Close verdict">✕</button>
      <p className="eyebrow">The panel has decided</p>
      <h2 id="verdict-title">{winner ? winner.title : 'No agreed answer'}</h2>
      <p className="verdict-topic">on “{topic}”</p>

      {winner ? <>
        <div className="verdict-answer" style={{ '--note-accent': winner.color }}>
          <div className="note-body"><Markdown text={winner.text} /></div>
          <footer>
            <span>proposed by <strong>{winner.author}</strong></span>
            <span className="note-votes">▲ {votes} {votes === 1 ? 'vote' : 'votes'}</span>
          </footer>
        </div>
        {winner.voters?.length > 0 && <p className="verdict-voters">Carried by {winner.voters.join(', ')}.</p>}
      </> : <p className="verdict-voters">The plenary closed without carrying a proposal — the panel talked it out but nobody's motion took the room.</p>}

      <div className="verdict-stats">
        <div><strong>{ideas.length}</strong><small>{ideas.length === 1 ? 'proposal' : 'proposals'}</small></div>
        <div><strong>{ballots}</strong><small>{ballots === 1 ? 'vote held' : 'votes held'}</small></div>
        <div><strong>{milestones.length}</strong><small>{milestones.length === 1 ? 'turning point' : 'turning points'}</small></div>
      </div>

      <h3>How they got there</h3>
      <ol className="verdict-trail">
        {milestones.map(step => <li key={step.id} className={step.kind}>
          <span className="trail-mark" aria-hidden="true">{step.mark}</span>
          <div>
            {step.text}
            {step.room && <span className="room-tag">{step.room}</span>}
          </div>
        </li>)}
      </ol>

      <div className="verdict-actions"><button className="button" onClick={onClose}>Back to the stage</button></div>
    </div>
  </div>;
}
