const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function post(path, body, signal) {
  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal,
    });
  } catch (exception) {
    // Browsers report a refused connection as a bare "Load failed" / "Failed to
    // fetch", which tells you nothing. Almost always the backend just isn't up.
    if (exception.name === 'AbortError') throw exception;
    throw new Error(
      `Can't reach the API at ${API_URL}. Start it with: uvicorn main:app --reload --port 8000`,
    );
  }
  if (!response.ok) {
    const detail = await response.json().then(b => b.detail).catch(() => null);
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return response.json();
}

// Runs a whole orchestrated meeting server-side and returns its event log for
// playback. With a Mistral key configured this is many sequential model calls,
// so expect it to take a while; without one it's an instant offline mock.
export function runMeeting(topic, { panellists, mode }, signal) {
  return post('/api/meeting', { topic, panellists, mode }, signal);
}

export async function streamMeeting(topic, { panellists, mode }, handlers = {}, signal) {
  let response;
  try {
    response = await fetch(`${API_URL}/api/meeting/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic, panellists, mode }),
      signal,
    });
  } catch (exception) {
    if (exception.name === 'AbortError') throw exception;
    throw new Error(`Can't reach the API at ${API_URL}. Start it with: uvicorn main:app --reload --port 8000`);
  }
  if (!response.ok) {
    const detail = await response.json().then(body => body.detail).catch(() => null);
    throw new Error(detail || `Request failed (${response.status})`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let result;
  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    for (const line of lines) {
      if (!line.trim()) continue;
      const update = JSON.parse(line);
      if (update.type === 'error') throw new Error(update.message);
      if (update.type === 'result') result = update;
      const handler = handlers[update.type];
      if (handler) await handler(update);
    }
    if (done) break;
  }
  return result;
}

// Tells the backend to abandon a running meeting. Aborting the fetch only stops
// the playback — the panel keeps calling Mistral server-side until this lands.
export function stopMeeting(id) {
  return post('/api/meeting/stop', { id });
}

// Casts the panel, gets everyone's opening pitch, and runs the deliberation.
// That's a dozen sequential Mistral calls, so expect this to take a while.
export function startSession(topic, { panellists, mode }, signal) {
  return post('/api/session', { topic, panellists, mode }, signal);
}

export function replyAs(topic, persona, message, signal) {
  return post('/api/reply', { topic, persona, message }, signal);
}

// Adds one more voice to a panel that's already on stage. The existing cast and
// their pitches go along so the newcomer differs from everyone in the room.
export function addPanellist(topic, { mode, cast, pitches }, signal) {
  return post('/api/panellist', { topic, mode, cast, pitches }, signal);
}
