"""Тесты игровой логики «Кота-сапёра»."""

import unittest

from game import Game, LEVELS


class GameTests(unittest.TestCase):
    """Проверить безопасный старт, потерю жизни и победу."""

    def test_first_move_is_safe(self):
        """Первый ход и его соседи безопасны на всех уровнях."""
        first_cell = (4, 4)
        for level in LEVELS:
            with self.subTest(level=level):
                game = Game(level)
                game.reveal(first_cell)
                safe_cells = {first_cell, *game.neighbors(first_cell)}
                self.assertTrue(safe_cells.isdisjoint(game.mines))
                self.assertTrue(safe_cells <= game.opened)
                self.assertEqual(len(game.mines), game.mine_count)
                self.assertEqual(game.lives, 3)

    def test_mine_takes_only_one_life(self):
        """Повторное нажатие на ту же мину сохраняет жизни."""
        game = Game()
        game.reveal((0, 0))
        mine = next(iter(game.mines))
        self.assertTrue(game.reveal(mine))
        self.assertEqual(game.lives, 2)
        self.assertIn(mine, game.hits)
        self.assertFalse(game.reveal(mine))
        self.assertEqual(game.lives, 2)

    def test_opening_all_safe_cells_wins(self):
        """Открытие всех безопасных клеток завершает партию победой."""
        game = Game("Лёгкий")
        game.reveal((0, 0))
        safe_cells = set(game.cells) - game.mines
        for cell in safe_cells:
            game.reveal(cell)
        self.assertEqual(game.opened, safe_cells)
        self.assertEqual(game.status, "won")
