from __future__ import annotations

from dataclasses import dataclass


def attack_release(current: float, target: float, *, attack: float = 0.35, release: float = 0.08) -> float:
    """Move toward target quickly on attack and slowly on release."""
    rate = attack if target > current else release
    return current + (target - current) * _clamp01(rate)


@dataclass
class FormState:
    """Small mutable state for generators that want behavior and memory."""

    energy_memory: float = 0.0
    damage_memory: float = 0.0
    growth_pressure: float = 0.0
    cooldown: float = 0.0
    brightness_memory: float = 0.0
    roughness_memory: float = 0.0

    def update(
        self,
        *,
        energy: float,
        event_strength: float = 0.0,
        brightness: float = 0.0,
        roughness: float = 0.0,
        silence: bool = False,
        memory: float = 0.92,
        attack: float = 0.40,
        release: float = 0.08,
        heal_rate: float = 0.035,
        cooldown_release: float = 0.16,
    ) -> "FormState":
        """Update dynamic state from one feature frame.

        Loudness builds pressure, events accumulate damage/scars, silence heals,
        and cooldown keeps repeated events from behaving like isolated spikes.
        """
        memory = _clamp01(memory)
        energy = _clamp01(energy)
        event_strength = _clamp01(event_strength)
        brightness = _clamp01(brightness)
        roughness = _clamp01(roughness)

        self.energy_memory = attack_release(self.energy_memory, energy, attack=attack, release=release)
        self.brightness_memory = attack_release(self.brightness_memory, brightness, attack=attack * 0.75, release=release)
        self.roughness_memory = attack_release(self.roughness_memory, roughness, attack=attack, release=release * 1.5)

        pressure_target = 0.65 * self.energy_memory + 0.35 * max(event_strength, self.cooldown)
        self.growth_pressure = (self.growth_pressure * memory) + (pressure_target * (1.0 - memory))

        self.damage_memory = max(self.damage_memory * memory, event_strength)
        if silence:
            self.damage_memory = max(0.0, self.damage_memory - heal_rate)
            self.growth_pressure *= 1.0 - (heal_rate * 0.8)

        self.cooldown = max(event_strength, self.cooldown * (1.0 - _clamp01(cooldown_release)))
        return self

    def snapshot(self) -> dict[str, float]:
        return {
            "energy_memory": float(self.energy_memory),
            "damage_memory": float(self.damage_memory),
            "growth_pressure": float(self.growth_pressure),
            "cooldown": float(self.cooldown),
            "brightness_memory": float(self.brightness_memory),
            "roughness_memory": float(self.roughness_memory),
        }


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
