import unittest
from types import SimpleNamespace

from mitral.meeting import PLENARY, Meeting, TURN_SYSTEM


def persona(name):
    return SimpleNamespace(name=name)


class MeetingDecisionTests(unittest.TestCase):
    def meeting(self, vote_fn=lambda _persona, _question: True):
        return Meeting(
            "a night coffee shop",
            [persona("Builder"), persona("Skeptic"), persona("Operator")],
            turn_fn=lambda _persona, _context: {},
            vote_fn=vote_fn,
            working_rooms=False,
        )

    def test_vote_requires_another_panellists_upvote(self):
        meeting = self.meeting()
        builder = meeting.agents["Builder"]
        meeting._apply_action(builder, {
            "tool": "propose", "title": "Run the numbers", "body": "Model one shift."
        })
        meeting._apply_action(builder, {"tool": "upvote", "proposal_id": "p1"})

        meeting._apply_action(builder, {"tool": "call_vote", "proposal_id": "p1"})

        self.assertNotIn("plenary", meeting.pending_votes)
        self.assertIn("needs another panellist's upvote", builder.receipts[-1])

    def test_vote_prompt_includes_alternatives(self):
        questions = []
        meeting = self.meeting(lambda _persona, question: questions.append(question) or True)
        builder = meeting.agents["Builder"]
        skeptic = meeting.agents["Skeptic"]
        meeting._apply_action(builder, {
            "tool": "propose", "title": "Run the numbers", "body": "Model one shift."
        })
        meeting._apply_action(skeptic, {
            "tool": "propose", "title": "Shadow a nurse", "body": "Observe one route."
        })
        meeting._apply_action(skeptic, {"tool": "upvote", "proposal_id": "p1"})
        meeting._apply_action(builder, {"tool": "call_vote", "proposal_id": "p1"})

        meeting._resolve_votes()

        self.assertEqual(len(questions), 2)
        self.assertIn('p2 "Shadow a nurse"', questions[0])

    def test_proposal_prompt_keeps_board_copy_concise(self):
        self.assertIn("title of 2-6 words", TURN_SYSTEM)
        self.assertIn("2-3 natural sentences totaling at most 60 words", TURN_SYSTEM)
        self.assertIn("why it is the best fit", TURN_SYSTEM)
        self.assertIn("why the strongest alternatives are worse", TURN_SYSTEM)
        self.assertIn("No headings, bullets, markdown", TURN_SYSTEM)

    def test_turn_prompt_treats_user_idea_as_the_brief(self):
        self.assertIn("Work with their idea", TURN_SYSTEM)
        self.assertIn("Direct most criticism at the other panellists", TURN_SYSTEM)
        self.assertIn("preserves their intent", TURN_SYSTEM)


class RoomIsolationTests(unittest.TestCase):
    """The promise the UI's per-room transcript rests on: what is said in a
    working room reaches nobody outside it, and nobody who was not there when
    it was said."""

    def meeting(self):
        return Meeting(
            "a night coffee shop",
            [persona("Builder"), persona("Skeptic"), persona("Operator"), persona("Latecomer")],
            turn_fn=lambda _persona, _context: {},
            vote_fn=lambda _persona, _question: True,
        )

    def test_side_room_talk_is_invisible_in_plenary(self):
        meeting = self.meeting()
        builder, skeptic = meeting.agents["Builder"], meeting.agents["Skeptic"]
        meeting._move(builder, "room-a", kind="joined")
        meeting._move(skeptic, "room-a", kind="joined")
        meeting._emit("room-a", "spoke", "Builder", {"text": "the secret plan"})
        meeting._emit(PLENARY, "spoke", "Operator", {"text": "said in the open"})

        self.assertIn("the secret plan", meeting._render_context(skeptic))
        operator = meeting._render_context(meeting.agents["Operator"])
        self.assertNotIn("the secret plan", operator)
        self.assertIn("said in the open", operator)

    def test_joining_a_room_does_not_reveal_what_was_said_before(self):
        meeting = self.meeting()
        builder, skeptic = meeting.agents["Builder"], meeting.agents["Skeptic"]
        meeting._move(builder, "room-a", kind="joined")
        meeting._move(skeptic, "room-a", kind="joined")
        meeting._emit("room-a", "spoke", "Builder", {"text": "before you arrived"})

        latecomer = meeting.agents["Latecomer"]
        meeting._move(latecomer, "room-a", kind="joined")
        meeting._emit("room-a", "spoke", "Builder", {"text": "after you arrived"})

        context = meeting._render_context(latecomer)
        self.assertNotIn("before you arrived", context)
        self.assertIn("after you arrived", context)

    def test_every_event_is_stamped_with_the_room_it_happened_in(self):
        """The per-room transcript filters on this field, so nothing may be
        emitted without a room."""
        meeting = self.meeting()
        builder = meeting.agents["Builder"]
        meeting._move(builder, "room-b", kind="joined")
        meeting._apply_action(builder, {
            "tool": "propose", "title": "Run the numbers", "body": "Model one shift."
        })

        self.assertTrue(meeting.log)
        self.assertTrue(all(ev.room for ev in meeting.log))
        self.assertEqual([ev.room for ev in meeting.log if ev.kind == "proposed"], ["room-b"])
        self.assertEqual(meeting.proposals["p1"].room, "room-b")


if __name__ == "__main__":
    unittest.main()
