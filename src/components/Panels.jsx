import { useEffect, useRef } from 'react';

export function Transcript({ entries }) {
  const list = useRef(null);

  useEffect(() => {
    const element = list.current;
    if (!element) return;
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    element.scrollTo({ top: element.scrollHeight, behavior: reducedMotion ? 'auto' : 'smooth' });
  }, [entries.length]);

  return <aside className="transcript card">
    <h2>Chat <span>all rooms</span></h2>
    <div ref={list} className="transcript-list" aria-live="polite">
      {entries.map(entry => <div className={`entry ${entry.type || ''}`} key={entry.id} style={{ '--entry': entry.color }}>
        {entry.room && <span className="room-tag">{entry.room}</span>}
        {entry.who && <strong>{entry.who}: </strong>}{entry.text}
      </div>)}
    </div>
  </aside>;
}

export function IdeaBoard({ ideas, winner }) {
  return <section className="board card">
    <h2>Proposal board <span>{ideas.length} {ideas.length === 1 ? 'proposal' : 'proposals'}</span></h2>
    <div className="idea-shelf">
      {!ideas.length && <p className="empty">Proposals from every room get pinned here…</p>}
      {ideas.map(idea => <article className={`note ${winner === idea.pid ? 'winner' : ''}`} key={idea.id} style={{ '--note-accent': idea.color }}>
        <strong>{idea.pid && <b className="proposal-id">{idea.pid}</b>}{idea.title} <span>· {idea.author}</span></strong>
        <p>{idea.text}</p>
        <footer>
          <span className="note-room">{idea.carried ? '📌 carried to plenary' : idea.room}</span>
          {idea.votes > 0 && <span className="note-votes">▲ {idea.votes}</span>}
        </footer>
      </article>)}
    </div>
  </section>;
}
