from typing import Tuple
import pygame
from pygame import Vector2, Surface

faction_colors = {
    0: (180, 0, 0),
    1: (0, 180, 0),
    2: (0, 0, 180),
    3: (180, 180, 0),
    4: (180, 0, 180),
    5: (0, 180, 180),
    6: (180, 180, 180),
}


def clamp(x, a, b=None):
    if b is None:
        a, b = -a, a
    return max(a, min(x, b))


def map_range(x, a, b, c, d):
    return (x - a) / (b - a) * (d - c) + c


def circle_collide_rect(c_pos, radius, r_pos, r_size):
    test = Vector2()
    if c_pos.x < r_pos.x:
        test.x = r_pos.x
    elif c_pos.x > r_pos.x + r_size.x:
        test.x = r_pos.x + r_size.x
    if c_pos.y < r_pos.y:
        test.y = r_pos.y
    elif c_pos.y > r_pos.y + r_size.y:
        test.y = r_pos.y + r_size.y
    return (c_pos - test).length_squared() <= radius**2


def generate_circle_surface(color: Tuple[int, int, int, int], radius: int, line_width: int = 0) -> Surface:
    size = Vector2(radius*2, radius*2)
    surf = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.circle(surf, color, size/2, radius, line_width)
    return surf


def draw_circle(surface: pygame.Surface, color: Tuple[int, int, int, int], pos: Vector2, radius: int, line_width: int = 0) -> None:
    surf = generate_circle_surface(color, radius, line_width)
    surface.blit(surf, pos - Vector2(surf.get_size())/2)


def generate_hp_surface(width: int, height: int, pct: float) -> Surface:
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    # border
    pygame.draw.rect(surf, (0, 0, 0, 100), ((0, 0), (width, height)), 1)
    # red hp bar
    pygame.draw.rect(surf, (100, 0, 0), ((1, 1), (width-2, height-2)))
    # green hp bar
    pygame.draw.rect(surf, (0, 100, 0),
                     ((1, 1), ((width-2) * pct, (height-2))))
    return surf


def draw_hp(surface: pygame.Surface, pos: Vector2, size: Vector2, pct: float) -> None:
    surf = generate_hp_surface(size.x, size.y, pct)
    surface.blit(surf, pos - Vector2(surf.get_size())/2)
