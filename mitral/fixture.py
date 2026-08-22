"""A prewritten panel, for developing the UI without waiting on Mistral.

A real session is a dozen sequential model calls and about a minute. That is
fine for a demo and miserable for tweaking a stylesheet, so dev mode serves this
instead: the same shapes, the same code path through `main._agent`, no network.

The traits are sampled from the real pools so the profile cards have honest
content; only the prose is hand-written. The pitches are about a night cafe
whatever topic you type — that is the tradeoff, and why this is off in prod.
"""

import random

from .personality import Deliberation, Persona, Pitch, sample_traits

# name, tagline, bio, how_they_argue, pet_peeve, opening_move,
# idea, mechanism, pitch, sharp_edge
PANEL = [
    (
        "The Lighthouse Keeper",
        "Keeps the thing running at 3am",
        "Spent nine years on call for a payments system that was never allowed to "
        "stop. Now measures every idea by how it behaves when nobody is watching it.",
        "Asks who is awake when this breaks, and waits for a real answer.",
        "Plans that quietly assume someone will be there to intervene.",
        "Walks through one bad night, minute by minute.",
        "One button that closes the whole shop",
        "single reversible switch instead of a shutdown checklist",
        "Everything here dies at 4am eventually, so build for the death first. One "
        "switch, one person, sixty seconds — and the room is dark, the till is "
        "closed, and nothing is left half-finished for the morning.",
        "The closing sequence is eleven steps today, and step seven is where the money goes missing.",
    ),
    (
        "The Locksmith",
        "Designs it by picking it first",
        "Used to test physical security for a chain of jewellers, then moved into "
        "product. Has never once been shown a system she couldn't get into within a week.",
        "Breaks the idea in front of you, then helps you rebuild it.",
        "Being told a failure mode is 'an edge case'.",
        "Describes exactly how she'd rob the place.",
        "Let the regulars run the door",
        "shifting trust from staff to a known crowd",
        "You cannot staff a door at 3am cheaply, so stop trying. Give forty regulars "
        "a key and the whole security model changes from strangers-by-default to "
        "friends-by-default. The people who'd wreck it aren't the ones who joined.",
        "Every night venue that survived past year two did this, and none of them advertise it.",
    ),
    (
        "The Cartographer",
        "Draws the map nobody asked for",
        "Trained as a transport planner and never stopped thinking in flows. Turns "
        "arguments into diagrams on the nearest surface, usually before anyone agrees to it.",
        "Redraws the problem until the empty space is obvious.",
        "Debates where nobody has defined the boundary of the thing.",
        "Sorts everyone's ideas into a grid.",
        "Sell the table, not the coffee",
        "charging for occupancy instead of product",
        "There are four things you can sell at 2am and coffee is the worst of them. "
        "Price the seat by the hour and the entire menu becomes a rounding error — "
        "you're a room, not a cafe, and rooms have better margins.",
        "A £4 flat white for three hours is £1.30 an hour; the co-working place next door gets £6.",
    ),
    (
        "The Magpie",
        "Brings in whatever she read this week",
        "Runs a research newsletter and has an unreasonable memory for other "
        "people's experiments. Half her ideas are stolen and she'll tell you from whom.",
        "Names the place it already worked, then argues about the differences.",
        "Reinventing something a competitor open-sourced two years ago.",
        "Opens with a story about somewhere else entirely.",
        "Copy the hospital canteen",
        "borrowing a proven overnight service model",
        "Nobody talks about it, but hospital canteens have solved night trade "
        "completely — fixed menu, no queue, and staff who are on the same shift "
        "cycle as the customers. Steal all three and skip four years of learning.",
        "The Royal London's night canteen turns over £900 between midnight and 5am with two staff.",
    ),
    (
        "The Undertaker",
        "Asks what killed the last one",
        "Twenty years in restaurant turnarounds, which mostly means being in the "
        "room when someone finally admits it is over. Keeps a list of why each one died.",
        "Digs up the previous attempt and reads out the cause of death.",
        "Optimism that hasn't checked whether this was tried already.",
        "Starts with the obituary.",
        "Open five nights, never seven",
        "deliberate scarcity to protect the staffing model",
        "Every night place I have buried died of Tuesdays. Not of rent, not of "
        "competition — of opening on a night that never paid for itself and burning "
        "out the two people who could actually run the room.",
        "Wednesday through Sunday, and the staff rota stops being a monthly crisis.",
    ),
    (
        "The Quartermaster",
        "Counts what it actually costs",
        "Spent a decade doing procurement for expedition logistics, where a missing "
        "crate is not an inconvenience. Reads a P&L the way other people read a menu.",
        "Puts a number on it before anyone is allowed an opinion.",
        "Ideas priced in adjectives instead of pounds.",
        "Asks what the second-largest line item is.",
        "Rent the kitchen out by day",
        "double-using the same fixed asset",
        "The building is the expense and you are proposing to use it eight hours in "
        "twenty-four. Let a bakery have it from six to two and the rent stops being "
        "your problem — it becomes theirs, and you keep the equipment.",
        "Commercial kitchen hire in this city is £22 an hour, which is most of a night's takings.",
    ),
    (
        "The Understudy",
        "Speaks for whoever joins next year",
        "Came up through hospitality floors rather than offices, and remembers being "
        "the newest person in every room. Notices what a plan assumes you already know.",
        "Asks how someone on their second shift would handle it.",
        "Processes that only work because one veteran is holding them together.",
        "Reads the plan back as if she'd never seen it.",
        "Write the menu on the wall in chalk",
        "removing training load from the offer itself",
        "Six items, on a wall, changed weekly. It sounds like a design choice and it "
        "isn't — it means a new hire is useful on night one instead of night ten, "
        "and at 3am that is the entire difference.",
        "Training a barista on a full menu takes eleven shifts; on six items it takes two.",
    ),
    (
        "The Tide Watcher",
        "Thinks in seasons, not evenings",
        "Studied coastal erosion before drifting into operations consulting, and "
        "still thinks on a timescale that irritates people who want an answer today.",
        "Plays the idea forward a year and reports what changed.",
        "Decisions optimised for the first month of trading.",
        "Asks what this looks like in February.",
        "Build for the exam-season peak",
        "sizing to the annual spike rather than the average",
        "Your busiest six weeks will do a third of your year, and they are the same "
        "six weeks every single year. Size the room, the rota and the stock for "
        "those, and let the quiet months be quiet on purpose.",
        "Two university terms give you eleven predictable spike weeks; nothing else moves the curve.",
    ),
]

WHY = (
    "It is the only idea that changes the cost base instead of the menu, and it "
    "survives the night the room is empty."
)

REPLIES = [
    "That only holds if the person doing it has done it before — and on this plan, nobody has.",
    "Agreed, but say the number out loud. If it is under two hundred a night we are decorating, not deciding.",
    "I would run that for one week before I believed a word of it, including my own.",
    "Someone tried exactly that four streets away in 2019. Worth knowing why they stopped.",
    "Push that further and it stops being a cafe entirely — which might be the good version.",
]


def _persona(entry: tuple, traits) -> Persona:
    name, tagline, bio, argues, peeve, opening = entry[:6]
    return Persona(
        name=name, tagline=tagline, bio=bio, how_they_argue=argues,
        pet_peeve=peeve, opening_move=opening, traits=traits,
    )


def _pitch(entry: tuple) -> Pitch:
    idea, mechanism, pitch, edge = entry[6:]
    return Pitch(idea=idea, mechanism=mechanism, pitch=pitch, sharp_edge=edge)


def canned_session(n: int, mode: str, seed: int) -> tuple[list[Persona], list[Pitch]]:
    """The first n panellists, with real sampled traits behind the written prose."""
    entries = PANEL[:n]
    traits = sample_traits(len(entries), random.Random(seed), mode)
    return (
        [_persona(e, t) for e, t in zip(entries, traits)],
        [_pitch(e) for e in entries],
    )


def canned_extra(cast: list[Persona], mode: str) -> tuple[Persona, Pitch]:
    """The next unused panellist, for 'add someone' in dev mode."""
    taken = {p.name for p in cast}
    entry = next((e for e in PANEL if e[0] not in taken), None)
    if entry is None:
        raise ValueError("the prewritten panel is out of people — that's as big as dev mode gets")
    traits = sample_traits(1, random.Random(len(cast)), mode, used=[p.traits for p in cast])[0]
    return _persona(entry, traits), _pitch(entry)


def canned_deliberation(cast: list[Persona]) -> Deliberation:
    """Plan, stress-test and verdict, spread across whoever is actually here."""
    names = [p.name for p in cast]
    return Deliberation(
        plan_speaker=names[min(2, len(names) - 1)],
        plan_text="Give me one site, one month, and the five nights we just agreed on. "
                  "If the Tuesday-shaped hole shows up anyway, we killed it for four grand.",
        test_speaker=names[min(1, len(names) - 1)],
        test_text="It falls over the first night a regular brings someone who isn't one. "
                  "Nothing in this plan says what the person behind the counter does then.",
        winner_speaker=names[min(5, len(names) - 1)],
        why=WHY,
    )


def canned_reply(persona: Persona, message: str) -> str:
    """Deterministic per persona and message, so a reply doesn't change under you."""
    return REPLIES[(len(persona.name) + len(message)) % len(REPLIES)]
