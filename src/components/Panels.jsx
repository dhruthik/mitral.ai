import Markdown from './Markdown';

export function Transcript({ entries }) {
  return <aside className="transcript card">
    <h2>Chat <span>all rooms</span></h2>
    <div className="transcript-list" aria-live="polite">
      {entries.map(entry => <div className={`entry ${entry.type || ''}`} key={entry.id} style={{ '--entry': entry.color }}>
        {entry.room && <span className="room-tag">{entry.room}</span>}
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
        <strong>{idea.title} <span>· {idea.author}</span></strong>
        <div className="note-body"><Markdown text={idea.text} /></div>
        <footer>
          <span className="note-room">{idea.carried ? '📌 carried to plenary' : idea.room}</span>
          {idea.votes > 0 && <span className="note-votes">▲ {idea.votes}</span>}
        </footer>
      </article>)}
    </div>
  </section>;
}
