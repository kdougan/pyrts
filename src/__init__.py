import pygame
import random
from pygame import Vector2

from src.util import circle_collide_rect
from src.util import draw_circle

from .unit import Unit
from .gui import GUI

pygame.init()


class Options:
    def __init__(self):
        self.show_fps = False
        self.show_grid = False
        self.show_path = False
        self.show_health = False
        self.show_perception = False


class Game:
    def __init__(self) -> None:
        self.scale = 3
        self.screen_size = Vector2(240, 240)
        self.scr = pygame.Surface(self.screen_size)
        self.win = pygame.display.set_mode(
            list(map(int, self.screen_size*self.scale)))
        self.clock = pygame.time.Clock()

        self.selection = None
        self.select_start = None

        self.units = [
            Unit((self.screen_size//4)*3),
            Unit((self.screen_size//4), faction=1)
        ]
        self.units[1].set_defensive_state()

        self.selected_units = []

        self.options = Options()

        self.grid = Grid(self.screen_size, self.screen_size//8)

        self.buildings = []

        self.gui = GUI(self)

    def run(self) -> None:
        while 1:
            dt = self.clock.tick(60)*.001
            self.update(dt)
            self.draw()

    def update(self, dt: float) -> None:
        for event in pygame.event.get():
            self.gui.process_events(event)
            self.process_events(event)

        self.gui.update(dt)

        self.grid.clear()
        self.grid.add_all(self.units)

        [unit.update(dt, others=self.grid.query_circle(unit.pos, unit.perception))
         for unit in self.units]
        [unit.update(dt, others=self.units) for unit in self.units]
        [building.update(dt) for building in self.buildings]
        self.units[:] = [unit for unit in self.units if unit.alive]
        self.selected_units[:] = [unit for unit in self.selected_units
                                  if unit.alive]

    def process_events(self, event) -> None:
        if (event.type == pygame.QUIT or
            (event.type == pygame.KEYDOWN and
                event.key == pygame.K_ESCAPE)):
            pygame.quit()
            exit()
        self.process_key_events(event)
        self.process_mouse_events(event)

    def process_key_events(self, event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                rpos = Vector2(random.random()-0.5, random.random()-0.5)
                self.units.append(Unit(((self.screen_size//4)*3)+rpos))
            if event.key == pygame.K_e:
                rpos = Vector2(random.random()-0.5, random.random()-0.5)
                self.units.append(Unit((self.screen_size//4)+rpos, faction=1))
            elif event.key == pygame.K_g:
                [unit.set_guard_mode() for unit in self.selected_units]

    def process_mouse_events(self, event) -> None:
        mpos = Vector2(pygame.mouse.get_pos())/self.scale
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.selected_units = []
                self.select_start = mpos
            elif event.button == 4:
                self.scale *= 1.1
            elif event.button == 5:
                self.scale /= 1.1

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if unit := self.get_unit_at(mpos):
                    self.selected_units = [unit]
                self.select_start = None
                self.selection = None
            elif event.button == 3:
                if self.selected_units:
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        [unit.add_move_target(mpos)
                         for unit in self.selected_units]
                    else:
                        [unit.set_move_target(mpos)
                         for unit in self.selected_units]

        elif event.type == pygame.MOUSEMOTION:
            if self.select_start and not self.selection:
                self.selection = Selection(self.select_start)
            if self.selection:
                self.selection.update(mpos)
                self.selected_units = self.get_units_in_rect(
                    self.selection.rect)

    def get_unit_at(self, pos: Vector2) -> Unit:
        for unit in self.units:
            if unit.pos.distance_to(pos) < unit.size + 4:
                return unit
        return None

    def get_units_in_rect(self, rect: pygame.Rect) -> list:
        return [unit for unit in self.units if rect.collidepoint(unit.pos)]

    def draw(self) -> None:
        self.scr.fill((40, 30, 40))

        # self.grid.draw(self.scr)

        # draw the unit targets
        [draw_circle(self.scr, (0, 200, 0, 100), unit.move_target, 2, 1)
            for unit in self.selected_units if unit.move_target]

        # draw the unit trails
        [t.draw(self.scr) for u in self.units for t in u.trails]

        # draw the units
        [unit.draw(self.scr) for unit in self.units]

        # draw the buildings
        [building.draw(self.scr) for building in self.buildings]

        # draw the selection rings
        [draw_circle(self.scr, (0, 200, 0, 100), unit.pos, unit.size+4, 1)
            for unit in self.selected_units]

        # draw the perception rings
        if self.options.show_perception:
            for unit in self.units:
                pygame.draw.circle(
                    self.scr, (0, 0, 100),
                    unit.pos,
                    unit.perception, 1)

        # draw the hp bars
        if self.options.show_health:
            [unit.draw_hp(self.scr) for unit in self.units]

        # draw the selection rect
        if self.selection:
            pygame.draw.rect(self.scr, (0, 200, 100),
                             (self.selection.rect), 1)

        pygame.transform.scale(self.scr, self.win.get_size(), self.win)
        self.gui.draw()
        pygame.display.flip()


class Selection:
    def __init__(self, pos: Vector2):
        self.pos = Vector2(pos)
        self.rect = pygame.Rect(pos.x, pos.y, 1, 1)

    def update(self, new_pos: Vector2) -> None:
        pos = Vector2(self.pos)
        size = new_pos - self.pos
        size = Vector2(abs(size.x), abs(size.y))
        if new_pos.x < pos.x:
            pos.x = new_pos.x
        if new_pos.y < pos.y:
            pos.y = new_pos.y
        self.rect = pygame.Rect(pos, size)


class Grid:
    def __init__(self, size: Vector2, cell_size: Vector2):
        self.size = size
        self.cell_size = cell_size
        self.cells = {}
        self.clear()

    def clear(self):
        self.cells = {}
        for x in range(int(self.size.x // self.cell_size.x)):
            for y in range(int(self.size.y // self.cell_size.y)):
                self.cells[(x, y)] = []

    def to_key(self, pos: Vector2):
        return (int(pos.x//self.cell_size.x), int(pos.y//self.cell_size.y))

    def add(self, obj: object):
        key = self.to_key(obj.pos)
        self.cells.setdefault(key, []).append(obj)

    def add_all(self, objs: list):
        for obj in objs:
            self.add(obj)

    def query_circle(self, pos: Vector2, radius: float) -> list:
        objs = []
        for x in range(int(pos.x-radius), int(pos.x+radius), int(self.cell_size.x)):
            for y in range(int(pos.y-radius), int(pos.y+radius), int(self.cell_size.y)):
                if circle_collide_rect(pos, radius, Vector2(x, y), self.cell_size):
                    objs.extend(self.cells.get(self.to_key(Vector2(x, y)), []))
        return objs

    # draw each cell as a rectangle
    def draw(self, surf: pygame.Surface):
        for x in range(int(self.size.x//self.cell_size.x)):
            for y in range(int(self.size.y//self.cell_size.y)):
                pygame.draw.rect(surf, (0, 0, 0, 10),
                                 (x*self.cell_size.x, y*self.cell_size.y,
                                  self.cell_size.x, self.cell_size.y), 1)
