const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function runMeeting(topic, options = {}, signal) {
  const response = await fetch(`${API_URL}/api/meeting`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic, ...options }),
    signal,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Meeting request failed (${response.status})`);
  }
  return response.json();
}

export async function brainstormWithLlm(topic, messages, signal) {
  const response = await fetch(`${API_URL}/api/brainstorm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic, messages }),
    signal,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `LLM request failed (${response.status})`);
  }
  return response.json();
}
