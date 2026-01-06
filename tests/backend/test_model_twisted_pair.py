import unittest
from talustrace.backend.models import TwistedPair, Harness

class TestTwistedPair(unittest.TestCase):

    def setUp(self):
        self.twisted_pair = TwistedPair(
            id="tp1",
            node_a=(1.0, 2.0),
            node_b=(3.0, 4.0),
            rotation_a=90,
            rotation_b=180,
            wire_id_1="wire1",
            wire_id_2="wire2"
        )

    def test_twisted_pair_initialization(self):
        self.assertEqual(self.twisted_pair.id, "tp1")
        self.assertEqual(self.twisted_pair.node_a, (1.0, 2.0))
        self.assertEqual(self.twisted_pair.node_b, (3.0, 4.0))
        self.assertEqual(self.twisted_pair.rotation_a, 90)
        self.assertEqual(self.twisted_pair.rotation_b, 180)
        self.assertEqual(self.twisted_pair.wire_id_1, "wire1")
        self.assertEqual(self.twisted_pair.wire_id_2, "wire2")

    def test_harness_twisted_pairs(self):
        harness = Harness()
        harness.twisted_pairs.append(self.twisted_pair)
        self.assertEqual(len(harness.twisted_pairs), 1)
        self.assertEqual(harness.twisted_pairs[0].id, "tp1")

if __name__ == '__main__':
    unittest.main()