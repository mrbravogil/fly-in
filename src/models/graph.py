"""Graph model and validation rules for the Fly-in simulation."""

from __future__ import annotations

from pydantic import BaseModel, model_validator

from .models import Connection, Hub, Drone


class Graph(BaseModel):
    """Holds parsed graph generation configuration values.

    Attributes:

    drones: List of drones registered in the simulation.
    n_drones: Number of drones used in the simulation.
    start_hub: Coordinates and color of start hub.
    hubs: Coordinates of different hubs.
    end_hub: Coordinates and color of end hub.
    connections: Connections between hubs.
    width: Graph's width based on hubs' coordinates.
    height: Graph's height based on hubs' coordinates.

    """
    drones: list[Drone]
    n_drones: int
    start_hub: Hub
    end_hub: Hub
    hubs: list[Hub]
    connections: list[Connection]
    width: int = 0
    height: int = 0

    @model_validator(mode='after')
    def graph_dimensions(self) -> Graph:
        """Compute the graph width and height from the hub coordinates."""
        min_x = min(h.x for h in self.hubs)
        min_y = min(h.y for h in self.hubs)
        max_x = max(h.x for h in self.hubs)
        max_y = max(h.y for h in self.hubs)

        self.width = (max_x - min_x) + 1
        self.height = (max_y - min_y) + 1
        return self

    @model_validator(mode='after')
    def get_hub_weights(self) -> Graph:
        """Assign a weight to each hub according to its zone."""
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
        """Ensure the start and end hubs are not at the same position."""
        sx, sy = self.start_hub.x, self.start_hub.y
        ex, ey = self.end_hub.x, self.end_hub.y

        if sx == ex and sy == ey:
            raise ValueError('coordinates of start and end must be unique.')
        return self

    @model_validator(mode='after')
    def validate_connections(self) -> Graph:
        """Verify that every connection references valid hubs."""
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

            if a_hub in a_hub.connections or b_hub in b_hub.connections:
                raise ValueError(
                    'connection error: a hub cannot connect to itself.')
            a_hub.connections.append(b_hub)
            b_hub.connections.append(a_hub)

        self._bidirectional_coon()

        return self

    def _bidirectional_coon(self) -> None:
        """Add the reverse links for each connection."""
        i = len(self.connections) + 1
        current_coons: list[Connection] = self.connections
        bi_coons: list[Connection] = []

        for c in current_coons:
            a, b = c.hub_a, c.hub_b
            id: str = f'C{str(i)}'
            bi_conn = Connection(id=id, hub_a=b, hub_b=a,
                                 max_link_capacity=c.max_link_capacity)
            bi_coons.append(bi_conn)
            i += 1

        self.connections.extend(bi_coons)

    def create_drones(self) -> None:
        """Create the drone instances and place them at the start hub."""
        drones: list[Drone] = []
        i = 1
        while i <= self.n_drones:
            d_name = f'D{str(i)}'
            drone = Drone(id=d_name, current_hub=self.start_hub)
            drones.append(drone)
            i += 1

        self.drones = drones

    def _find_hub(self, name: str) -> Hub:
        """Return a hub from the graph by its name."""
        for hub in self.hubs:
            if name == hub.name:
                return hub

        raise ValueError(f'hub error, no hub registered with name: {name}')

    def find_connection(self, hub_a: str, hub_b: str) -> Connection | None:
        """Return the connection between two hubs, if it exists."""
        for connection in self.connections:
            if connection.hub_a == hub_a and connection.hub_b == hub_b:
                return connection
        return None
