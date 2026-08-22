import { useEffect, useRef } from 'react';
import { drawSprite } from '../sprites';

export default function Avatar({ agent, compact = false, speaking = false, bubble = null }) {
  const canvas = useRef(null);

  useEffect(() => {
    const element = canvas.current;
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let flip = false;
    let blinkTimer;
    drawSprite(element, agent.sprite, speaking ? 'talk' : 'idle');
    if (reducedMotion) return undefined;
    const timer = window.setInterval(() => {
      if (speaking) {
        flip = !flip;
        drawSprite(element, agent.sprite, flip ? 'talk' : 'idle');
      } else if (Math.random() < .12) {
        drawSprite(element, agent.sprite, 'blink');
        blinkTimer = window.setTimeout(() => drawSprite(element, agent.sprite), 140);
      }
    }, 170);
    return () => { window.clearInterval(timer); window.clearTimeout(blinkTimer); };
  }, [agent.sprite, speaking]);

  return (
    <div className={`avatar ${compact ? 'compact' : ''} ${speaking ? 'speaking' : ''}`} style={{ '--agent': agent.color }}>
      {bubble && <div className={`speech-bubble ${bubble.type}`} role="status">{bubble.text}</div>}
      <div className="sprite-wrap"><canvas ref={canvas} className="pixel-person" width="12" height="16" aria-hidden="true" /></div>
      <strong>{agent.name}</strong>
      <small>{agent.role}</small>
    </div>
  );
}
