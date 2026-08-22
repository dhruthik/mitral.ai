export function Transcript({ entries }) {
  return <aside className="transcript card">
    <h2>Chat <span>all rooms</span></h2>
    <div className="transcript-list" aria-live="polite">
      {entries.map(entry => <div className={`entry ${entry.type || ''}`} key={entry.id} style={{ '--entry': entry.color }}>
        {entry.room && <span className="room-tag">{entry.room}</span>}
        {entry.who && <strong>{entry.who}: </strong>}{entry.text}
      </div>)}
    </div>
  </aside>;
}

export function IdeaBoard({ ideas, winner }) {
  return <section className="board card">
    <h2>Idea board <span>{ideas.length} {ideas.length === 1 ? 'idea' : 'ideas'}</span></h2>
    <div className="idea-shelf">
      {!ideas.length && <p className="empty">Ideas from every room get pinned here…</p>}
      {ideas.map(idea => <article className={`note ${winner === idea.id ? 'winner' : ''}`} key={idea.id} style={{ '--note-accent': idea.color }}>
        <strong>{idea.author} <span>· {idea.room}</span></strong><p>{idea.text}</p>
      </article>)}
    </div>
  </section>;
}
