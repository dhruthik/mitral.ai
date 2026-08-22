import { useEffect, useRef, useState } from 'react';
import Setup from './components/Setup';
import Stage from './components/Stage';
import { IdeaBoard, Transcript } from './components/Panels';
import { runMeeting, replyAs } from './api';
import { decorateAgents } from './data';

const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const id = () => crypto.randomUUID();

// Playback pacing per event kind (ms). The backend returns the whole meeting
// at once; the theater is entirely client-side.
const DELAYS = {
  spoke: 1400, proposed: 1300, upvoted: 550, invited: 750, joined: 850,
  returned: 700, vote_called: 950, vote_passed: 1100, vote_failed: 950,
  done: 500, kicked: 900, room_closed: 850, session_closed: 900,
};

const roomLabel = room => room === 'plenary' ? 'PLENARY' : room.replace('room-', 'ROOM ').toUpperCase();

// The casting call is a full minute of sequential Mistral calls, so the screen
// rotates through these rather than staring at one line the whole time.
const CASTING_LINES = [
  'Rounding up strangers with opinions…',
  'Handing out contradictory worldviews…',
  'Teaching someone to disagree politely…',
  'Assigning one person far too much confidence…',
  'Checking nobody brought the same idea twice…',
  'Pouring the coffee, dimming the lights…',
  'Writing bios nobody will fact-check…',
  'Seating the quiet one next to the loud one…',
];

function CastingHeadline() {
  const [index, setIndex] = useState(0);
  useEffect(() => {
    const timer = setInterval(() => setIndex(current => (current + 1) % CASTING_LINES.length), 3200);
    return () => clearInterval(timer);
  }, []);
  return <h1 key={index} className="casting-line">{CASTING_LINES[index]}</h1>;
}

export default function App() {
  const [topic, setTopic] = useState("a coffee shop that's only open at night");
  const [panellists, setPanellists] = useState(4);
  const [mode, setMode] = useState('grounded');
  const [depth, setDepth] = useState('fast');
  const [crew, setCrew] = useState([]);
  const [phase, setPhase] = useState('setup'); // setup | casting | running
  const [paused, setPaused] = useState(false);
  const [entries, setEntries] = useState([]);
  const [ideas, setIdeas] = useState([]);
  const [speaker, setSpeaker] = useState(null);
  const [winner, setWinner] = useState(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [model, setModel] = useState('');
  const session = useRef(null);
  const cancelled = useRef(false);
  const pausedRef = useRef(false);
  const skipping = useRef(false);
  const addEntry = entry => setEntries(current => [...current, { id: id(), ...entry }]);

  async function start() {
    const cleanTopic = topic.trim() || 'a delightful new community space';
    setTopic(cleanTopic); setPhase('casting'); setError('');
    setPaused(false); pausedRef.current = false; skipping.current = false;
    setWinner(null); setIdeas([]); setEntries([]); setCrew([]); setSpeaker(null);
    cancelled.current = false;

    let data;
    try {
      data = await runMeeting(cleanTopic, { panellists, mode, depth });
    } catch (exception) {
      if (!cancelled.current) { setError(exception.message); setPhase('setup'); }
      return;
    }
    if (cancelled.current) return;

    session.current = data;
    const engineLabel = data.engine === 'llm' ? data.model : 'offline demo';
    const depthLabel = data.depth === 'deep' ? 'deep dive' : 'fast take';
    setModel(`${engineLabel} · ${depthLabel}`);
    const agents = decorateAgents(data.agents);
    setCrew(agents);
    setPhase('running');
    addEntry({ type: 'system', text: `🎭 ${agents.map(a => a.name).join(', ')} take the stage — ${data.turns} turns over ${data.rounds} rounds.` });
    playback(data, agents);
  }

  async function playback(data, agents) {
    const byName = Object.fromEntries(agents.map(agent => [agent.name, agent]));
    for (const event of data.events) {
      while (pausedRef.current && !cancelled.current) await wait(200);
      if (cancelled.current) return;
      applyEvent(event, byName);
      if (!skipping.current) await wait(DELAYS[event.kind] ?? 500);
    }
    setSpeaker(null);
  }

  function applyEvent(event, byName) {
    const agent = byName[event.agent];
    const room = roomLabel(event.room);
    const data = event.data || {};
    switch (event.kind) {
      case 'spoke':
        setSpeaker(agent?.id ?? null);
        addEntry({ who: event.agent, text: data.text, room, color: agent?.color });
        break;
      case 'proposed':
        if (data.carried_from) {
          setIdeas(current => current.map(idea => idea.pid === data.proposal_id ? { ...idea, room, carried: true } : idea));
          addEntry({ type: 'system', text: `📌 ${event.agent} carries “${data.title}” back to the plenary.` });
        } else {
          setIdeas(current => [...current, { id: id(), pid: data.proposal_id, title: data.title, text: data.body, author: event.agent, room, votes: 0, color: agent?.color }]);
          addEntry({ type: 'action', text: `📝 ${event.agent} pins ${data.proposal_id}: “${data.title}”`, room });
        }
        break;
      case 'upvoted':
        setIdeas(current => current.map(idea => idea.pid === data.proposal_id ? { ...idea, votes: idea.votes + 1 } : idea));
        addEntry({ type: 'action', text: `▲ ${event.agent} upvotes ${data.proposal_id}`, room });
        break;
      case 'joined':
      case 'returned':
        if (agent) {
          const movers = new Set(data.group || [event.agent]);
          setCrew(current => current.map(a => movers.has(a.name) ? { ...a, room: event.room } : a));
        }
        addEntry({ type: 'action', text: `🚪 ${event.agent} ${event.kind === 'joined' ? 'heads to' : 'returns to'} ${room}`, room });
        break;
      case 'invited':
        addEntry({ type: 'action', text: `✉️ ${event.agent} slips an invitation to ${data.target} — “meet me in ${roomLabel(data.room)}”`, room });
        break;
      case 'vote_called':
        addEntry({ type: 'system', text: `🗳 ${event.agent} calls a vote on ${data.proposal_id} in ${room}.` });
        break;
      case 'vote_passed':
        addEntry({ type: 'system', text: `✅ Vote passes ${data.yes}/${data.of} in ${room}.` });
        break;
      case 'vote_failed':
        addEntry({ type: 'system', text: `❌ Vote fails ${data.yes}/${data.of} in ${room}.` });
        break;
      case 'done':
        addEntry({ type: 'action', text: `🤐 ${event.agent} has nothing further`, room });
        break;
      case 'kicked':
        addEntry({ type: 'system', text: `💥 ${event.agent} is voted out of ${room}.` });
        break;
      case 'room_closed':
        addEntry({ type: 'system', text: `🔒 ${room} wraps up.` });
        break;
      case 'session_closed':
        if (data.answer) setWinner(data.answer);
        addEntry({ type: 'system', text: data.answer ? `🏛 The session closes — ${data.answer} is the panel's answer.` : '🏛 The session closes without an agreed answer.' });
        setSpeaker(null);
        break;
      default:
        break;
    }
  }

  async function interject(event) {
    event.preventDefault();
    const text = message.trim();
    if (!text || !session.current) return;
    addEntry({ who: 'You', text, type: 'user' });
    setMessage('');
    const mentioned = crew.find(agent => text.toLowerCase().includes(`@${agent.name.split(' ')[0].toLowerCase()}`));
    const responder = mentioned || crew[Math.floor(Math.random() * crew.length)];
    setSpeaker(responder.id);
    try {
      const { text: answer } = await replyAs(topic, responder.persona, text.replace(/^@\w+\s*/, ''));
      addEntry({ who: responder.name, text: answer, room: roomLabel(responder.room), color: responder.color });
    } catch (exception) {
      addEntry({ type: 'system', text: `⚠️ ${responder.name} couldn't answer: ${exception.message}` });
    } finally {
      setSpeaker(null);
    }
  }

  function leave() {
    cancelled.current = true; session.current = null;
    setPhase('setup'); setSpeaker(null);
  }

  return <>
    <div className="app-shell">
      <header><div className="logo">BRAINSTORM STAGE<span>_</span></div><p>One stage, many ways of thinking.</p></header>
      {phase === 'setup' && <Setup {...{ topic, setTopic, panellists, setPanellists, mode, setMode, depth, setDepth, start, error }} />}
      {phase === 'casting' && <main className="setup card">
        <p className="eyebrow">Casting the panel</p>
        <CastingHeadline />
        <p className="intro">The panel, its proposals, and every vote are decided before the curtain rises — then played back live on the stage.</p>
        <button className="button secondary" onClick={leave}>Cancel</button>
      </main>}
      {phase === 'running' && <main className="session">
        <div className="topic-chip"><small>TOPIC</small>{topic}<span className="api-state connected">{model}</span></div>
        <div className="workspace"><Stage crew={crew} activeSpeaker={speaker} /><Transcript entries={entries} /></div>
        <IdeaBoard ideas={ideas} winner={winner} />
      </main>}
    </div>
    {phase === 'running' && <footer className="dock"><div className="dock-inner">
      <div className="controls">
        <button className="button secondary" onClick={() => setPaused(value => { pausedRef.current = !value; return !value; })}>{paused ? '▶ Resume' : '⏸ Pause'}</button>
        <button className="button secondary" onClick={() => { skipping.current = true; pausedRef.current = false; setPaused(false); }}>⏭ Skip to verdict</button>
        <button className="button secondary" onClick={leave}>✕ New session</button>
      </div>
      <form onSubmit={interject}><input value={message} onChange={event => setMessage(event.target.value)} placeholder="Jump in… @mention any agent" aria-label="Message the group" /><button className="button">Say it</button></form>
    </div></footer>}
  </>;
}
