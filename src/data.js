import { makeSprite } from './sprites';

const PERSONAS = [
  ['Nova', 'dreamer', '#7c5ce8'],
  ['Rex', 'skeptic', '#e09a2f'],
  ['June', 'pragmatist', '#4c9be0'],
  ['Priya', 'advocate', '#e86a8a'],
  ['Zed', 'wildcard', '#2fb8a6'],
  ['Lumi', 'dreamer', '#c05ce8'],
  ['Otto', 'pragmatist', '#64748b'],
];

export function makeCrew() {
  return [...PERSONAS].sort(() => Math.random() - .5).slice(0, Math.random() > .5 ? 6 : 5)
    .map(([name, stance, color], index) => ({ id: name.toLowerCase(), name, stance, role: `the ${stance}`, color, sprite: makeSprite(stance), room: 'dream', index }));
}

const angles = ['tiny', 'members-only', 'after-hours', 'pay-what-you-want', 'neighborhood', 'secret'];
const formats = ['club', 'ritual', 'passport', 'wall of notes', 'pop-up', 'swap meet'];

export function mockIdeas(topic) {
  const words = topic.toLowerCase().match(/[a-z']{4,}/g) || ['idea'];
  const seed = () => `A ${angles[Math.floor(Math.random() * angles.length)]} ${formats[Math.floor(Math.random() * formats.length)]} built around ${words[Math.floor(Math.random() * words.length)]}.`;
  return [seed(), seed()];
}
