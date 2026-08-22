const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
