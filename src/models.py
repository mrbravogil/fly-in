from pydantic import BaseModel, Field, model_validator
from typing import Any
import os


class Drone(BaseModel):
    """Represents a single drone entity in the simulation."""

    id: str = f'D{id}'
    x: int
    y: int

    def move(self, hub: 'Hub') -> None:
        if self.x == hub.x and self.y == hub.y:
            raise ValueError('drone cannot stay in the same spot.')

        self.x = hub.x
        self.y = hub.y

    def has_finished(self, hub: 'Hub') -> bool:
        if hub.is_end:
            if self.x == hub.x and self.y == hub.y:
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
    capacity: int = Field(ge=1, default=1)
    zone: str = 'normal'
    drones: int = 0
    max_drones: int = Field(ge=0, default=0)
    connections: dict[int, tuple['Hub', int]] = {}
    weight: int = 0
    reserved: bool = False
    is_start: bool = False
    is_end: bool = False

    @model_validator(mode='after')
    def drone_capacity(self) -> None:
        if self.drones > self.max_drones:
            raise ValueError(f'reached max_drones limit: {self.max_drones}')

    def define_hub_connections(self, graph: 'Graph') -> None:
        if len(self.connections) == 0:
            raise ValueError('hub error, no connections found.')


class Graph(BaseModel):
    """Holds parsed graph generation configuration values.

    Attributes:

    drones: Number of drones used in the simulation
    start_hub: Coordinates and color of start hub
    hubs: Coordinates of different hubs
    end_hub: Coordinates and color of end hub
    connections: Connections between hubs

    """

    drones: int
    start_hub: Hub
    end_hub: Hub
    hubs: list[Hub]
    width: int = 0
    height: int = 0
    connections: dict[int, dict[str, Any]]
    output_file: str

    @model_validator(mode='after')
    def graph_dimensions(self) -> None:
        min_x = min(h.x for h in self.hubs)
        min_y = min(h.y for h in self.hubs)
        max_x = max(h.x for h in self.hubs)
        max_y = max(h.y for h in self.hubs)

        self.width = (max_x - min_x) + 1
        self.height = (max_y - min_y) + 1

    @model_validator(mode='after')
    def validate_start_end(self) -> None:
        sx, sy = self.start_hub.x, self.start_hub.y
        ex, ey = self.end_hub.x, self.end_hub.y

        if sx == ex and sy == ey:
            raise ValueError('Coordinates of start and end must be unique.')

    @model_validator(mode='after')
    def validate_output_path(self) -> None:
        parent_dir = os.path.dirname(os.path.abspath(self.output_file))
        if parent_dir and not os.path.isdir(parent_dir):
            raise Exception(f"Output directory does not exist: '{parent_dir}'")
