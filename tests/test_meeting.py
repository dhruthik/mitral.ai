import unittest
from types import SimpleNamespace

from mitral.meeting import Meeting, TURN_SYSTEM


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
        self.assertIn("one natural sentence of at most 25 words", TURN_SYSTEM)
        self.assertIn("No headings, bullets, markdown", TURN_SYSTEM)

    def test_turn_prompt_treats_user_idea_as_the_brief(self):
        self.assertIn("Work with their idea", TURN_SYSTEM)
        self.assertIn("Direct most criticism at the other panellists", TURN_SYSTEM)
        self.assertIn("preserves their intent", TURN_SYSTEM)


if __name__ == "__main__":
    unittest.main()
