"""Правила игры «Кот-сапёр»."""

from random import sample


LEVELS = {
    "Лёгкий": (9, 9, 10),
    "Средний": (16, 16, 40),
    "Сложный": (16, 30, 99),
}


class Game:
    """Хранит поле, жизни и результат одной партии."""

    def __init__(self, level="Средний"):
        """Создать закрытое поле выбранного уровня."""
        self.rows, self.cols, self.mine_count = LEVELS[level]
        self.cells = [
            (row, col)
            for row in range(self.rows)
            for col in range(self.cols)
        ]
        self.mines = set()
        self.opened = set()
        self.flags = set()
        self.hits = set()
        self.lives = 3
        self.status = "playing"

    def neighbors(self, cell):
        """Перебрать соседей клетки в пределах поля."""
        row, col = cell
        for y in range(max(0, row - 1), min(self.rows, row + 2)):
            for x in range(max(0, col - 1), min(self.cols, col + 2)):
                if (y, x) != cell:
                    yield y, x

    def number(self, cell):
        """Посчитать соседние мины, включая сработавшие."""
        return sum(
            other in self.mines for other in self.neighbors(cell)
        )

    def toggle_flag(self, cell):
        """Поставить или снять флажок на закрытой клетке."""
        if self.status != "playing" or cell in self.opened | self.hits:
            return
        if cell in self.cells:
            self.flags.symmetric_difference_update({cell})

    def reveal(self, cell):
        """Открыть клетку и вернуть True при попадании на мину."""
        unavailable = self.flags | self.opened | self.hits
        if (
            self.status != "playing"
            or cell not in self.cells
            or cell in unavailable
        ):
            return False

        if not self.mines:
            safe = {cell, *self.neighbors(cell)}
            candidates = [other for other in self.cells if other not in safe]
            self.mines = set(sample(candidates, self.mine_count))

        if cell in self.mines:
            self.hits.add(cell)
            self.lives -= 1
            if self.lives == 0:
                self.status = "lost"
            return True

        pending = [cell]
        self.opened.add(cell)
        while pending:
            current = pending.pop()
            if self.number(current) == 0:
                # Помечаем клетку сразу, чтобы не добавлять её повторно.
                for other in self.neighbors(current):
                    if other not in self.opened and other not in self.flags:
                        self.opened.add(other)
                        pending.append(other)

        if len(self.opened) == len(self.cells) - self.mine_count:
            self.status = "won"
        return False
