export default function Setup({ topic, setTopic, panellists, setPanellists, mode, setMode, start, error }) {
  return <main className="setup card">
    <p className="eyebrow">One stage for every way of thinking</p>
    <h1>What should the gang brainstorm?</h1>
    <p className="intro">Dream freely, make an idea practical, test its weak spots, and converge on a decision—all without leaving the stage.</p>
    <form className="topic-form" onSubmit={(event) => { event.preventDefault(); start(); }}>
      <input value={topic} onChange={(event) => setTopic(event.target.value)} aria-label="Brainstorm topic" />
      <button className="button" type="submit">Spawn the session</button>
    </form>
    <div className="setup-options">
      <label>Panellists
        <select value={panellists} onChange={event => setPanellists(Number(event.target.value))}>
          {[3, 4, 5, 6, 7, 8].map(n => <option key={n} value={n}>{n}</option>)}
        </select>
      </label>
      <label>Cast
        <select value={mode} onChange={event => setMode(event.target.value)}>
          <option value="grounded">Grounded colleagues</option>
          <option value="wild">Eccentric outsiders</option>
        </select>
      </label>
    </div>
    <p className="intro">The panel is written from scratch by Mistral every run—no two sessions have the same people in the room.</p>
    {error && <p className="setup-error" role="alert">⚠️ {error}</p>}
  </main>;
}
