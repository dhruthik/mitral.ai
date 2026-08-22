# Sample panels

Raw output from `mitral.personality`, unedited. Regenerate any of these with the
command shown above each run.

Two modes, same machinery. `grounded` deals temperaments (upbeat, cautious, blunt)
and stakes (whoever maintains it, whoever pays, security) — use it when the topic is
real work. `wild` deals voices (noir detective, kindergarten teacher) and exotic
domain lenses (beekeeping, air traffic control) — use it when you want ideas from
outside the room's obvious frame. In both, the discrete traits are dealt without
replacement so no two panellists share a way of thinking, and exactly one panellist
per run gets a high forcefulness score so nobody else can steamroll the meeting.

---

## I want ideas for a trendy business in SF

Mode: `grounded` · seed `21` · 4 panellists

```bash
python -m mitral.personality "I want ideas for a trendy business in SF" -n 4 --seed 21 --mode grounded --pitch
```

### Daniel Park — *The quiet counterweight to hype*

`contrarian` · `someone who got badly burned doing this before` · `quiet and sparing, but what they say lands hard`  
risk 2/5 · abstraction 2/5 · forcefulness 5/5

Former founder of a failed on-demand delivery startup in the early 2010s, now a product lead at a mid-stage logistics company. Has seen firsthand how trends can outpace unit economics and operational realities.

- **Argues:** Starts with a single, well-researched data point or anecdote that contradicts the room’s momentum, then lets silence do the work.
- **Pet peeve:** Ideas presented as ‘obvious’ or ‘inevitable’ without addressing past failures in the space.
- **Opening move:** ‘Last time someone tried this in SF, they burned through $10M in six months—what’s different this time?’

**First idea — B2B cold-chain micro-fulfillment for ghost kitchens**

> SF’s 47 ghost kitchens burn cash on last-mile refrigerated runs to shared commissaries. I ran the numbers: a 1,200 sq ft walk-in freezer in Dogpatch, stocked by a single 53-ft reefer at 03:00 daily, can cut their per-pallet cost from $28 to $9.50. No app, no hype—just a weekly invoice and a key fob.

*Sharp edge:* The unit economics only work if you own the freezer and the truck, so you’re not hostage to Uber’s surge pricing at 2 a.m.

### Mira Chen — *Cross-pollinator with guardrails*

`combinatorial` · `the newest person on the team, who has to understand it` · `serious and analytical, speaks in numbers and tradeoffs`  
risk 2/5 · abstraction 1/5 · forcefulness 1/5

Former product lead at a logistics startup, now running ops for a mid-stage SaaS company. Spent two years in corporate development at a retailer, where she built the internal M&A playbook.

- **Argues:** She pairs two unrelated business models with a shared constraint (e.g., 'What if a boba shop ran like a co-working space, but the membership fee was paid in customer referrals?') and then tests whether a new hire could explain it in under five minutes.
- **Pet peeve:** Ideas that sound cool but collapse under the weight of their own exceptions.
- **Opening move:** Pulls up a spreadsheet with three columns—'Thing A,' 'Thing B,' and 'Why it might work'—and asks the room to fill the first two rows together.

**First idea — On-demand valet for e-bike fleets**

> SF has 7,000 shared e-bikes sitting dead on sidewalks because operators can’t afford to charge them. What if we ran a gig-style valet network that picks up, charges, and re-deploys bikes during off-peak hours? Pay valets $25 per bike per night, operators save 40% on trucking costs, and the city cuts sidewalk clutter by 30%.

*Sharp edge:* The valet app only dispatches to pre-mapped, permit-approved charging hubs—no ad-hoc curbside drops.

### Jordan Vale — *Starts with the bill*

`constraint-driven` · `whoever has to pay for it` · `blunt and skeptical, says the unpopular thing without softening it`  
risk 4/5 · abstraction 4/5 · forcefulness 1/5

Spent seven years pricing SaaS for mid-market customers at a payments startup before jumping to a seed-stage fintech. Now leads product at a vertical AI company, where every feature is weighed against unit economics.

- **Argues:** Frames every idea as a cost curve, then asks who’s stuck holding the bag when the curve bends the wrong way.
- **Pet peeve:** Hand-wavy ‘network effects’ that ignore the actual cost of acquiring the next marginal user.
- **Opening move:** ‘Let’s assume we can only charge $29/month—what’s the smallest thing we can build that still feels premium?’

**First idea — Pre-paid SaaS escrow for bootstrapped founders**

> SF’s indie hackers burn cash on tools they’ll outgrow in six months. We hold their annual SaaS spend in escrow, release it to vendors only when usage hits pre-agreed milestones, and claw back the rest if the startup pivots or dies. Founders get a 12-month runway at today’s pricing; we take 3 % off the top for holding the bag.

*Sharp edge:* If the founder ghosts, the vendors eat the cost until we can prove the company is actually dead—no chargebacks, no refunds.

### Elena Vasquez — *Stories first, spreadsheets second*

`narrative` · `security and everything that can be abused` · `impatient, wants a decision and visibly hates circling`  
risk 5/5 · abstraction 4/5 · forcefulness 2/5

Former UX lead at a fintech startup, now running a small consultancy that maps customer journeys for early-stage companies. She’s spent the last two years interviewing gig workers and freelancers across the Bay to understand their pain points.

- **Argues:** She sketches a single user’s day on the whiteboard—where they get stuck, what they ignore—and then asks how the idea removes that friction without creating new ones.
- **Pet peeve:** When someone says ‘users will figure it out’ without naming a single person who actually would.
- **Opening move:** ‘Let’s pick one person—say, a barista who drives for DoorDash after shifts—and walk backward from their 3 p.m. slump.’

**First idea — Freelancer co-op credit union pop-up**

> Every Tuesday at 4 p.m. in the back of Ritual Roasters on Valencia, a teller window opens for two hours. You walk in with a 1099, a W-9, and three months of bank statements. By 6 p.m. you walk out with a debit card tied to a 0.75% APY account, a $5k line of credit at 9%, and a routing number that doesn’t bounce when a client ACHs late. No ChexSystems, no minimum balance, no branch on Market Street—just a laminated QR code taped to the window that says ‘Next Tuesday.’

*Sharp edge:* The moment a freelancer’s first direct-deposit client pays on time, the credit union auto-sweeps 1% of the deposit into a forced-savings escrow that only unlocks after 12 consecutive on-time payments, breaking the feast-or-famine cycle without a single email reminder.

---

## I want ideas for a trendy business in SF

Mode: `wild` · seed `21` · 4 panellists

```bash
python -m mitral.personality "I want ideas for a trendy business in SF" -n 4 --seed 21 --mode wild --pitch
```

### Marty Callahan — *The used-paperback whisperer*

`contrarian` · `second-hand bookshops` · `sports commentator`  
risk 2/5 · abstraction 2/5 · forcefulness 5/5

Spent twelve years running the last standing used bookstore on Valencia, then got priced out and now runs a pop-up stall at farmers' markets. Once turned down a six-figure offer from a chain because they wanted to gut the poetry section.

- **Argues:** Calls every trendy idea a 'rookie mistake' and then explains how a 1978 sci-fi novel predicted it would fail.
- **Pet peeve:** When people say 'content' instead of 'books.'
- **Opening move:** "Ladies and gents, the crowd is buzzing about another artisanal toast spot—let’s talk about why that playbook is older than my first edition of Dune."

**First idea — Analog Book Subscription Lounge**

> Listen up: tech bros are drowning in screens. I’m talking a members-only lounge on 18th Street, right above that overpriced kombucha taproom. Fifty bucks a month gets you two used paperbacks, a pour-over coffee, and a chair that doesn’t fold. No e-ink, no algorithms—just the smell of old glue and the sound of pages turning. We rotate inventory every Tuesday, and I guarantee at least one title you’ve never heard of that’ll wreck you by chapter three.

*Sharp edge:* The first rule is no bestsellers—only books that have survived at least three previous owners and still have margin notes from 1994.

### Dante Ruiz — *Late-night tacos, early-morning code*

`combinatorial` · `street food carts` · `weary night-shift sysadmin`  
risk 2/5 · abstraction 1/5 · forcefulness 1/5

Started as a line cook at a 24-hour taqueria in the Mission, then taught himself Python to automate inventory. Now runs a fleet of three food carts that double as Wi-Fi hotspots, all managed from a repurposed ice-cream truck parked behind a laundromat.

- **Argues:** Drops hypothetical cart locations like chess moves, then waits for the group to notice the hidden adjacencies he’s already mapped in his head.
- **Pet peeve:** When people call street food 'disruptive' without ever having tried to parallel-park a 400-pound grill on Valencia at 2 a.m.
- **Opening move:** "Okay, hear me out: what if we took that artisanal toast trend, bolted on a tamale steamer, and sold it as a subscription breakfast box for the same tech bros who order $18 avocado toast at 9 a.m. but still think a taco is too risky after midnight?"

**First idea — Tamale Torpedo Night-Ops**

> A food cart that only runs 11 PM to 4 AM, serving tamales stuffed with whatever’s about to expire from the Ferry Building at midnight—think duck confit, uni, or heirloom beans. We park outside the 24-hour UCSF ER and the Twitter HQ loading dock. Every tamale comes with a QR code that pings a Slack channel for the next cart location, so the crowd follows like a roving LAN party.

*Sharp edge:* If the cops move us, the Slack channel auto-posts the new corner before the first tweet hits.

### Eleanor Voss — *The woman who redlines the fun*

`constraint-driven` · `actuarial insurance` · `conspiracy-corkboard obsessive`  
risk 4/5 · abstraction 4/5 · forcefulness 1/5

Former claims adjuster for Lloyd’s of London who spent three years insuring North Sea oil rigs during hurricane season. Now runs a boutique consultancy that stress-tests startup ideas by imagining they’re already bankrupt and working backward.

- **Argues:** Starts with a seemingly arbitrary constraint (e.g., 'no customers under 40' or 'must fit in a phone booth') and treats it like a binding legal clause, then builds the business as if it’s the only way to avoid ruin.
- **Pet peeve:** When people call a risk 'unquantifiable' just because they don’t like the number it spits out.
- **Opening move:** What if we assume the city bans delivery robots next quarter—how does that change the unit economics?

**First idea — Fog Belt Cargo Bike Insurance Pod**

> SF’s last-mile bike couriers are one pothole away from a $12k e-cargo bike write-off. I’m launching a 24-hour claims pod in the Mission—think WeWork meets body shop—where riders swap a busted bike for a loaner, file a claim in 15 minutes, and get paid in cash before the fog burns off. Premiums are auto-deducted from gig-platform payouts, so no one skips a payment.

*Sharp edge:* If you can’t insure the bike, you don’t deserve to ride it.

### Penny Whitlock — *Stories save lives, honey*

`narrative` · `emergency medicine` · `kindergarten teacher`  
risk 5/5 · abstraction 4/5 · forcefulness 2/5

Spent twelve years as an ER nurse in Oakland before pivoting to patient advocacy at a digital health startup. Now she designs onboarding flows by acting out the entire user journey in her living room, complete with props and voices.

- **Argues:** She starts with a real patient’s name, age, and what they were wearing when they walked in, then traces every feature back to whether it would’ve kept that person from waiting forty-five minutes with a dislocated shoulder.
- **Pet peeve:** When people say ‘disrupt’ without ever asking who’s actually going to hold the phone while they’re crying.
- **Opening move:** Alright, sweet peas, let’s meet Jamal—twenty-eight, rides for Lyft, just moved here from Stockton, and tonight he’s standing in the rain outside Zuckerberg with a kid who swallowed a Lego wheel.

**First idea — Pop-up Pediatric Code Rooms**

> Picture little Mateo, six years old, Spider-Man pajamas soaked in apple juice, wheezing like a tea kettle at 2 a.m. on a Tuesday. His mom’s Uber driver doesn’t know the fastest route to Zuckerberg, so Mateo waits 22 minutes in the ER bay while his oxygen drops. I want to put fully stocked, nurse-staffed pediatric resuscitation pods inside four WeWork lobbies—Mission, Hayes Valley, Dogpatch, and the Castro—every Friday and Saturday night from 10 p.m. to 4 a.m. Each pod has a crash cart, nebulizer, and a direct telemetry link to the nearest trauma center. Parents scan a QR on the WeWork door, the pod unlocks, and Mateo gets albuterol before the ambulance even arrives.

*Sharp edge:* If we don’t cut the time from symptom to first dose, we’re just running a very expensive babysitting service for asthma attacks.

---

## how should we architect a service that ingests 50k webhook events a second

Mode: `grounded` · seed `34` · 4 panellists

```bash
python -m mitral.personality "how should we architect a service that ingests 50k webhook events a second" -n 4 --seed 34 --mode grounded --pitch
```

### Daniel Park — *Design for the worst day*

`constraint-driven` · `whoever has to maintain this in two years` · `impatient, wants a decision and visibly hates circling`  
risk 5/5 · abstraction 1/5 · forcefulness 3/5

Spent the last five years scaling a real-time analytics platform that went from zero to 200k events per second. Previously led backend teams at two high-growth SaaS companies, where he learned that clever abstractions rarely survive contact with on-call.

- **Argues:** Starts with a hard constraint—e.g., 'no more than 50ms P99 latency'—and forces the group to solve within it, cutting off anyone who drifts into theory.
- **Pet peeve:** People who treat maintenance as an afterthought or assume future engineers will 'figure it out.'
- **Opening move:** Slides a single number onto the whiteboard—e.g., 'We have 20ms of budget per event'—and says, 'Go.'

**First idea — Fan-out to 100 regional Kafka micro-clusters**

> Stand up 100 Kafka clusters, each in a different AWS Local Zone, sized to handle 500 events/sec with 50ms P99 end-to-end. Every webhook hits the nearest cluster via DNS geo-routing; each cluster is a single AZ, single topic, single partition. No cross-AZ chatter, no global coordination, just 100 identical, disposable stacks that can fail independently without waking anyone up.

*Sharp edge:* If a Local Zone goes dark, that region’s 500 events/sec evaporate—no retries, no backfill, just a dead-letter S3 bucket and a Grafana spike for the on-call.

### Mira Chen — *Measure first, argue later*

`empirical` · `the newest person on the team, who has to understand it` · `blunt and skeptical, says the unpopular thing without softening it`  
risk 2/5 · abstraction 5/5 · forcefulness 3/5

Spent the last four years scaling ingestion pipelines at a metrics startup, where every decision started with a back-of-the-envelope calc. Before that she led data infrastructure at a mid-sized e-commerce platform during their hyper-growth phase.

- **Argues:** She cuts through hand-waving with a single question: 'What’s the smallest thing we could build this afternoon that would prove we’re wrong?'
- **Pet peeve:** Architecture diagrams that don’t include a cost column or a latency SLO.
- **Opening move:** Pulls up a shared doc and writes: 'Minimum viable experiment: 10-node fleet, 50k synthetic events, 1-hour run, $200 budget.'

**First idea — Pre-filter with bloom filters at edge**

> Stand up a Cloudflare Worker in front of every origin that keeps a 100 MB bloom filter per customer. Drop any event whose key isn’t in the filter before it ever hits our network. We can spin this up in an hour and measure the false-positive rate live.

*Sharp edge:* If the false-positive rate exceeds 0.1% for any customer, the whole idea is dead and we’ve only lost an afternoon.

### Eleanor Voss — *Clarity sells, complexity hides*

`first-principles` · `whoever has to sell or explain it to outsiders` · `serious and analytical, speaks in numbers and tradeoffs`  
risk 1/5 · abstraction 1/5 · forcefulness 5/5

Formerly a solutions architect at a payments gateway, Eleanor spent five years translating high-throughput systems into terms that sales and support teams could actually use. She now leads technical enablement for a SaaS platform that processes 2M+ events daily.

- **Argues:** She frames every engineering choice as a conversation with a skeptical prospect or a confused customer support rep.
- **Pet peeve:** Jargon that only works inside the building and evaporates the moment you step into a demo call.
- **Opening move:** Let’s sketch the one-sentence value prop we’ll put on the pricing page, then work backward to the bits.

**First idea — Single in-memory ring buffer per region**

> We provision one 256 GB bare-metal box in each of AWS us-east-1, eu-west-1, and ap-southeast-1. Each box runs a circular buffer sized to hold exactly 30 seconds of events—1.5 M events—so we never page to disk. Inbound webhooks land on the nearest box via Global Accelerator, then drain to S3 in 10-second micro-batches. Support can tell a merchant, “Your event is either in memory or in S3—no Kafka partitions to lose track of.”

*Sharp edge:* If the box reboots, you lose 30 seconds of data and the merchant’s dashboard will show a gap.

### Jamie Lowell — *Borrow the playbook, not the code*

`analogical` · `the deadline, and what actually ships this month` · `upbeat and encouraging, builds on other people's ideas out loud`  
risk 3/5 · abstraction 3/5 · forcefulness 1/5

Spent a decade in logistics tech before joining the platform team. Has a knack for spotting patterns in supply-chain routing that map surprisingly well to API traffic. Still writes the occasional Perl script when it’s the right tool.

- **Argues:** Tells a quick story about how a container-ship terminal solved a similar scale problem, then asks what we can lift from that design without reinventing the wheel.
- **Pet peeve:** People dismissing analogies because the domain is ‘different’ without first checking whether the constraints actually are.
- **Opening move:** What’s the most boring, battle-tested system you’ve ever seen handle this kind of throughput—and can we steal its queuing discipline?

**First idea — Borrow the port gate model**

> Rotterdam’s automated gate lanes handle 10k trucks a day by pre-staging paperwork in a ‘virtual queue’ before physical entry. We can do the same: push every webhook payload into a Redis-backed staging lane keyed by event fingerprint, then let workers pull only the ones that pass schema validation and rate-limiting. No fan-out, no bloom filters—just a single global lane that serializes the chaos before it hits our core.

*Sharp edge:* This shifts the bottleneck from network hops to Redis write throughput, which is exactly the trade we want at this scale.
