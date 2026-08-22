import { useRef, useState } from 'react';
import Setup from './components/Setup';
import Stage from './components/Stage';
import { IdeaBoard, Transcript } from './components/Panels';
import { startSession, replyAs, addPanellist } from './api';

const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const id = () => crypto.randomUUID();

export default function App() {
  const [topic, setTopic] = useState("a coffee shop that's only open at night");
  const [panellists, setPanellists] = useState(5);
  const [mode, setMode] = useState('grounded');
  const [crew, setCrew] = useState([]);
  const [phase, setPhase] = useState('setup'); // setup | casting | running
  const [paused, setPaused] = useState(false);
  const [entries, setEntries] = useState([]);
  const [ideas, setIdeas] = useState([]);
  const [speaker, setSpeaker] = useState(null);
  const [winner, setWinner] = useState(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [selected, setSelected] = useState(null);
  const [adding, setAdding] = useState(false);
  const [model, setModel] = useState('');
  const session = useRef(null);
  const cancelled = useRef(false);
  const pausedRef = useRef(false);
  const addEntry = entry => setEntries(current => [...current, { id: id(), ...entry }]);

  async function start() {
    const cleanTopic = topic.trim() || 'a delightful new community space';
    setTopic(cleanTopic); setPhase('casting'); setError('');
    setPaused(false); pausedRef.current = false;
    setWinner(null); setIdeas([]); setEntries([]); setCrew([]); setSelected(null);
    cancelled.current = false;

    let data;
    try {
      data = await startSession(cleanTopic, { panellists, mode });
    } catch (exception) {
      if (!cancelled.current) { setError(exception.message); setPhase('setup'); }
      return;
    }
    if (cancelled.current) return;

    session.current = data;
    setModel(data.model);
    setCrew(data.agents.map(agent => ({ ...agent, room: 'dream' })));
    setPhase('running');
    runSession(data);
  }

  async function runSession(data) {
    const byId = Object.fromEntries(data.agents.map(agent => [agent.id, agent]));
    const beats = [
      ...data.pitches.map(pitch => ({
        agent: byId[pitch.agent], room: 'DREAM', text: pitch.pitch, idea: pitch.idea,
      })),
      { agent: byId[data.deliberation.plan.agent], room: 'PLAN', text: data.deliberation.plan.text },
      { agent: byId[data.deliberation.test.agent], room: 'TEST', text: data.deliberation.test.text },
    ];

    addEntry({ type: 'system', text: `🧬 ${data.agents.length} panellists convened on “${data.topic}”.` });
    addEntry({ type: 'system', text: '🚪 Dream it, plan it, break it, then decide together.' });

    for (let index = 0; index < beats.length; index++) {
      while (pausedRef.current && !cancelled.current) await wait(200);
      if (cancelled.current) return;
      const beat = beats[index];
      if (beat.room === 'PLAN') setCrew(current => current.map((a, i) => ({ ...a, room: i % 2 ? 'test' : 'plan' })));
      setSpeaker(beat.agent.id);
      await wait(550);
      addEntry({ who: beat.agent.name, text: beat.text, room: beat.room, color: beat.agent.color });
      if (beat.idea) setIdeas(current => [...current, {
        id: beat.agent.id, text: beat.idea, author: beat.agent.name, room: beat.room, color: beat.agent.color,
      }]);
      await wait(900);
    }
    setSpeaker(null);
  }

  async function addSomeone() {
    const data = session.current;
    if (!data || adding) return;
    setAdding(true);
    try {
      const { agent, pitch } = await addPanellist(topic, {
        mode,
        cast: data.agents.map(a => a.persona),
        pitches: data.pitches,
      });
      // Keep the session in step so the quorum and @mentions know about them.
      data.agents = [...data.agents, agent];
      data.pitches = [...data.pitches, pitch];
      setCrew(current => [...current, { ...agent, room: 'dream' }]);
      addEntry({ who: agent.name, text: pitch.pitch, room: 'DREAM', color: agent.color });
      setIdeas(current => [...current, {
        id: agent.id, text: pitch.idea, author: agent.name, room: 'DREAM', color: agent.color,
      }]);
    } catch (exception) {
      addEntry({ type: 'system', text: `⚠️ Couldn't cast anyone new: ${exception.message}` });
    } finally {
      setAdding(false);
    }
  }

  function callQuorum() {
    const data = session.current;
    if (!data) return;
    setCrew(current => current.map(agent => ({ ...agent, room: 'vote' })));
    const { agent, why } = data.deliberation.winner;
    setWinner(agent);
    const chosen = data.agents.find(a => a.id === agent);
    addEntry({ type: 'system', text: `🏛 The Quorum backs ${chosen?.name ?? 'the leading idea'}: ${why}` });
  }

  async function interject(event) {
    event.preventDefault();
    const text = message.trim();
    if (!text || !session.current) return;
    addEntry({ who: 'You', text, type: 'user' });
    setMessage('');
    // Everyone is "The Something", so match on the noun, not the first word.
    const mentioned = crew.find(agent => {
      const words = agent.name.toLowerCase().split(' ');
      return text.toLowerCase().includes(`@${words[words.length - 1]}`);
    });
    const responder = mentioned || crew[Math.floor(Math.random() * crew.length)];
    setSpeaker(responder.id);
    try {
      const { text: answer } = await replyAs(topic, responder.persona, text.replace(/^@\w+\s*/, ''));
      addEntry({ who: responder.name, text: answer, room: responder.room.toUpperCase(), color: responder.color });
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
      {phase === 'setup' && <Setup {...{ topic, setTopic, panellists, setPanellists, mode, setMode, start, error }} />}
      {phase === 'casting' && <main className="setup card">
        <p className="eyebrow">Casting the panel</p>
        <h1>Mistral is writing your panellists…</h1>
        <p className="intro">Every panellist, their opening idea, and the argument that follows is generated fresh. It takes a minute.</p>
        <button className="button secondary" onClick={leave}>Cancel</button>
      </main>}
      {phase === 'running' && <main className="session">
        <div className="topic-chip"><small>TOPIC</small>{topic}<span className="api-state connected">{model}</span></div>
        <div className="workspace"><Stage crew={crew} activeSpeaker={speaker} selected={selected} onSelect={setSelected} onAdd={addSomeone} adding={adding} /><Transcript entries={entries} /></div>
        <IdeaBoard ideas={ideas} winner={winner} />
      </main>}
    </div>
    {phase === 'running' && <footer className="dock"><div className="dock-inner">
      <div className="controls"><button className="button secondary" onClick={() => setPaused(value => { pausedRef.current = !value; return !value; })}>{paused ? '▶ Resume' : '⏸ Pause'}</button><button className="button secondary" onClick={callQuorum}>🏛 Call the quorum</button><button className="button secondary" onClick={leave}>✕ New session</button></div>
      <form onSubmit={interject}><input value={message} onChange={event => setMessage(event.target.value)} placeholder="Jump in… @mention any agent" aria-label="Message the group" /><button className="button">Say it</button></form>
    </div></footer>}
  </>;
}
