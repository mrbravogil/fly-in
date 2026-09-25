from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .graph import Graph


class Drone(BaseModel):
    """Represents a single drone entity in the simulation."""

    id: str = 'D0'
    current_hub: Hub | None = None
    current_connection: Connection | None = None
    path: list[Hub] = []
    path_index: int = 0
    status: str = 'normal'

    def can_move(self, connection: 'Connection') -> bool:
        next_hub = self.next_hub()
        if next_hub is None:
            return False

        elif (
            next_hub is not None
            and next_hub.max_drone_capacity() is False
            and self.has_finished() is False
        ):
            return True

        return False

    def next_hub(self) -> 'Hub' | None:
        i: int = 0
        for hub in self.path:
            if self.current_hub and hub.name == self.current_hub.name:
                if self.path[i].name == 'goal':
                    self.current_hub
                else:
                    return self.path[i + 1]
            i += 1

        return self.current_hub

    def move_next_hub(self, hub: 'Hub') -> None:
        if hub.max_drone_capacity() is False and self.current_hub:
            if len(self.current_hub.drones):
                self.current_hub.drones.pop(0)
            self.current_hub = hub
            hub.drones.append(self)

    def has_finished(self) -> bool:
        if self.current_hub and self.current_hub.is_end:
            return True
        return False


class Hub(BaseModel):
    """Represents a zone or hub in the network.

    Attributes:
        color: ANSI color code for terminal visualization.
        type: Zone type ("start", "end", "hub", or "normal").
        reset: ANSI reset code for terminal color.
        drones: List of drones currently occupying this cell.
        capacity: Maximum number of drones allowed in this cell.
        zone: Zone behavior type ("normal", "restricted", "priority",
            "blocked").
        reserved: Count of reserved capacity slots (unused in current
            implementation).
    """

    name: str
    x: int
    y: int
    colour: str = 'white'
    zone: str = 'normal'
    drones: list[Drone] = Field(default_factory=list)
    max_drones: int = Field(ge=1, default=9999)
    connections: list['Hub'] = Field(default_factory=list)
    weight: int = 0
    reserved: bool = False
    is_start: bool = False
    is_end: bool = False
    occupied: bool = False

    def max_drone_capacity(self) -> bool:
        if len(self.drones) == self.max_drones:
            return True
        return False

    def define_hub_connections(self, graph: 'Graph') -> None:
        if len(self.connections) == 0:
            raise ValueError('hub error, no connections found.')


class Connection(BaseModel):

    id: str = 'C0'
    hub_a: str
    hub_b: str
    current_drones: list[Drone] = []
    max_link_capacity: int = 9999

    def has_capacity(self) -> bool:
        if len(self.current_drones) == self.max_link_capacity:
            return False
        return True

    def enter(self, drone: Drone) -> None:
        if self.has_capacity is True:
            self.current_drones.append(drone)
            drone.current_connection = self

    def leave(self, drone: Drone) -> None:
        self.current_drones.remove(drone)
        drone.current_connection = None


"""model_rebuild() tells Pydantic to resolve forward references
in type annotations after all classes are defined.

Replaces type name written as text with the actual class
"""
Drone.model_rebuild()
Hub.model_rebuild()
