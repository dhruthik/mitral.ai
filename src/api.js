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

// Casts the panel, gets everyone's opening pitch, and runs the deliberation.
// That's a dozen sequential Mistral calls, so expect this to take a while.
export function startSession(topic, { panellists, mode }, signal) {
  return post('/api/session', { topic, panellists, mode }, signal);
}

export function replyAs(topic, persona, message, signal) {
  return post('/api/reply', { topic, persona, message }, signal);
}
