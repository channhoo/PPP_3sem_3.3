"""Окно и управление игры «Кот-сапёр»."""

from math import cos, sin, tau
from pathlib import Path
from random import Random

import pygame

from game import Game, LEVELS


ASSETS = Path(__file__).with_name("assets")
WIDTH, HEIGHT = 1120, 700
CREAM = "#f2e8d5"
DARK = "#29232b"
GOLD = "#f4ce86"
NUMBER_COLORS = (
    DARK, "#294666", "#36562c", "#922f28", "#544284",
    "#774323", "#286569", "#542842", DARK,
)


def load_image(name, size, keep_ratio=True):
    """Загрузить PNG и подобрать размер для игрового окна."""
    path = ASSETS / f"{name}.png"
    if not path.is_file():
        raise FileNotFoundError(f"Положи файл {name}.png в папку assets")

    image = pygame.image.load(path).convert_alpha()
    if keep_ratio:
        size = image.get_rect().fit(pygame.Rect((0, 0), size)).size
    return pygame.transform.smoothscale(image, size)


def make_tile(size, base, light, shadow, flecks):
    """Нарисовать плитку с лёгкой пиксельной фактурой."""
    tile = pygame.Surface((size, size), pygame.SRCALPHA)
    rect = tile.get_rect()

    pygame.draw.rect(tile, shadow, rect, border_radius=4)
    pygame.draw.rect(tile, base, rect.inflate(-2, -2), border_radius=3)
    pygame.draw.line(tile, light, (4, 2), (size - 5, 2))

    rng = Random(17)
    for _ in range(size // 2):
        x = rng.randrange(4, size - 5)
        y = rng.randrange(4, size - 5)
        color = rng.choice(flecks)
        pygame.draw.rect(tile, color, (x, y, rng.randint(1, 3), 2))

    return tile

class App:
    """Рисует игру и обрабатывает нажатия мыши и клавиатуры."""

    def __init__(self):
        """Создать окно, загрузить картинки и начать партию."""
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Кот-сапёр")
        self.clock = pygame.time.Clock()
        self.title_font = pygame.font.SysFont("georgia,dejavuserif", 42, True)
        self.font = pygame.font.SysFont("arial,dejavusans", 20, True)
        self.small_font = pygame.font.SysFont("arial,dejavusans", 16)

        self.background = load_image("background", (WIDTH, HEIGHT), False)
        self.cat = load_image("cat", (290, 390))
        self.win = load_image("win", (290, 290))
        self.lose = load_image("lose", (290, 290))
        self.bomb_image = load_image("bomb", (128, 128))

        self.level_buttons = {
            level: pygame.Rect(380 + index * 128, 24, 120, 42)
            for index, level in enumerate(LEVELS)
        }
        self.restart = pygame.Rect(865, 24, 220, 42)
        self.level = "Средний"
        self.new_game()

    def new_game(self):
        """Сбросить партию и подобрать размер плиток."""
        self.game = Game(self.level)
        self.hit_cell = None
        self.hit_time = 0

        self.tile = min(54, 736 // self.game.cols, 544 // self.game.rows)
        size = self.tile - 2
        self.closed_tile = make_tile(
            size, "#686b47", "#91936b", "#41452f",
            ("#717551", "#606544"),
        )
        self.open_tile = make_tile(
            size, "#e4d8bf", "#fff1d5", "#ad9c81",
            ("#eaddc5", "#dbcdb2"),
        )
        self.hit_tile = make_tile(
            size, "#753c3e", "#af6862", "#4d292d",
            ("#804648", "#6e3639"),
        )
        self.board = pygame.Rect(
            0, 0, self.tile * self.game.cols, self.tile * self.game.rows
        )
        self.board.center = (392, 380)
        self.number_font = pygame.font.SysFont(
            "arial,dejavusans", int(self.tile * 0.6), True
        )
        size = self.tile - 4
        icon_size = self.bomb_image.get_rect().fit(
            pygame.Rect(0, 0, size, size)
        ).size
        self.bomb = pygame.transform.smoothscale(self.bomb_image, icon_size)
        self.faded_bomb = self.bomb.copy()
        self.faded_bomb.set_alpha(105)

    def click(self, pos, button):
        """Обработать клик по кнопке или клетке."""
        if button == 1:
            if self.restart.collidepoint(pos):
                self.new_game()
                return
            for level, rect in self.level_buttons.items():
                if rect.collidepoint(pos):
                    if self.level != level:
                        self.level = level
                        self.new_game()
                    return

        if not self.board.collidepoint(pos):
            return

        cell = (
            (pos[1] - self.board.y) // self.tile,
            (pos[0] - self.board.x) // self.tile,
        )
        if button == 3:
            self.game.toggle_flag(cell)
        elif button == 1 and self.game.reveal(cell):
            self.hit_cell = cell
            self.hit_time = pygame.time.get_ticks()

    def _text(self, text, center, font=None, color=CREAM):
        label = (font or self.font).render(text, True, color)
        self.screen.blit(label, label.get_rect(center=center))

    def _button(self, rect, text, active):
        color = "#602b27" if active else "#49404e"
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        pygame.draw.rect(self.screen, "#ab927e", rect, 1, border_radius=8)
        self._text(text, rect.center)

    def _cell_rect(self, cell):
        row, col = cell
        return pygame.Rect(
            self.board.x + col * self.tile,
            self.board.y + row * self.tile,
            self.tile,
            self.tile,
        )

    def _flag(self, rect, wrong):
        x, y = rect.x + rect.width // 3, rect.y + rect.height // 4
        pygame.draw.line(
            self.screen, CREAM, (x, y), (x, rect.bottom - 4), 2
        )
        pygame.draw.polygon(
            self.screen, "#ea926f",
            [(x, y), (rect.right - 4, y + 4), (x, y + 8)],
        )
        if wrong:
            pygame.draw.line(
                self.screen, GOLD, rect.bottomleft, rect.topright, 2
            )

    def _draw_board(self, elapsed):
        frame = self.board.inflate(12, 12)
        pygame.draw.rect(self.screen, DARK, frame, border_radius=9)
        pygame.draw.rect(self.screen, "#ab927e", frame, 2, border_radius=9)
        mouse = pygame.mouse.get_pos()
        ended = self.game.status != "playing"

        for cell in self.game.cells:
            rect = self._cell_rect(cell)
            face = rect.inflate(-2, -2)
            opened = cell in self.game.opened
            hit = cell in self.game.hits
            tile_image = self.open_tile if opened else self.closed_tile
            if hit:
                tile_image = self.hit_tile
            self.screen.blit(tile_image, face.topleft)
            
            if opened:
                number = self.game.number(cell)
                if number:
                    self._text(
                        str(number), rect.center, self.number_font,
                        NUMBER_COLORS[number],
                    )
            elif hit or (ended and cell in self.game.mines):
                icon = self.bomb if hit else self.faded_bomb
                self.screen.blit(icon, icon.get_rect(center=rect.center))
            elif cell in self.game.flags:
                self._flag(face, wrong=ended)

            if not ended and not opened and not hit:
                if rect.collidepoint(mouse):
                    pygame.draw.rect(
                        self.screen, GOLD, face, 2, border_radius=4
                    )

        if self.hit_cell is not None and elapsed < 380:
            x, y = self._cell_rect(self.hit_cell).center
            radius = self.tile * (0.35 + elapsed / 500)
            size = max(2, 6 - elapsed // 80)
            for index in range(8):
                angle = tau * index / 8
                px = int(x + cos(angle) * radius)
                py = int(y + sin(angle) * radius)
                pygame.draw.rect(self.screen, GOLD, (px, py, size, size))

    def _draw_sidebar(self, elapsed):
        panel = pygame.Rect(786, 108, 310, 544)
        pygame.draw.rect(self.screen, DARK, panel, border_radius=14)

        title, picture = "В игре", self.cat
        if self.game.status == "won":
            title, picture = "Победа", self.win
        elif self.game.status == "lost":
            title, picture = "Поражение", self.lose
        elif elapsed < 900:
            title, picture = "Айай…", self.lose

        for index in range(3):
            x = 887 + 54 * index
            color = "#e77b77" if index < self.game.lives else "#50434d"
            pygame.draw.circle(self.screen, color, (x - 7, 146), 9)
            pygame.draw.circle(self.screen, color, (x + 7, 146), 9)
            pygame.draw.polygon(
                self.screen, color,
                [(x - 15, 149), (x + 15, 149), (x, 168)],
            )

        self._text(title, (941, 193))
        self.screen.blit(picture, picture.get_rect(center=(941, 408)))
        self._text(
            f"Мин: {self.game.mine_count}    Флажков: {len(self.game.flags)}",
            (941, 628), self.small_font,
        )

    def draw(self):
        """Нарисовать текущий кадр."""
        self.screen.blit(self.background, (0, 0))
        pygame.draw.rect(self.screen, DARK, (0, 0, WIDTH, 84))
        self._text("Кот-сапёр", (165, 43), self.title_font)

        for level, rect in self.level_buttons.items():
            self._button(rect, level, active=(level == self.level))
        self._button(self.restart, "Новая игра", active=True)

        elapsed = 9999
        if self.hit_cell is not None:
            elapsed = pygame.time.get_ticks() - self.hit_time

        self._draw_board(elapsed)
        self._draw_sidebar(elapsed)
        self._text(
            "ЛКМ — открыть    ПКМ — флажок    R — новая игра",
            (392, 675), self.small_font,
        )

    def run(self):
        """Обновлять окно до его закрытия."""
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                    if event.key == pygame.K_r:
                        self.new_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.click(event.pos, event.button)

            self.draw()
            pygame.display.flip()
            self.clock.tick(60)


def main():
    """Запустить игру."""
    pygame.display.init()
    pygame.font.init()
    try:
        App().run()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
