from __future__ import annotations

import os

from pydantic import BaseModel, model_validator

from .models import Connection, Hub


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
    def graph_dimensions(self) -> Graph:
        min_x = min(h.x for h in self.hubs)
        min_y = min(h.y for h in self.hubs)
        max_x = max(h.x for h in self.hubs)
        max_y = max(h.y for h in self.hubs)

        self.width = (max_x - min_x) + 1
        self.height = (max_y - min_y) + 1
        return self

    @model_validator(mode='after')
    def get_hub_weights(self) -> Graph:
        for v in self.hubs:
            if v.zone == 'normal':
                v.weight = 1
            if v.zone == 'priority':
                v.weight = 1
            if v.zone == 'restricted':
                v.weight = 2
            if v.zone == 'blocked':
                v.weight = 0
        return self

    @model_validator(mode='after')
    def validate_start_end(self) -> Graph:
        sx, sy = self.start_hub.x, self.start_hub.y
        ex, ey = self.end_hub.x, self.end_hub.y

        if sx == ex and sy == ey:
            raise ValueError('coordinates of start and end must be unique.')
        return self

    @model_validator(mode='after')
    def validate_output_path(self) -> Graph:
        parent_dir = os.path.dirname(os.path.abspath(self.output_file))
        if parent_dir and not os.path.isdir(parent_dir):
            raise Exception(f"output directory does not exist: '{parent_dir}'")
        return self

    @model_validator(mode='after')
    def validate_connections(self) -> Graph:
        hub_list: list[str] = []
        for h in self.hubs:
            hub_list.append(h.name)

        for c in self.connections:
            a, b = c.hub_a, c.hub_b
            if a not in hub_list or b not in hub_list:
                raise ValueError(f'connection error: {a} - {b} is not '
                                 'a registered hub')

            a_hub: Hub = self._find_hub(a)
            b_hub: Hub = self._find_hub(b)
            a_hub.connections.append(b_hub)
            b_hub.connections.append(a_hub)

            if a_hub in a_hub.connections or b_hub in b_hub.connections:
                raise ValueError(
                    'connection error: a hub cannot connect to itself.')
        return self

    def _find_hub(self, name: str) -> Hub:
        for hub in self.hubs:
            if name == hub.name:
                return hub

        raise ValueError(f'hub error, no hub registered with name: {name}')
