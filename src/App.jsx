import { useRef, useState } from 'react';
import Setup from './components/Setup';
import Stage from './components/Stage';
import { IdeaBoard, Transcript } from './components/Panels';
import { brainstormWithLlm } from './api';
import { makeCrew, mockIdeas } from './data';

const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const id = () => crypto.randomUUID();

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
  const addEntry = entry => setEntries(current => [...current, { id: id(), ...entry }]);

  async function start() {
    const cleanTopic = topic.trim() || 'a delightful new community space';
    setTopic(cleanTopic); setRunning(true); setPaused(false); pausedRef.current = false; setWinner(null); setIdeas([]); setEntries([]);
    setCrew(current => current.map(agent => ({ ...agent, room: 'dream' })));
    cancelled.current = false;
    addEntry({ type: 'system', text: `🧬 Spawning ${crew.length} agents for “${cleanTopic}”…` });
    addEntry({ type: 'system', text: '🚪 Dream it, plan it, break it, then decide together.' });

    let generated;
    try {
      const result = await brainstormWithLlm(cleanTopic, []);
      generated = result.ideas;
      setLlmStatus('connected');
    } catch {
      generated = mockIdeas(cleanTopic);
      setLlmStatus('mock');
    }
    if (cancelled.current) return;
    runSession(generated, cleanTopic);
  }

  async function runSession(generated, cleanTopic) {
    const dreamer = crew.find(a => a.role.includes('dreamer')) || crew[0];
    const skeptic = crew.find(a => a.role.includes('skeptic')) || crew[1];
    const planner = crew.find(a => a.role.includes('pragmatist')) || crew[2];
    const speakers = [dreamer, crew.find(a => a.id !== dreamer.id) || crew[1]];
    const lines = [
      [speakers[0], 'DREAM', `No criticism yet—every idea is legal. What could “${cleanTopic}” become?`],
      [speakers[0], 'DREAM', generated[0]],
      [speakers[1], 'DREAM', generated[1]],
      [planner, 'PLAN', `Let’s make the first idea testable: one small pilot, a simple landing page, and a success metric we can observe.`],
      [skeptic, 'TEST', `Stress test: who returns a second time, and what happens on a slow week? The idea needs an answer.`],
    ];
    for (let index = 0; index < lines.length; index++) {
      while (pausedRef.current && !cancelled.current) await wait(200);
      if (cancelled.current) return;
      const [agent, room, text] = lines[index];
      if (index === 3) setCrew(current => current.map((a, i) => ({ ...a, room: i % 2 ? 'test' : 'plan' })));
      setSpeaker(agent.id);
      await wait(550);
      addEntry({ who: agent.name, text, room, color: agent.color });
      if (index === 1 || index === 2) setIdeas(current => [...current, { id: id(), text, author: agent.name, room, color: agent.color }]);
      await wait(900);
    }
    setSpeaker(null);
  }

  function callQuorum() {
    setCrew(current => current.map(agent => ({ ...agent, room: 'vote' })));
    const chosen = ideas[0];
    if (chosen) setWinner(chosen.id);
    addEntry({ type: 'system', text: chosen ? `🏛 The Quorum convenes. The first concept wins the dot vote: “${chosen.text}”` : '🏛 The Quorum convenes.' });
  }

  function interject(event) {
    event.preventDefault();
    const text = message.trim();
    if (!text) return;
    addEntry({ who: 'You', text, type: 'user' });
    setMessage('');
    const mentioned = crew.find(agent => text.toLowerCase().includes(`@${agent.name.toLowerCase()}`));
    const responder = mentioned || crew[Math.floor(Math.random() * crew.length)];
    setTimeout(() => addEntry({ who: responder.name, text: `Good steer. I’m folding “${text.replace(/^@\w+\s*/, '')}” into our next pass.`, room: responder.room.toUpperCase(), color: responder.color }), 450);
  }

  return <>
    <div className="app-shell">
      <header><div className="logo">BRAINSTORM STAGE<span>_</span></div><p>One stage, many ways of thinking.</p></header>
      {!running ? <Setup topic={topic} setTopic={setTopic} crew={crew} reroll={() => setCrew(makeCrew())} start={start} /> : <main className="session">
        <div className="topic-chip"><small>TOPIC</small>{topic}<span className={`api-state ${llmStatus}`}>{llmStatus === 'connected' ? 'LLM connected' : 'demo dialogue'}</span></div>
        <div className="workspace"><Stage crew={crew} activeSpeaker={speaker} /><Transcript entries={entries} /></div>
        <IdeaBoard ideas={ideas} winner={winner} />
      </main>}
    </div>
    {running && <footer className="dock"><div className="dock-inner">
      <div className="controls"><button className="button secondary" onClick={() => setPaused(value => { pausedRef.current = !value; return !value; })}>{paused ? '▶ Resume' : '⏸ Pause'}</button><button className="button secondary" onClick={callQuorum}>🏛 Call the quorum</button></div>
      <form onSubmit={interject}><input value={message} onChange={event => setMessage(event.target.value)} placeholder="Jump in… @mention any agent" aria-label="Message the group" /><button className="button">Say it</button></form>
    </div></footer>}
  </>;
}
