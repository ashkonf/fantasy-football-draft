import unittest
from src.infra import Player

class TestPlayer(unittest.TestCase):
    def test_similarity(self):
        # Test case 1: Identical names
        player1 = Player("John Doe")
        player2 = Player("John Doe")
        self.assertEqual(player1.similarity(player2), 0.0)

        # Test case 2: Simplified names
        player3 = Player("John Doe Jr.")
        player4 = Player("John Doe")
        self.assertEqual(player3.similarity(player4), 1.0)

        # Test case 3: Different names
        player5 = Player("Jane Smith")
        player6 = Player("John Doe")
        self.assertEqual(player5.similarity(player6), float('inf'))

if __name__ == '__main__':
    unittest.main()

