import { useRef, useState } from 'react';
import { transcribeAudio } from '../api';

export default function Setup({ topic, setTopic, panellists, setPanellists, mode, setMode, depth, setDepth, start, error }) {
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [micError, setMicError] = useState('');
  const recorder = useRef(null);
  const chunks = useRef([]);

  async function toggleMic() {
    setMicError('');
    if (recording) {
      recorder.current?.stop();
      return;
    }
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setMicError("Couldn't access your microphone — check the browser's permission prompt.");
      return;
    }
    const rec = new MediaRecorder(stream);
    chunks.current = [];
    rec.ondataavailable = event => { if (event.data.size > 0) chunks.current.push(event.data); };
    rec.onstop = async () => {
      stream.getTracks().forEach(track => track.stop());
      setRecording(false);
      const blob = new Blob(chunks.current, { type: 'audio/webm' });
      setTranscribing(true);
      try {
        const { text } = await transcribeAudio(blob);
        if (text) setTopic(text);
      } catch (exception) {
        setMicError(exception.message);
      } finally {
        setTranscribing(false);
      }
    };
    recorder.current = rec;
    rec.start();
    setRecording(true);
  }

  return <main className="setup card">
    <p className="eyebrow">One stage for every way of thinking</p>
    <h1>What should the gang brainstorm?</h1>
    <p className="intro">Dream freely, make an idea practical, test its weak spots, and converge on a decision—all without leaving the stage.</p>
    <form className="topic-form" onSubmit={(event) => { event.preventDefault(); start(); }}>
      <input value={topic} onChange={(event) => setTopic(event.target.value)} aria-label="Brainstorm topic" />
      <button
        type="button"
        className={`button secondary mic-button${recording ? ' recording' : ''}`}
        onClick={toggleMic}
        disabled={transcribing}
        aria-label={recording ? 'Stop recording' : 'Speak your topic'}
        title={recording ? 'Stop recording' : 'Speak your topic'}
      >
        {transcribing ? '…' : recording ? '⏹' : '🎤'}
      </button>
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
      <label>Depth
        <select value={depth} onChange={event => setDepth(event.target.value)}>
          <option value="fast">⚡ Fast take</option>
          <option value="deep">🔬 Deep dive</option>
        </select>
      </label>
    </div>
    <p className="intro">The panel is written from scratch by Mistral every run—no two sessions have the same people in the room.</p>
    {(error || micError) && <p className="setup-error" role="alert">⚠️ {error || micError}</p>}
  </main>;
}
