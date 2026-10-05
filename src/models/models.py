from __future__ import annotations

from pydantic import BaseModel, Field


class Drone(BaseModel):
    """Represents a single drone entity in the simulation."""

    id: str = 'D0'
    current_hub: Hub | None = None
    current_connection: Connection | None = None
    reserved_hub: str | None = None
    reserved_turn: int | None = None
    path: list[Hub] = []
    path_index: int = 0
    status: str = 'normal'

    def can_move(self, connection: 'Connection', turn: int) -> bool:
        """Check whether the drone can move across a connection this turn."""
        next_hub = self.next_hub()
        if next_hub is None:
            return False

        if next_hub.zone == 'blocked':
            return False

        if next_hub.max_drone_capacity(turn) is True:
            return False

        if self.has_finished() is True:
            return False

        if next_hub.zone == 'restricted' and self.status == 'restricted':
            return True

        if connection.has_capacity(turn) is False:
            return False

        return True

    def next_hub(self) -> 'Hub' | None:
        """Return the next hub along the drone's planned route."""
        i: int = 0
        for hub in self.path:
            if self.current_hub and hub.name == self.current_hub.name:
                if self.current_hub.is_end is False:
                    return self.path[i + 1]
            i += 1

        return self.current_hub

    def move_next_hub(self, hub: 'Hub', turn: int) -> None:
        """Move the drone to the destination hub for this turn."""
        if hub.max_drone_capacity(turn) is True or self.current_hub is None:
            return

        previous_hub = self.current_hub
        if self in previous_hub.drones:
            previous_hub.drones.remove(self)

        if self.current_connection is not None:
            self.current_connection.leave(self)

        self.current_hub = hub
        self.status = 'normal'

        if self not in hub.drones:
            hub.drones.append(self)

    def has_finished(self) -> bool:
        """Return True when the drone has reached the end hub."""
        if self.current_hub and self.current_hub.is_end:
            return True
        return False


class Hub(BaseModel):
    """Represents a zone or hub in the network."""

    name: str
    x: int
    y: int
    colour: str = 'white'
    zone: str = 'normal'
    drones: list[Drone] = Field(default_factory=list)
    max_drones: int = 9999
    turn_capacity: dict[int, int] = Field(default_factory=dict)
    connections: list['Hub'] = Field(default_factory=list)
    weight: float = 0.0
    reserved: bool = False
    is_start: bool = False
    is_end: bool = False
    occupied: bool = False

    def max_drone_capacity(self, turn: int) -> bool:
        """Return True when the hub is full for the given turn."""

        reserved: int = self.turn_capacity.get(turn, 0)
        return (len(self.drones) + reserved) >= self.max_drones

    def reserve_turn(self, turn: int) -> None:
        """Reserve one slot in the hub for the given turn."""

        self.turn_capacity[turn] = self.turn_capacity.get(turn, 0) + 1


class Connection(BaseModel):
    """Represents a link between two hubs in the graph."""

    id: str = 'C0'
    hub_a: str
    hub_b: str
    current_drones: list[Drone] = []
    turn_capacity: dict[int, int] = Field(default_factory=dict)
    max_link_capacity: int = 9999

    def has_capacity(self, turn: int) -> bool:
        """Return True when the connection still has room for this turn."""
        self.turn_capacity[turn] = len(self.current_drones)
        return self.turn_capacity[turn] < self.max_link_capacity

    def reserve_turn(self, turn: int) -> None:
        """Reserve one slot in the connection for the given turn."""
        self.turn_capacity[turn] = self.turn_capacity.get(turn, 0) + 1

    def enter(self, drone: Drone, turn: int) -> bool:
        """Register a drone entering the connection."""

        if not self.has_capacity(turn):
            return False

        if drone not in self.current_drones:
            self.current_drones.append(drone)
            drone.current_connection = self
            next_hub = drone.next_hub()
            if next_hub is not None and next_hub.zone == 'restricted':
                drone.status = 'restricted'

        return True

    def leave(self, drone: Drone) -> None:
        """Remove a drone from the connection when it leaves."""
        if drone in self.current_drones:
            self.current_drones.remove(drone)
            drone.current_connection = None


"""model_rebuild() tells Pydantic to resolve forward references
in type annotations after all classes are defined.

Replaces type name written as text with the actual class
"""
Drone.model_rebuild()
Hub.model_rebuild()
