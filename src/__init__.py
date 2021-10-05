import pygame
import random
from pygame import Vector2

from src.util import circle_collide_rect, draw_hp
from src.util import draw_circle

from .unit import Unit
from .unit import Infantry
from .gui import GUI

pygame.init()


class Options:
    def __init__(self):
        self.show_fps = False
        self.show_grid = False
        self.show_path = False
        self.show_health = False
        self.show_range = False


class Game:
    def __init__(self) -> None:
        self.scale = 3
        self.screen_size = Vector2(240, 240)
        self.scr = pygame.Surface(self.screen_size)
        self.win = pygame.display.set_mode(
            list(map(int, self.screen_size*self.scale)))
        pygame.display.set_caption('micro capture')
        self.clock = pygame.time.Clock()

        self.selection = None
        self.select_start = None

        self.units = []

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

        for unit in self.units:
            unit.separation(self.grid.query_circle(
                unit.pos, unit.size + unit.size/2))
            unit.find_target(self.grid.query_circle(
                unit.pos, unit.weapon.range))
            unit.update(dt)
            unit.restrict_to_surface(self.scr)

        [building.update(dt) for building in self.buildings]
        self.units = [unit for unit in self.units if unit.alive]
        self.selected_units = [unit for unit in self.selected_units
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
        # if event.type == pygame.KEYDOWN:
        #     pass

        keys = pygame.key.get_pressed()
        rpos = Vector2(random.random()-0.5, random.random()-0.5)
        if keys[pygame.K_1]:
            pos = Vector2(60, 60) + rpos
            self.units.append(Infantry(pos, faction=0))
        if keys[pygame.K_2]:
            pos = Vector2(self.screen_size.x - 60, 60) + rpos
            self.units.append(Infantry(pos, faction=1))
        if keys[pygame.K_3]:
            pos = Vector2(self.screen_size.x - 60,
                          self.screen_size.y - 60) + rpos
            self.units.append(Infantry(pos, faction=2))
        if keys[pygame.K_4]:
            pos = Vector2(60, self.screen_size.y - 60) + rpos
            self.units.append(Infantry(pos, faction=3))

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
                dist = self.select_start.distance_to(mpos)
                unit = self.get_unit_at(mpos)
                if dist <= 1 and unit:
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
        # [t.draw(self.scr) for u in self.units for t in u.trails]

        # draw the selection rings
        [draw_circle(self.scr, (0, 200, 0, 100), unit.pos, unit.size+2, 1)
            for unit in self.selected_units]

        # draw the units
        [unit.draw(self.scr) for unit in self.units]

        # draw the buildings
        [building.draw(self.scr) for building in self.buildings]

        # draw the range rings
        if self.options.show_range:
            for unit in self.units:
                draw_circle(
                    self.scr, (0, 0, 100, 10),
                    unit.pos,
                    unit.weapon.range, 1)

        # draw the hp bars
        if self.options.show_health:
            [draw_hp(surface=self.scr,
                     pos=Vector2(unit.pos.x, unit.pos.y - 4),
                     size=Vector2(8, 3),
                     pct=unit.health/unit.max_health)
             for unit in self.units]

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
        start_x = int((pos.x - radius)//self.cell_size.x)
        start_y = int((pos.y - radius)//self.cell_size.y)
        end_x = int((pos.x + radius)//self.cell_size.x)
        end_y = int((pos.y + radius)//self.cell_size.y)
        for x in range(start_x, end_x+1):
            for y in range(start_y, end_y+1):
                objs.extend(self.cells.get((x, y), []))
        return objs

    # draw each cell as a rectangle
    def draw(self, surf: pygame.Surface):
        for x in range(int(self.size.x//self.cell_size.x)):
            for y in range(int(self.size.y//self.cell_size.y)):
                pygame.draw.rect(surf, (0, 0, 0, 10),
                                 (x*self.cell_size.x, y*self.cell_size.y,
                                  self.cell_size.x, self.cell_size.y), 1)
