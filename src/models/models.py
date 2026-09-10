from pydantic import BaseModel, Field, model_validator
from .graph import Graph


class Drone(BaseModel):
    """Represents a single drone entity in the simulation."""

    id: str = f'D{id}'
    current_hub: 'Hub'
    path: list[tuple[str, str]] = []
    path_index: int
    status: str = 'normal'

    def move(self, hub: 'Hub') -> None:
        if self.current_hub.x == hub.x and self.current_hub.y == hub.y:
            raise ValueError('drone cannot stay in the same spot.')

        if not hub.max_drone_capacity():
            self.current_hub = hub
            hub.drones.append(self)
        else:
            raise ValueError('hub has reached max_drone_capacity')

    def has_finished(self) -> bool:
        if self.current_hub.is_end:
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
    color: str = 'white'
    zone: str = 'normal'
    drones: list[Drone] = []
    max_drones: int = Field(ge=1, default=1)
    connections: list['Hub'] = []
    weight: int = 0
    reserved: bool = False
    is_start: bool = False
    is_end: bool = False
    occupied: bool = False

    def max_drone_capacity(self) -> bool:
        if len(self.drones) >= self.max_drones:
            return True
        return False

    def define_hub_connections(self, graph: 'Graph') -> None:
        if len(self.connections) == 0:
            raise ValueError('hub error, no connections found.')


class Connection(BaseModel):

    id: str = f'C{id}'
    hub_a: Hub
    hub_b: Hub
    max_link_capacity: int = 0
