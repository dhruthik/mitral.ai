// The generator writes far more of a person than the stage can show — a whole
// background, how they argue, what they refuse to let slide. This is where you
// get to read it.
const METERS = [
  ['Risk appetite', 'risk'],
  ['Abstraction', 'abstraction'],
  ['Forcefulness', 'dominance'],
];

export default function Profile({ agent, onClose }) {
  const persona = agent.persona;
  const t = persona?.traits;
  const wild = t?.mode === 'wild';
  return <aside className="profile" style={{ '--agent': agent.color }}>
    <header>
      <div className="sprite" aria-hidden="true"><span>{agent.glyph}</span></div>
      <div className="profile-name"><h3>{agent.name}</h3><p>{agent.role}</p></div>
      <button type="button" onClick={onClose} aria-label="Close profile">✕</button>
    </header>

    <p className="profile-bio">{agent.bio}</p>

    {persona && <div className="profile-rows">
      <p><span>Argues by</span>{persona.how_they_argue}</p>
      <p><span>Can't stand</span>{persona.pet_peeve}</p>
      <p><span>Opens with</span>{persona.opening_move}</p>
    </div>}

    {t && <div className="profile-foot">
      <ul className="profile-facts">
        <li>Thinks <b>{t.cognition}</b> — {t.cognition_desc}</li>
        <li>{wild ? <>Drags everything back to <b>{t.lens}</b></> : <>Argues on behalf of <b>{t.lens}</b></>}</li>
        <li>{wild ? <>Talks like a <b>{t.voice}</b></> : <>In the room, <b>{t.voice}</b></>}</li>
      </ul>
      <dl className="profile-meters">
        {METERS.map(([label, key]) => <div key={key}>
          <dt>{label}</dt>
          <dd><i style={{ '--fill': `${t[key] * 20}%` }} /><b>{t[key]}/5</b></dd>
        </div>)}
      </dl>
    </div>}
  </aside>;
}
