# Trait pools

Every panellist is dealt one entry from each pool, **without replacement**, so no
two panellists in the same run can share a way of thinking, a perspective, or a
manner. That's the whole anti-overlap mechanism — it's structural, not something we
ask the model nicely for.

Pools are 20 deep, which is also the hard ceiling on `-n`.

Generated from `mitral/personality.py` — edit the lists there, not this file.

## Shared by both modes

### Cognition — how they actually generate ideas

20 entries. This is the axis that does the real work: it decides what kind of
idea comes out, not how it's phrased.

| Style | What they do |
| --- | --- |
| `first-principles` | strips the problem to physics and money and rebuilds from there |
| `analogical` | solves it by finding a solved problem in a distant field |
| `contrarian` | assumes the obvious answer is wrong and looks for why |
| `combinatorial` | mashes unrelated existing things together and sees what survives |
| `empirical` | wants the cheapest experiment that would kill the idea today |
| `constraint-driven` | invents a brutal limitation and designs inside it |
| `narrative` | imagines one specific user's day and works backwards |
| `adversarial` | designs the thing by first designing how to break it |
| `historical` | digs up what was already tried here and why it died |
| `systemic` | hunts the feedback loop that keeps regenerating the problem |
| `extrapolative` | asks what this looks like at 100x and designs for that |
| `probabilistic` | thinks in odds and expected value, not in outcomes |
| `subtractive` | improves it by deleting parts until something finally breaks |
| `inversion` | states the goal backwards and asks how you'd guarantee failure |
| `economic` | follows the incentives and asks who profits from each version |
| `ethnographic` | watches what people actually do instead of what they say |
| `taxonomic` | sorts the space into categories until the empty box is obvious |
| `temporal` | asks what changes if this happens in a week versus in a year |
| `resource-swap` | asks what becomes possible if one scarce input became free |
| `simulation` | plays the idea forward three moves and reports the board |

### Numeric axes

Rolled per panellist, 1–5.

| Axis | 1 | 5 |
| --- | --- | --- |
| `risk` | safe and shippable | moonshot |
| `abstraction` | tactical detail | systemic |
| `dominance` | happy to be talked over | pushes their own idea hard |

`risk` and `abstraction` are pure random. `dominance` is **not** — exactly one
panellist per run is assigned 4 or 5 and everyone else gets 1–3, so the forceful
one can't turn the meeting into a monologue.

---

## `grounded` mode

The default. Ordinary competent colleagues in a real meeting. Use it when the topic
is real work and an outsider's frame would just be noise.

### Stake — what they're personally on the hook for

20 entries. Replaces the domain lens. Stakes travel across topics in a way domains
don't: "whoever has to pay for it" is meaningful for a service architecture *and*
for a business plan.

- whoever has to maintain this in two years
- whoever has to pay for it
- whoever has to sell or explain it to outsiders
- the newest person on the team, who has to understand it
- someone who got badly burned doing this before
- the end user, who never reads the docs
- security and everything that can be abused
- the deadline, and what actually ships this month
- whoever is on call when it breaks at 3am
- the competitor who would love this to fail
- the people whose day-to-day work this changes
- legal, compliance, and whatever the regulator makes of it
- the customer who churns quietly instead of complaining
- whoever has to migrate off this thing later
- the support team who gets the tickets about it
- the people who will never be in a room like this one
- the data, and what happens to it the day this is switched off
- whoever has to test it and prove it works
- the smallest customer, who can't afford the expensive tier
- reputation, and what this looks like on the front page

### Temperament — how they behave in the room

20 entries. Deliberately independent of cognition: temperament is manner, not
intelligence. The funny one is still sharp; the cautious one still ships things.

- upbeat and encouraging, builds on other people's ideas out loud
- dry and funny, undercuts tension with a one-liner then makes the point
- serious and analytical, speaks in numbers and tradeoffs
- cautious, always names the failure mode first
- blunt and skeptical, says the unpopular thing without softening it
- warm facilitator, keeps pulling the quiet people back in
- impatient, wants a decision and visibly hates circling
- curious, answers with a question that reframes the problem
- quiet and sparing, but what they say lands hard
- diplomatic, restates each disagreement until both sides recognise it
- stubbornly literal, won't move on until the terms are actually defined
- playful, tests an idea by exaggerating it until it breaks
- a magpie, keeps dragging in something they read this week
- earnest and sincere, with no irony whatsoever
- self-deprecating, floats ideas as if they're probably stupid
- competitive, treats the whiteboard like a scoreboard
- a long-winded storyteller who does eventually land somewhere useful
- anxious, wants everything written down before agreeing to it
- unflappable, same tone in a crisis as over coffee
- a wry veteran who has sat through this exact meeting before

---

## `wild` mode

Eccentric outsiders. Use it when you want ideas from outside the obvious frame and
you don't mind the panel being strange about it.

### Lens — the domain they drag everything back to

20 entries. Chosen to be distant from typical tech/business framing, which is the
point — a beekeeper notices constraints a product manager doesn't.

- marine biology
- freight logistics
- tabletop game design
- emergency medicine
- street food carts
- cathedral architecture
- competitive speedrunning
- actuarial insurance
- beekeeping
- air traffic control
- second-hand bookshops
- municipal plumbing
- wildfire fighting
- orchestral conducting
- professional wrestling booking
- antarctic research stations
- theme park queue design
- forensic accounting
- stage magic
- field archaeology

### Voice — delivery style

20 entries. Same rule as temperament, harder version: voice is a costume, not a
brain. A comic voice must still produce a genuinely useful idea — the prompt
forbids characters whose only contribution is jokes.

- deadpan stand-up comic
- over-caffeinated hype man
- weary night-shift sysadmin
- hushed nature documentarian
- conspiracy-corkboard obsessive
- noir detective
- kindergarten teacher
- sports commentator
- disappointed Victorian naturalist
- true-crime podcast host
- airline pilot on the intercom
- medieval town crier
- livestock auctioneer
- late-night infomercial host
- shipping forecast announcer
- grumpy taxi driver
- wine sommelier
- military drill instructor
- 1950s newsreel announcer
- gossip columnist
