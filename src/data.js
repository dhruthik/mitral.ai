import { makeSprite } from './sprites';

// Map the backend's cognition trait onto one of the five sprite bodies.
const COGNITION_STANCE = {
  contrarian: 'skeptic', adversarial: 'skeptic', inversion: 'skeptic', historical: 'skeptic', subtractive: 'skeptic',
  analogical: 'dreamer', extrapolative: 'dreamer', 'resource-swap': 'dreamer',
  combinatorial: 'wildcard', simulation: 'wildcard', taxonomic: 'wildcard',
  narrative: 'advocate', ethnographic: 'advocate',
};

// The server describes who is on the panel; the pixel body is stage costume,
// picked client-side from how each panellist thinks.
export function decorateAgents(agents) {
  return agents.map(agent => ({
    ...agent,
    room: 'plenary',
    sprite: makeSprite(COGNITION_STANCE[agent.cognition] || 'pragmatist'),
  }));
}
