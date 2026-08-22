# Example run, annotated

The unedited output of one command, with an explanation of what each part is and
where it came from.

```bash
python -m mitral.personality "I want ideas for a trendy business in SF" -n 8 --mode grounded --pitch
```

No `--seed`, so this exact panel is not reproducible — rerunning gives eight
different people.

## How to read each entry

Every panellist prints in the same shape:

```
Name — tagline
  cognition · stake · temperament · risk N abstraction N force N
  bio
  Argues:  how they push an idea in the room
  Hates:   the thing they refuse to let slide
  Opens:   their first move when the meeting starts

  >> IDEA TITLE
  the pitch, in their voice
  Edge:    the concrete thing that makes it more than a vibe
```

The second line is **dealt, not generated** — those traits are sampled in Python
before any API call, one from each pool, without replacement. Everything else is
the model writing a person to fit those traits. So the traits are the guarantee
of difference; the prose is downstream of them.

`force` is the dominance score. Exactly one panellist per run gets 4 or 5.
Here it's Mira Patel at 5.

---

## The panel

### Jordan Cole — *Plans the un-plan first*

`inversion` · `whoever has to test it and prove it works` · `cautious, always names the failure mode first`
risk 4 · abstraction 4 · force 3

Spent six years scaling operations at a mid-stage SaaS company, then led product validation at a seed-stage marketplace. Knows how fast a trend can turn into a liability if the unit economics don't pencil out.

- **Argues:** Starts every proposal by listing three ways it could collapse, then asks what evidence would falsify the idea.
- **Hates:** People who confuse 'novel' with 'validated' and skip the messy work of proving it actually works in the wild.
- **Opens:** 'Let's say we're trying to build the *least* defensible version of this—what would that look like?'

**>> Micro-fulfillment dark stores for chefs**

> Instead of ghost kitchens, put 500-square-foot refrigerated pods inside parking garages in the Mission and North Beach. Stock them with 200 SKUs of premium dry-aged meats, heirloom grains, and local foraged mushrooms—exactly what line cooks need at 3 p.m. when the purveyor's truck is late. Charge a $99 weekly membership that includes 24/7 RFID access and same-day delivery via electric cargo bike to any kitchen within a 1.5-mile radius.

*Edge:* If the top 100 SF restaurants don't adopt within 90 days, the perishable inventory write-off will wipe out the first quarter's gross margin.

### Mira Patel — *Grounds trends in local memory*

`historical` · `the people whose day-to-day work this changes` · `anxious, wants everything written down before agreeing to it`
risk 2 · abstraction 2 · **force 5**

Former policy analyst at the SF Office of Economic and Workforce Development, now consulting for small businesses on regulatory navigation. Spent years mapping failed ventures in the city and the policy shifts that followed.

- **Argues:** She cites specific past businesses—names, dates, and exact reasons for closure—then ties them to current market conditions or municipal pain points.
- **Hates:** When someone dismisses a 'been there, done that' idea without checking why it didn't stick the first time.
- **Opens:** 'Before we get excited, let's pull the permitting records from 2015–2019—there's a graveyard of pop-ups that looked just like this.'

**>> Neighborhood compost hubs with pay-per-pound pickup**

> Remember how SF Recology's curbside compost program cut landfill waste by 80% in the early 2000s but left restaurants and small grocers drowning in overflowing bins? Now, with the city's new $100/ton organic waste fine, those same businesses are scrambling. I'm proposing fixed-location compost hubs in every district—like the old Sunset Scavenger stations—where anyone can drop off scraps for a fee, and we sell the finished compost to urban farms in the Central Valley. We'd use the same 3-cubic-yard roll-off containers Recology uses, but charge $0.15 per pound instead of their flat rate. The hubs double as community education sites, so we'd partner with the SF Environment Department to train staff.

*Edge:* This isn't another cute urban farming co-op—it's a regulatory arbitrage play that turns a city mandate into a revenue stream for small businesses.

### Eleanor Voss — *Follows the money to the doorstep*

`economic` · `reputation, and what this looks like on the front page` · `a wry veteran who has sat through this exact meeting before`
risk 2 · abstraction 1 · force 3

Spent a decade in commercial real-estate finance before shifting to urban economic development for the city. Knows every tax-increment district, vacant lot valuation, and which permits actually move the needle.

- **Argues:** She maps each idea to a concrete revenue stream or cost center, then asks who controls that line item and what they actually want.
- **Hates:** Ideas that assume infinite subsidy or goodwill without naming the budget it comes from.
- **Opens:** Let's start with the simplest question: who pays, who gets paid, and what do they have to lose?

**>> Valet EV charging for rent-controlled buildings**

> There are 187,000 rent-controlled units in SF, most with no off-street parking. Landlords can't raise rents to cover charging infrastructure, but they also can't ignore the 30% of tenants who now own EVs. We run a valet service that swaps depleted batteries from a central depot on 3rd Street—batteries we lease from the utility under their demand-response program. Charge $120/month per tenant, split 60/40 with the building owner, and the city fast-tracks our curb-cut permits because we're reducing street congestion.

*Edge:* The moment PG&E realizes we're arbitraging their time-of-use rates, they'll rewrite the tariff—and we'll be holding the bag on 2,000 leased batteries.

### Daniel Reyes — *Builds for the next owner*

`constraint-driven` · `whoever has to migrate off this thing later` · `stubbornly literal, won't move on until the terms are actually defined`
risk 1 · abstraction 1 · force 2

Former ops lead at a mid-stage SaaS company, now consulting on platform migrations and technical debt. Spent two years decommissioning a legacy system that outlasted its original team.

- **Argues:** Insists on defining every term upfront, then tests ideas against a single, unforgiving constraint (e.g., 'What if we have to sunset this in 18 months?').
- **Hates:** Vague promises about 'future-proofing' without a concrete exit plan.
- **Opens:** Asks, 'What's the first thing a successor would hate about this?' before any other discussion.

**>> Ephemeral API debt escrow for startups**

> Build a 12-month escrow service where startups stash their API keys, rate limits, and migration playbooks before they pivot or shut down. Charge $500/month flat, include a notarized sunset clause that auto-releases the keys to a successor entity or open-sources them if the company dissolves. Only works with APIs that have less than 50k monthly active users—small enough to audit, big enough to matter.

*Edge:* If the successor entity doesn't exist, the escrow burns the keys on day 366 and emails every registered developer.

### Priya Mehta — *Turns constraints into new markets*

`resource-swap` · `the smallest customer, who can't afford the expensive tier` · `diplomatic, restates each disagreement until both sides recognise it`
risk 5 · abstraction 4 · force 2

Former operations lead at a last-mile logistics startup, where she cut delivery costs by repurposing underused urban assets. Now advises early-stage companies on scaling without traditional capital raises.

- **Argues:** Frames every idea as a resource swap—what if X were suddenly abundant, who would pay for Y instead?
- **Hates:** Assuming the expensive tier is the only path to viability.
- **Opens:** Asks the group to list the three most expensive inputs in the current version of the business, then brainstorms what happens if one of them becomes free.

**>> Night-shift ghost kitchens in Muni lots**

> SF Municipal Railway shuts down half its surface lots at 9 p.m. every night. We sign 6-month revocable permits for $1/sq ft/month, drop in 20-ft shipping containers with induction burners, and run 10-pm–4-am shifts for delivery-only brands. Each kitchen pays us $800/night, which is cheaper than their current commissary fees, and we pocket the difference after power hookups.

*Edge:* If the city won't let us use the lots, we'll lease the curb space from adjacent restaurants that close at 10 p.m. and already have the permits.

### Gregory Shaw — *Tests the pitch before the product*

`adversarial` · `whoever has to sell or explain it to outsiders` · `quiet and sparing, but what they say lands hard`
risk 4 · abstraction 1 · force 2

Former head of growth at a mid-stage SaaS company, now consulting for early-stage startups on go-to-market fit. Spent years in enterprise sales, so he knows what makes a deal stall or close.

- **Argues:** Starts with the weakest link in the value chain—distribution, messaging, or support—and forces the group to harden it before moving forward.
- **Hates:** Ideas that sound great in a deck but collapse when a skeptical buyer asks, 'How does this actually work?'
- **Opens:** Asks, 'What's the one-line that would make a stranger at a bar lean in—and what's the follow-up question that would make them walk away?'

**>> White-glove SaaS onboarding concierge**

> Every founder in SF knows their first 10 enterprise customers will decide if the product lives or dies, yet nobody wants to pay for a 4-week implementation sprint. We run a 24-hour SLA onboarding squad that embeds inside the customer's Slack for the first month—no more 'let me check with engineering' delays. Charge $15k upfront, and the customer signs before they realize they're paying for something their sales rep should've done.

*Edge:* If the customer churns after 30 days, we eat the cost of the squad's time—so we're incentivized to make the product sticky, not just pretty.

### Lena Choi — *Finds the fatal flaw by removing it*

`subtractive` · `someone who got badly burned doing this before` · `dry and funny, undercuts tension with a one-liner then makes the point`
risk 3 · abstraction 2 · force 3

Former operations lead at a failed meal-kit startup, now running a small-batch food distribution co-op. Spent two years unwinding a supply chain that collapsed under its own complexity. Knows which corners can't be cut because she cut them first.

- **Argues:** Starts with a deadpan 'What if we just… don't?' then strips the idea layer by layer until the room either fixes the weak point or abandons the whole thing.
- **Hates:** Hearing 'disruptive' used to describe something that's just undercapitalized and over-engineered.
- **Opens:** 'Let's list every assumption we're making—then delete the top three and see if the business still stands.'

**>> Single-ingredient pantry pallets for bodegas**

> What if we just… don't ship mixed SKUs to corner stores? Every bodega in the Mission orders the same 20-pound bag of Goya black beans, but they all get it buried in a 200-item pallet from a distributor who's also delivering toilet paper and energy drinks. We run a weekly route with 12-foot box trucks, selling only bulk staples—beans, rice, oil, sugar—at 5% below Sysco's price. No invoices, no minimums, cash or Venmo on delivery. The bodega owner saves shelf space, we save fuel, and nothing ever expires in the back room.

*Edge:* The moment a bodega owner realizes they've been paying for the privilege of storing Sysco's dead inventory, they'll cancel their standing order before we finish our pitch.

### Omar Ruiz — *Proves it before we bet on it*

`empirical` · `the deadline, and what actually ships this month` · `curious, answers with a question that reframes the problem`
risk 5 · abstraction 2 · force 1

Spent five years running growth experiments at a Series B SaaS company, where he learned that most 'trends' are just untested assumptions. Now consults with early-stage teams on how to validate demand without overbuilding.

- **Argues:** Reframes every proposal as a falsifiable hypothesis and asks what the smallest, fastest test would be to disprove it.
- **Hates:** Hearing 'we'll figure it out later' when the cost of figuring it out now is a $50 ad and an hour of work.
- **Opens:** What's the cheapest way we could find out this idea is wrong by Friday?

**>> On-demand cold-chain microhubs for home chefs**

> SF has 3,200 licensed home kitchens under the Microenterprise Home Kitchen Operations ordinance, but none can scale because they can't hold inventory below 41°F. Drop a 16-foot refrigerated box truck in the Bayview for $2,800/month, rent shelf space by the hour, and run a Shopify app that texts the chef when their salmon arrives. If fewer than 12 chefs reserve slots in the first 30 days, the idea's dead.

*Edge:* If the city won't let you park the truck overnight, the whole model collapses before you hit unit economics.

---

## What worked

**The traits actually drive the ideas.** Mira has the `historical` cognition, and
she's the only one who reaches for the Recology precedent and the $100/ton
organics fine. Daniel is on the hook for "whoever has to migrate off this later",
and he invents an escrow with a sunset clause. You could not swap those two ideas
between those two people.

**Temperament didn't cost intelligence.** Lena's temperament is "dry and funny",
and her pitch opens with a joke — then lands on the observation that bodegas are
effectively paying to warehouse a distributor's dead stock. That's the whole
reason temperament is a separate axis from cognition: the funny one is funny in
delivery only.

**One loud voice, not five.** Mira is the only panellist above force 3. In a real
meeting she's the one who'd dominate, and the assignment rule means that's a
deliberate single seat rather than something that happens to half the room.

**`sharp_edge` is the hook for the conversation layer.** It's the falsifiable bit
of each pitch — the thing another agent can attack, upvote, or build a
subcommittee around. Eleanor's PG&E tariff risk and Omar's parking-permit
dependency are both concrete enough to argue with.

## What didn't

**Three of eight converged on cold chain.** Jordan's refrigerated pods, Priya's
container kitchens and Omar's refrigerated truck are the same idea wearing
different hats. The de-dup step shows each panellist the *titles* of previous
ideas, and "micro-fulfillment dark stores" and "night-shift ghost kitchens" don't
look alike as strings, so nobody noticed. Fixing this means showing the full
previous pitches and forbidding overlap on the underlying mechanism rather than
the wording.

**The bios rhyme.** Four of eight are some flavour of "former ops lead at a
mid-stage SaaS company". The persona prompt only shows previous names and
taglines for differentiation, so backstories drift toward the same default. Same
fix: show more of what came before.

**Trait fidelity varies.** Gregory is dealt `adversarial` — designs the thing by
first designing how to break it — but his pitch is a fairly ordinary services
business. The cognition style shows up in his *opening move* but not in his
actual idea.
