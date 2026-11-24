"""Окно и управление игры «Кот-сапёр»."""

from math import cos, sin, tau
from pathlib import Path
from random import Random

import pygame

from game import LEVELS, Game

ASSETS = Path(__file__).with_name("assets")
WIDTH, HEIGHT = 1120, 700
CREAM = "#f2e8d5"
DARK = "#29232b"
GOLD = "#f4ce86"
NUMBER_COLORS = (
    DARK,
    "#294666",
    "#36562c",
    "#922f28",
    "#544284",
    "#774323",
    "#286569",
    "#542842",
    DARK,
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


def make_tile(size, base, light, shadow, flecks, grass=False):
    """Нарисовать плитку с пиксельной фактурой."""
    tile = pygame.Surface((size, size), pygame.SRCALPHA)
    rect = tile.get_rect()
    pygame.draw.rect(tile, shadow, rect, border_radius=4)

    inner = pygame.Rect(1, 1, size - 3, size - 4)
    pygame.draw.rect(tile, base, inner, border_radius=3)

    rng = Random(17)
    if grass:
        block = max(3, size // 7)
        tile.set_clip(inner.inflate(-2, -2))

        for _ in range(16):
            x = rng.randrange(2, size - 3)
            y = rng.randrange(2, size - 4)
            color = rng.choice(flecks)
            pygame.draw.rect(tile, color, (x, y, block * 2, block))
            pygame.draw.rect(tile, color, (x + block, y - block, block, block * 3))

        tile.set_clip(None)
    else:
        for _ in range(size // 3):
            x = rng.randrange(4, size - 5)
            y = rng.randrange(4, size - 5)
            pygame.draw.rect(tile, rng.choice(flecks), (x, y, 3, 2))

    pygame.draw.line(tile, light, (4, 2), (size - 5, 2))
    pygame.draw.line(tile, light, (2, 4), (2, size - 6))
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
            size,
            "#708038",
            "#a7b758",
            "#384520",
            ("#839344", "#77873e", "#627332", "#55652c"),
            grass=True,
        )
        self.open_tile = make_tile(
            size,
            "#e4d8bf",
            "#fff1d5",
            "#ad9c81",
            ("#eaddc5", "#dbcdb2"),
        )
        self.hit_tile = make_tile(
            size,
            "#753c3e",
            "#af6862",
            "#4d292d",
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
        icon_size = self.bomb_image.get_rect().fit(pygame.Rect(0, 0, size, size)).size
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
        """Нарисовать кнопку с тенью и подсветкой при наведении."""
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        text_color = "#472d22"

        if rect == self.restart:
            fill = "#b95b43" if hovered else "#a94228"
            border = "#f0b18b"
            highlight = "#df8a68"
            text_color = "#fff1dc"
        elif active:
            fill = "#f7d998" if hovered else "#eac480"
            border = "#ffebb6"
            highlight = "#fff2cf"
        else:
            fill = "#fff0d1" if hovered else "#e6d3ad"
            border = "#be9768"
            highlight = "#fff2d9"

        pygame.draw.rect(self.screen, "#211a18", rect.move(0, 3), border_radius=8)
        pygame.draw.rect(self.screen, fill, rect, border_radius=8)
        pygame.draw.rect(self.screen, border, rect, 2, border_radius=8)
        pygame.draw.line(
            self.screen,
            highlight,
            (rect.left + 8, rect.top + 3),
            (rect.right - 9, rect.top + 3),
        )
        self._text(text, rect.center, color=text_color)

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
        pygame.draw.line(self.screen, CREAM, (x, y), (x, rect.bottom - 4), 2)
        pygame.draw.polygon(
            self.screen,
            "#ea926f",
            [(x, y), (rect.right - 4, y + 4), (x, y + 8)],
        )
        if wrong:
            pygame.draw.line(self.screen, GOLD, rect.bottomleft, rect.topright, 2)

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
                        str(number),
                        rect.center,
                        self.number_font,
                        NUMBER_COLORS[number],
                    )
            elif hit or (ended and cell in self.game.mines):
                icon = self.bomb if hit else self.faded_bomb
                self.screen.blit(icon, icon.get_rect(center=rect.center))
            elif cell in self.game.flags:
                self._flag(face, wrong=ended)

            can_hover = not ended and not opened and not hit
            if can_hover and rect.collidepoint(mouse):
                pygame.draw.rect(self.screen, GOLD, face, 2, border_radius=4)

        if self.hit_cell is not None and elapsed < 380:
            x, y = self._cell_rect(self.hit_cell).center
            radius = self.tile * (0.35 + elapsed / 500)
            size = max(2, 6 - elapsed // 80)
            for index in range(8):
                angle = tau * index / 8
                px = int(x + cos(angle) * radius)
                py = int(y + sin(angle) * radius)
                pygame.draw.rect(self.screen, GOLD, (px, py, size, size))

    def _draw_heart(self, x, y, filled):
        pattern = (
            ".##...##.",
            "####.####",
            "#########",
            "#########",
            ".#######.",
            "..#####..",
            "...###...",
            "....#....",
        )
        pixel = 4
        color = "#e77b77" if filled else "#62556a"
        shadow = "#813f49" if filled else "#3d3445"

        for row, line in enumerate(pattern):
            for col, mark in enumerate(line):
                if mark == "#":
                    rect = pygame.Rect(x + col * pixel, y + row * pixel, pixel, pixel)
                    pygame.draw.rect(self.screen, shadow, rect.move(0, 3))
                    pygame.draw.rect(self.screen, color, rect)

        if filled:
            pygame.draw.rect(self.screen, "#ffb9b2", (x + 4, y + 4, pixel * 2, pixel))

    def _draw_sidebar(self, elapsed):
        center_x = 941
        title, picture = "В игре", self.cat

        if self.game.status == "won":
            title, picture = "Победа", self.win
        elif self.game.status == "lost":
            title, picture = "Поражение", self.lose
        elif elapsed < 900:
            title, picture = "Айай…", self.lose

        header = pygame.Rect(813, 111, 256, 96)
        pygame.draw.rect(self.screen, DARK, header, border_radius=12)
        pygame.draw.rect(self.screen, "#ab927e", header, 1, border_radius=12)

        for index in range(3):
            self._draw_heart(869 + index * 54, 125, index < self.game.lives)

        finished = self.game.status in ("won", "lost")
        if not finished:
            self._text(title, (center_x, 183))

        picture_rect = picture.get_rect(center=(center_x, 411))
        if picture is not self.cat:
            border = "#ab927e"
            banner_color = DARK
            if self.game.status == "won":
                border, banner_color = "#edc474", "#53612d"
            elif self.game.status == "lost":
                border, banner_color = "#dc896c", "#753c3e"

            frame = picture_rect.inflate(12, 12)
            pygame.draw.rect(self.screen, "#211a18", frame.move(0, 4), border_radius=9)
            pygame.draw.rect(self.screen, DARK, frame, border_radius=9)
            pygame.draw.rect(self.screen, border, frame, 3, border_radius=9)

        self.screen.blit(picture, picture_rect)

        if finished:
            banner = pygame.Rect(0, 0, 180, 36)
            banner.midbottom = (center_x, picture_rect.top + 14)
            pygame.draw.rect(self.screen, "#211a18", banner.move(0, 3), border_radius=8)
            pygame.draw.rect(self.screen, banner_color, banner, border_radius=8)
            pygame.draw.rect(self.screen, border, banner, 2, border_radius=8)
            self._text(title, banner.center)

        footer = pygame.Rect(813, 622, 256, 36)
        pygame.draw.rect(self.screen, DARK, footer, border_radius=8)
        self._text(
            f"Мин: {self.game.mine_count}    Флажков: {len(self.game.flags)}",
            footer.center,
            self.small_font,
        )

    def _title_flower(self, x, y):
        """Нарисовать маленький сиреневый цветок в шапке."""
        pygame.draw.rect(self.screen, "#596336", (x - 2, y + 3, 4, 13))
        pygame.draw.rect(self.screen, "#82904b", (x - 8, y + 9, 7, 4))
        pygame.draw.rect(self.screen, "#82904b", (x + 2, y + 7, 7, 4))

        for dx, dy in ((0, -7), (-7, 0), (7, 0), (0, 7)):
            petal = pygame.Rect(x + dx - 4, y + dy - 4, 8, 8)
            pygame.draw.rect(self.screen, "#806397", petal.move(0, 2))
            pygame.draw.rect(self.screen, "#cbb4e2", petal)

        pygame.draw.rect(self.screen, "#f4ce86", (x - 3, y - 3, 6, 6))

    def draw(self):
        """Нарисовать текущий кадр."""
        self.screen.blit(self.background, (0, 0))
        pygame.draw.rect(self.screen, DARK, (0, 0, WIDTH, 84))
        pygame.draw.line(self.screen, "#ab927e", (0, 83), (WIDTH, 83), 2)
        title = "Кот-сапёр"
        half_width = self.title_font.size(title)[0] // 2
        offset = half_width + 19

        self._title_flower(165 - offset, 42)
        self._title_flower(165 + offset, 42)
        self._text(title, (165, 43), self.title_font)

        for level, rect in self.level_buttons.items():
            self._button(rect, level, active=(level == self.level))
        self._button(self.restart, "Новая игра", active=True)

        elapsed = 9999
        if self.hit_cell is not None:
            elapsed = pygame.time.get_ticks() - self.hit_time

        self._draw_board(elapsed)
        self._draw_sidebar(elapsed)

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
