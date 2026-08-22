# Conversation flow

Recommended orchestration model for the meeting layer. The goal is that the hard
cases — two agents summoning the same third, someone wanting to leave a
conversation mid-sentence — are **impossible to represent**, rather than
something the orchestrator has to arbitrate.

## The one rule everything else follows from

**Agents never talk to each other. They speak into a room, and a deterministic
orchestrator decides who is in which room and who speaks next.**

Every agent tool call is a *request*, not an action. The agent asks; plain Python
decides. There is no agent-to-agent messaging, no interrupts, no preemption.

## Rooms

Four rooms, always open, never created or destroyed.

| Room | Role |
| --- | --- |
| `plenary` | Everyone starts here and returns here. The only room where the final answer is agreed. |
| `room-a` / `room-b` / `room-c` | Working rooms. Agents split off into these to develop a specific proposal. |

Two invariants make the whole thing tractable:

1. **An agent is in exactly one room.** Membership is a single field, not a set.
   "B is talking to C while A summons B" cannot be represented, so it never has
   to be resolved.
2. **An empty or single-occupant room does not tick.** If an agent ends up alone
   in a working room, the orchestrator returns them to plenary. No monologues.

## The loop

The orchestrator runs in rounds. One round:

1. For each non-idle room, pick the next speaker and get one turn from them.
2. Apply the intents that turn produced (see tools below).
3. **Resolve movement.** Joins, invitations and kicks take effect here — at the
   round boundary, never mid-turn.
4. Check termination.

**Turn order is assigned, not chosen.** Weight it by the panellist's `dominance`
trait with a decay each time they speak, so the forceful one leads early without
monologuing. Agents never pick who speaks next.

**Lock-in.** After joining a room an agent must stay for N turns (start with 4)
before it can move again. Without this they thrash between rooms and nothing gets
finished.

## Tools the agents get

```python
speak(text)                      # say something in your current room
propose(title, body)             # put a named proposal on the room's table
upvote(proposal_id)              # +1; cheap, no discussion cost
join_room(room_id)               # request a move; applied at the round boundary
invite(agent_id, room_id)        # queued for the target, never delivered mid-turn
call_vote(proposal_id)           # room votes; majority closes the room
kick(agent_id, reason)           # requires a majority vote to take effect
done()                           # "I have nothing further" — see termination
```

Everything returns a receipt, not a result. `invite` returns *queued*, not the
target's answer.

## How invitations actually work

This is the case that looks complicated and isn't:

- `invite(A, "room-b")` does **not** reach A. It goes on the orchestrator's queue.
- A is inside their lock-in window, so nothing happens to them. The inviter is
  told "Priya is in room-a" and carries on.
- When A's lock-in expires at a round boundary, the orchestrator delivers the
  pending invitations to A as part of their next turn context.
- A answers with `join_room` or ignores it. **A is never interrupted, and never
  has to abandon a conversation mid-flow.**
- If two agents invite A to different rooms, A sees both and picks one. If A
  ignores both, nothing happens. No deadlock, no arbitration.

Busy-by-default plus queued invitations is the whole trick.

## Termination

Three independent stops, whichever fires first:

- **Vote.** `call_vote` passing with a majority closes that room; its members
  return to plenary carrying the proposal.
- **Consensus to stop.** All occupants have called `done()` since the last new
  proposal.
- **Budget.** A hard cap on turns per room and on total turns for the session.
  Always have this — it's what stops a runaway bill.

Plenary closing ends the session and produces the answer shown to the user.

## State

One **append-only event log** is the entire shared state. Every message, vote,
proposal, join, leave and kick is an event with a room id and a sequence number.

- Each agent's context is a *render* of only the rooms they were in. An agent in
  `room-a` never sees `room-b`, so rooms stay genuinely independent.
- When an agent returns to plenary they get a summary of what they missed, not a
  transcript.
- The log gives the UI free replay, and gives you deterministic re-runs when
  debugging.

## Scope for the hackathon

- **No nested rooms.** A working room cannot spawn another working room. This is
  where the design gets genuinely hard and it buys nothing on stage.
- **Cap total turns** before anything else.
- **Ship the plenary-only path first.** Everyone in one room, dominance-weighted
  turn order, vote to close. Get that working end to end, then enable the three
  working rooms. The room logic is additive — it doesn't change the loop.
