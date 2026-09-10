from pydantic import BaseModel, Field, model_validator
import os

from .models import Hub, Connection


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
    connections: list[Connection]
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
    def get_hub_weights(self) -> None:
        for v in self.hubs:
            if v.zone == 'normal':
                v.weight = 1
            if v.zone == 'priority':
                v.weight = 1
            if v.zone == 'restricted':
                v.weight = 2
            if v.zone == 'blocked':
                v.weight = 0

    @model_validator(mode='after')
    def validate_start_end(self) -> None:
        sx, sy = self.start_hub.x, self.start_hub.y
        ex, ey = self.end_hub.x, self.end_hub.y

        if sx == ex and sy == ey:
            raise ValueError('coordinates of start and end must be unique.')

    @model_validator(mode='after')
    def validate_output_path(self) -> None:
        parent_dir = os.path.dirname(os.path.abspath(self.output_file))
        if parent_dir and not os.path.isdir(parent_dir):
            raise Exception(f"output directory does not exist: '{parent_dir}'")

    @model_validator(mode='after')
    def validate_connections(self) -> None:
        hub_list: list[str] = []
        for h in self.hubs:
            hub_list.append(h.name)

        for c in self.connections:
            a, b = c.hub_a, c.hub_b
            if a not in hub_list or b not in hub_list:
                raise ValueError(f'connection error: {c["connection"]} is not '
                                 'a registered hub')

            a_hub: Hub = self._find_hub(a)
            b_hub: Hub = self._find_hub(b)
            a_hub.connections.append(b_hub)
            b_hub.connections.append(a_hub)

            if a_hub in a_hub.connections or b_hub in b_hub.connections:
                raise ValueError(
                    'connection error: a hub cannot connect to itself.')

    def _find_hub(self, name: str) -> Hub:
        for hub in self.hubs:
            if name == hub.name:
                return hub

        raise ValueError(f'hub error, no hub registered with name: {name}')
