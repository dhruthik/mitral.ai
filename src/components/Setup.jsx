import Avatar from './Avatar';

export default function Setup({ topic, setTopic, crew, reroll, start }) {
  return <main className="setup card">
    <p className="eyebrow">One stage for every way of thinking</p>
    <h1>What should the gang brainstorm?</h1>
    <p className="intro">Dream freely, make an idea practical, test its weak spots, and converge on a decision—all without leaving the stage.</p>
    <form className="topic-form" onSubmit={(event) => { event.preventDefault(); start(); }}>
      <input value={topic} onChange={(event) => setTopic(event.target.value)} aria-label="Brainstorm topic" />
      <button className="button" type="submit">Spawn the session</button>
    </form>
    <div className="crew-preview">{crew.map(agent => <Avatar agent={agent} compact key={agent.id} />)}</div>
    <button className="button secondary" onClick={reroll}>🎲 Re-roll the crew</button>
  </main>;
}
