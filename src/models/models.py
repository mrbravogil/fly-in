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

    def move_next_hub(self, hub: 'Hub') -> None:
        if hub.max_drone_capacity() is False:
            self.current_hub = hub
            hub.drones.append(self)
        else:
            raise ValueError('hub has reached max_drone_capacity')

    def has_finished(self) -> bool:
        if self.current_hub and self.current_hub.is_end:
            return True
        return False

    # def enter_connection(self, connection: 'Connection') -> None:
    #     self.current_connection = connection

    # def leave_connection(self, connection: Connection) -> None:
    #     if self.current_connection and self.current_connection == connection:
    #         self.current_connection = None


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
    color: str = 'white'
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
        if self.has_capacity is False:
            raise ValueError('connection has reached max capacity')

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
