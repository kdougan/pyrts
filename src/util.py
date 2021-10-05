from typing import Tuple
import pygame
from pygame import Vector2, Surface


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
