import { useRef, useState } from 'react';
import Setup from './components/Setup';
import Stage from './components/Stage';
import { IdeaBoard, Transcript } from './components/Panels';
import { runMeeting } from './api';
import { makeCrew, crewFromCast } from './data';

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

export default function App() {
  const [topic, setTopic] = useState("a coffee shop that's only open at night");
  const [crew, setCrew] = useState(makeCrew);
  const [running, setRunning] = useState(false);
  const [paused, setPaused] = useState(false);
  const [entries, setEntries] = useState([]);
  const [ideas, setIdeas] = useState([]);
  const [speaker, setSpeaker] = useState(null);
  const [winner, setWinner] = useState(null);
  const [message, setMessage] = useState('');
  const [llmStatus, setLlmStatus] = useState('mock');
  const cancelled = useRef(false);
  const pausedRef = useRef(false);
  const skipping = useRef(false);
  const addEntry = entry => setEntries(current => [...current, { id: id(), ...entry }]);

  async function start() {
    const cleanTopic = topic.trim() || 'a delightful new community space';
    setTopic(cleanTopic); setRunning(true); setPaused(false); pausedRef.current = false; skipping.current = false;
    setWinner(null); setIdeas([]); setEntries([]); setSpeaker(null);
    cancelled.current = false;
    addEntry({ type: 'system', text: `🧬 Convening a panel for “${cleanTopic}”…` });

    let meeting;
    try {
      meeting = await runMeeting(cleanTopic, { n: 4 });
    } catch (error) {
      addEntry({ type: 'system', text: `⚠️ Could not reach the meeting server: ${error.message}. Is the API running on :8000?` });
      return;
    }
    if (cancelled.current) return;
    setLlmStatus(meeting.mode === 'llm' ? 'connected' : 'mock');
    const cast = crewFromCast(meeting.cast);
    setCrew(cast);
    addEntry({ type: 'system', text: `🎭 ${cast.map(a => a.name).join(', ')} take the stage. ${meeting.turns} turns over ${meeting.rounds} rounds ahead.` });
    playback(meeting, cast);
  }

  async function playback(meeting, cast) {
    const byName = Object.fromEntries(cast.map(agent => [agent.name, agent]));
    for (const event of meeting.events) {
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
        if (agent) setCrew(current => current.map(a => a.id === agent.id ? { ...a, room: event.room } : a));
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
      case 'session_closed': {
        if (data.answer) setWinner(data.answer);
        addEntry({ type: 'system', text: data.answer ? `🏛 The session closes — ${data.answer} is the panel's answer.` : '🏛 The session closes without an agreed answer.' });
        setSpeaker(null);
        break;
      }
      default:
        break;
    }
  }

  function interject(event) {
    event.preventDefault();
    const text = message.trim();
    if (!text) return;
    addEntry({ who: 'You', text, type: 'user' });
    setMessage('');
    const mentioned = crew.find(agent => text.toLowerCase().includes(`@${agent.name.toLowerCase()}`));
    const responder = mentioned || crew[Math.floor(Math.random() * crew.length)];
    setTimeout(() => addEntry({ who: responder.name, text: `Good steer. I’m folding “${text.replace(/^@\w+\s*/, '')}” into our next pass.`, room: roomLabel(responder.room), color: responder.color }), 450);
  }

  return <>
    <div className="app-shell">
      <header><div className="logo">BRAINSTORM STAGE<span>_</span></div><p>One stage, many ways of thinking.</p></header>
      {!running ? <Setup topic={topic} setTopic={setTopic} crew={crew} reroll={() => setCrew(makeCrew())} start={start} /> : <main className="session">
        <div className="topic-chip"><small>TOPIC</small>{topic}<span className={`api-state ${llmStatus}`}>{llmStatus === 'connected' ? 'LLM panel' : 'demo panel'}</span></div>
        <div className="workspace"><Stage crew={crew} activeSpeaker={speaker} /><Transcript entries={entries} /></div>
        <IdeaBoard ideas={ideas} winner={winner} />
      </main>}
    </div>
    {running && <footer className="dock"><div className="dock-inner">
      <div className="controls">
        <button className="button secondary" onClick={() => setPaused(value => { pausedRef.current = !value; return !value; })}>{paused ? '▶ Resume' : '⏸ Pause'}</button>
        <button className="button secondary" onClick={() => { skipping.current = true; pausedRef.current = false; setPaused(false); }}>⏭ Skip to verdict</button>
      </div>
      <form onSubmit={interject}><input value={message} onChange={event => setMessage(event.target.value)} placeholder="Jump in… @mention any agent" aria-label="Message the group" /><button className="button">Say it</button></form>
    </div></footer>}
  </>;
}
