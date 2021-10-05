from __future__ import annotations

import random
from enum import Enum
from typing import List, Any

import pygame
from pygame import Vector2

from .util import clamp
from .util import map_range

faction_colors = {
    0: (180, 0, 0),
    1: (0, 180, 0),
    2: (0, 0, 180),
    3: (180, 180, 0),
    4: (180, 0, 180),
    5: (0, 180, 180),
    6: (180, 180, 180),
}

friction = 0.1


class Unit:
    def __init__(self, pos: Vector2, size: int = 2, max_hp: int = 100,
                 mass: float = 3, max_speed: float = 40, max_force: float = 0.95,
                 perception: float = 60, spacing=None, faction=0) -> None:
        self.pos = Vector2(pos)
        self.desired_pos = Vector2(pos)
        self.vel = Vector2()
        self.size = size
        self.max_hp = max_hp
        self.mass = mass
        self.hp = max_hp
        self.acc = Vector2()
        self.max_speed = max_speed
        self.max_force = max_force
        self.spacing = spacing or (self.size + 4)
        self.faction = faction
        self.perception = perception
        self.move_targets = Queue()
        self.attack_targets = Queue()

        self.state = UnitState.idle
        self.agression_state = AgressionState.aggressive

        self.attacker = None
        self.weapon = Weapon(cooldown=1, damage=1, range=100)

        self.trails = []

    @property
    def alive(self) -> bool:
        return self.hp > 0

    @property
    def move_target(self) -> Vector2:
        if len(self.move_targets) > 0:
            return self.move_targets[0]

    @property
    def attack_target(self) -> Vector2:
        if len(self.attack_targets) > 0:
            return self.attack_targets[0]

    # === MAIN UPDATE LOOP ===

    def update(self, dt: float, others: List = []) -> None:
        pos = Vector2(self.pos)

        self.weapon.update(dt)

        self.process_agression_state(others)

        if self.move_target and (self.move_target - self.pos).length() <= self.spacing:
            self.move_targets.pop()
            if len(self.move_targets) == 0:
                self.desired_pos = Vector2(self.pos)

        self.apply_forces(dt, others)

        if pos != self.pos:
            self.trails.append(Trail(self.pos, self.size + 2))

        [trail.update(dt) for trail in self.trails]
        self.trails[:] = [t for t in self.trails if t.alive]

    # === DRAW METHODS ===

    def draw(self, surf: pygame.Surface) -> None:
        self.weapon.draw(surf)
        pygame.draw.circle(
            surf, faction_colors[self.faction], self.pos, self.size, 1)

    def draw_hp(self, surf: pygame.Surface) -> None:
        tl = self.pos - Vector2(self.size + 3, self.size + 5)
        size = Vector2(self.size + 6, 2)
        hsurf = pygame.Surface(size+Vector2(2, 2), pygame.SRCALPHA)
        pygame.draw.rect(hsurf, (0, 0, 0, 100),
                         ((0, 0), size+Vector2(2, 2)), 1)
        pygame.draw.rect(hsurf, (100, 0, 0), (Vector2(1, 1), size), 1)
        pygame.draw.rect(hsurf, (0, 200, 0),
                         (Vector2(1, 1), (size.x * (self.hp / self.max_hp), size.y)))
        surf.blit(hsurf, tl)

    # === MOVEMENT ===

    def apply_forces(self, dt: float, others: List[Unit]) -> None:
        if self.move_target:
            if len(self.move_targets) > 1:
                force = self.seek(self.move_target)
            else:
                force = self.arrive(self.move_target)
            self.apply_force(force)
        elif self.attack_target:
            self.apply_force(
                self.within_range_of_target(self.attack_target)
            )

        self.apply_force(self.separation(others))
        self.apply_force(self.friction())

        self.vel += self.acc
        self.vel = Vector2(clamp(self.vel.x, self.max_speed),
                           clamp(self.vel.y, self.max_speed))

        if self.vel.length() < 0.01:
            self.desired_pos = Vector2(self.pos)
            self.stop()

        self.pos += self.vel * dt

        self.acc = Vector2()

    def stop(self) -> None:
        self.vel = Vector2()

    def apply_force(self, force: Vector2) -> None:
        self.acc += force

    def seek(self, target: Vector2, arrival: bool = False) -> Vector2:
        distance = (target - self.pos).length()
        if distance == 0:
            return Vector2()
        speed = self.max_speed
        if arrival:
            radius = self.size * self.mass
            if distance < radius:
                speed = map_range(distance, 0, radius, 0, speed)
        desired = (target - self.pos).normalize() * speed
        force = desired - self.vel
        return Vector2(clamp(force.x, self.max_force),
                       clamp(force.y, self.max_force))

    def arrive(self, target: Vector2) -> Vector2:
        return self.seek(target, True)

    def flee(self, target: Vector2) -> Vector2:
        return self.seek(target) * -1

    def persue(self, target: Unit) -> Vector2:
        return self.seek((target.pos + target.vel) * 10)

    def evade(self, target: Unit) -> Vector2:
        return self.persue(target) * -1

    def separation(self, others: List[Unit]) -> Vector2:
        summed = Vector2()
        for other in others:
            if other == self:
                continue
            distance = (other.pos - self.pos).length()
            if distance < self.spacing:
                force = self.pos - other.pos
                if force.length() > 0:
                    force.normalize_ip()
                else:
                    force = Vector2(random.random(), random.random())
                force *= self.mass
                force *= 1 / max(distance, 1)
                summed += force
        return summed

    def friction(self) -> Vector2:
        return -self.vel * friction

    def within_range_of_target(self, target: Unit) -> Vector2:
        attack_range = min(self.perception, self.weapon.range)
        diff = target.pos - self.pos
        distance = diff.length()
        if distance > attack_range:
            return diff.normalize() * self.max_force
        return Vector2()

    # === HELPERS ===

    def add_move_target(self, target: Vector2) -> None:
        self.move_targets.append(target)

    def set_move_target(self, target: Vector2) -> None:
        self.clear_move_targets()
        self.add_move_target(target)

    def clear_move_targets(self) -> None:
        self.move_targets.clear()

    def add_attack_target(self, target: Unit) -> None:
        self.attack_targets.append(target)

    def set_attack_target(self, target: Unit) -> None:
        self.clear_attack_targets()
        self.add_attack_target(target)

    def clear_attack_targets(self) -> None:
        self.attack_targets.clear()

    def prioritize_attack_target(self, target: Unit) -> None:
        self.attack_targets.remove(target)
        self.attack_targets.appendleft(target)

    def sort_attack_targets(self) -> None:
        self.attack_targets.sort(key=lambda x: x.hp)

    def take_damage(self, damage: int) -> None:
        self.hp -= damage

    def set_attacker(self, attacker: Unit) -> None:
        self.attacker = attacker

    def unit_within_attack_range(self, unit: Unit) -> bool:
        if not self.weapon:
            return False
        return (unit.pos - self.pos).length() <= min(self.perception, self.weapon.range)

    def shoot(self, target: Unit) -> None:
        if self.weapon:
            self.weapon.fire(self, target)

    # === PROCESS STATES ===

    def process_agression_state(self, others: List[Unit] = []) -> None:
        method = {
            AgressionState.aggressive: self.be_agressive,
            AgressionState.passive: self.be_passive,
            AgressionState.defensive: self.be_defensive
        }.get(self.agression_state, None)
        if method:
            method(others)

    def be_agressive(self, others: List[Unit] = []) -> None:
        self.find_targets(others)
        self.sort_attack_targets()
        if self.attack_target and self.unit_within_attack_range(self.attack_target):
            self.shoot(self.attack_target)

    def be_passive(self, others: List[Unit] = []) -> None:
        pass

    def be_defensive(self, others: List[Unit] = []) -> None:
        if self.attacker:
            self.be_agressive([self.attacker])

    def find_targets(self, others: List[Unit] = []) -> None:
        potential_targets = []
        for other in others:
            if other is self:
                continue
            if other.faction == self.faction:
                continue
            if self.pos.distance_to(other.pos) >= self.perception:
                continue
            potential_targets.append(other)
        if potential_targets:
            [self.add_attack_target(t) for t in potential_targets]

    # === SET STATES ===
    def set_agressive_state(self) -> None:
        self.agression_state = AgressionState.aggressive

    def set_passive_state(self) -> None:
        self.agression_state = AgressionState.passive

    def set_defensive_state(self) -> None:
        self.agression_state = AgressionState.defensive


class Trail:
    def __init__(self, pos: Vector2, size: int = 10, duration: float = 10) -> None:
        self.pos = Vector2(pos)
        self.size = size
        self.iduration = duration
        self.duration = duration

    @property
    def alive(self) -> bool:
        return self.duration > 0

    def update(self, dt: float) -> None:
        self.duration -= dt
        self.duration = max(self.duration, 0)

    def draw(self, surf):
        size = (self.size + 5) * (self.duration / self.iduration)
        radius = size/2
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(surface, (30, 20, 30, 1),
                           (radius, radius), radius)
        surf.blit(surface, self.pos - Vector2(radius, radius),
                  special_flags=pygame.BLEND_ALPHA_SDL2)


class UnitState(Enum):
    idle = 0
    moving = 1
    seeking = 2
    attacking = 3
    fleeing = 4
    persuing = 5
    evading = 6
    guarding = 7


class AgressionState(Enum):
    passive = 0
    aggressive = 1
    defensive = 2


class Queue:
    def __init__(self) -> None:
        self.queue = []

    def append(self, item) -> None:
        self.queue.append(item)

    def appendleft(self, item) -> None:
        self.queue.appendleft(item)

    def pop(self, index: int = 0) -> Any:
        return self.queue.pop(index)

    def clear(self) -> None:
        self.queue = []

    def remove(self, item) -> None:
        self.queue.remove(item)

    def sort(self, key) -> None:
        self.queue.sort(key=key)

    def first(self) -> Any:
        return self.queue[0]

    def __len__(self) -> int:
        return len(self.queue)

    def __getitem__(self, item) -> Any:
        return self.queue[item]


class Weapon:
    def __init__(self, cooldown: float = 1, damage: int = 10, range: int = 100) -> None:
        self.cooldown = cooldown
        self._cooldown = cooldown
        self.damage = damage
        self.range = range
        self.ready = True
        self.fired = None

    def fire(self, handler: Unit, target: Unit) -> None:
        if self.ready:
            target.take_damage(self.damage)
            target.set_attacker(handler)
            self._cooldown = self.cooldown
            self.ready = False
            self.fired = (handler, target)

    def update(self, dt: float) -> None:
        self._cooldown -= dt
        self._cooldown = max(self._cooldown, 0)
        if self._cooldown == 0:
            self.ready = True
        self.fired = None

    def draw(self, surf):
        if self.fired:
            handler, target = self.fired
            pygame.draw.line(surf, (255, 0, 0), handler.pos, target.pos)
