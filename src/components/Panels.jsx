import { useEffect, useRef } from 'react';
import Markdown from './Markdown';

export function Transcript({ entries, onCopy, copied, focusRoom, focusLabel, onClearFocus }) {
  const list = useRef(null);
  useEffect(() => {
    const element = list.current;
    if (!element) return;
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    element.scrollTo({ top: element.scrollHeight, behavior: reduced ? 'auto' : 'smooth' });
  }, [entries.length]);
  return <aside className="transcript card">
    <h2>{focusRoom ? focusLabel : 'Chat'} <button type="button" className="copy-log" onClick={onCopy} disabled={!entries.length}>{copied ? '✓ Copied' : '⧉ Copy log'}</button></h2>
    {focusRoom && <button type="button" className="room-filter" onClick={onClearFocus}>
      Only what was said in {focusLabel} <span>✕ all rooms</span>
    </button>}
    <div ref={list} className="transcript-list" aria-live="polite">
      {!entries.length && focusRoom && <p className="empty">Nothing has been said in {focusLabel} yet.</p>}
      {entries.map(entry => <div className={`entry ${entry.type || ''}`} key={entry.id} style={{ '--entry': entry.color }}>
        {entry.room && !focusRoom && <span className="room-tag">{entry.room}</span>}
        {entry.who && <strong>{entry.who}: </strong>}<Markdown text={entry.text} />
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
        <div className="note-body"><Markdown text={idea.text} /></div>
        <footer>
          <span className="note-room">{idea.carried ? '📌 carried to plenary' : idea.room}</span>
          {idea.votes > 0 && <span className="note-votes">▲ {idea.votes}</span>}
        </footer>
      </article>)}
    </div>
  </section>;
}
