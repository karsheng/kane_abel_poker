from kane.kane_player import Kane


class TestKane:
    def test_has_straight_draw(self):
        ranks1 = [2, 3, 4, 5, 10]
        ranks2 = [9, 10, 11, 12, 11]
        ranks3 = [2, 3, 6, 10, 10]
        ranks4 = [3, 3, 3, 10, 12]
        ranks5 = [4, 5, 7, 8, 10]
        ranks6 = [5, 7, 8, 10]

        kane = Kane()

        assert kane.has_straight_draw(ranks1) == True
        assert kane.has_straight_draw(ranks2) == True
        assert kane.has_straight_draw(ranks3) == False
        assert kane.has_straight_draw(ranks4) == False
        assert kane.has_straight_draw(ranks5) == True
        assert kane.has_straight_draw(ranks6) == False

    def test_has_flush_draw(self):
        suits1 = ["H", "H", "H", "H"]
        suits2 = ["C", "C", "C", "C"]
        suits3 = ["H", "C", "S", "C"]

        kane = Kane()

        assert kane.has_flush_draw(suits1) == True
        assert kane.has_flush_draw(suits2) == True
        assert kane.has_flush_draw(suits3) == False

    def test_has_drawing_potential(self):
        kane = Kane()
        assert (
            kane.has_drawing_potential(["S2", "HK"], ["S5", "S7", "DT", "C9", "D8"])
            == True
        )
        assert (
            kane.has_drawing_potential(["S7", "HK"], ["S5", "S6", "S2", "C9", "DT"])
            == True
        )

        assert (
            kane.has_drawing_potential(["S8", "HK"], ["S6", "S7", "S2", "C9", "D3"])
            == True
        )
        assert (
            kane.has_drawing_potential(["S2", "HK"], ["S4", "D6", "H8", "CT", "DQ"])
            == False
        )
