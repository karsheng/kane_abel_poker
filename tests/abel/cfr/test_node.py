from abel.cfr.holdem_cfr import Node


class TestNode:
    def test_convert_to_relative_pot(self):
        valid_actions = [
            {"action": "fold", "amount": 0},
            {"action": "call", "amount": 1},
            {"action": "raise", "amount": {"min": 2, "max": 100}},
        ]

        pot = 10

        expected = ["f", "c", 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, "a"]

        results = Node.convert_to_relative_pot(valid_actions, pot)
        assert expected == results

    def test_convert_to_relative_pot_min_max(self):
        valid_actions = [
            {"action": "fold", "amount": 0},
            {"action": "call", "amount": 0},
            {"action": "raise", "amount": {"min": 2, "max": 100}},
        ]
        pot = 50
        expected = ["c", 0.25, 0.5, 0.75, 1, 1.5, "a"]

        results = Node.convert_to_relative_pot(valid_actions, pot)
        assert expected == results
