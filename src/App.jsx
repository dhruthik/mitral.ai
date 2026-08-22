import { useRef, useState } from 'react';
import Setup from './components/Setup';
import Stage from './components/Stage';
import { IdeaBoard, Transcript } from './components/Panels';
import { streamMeeting, replyAs } from './api';
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

export default function App() {
  const [topic, setTopic] = useState("a coffee shop that's only open at night");
  const [panellists, setPanellists] = useState(4);
  const [mode, setMode] = useState('grounded');
  const [crew, setCrew] = useState([]);
  const [phase, setPhase] = useState('setup'); // setup | casting | running
  const [paused, setPaused] = useState(false);
  const [entries, setEntries] = useState([]);
  const [ideas, setIdeas] = useState([]);
  const [speaker, setSpeaker] = useState(null);
  const [bubble, setBubble] = useState(null);
  const [winner, setWinner] = useState(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const [model, setModel] = useState('');
  const session = useRef(null);
  const cancelled = useRef(false);
  const pausedRef = useRef(false);
  const skipping = useRef(false);
  const request = useRef(null);
  const addEntry = entry => setEntries(current => [...current, { id: id(), ...entry }]);

  async function start() {
    const cleanTopic = topic.trim() || 'a delightful new community space';
    setTopic(cleanTopic); setPhase('running'); setError('');
    setPaused(false); pausedRef.current = false; skipping.current = false;
    setWinner(null); setIdeas([]); setEntries([]); setCrew([]); setSpeaker(null); setBubble(null);
    cancelled.current = false;
    request.current?.abort();
    request.current = new AbortController();
    const byName = {};
    session.current = { agents: [] };
    setModel('assembling panel…');
    addEntry({ type: 'system', text: '🎭 The stage is open. Panellists will appear as they are created.' });

    let data;
    try {
      data = await streamMeeting(cleanTopic, { panellists, mode }, {
        meta: update => setModel(update.engine === 'llm' ? update.model : 'offline demo'),
        agent: update => {
          const agent = decorateAgents([update.agent])[0];
          byName[agent.name] = agent;
          session.current.agents.push(update.agent);
          setCrew(current => [...current, agent]);
          addEntry({ type: 'system', text: `✦ ${agent.name} joins the panel — ${agent.role}.` });
        },
        event: async update => {
          while (pausedRef.current && !cancelled.current) await wait(200);
          if (cancelled.current) return;
          applyEvent(update.event, byName);
          if (!skipping.current) await wait(DELAYS[update.event.kind] ?? 500);
        },
      }, request.current.signal);
    } catch (exception) {
      if (exception.name === 'AbortError') return;
      if (!cancelled.current) { setError(exception.message); setPhase('setup'); }
      return;
    }
    if (cancelled.current) return;

    session.current = data;
    setSpeaker(null); setBubble(null);
  }

  function applyEvent(event, byName) {
    const agent = byName[event.agent];
    const room = roomLabel(event.room);
    const data = event.data || {};
    switch (event.kind) {
      case 'spoke':
        setSpeaker(agent?.id ?? null);
        setBubble(agent ? { agent: agent.id, text: data.text, type: 'speech' } : null);
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
        setBubble(agent ? { agent: agent.id, text: `▲ ${data.proposal_id}`, type: 'vote' } : null);
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
        setBubble(null);
        break;
      default:
        break;
    }
  }

  // The whole run as plain text, for pasting into another model to judge the
  // output. Entries are already in order, so this is just a re-render of them
  // plus the context the transcript itself never spells out.
  function transcriptText() {
    const lines = [
      `TOPIC: ${topic}`,
      `MODE: ${mode} · ${crew.length} panellists · ${model}`,
      '',
      'PANEL',
      ...(crew.length ? crew.map(agent => `- ${agent.name} — ${agent.role} [${agent.cognition}]`) : ['(none yet)']),
      '',
      'ACTIVITY',
      ...entries.map(entry => {
        const room = entry.room ? `[${entry.room}] ` : '';
        return entry.who ? `${room}${entry.who}: ${entry.text}` : `${room}${entry.text}`;
      }),
    ];
    if (ideas.length) {
      lines.push('', 'PROPOSALS');
      for (const idea of ideas) {
        lines.push(`- ${idea.pid} “${idea.title}” — ${idea.author} · ▲${idea.votes}${winner === idea.pid ? ' · WINNER' : ''}`);
        lines.push(`  ${idea.text}`);
      }
    }
    return lines.join('\n');
  }

  async function copyTranscript() {
    const text = transcriptText();
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      // Clipboard API is unavailable outside secure contexts; fall back to the
      // old execCommand trick rather than silently doing nothing.
      const field = document.createElement('textarea');
      field.value = text;
      field.style.position = 'fixed';
      field.style.opacity = '0';
      document.body.appendChild(field);
      field.select();
      document.execCommand('copy');
      field.remove();
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
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
    setBubble({ agent: responder.id, text: '…', type: 'speech' });
    try {
      const { text: answer } = await replyAs(topic, responder.persona, text.replace(/^@\w+\s*/, ''));
      setBubble({ agent: responder.id, text: answer, type: 'speech' });
      addEntry({ who: responder.name, text: answer, room: roomLabel(responder.room), color: responder.color });
    } catch (exception) {
      addEntry({ type: 'system', text: `⚠️ ${responder.name} couldn't answer: ${exception.message}` });
    } finally {
      setSpeaker(null);
    }
  }

  function leave() {
    cancelled.current = true; request.current?.abort(); session.current = null;
    setPhase('setup'); setSpeaker(null); setBubble(null);
  }

  return <>
    <div className="app-shell">
      <header><div className="logo">BRAINSTORM STAGE<span>_</span></div><p>One stage, many ways of thinking.</p></header>
      {phase === 'setup' && <Setup {...{ topic, setTopic, panellists, setPanellists, mode, setMode, start, error }} />}
      {phase === 'running' && <main className="session">
        <div className="topic-chip"><small>TOPIC</small>{topic}<span className="api-state connected">{model}</span></div>
        <div className="workspace"><Stage crew={crew} activeSpeaker={speaker} bubble={bubble} /><Transcript entries={entries} onCopy={copyTranscript} copied={copied} /></div>
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
