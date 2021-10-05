from __future__ import annotations

import random
from typing import Any, Tuple
from typing import List

import pygame
from pygame import Vector2

from src.util import faction_colors


class Unit:
    def __init__(self, pos: Vector2, size: int, health: int, max_force: float, max_speed: float, faction: int):
        self.pos = Vector2(pos)
        self.vel = Vector2()
        self.acc = Vector2()
        self.size = size
        self.health = health
        self.max_health = health
        self.max_force = max_force
        self.max_speed = max_speed

        self.faction = faction

        self.move_target = None
        self.attack_target = None

        self.weapon = None

    @property
    def alive(self):
        return self.health > 0

    def update(self, dt):
        self.weapon.update(dt)
        if self.attack_target is not None:
            self.weapon.fire(self.attack_target)
            if not self.attack_target.alive:
                self.attack_target = None
        if self.move_target is not None:
            if (self.move_target - self.pos).length() <= self.size:
                self.vel = Vector2()
                self.move_target = None
            else:
                self.acc += self.seek(self.move_target)
        self.vel += self.acc
        self.pos += self.vel * dt
        self.vel *= 0.9
        self.acc = Vector2()

    def draw(self, surface, color: Tuple[int, int, int] = (255, 255, 255)):
        pygame.draw.circle(surface, color, self.pos, self.size//2)

    # === MOVEMENT ===

    def seek(self, target: Vector2, arrive_radius: int = 0):
        distance = (target - self.pos).length()
        if distance == 0:
            return Vector2()
        speed = self.max_speed
        if distance < arrive_radius:
            speed = (distance/arrive_radius) * speed
        desired = (target - self.pos).normalize() * speed
        return desired - self.vel

    def separation(self, others: List[Unit]) -> Vector2:
        summed = Vector2()
        for other in others:
            if other == self:
                continue
            distance = (other.pos - self.pos).length()
            if distance < self.size:
                force = self.pos - other.pos
                if force.length() > 0:
                    force.normalize_ip()
                else:
                    force = Vector2(random.random()-0.5, random.random()-0.5)
                force *= 3
                force *= 1 / max(distance, 1)
                summed += force
        self.acc += summed

    def set_move_target(self, target):
        self.move_target = target

    def restrict_to_surface(self, surf: pygame.Surface):
        size = surf.get_size()
        self.pos.x = max(self.pos.x, 4)
        self.pos.y = max(self.pos.y, 4)
        self.pos.x = min(self.pos.x, size[0]-4)
        self.pos.y = min(self.pos.y, size[1]-4)

    # === TARGETING ===

    def set_attack_target(self, target):
        self.attack_target = target

    def find_closest(self, targets: list):
        closest = None
        for target in targets:
            if target.faction == self.faction:
                continue
            if target == self:
                continue
            if closest is None:
                closest = target
            elif (target.pos - self.pos).length() < (closest.pos - self.pos).length():
                closest = target
        return closest

    def find_target(self, targets: list):
        closest = self.find_closest(targets)
        self.attack_target = None
        if closest is None:
            return None
        if (closest.pos - self.pos).length() <= self.weapon.range:
            self.attack_target = closest

    def take_damage(self, damage: int, attacker: Any):
        self.health -= damage


class Infantry(Unit):
    def __init__(self, pos: Vector2, faction: int):
        super().__init__(pos, size=2, health=100, max_force=1, max_speed=50, faction=faction)
        self.weapon = Weapon(owner=self, range=30, damage=10, cooldown=0.5)

    def draw(self, surface):
        return super().draw(surface, faction_colors[self.faction])


class Weapon:
    def __init__(self, owner: Unit, range: int, damage: int, cooldown: float):
        self.owner = owner
        self.range = range
        self.damage = damage
        self.cooldown = cooldown
        self.ready = True
        self.cooldown_timer = 0

    def update(self, dt):
        if self.ready:
            return
        self.cooldown_timer -= dt
        if self.cooldown_timer <= 0:
            self.cooldown_timer = self.cooldown
            self.ready = True

    def fire(self, target: Any):
        if self.ready:
            target.take_damage(self.damage, self.owner)
            self.ready = False
