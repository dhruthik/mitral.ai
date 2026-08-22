import random
import unittest

from mitral.personality import (
    NEUTRAL_TEMPERAMENTS,
    POSITIVE_TEMPERAMENTS,
    SKEPTICAL_TEMPERAMENT,
    sample_traits,
)


class TestGroundedTemperaments(unittest.TestCase):
    def test_cast_keeps_one_skeptic_and_balances_other_outlooks(self):
        traits = sample_traits(6, random.Random(7), mode="grounded")
        voices = [trait.voice for trait in traits]

        self.assertEqual(voices.count(SKEPTICAL_TEMPERAMENT), 1)
        self.assertEqual(sum(voice in POSITIVE_TEMPERAMENTS for voice in voices), 3)
        self.assertEqual(sum(voice in NEUTRAL_TEMPERAMENTS for voice in voices), 2)

    def test_small_cast_still_keeps_a_constructive_voice(self):
        traits = sample_traits(2, random.Random(7), mode="grounded")
        voices = [trait.voice for trait in traits]

        self.assertIn(SKEPTICAL_TEMPERAMENT, voices)
        self.assertTrue(any(voice in POSITIVE_TEMPERAMENTS for voice in voices))

    def test_full_trait_pool_can_still_be_dealt(self):
        traits = sample_traits(20, random.Random(7), mode="grounded")

        self.assertEqual(len(traits), 20)


if __name__ == "__main__":
    unittest.main()
