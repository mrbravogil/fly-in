"""Pathfinding utilities for navigating hub graphs.

This module provides Dijkstra's algorithm for calculating the shortest
weighted paths between hubs in a graph.
"""
from typing import Any
import random
from .models.graph import Graph
from .models.models import Hub


class PathFinder():
    """Finds the shortest path between hubs in a graph using Dijkstra's
    algorithm.

    The class builds distance, predecessor, and visited-node maps while
    traversing connected hubs based on their connection weights.
    """

    def build_path(self, start: Hub,
                   graph: Graph,
                   turn: int,
                   reservations: dict
                   ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Finds the shortest and most cost-effective path from the
        drone's current hub to the end hub."""

        distances: dict[str, float | int] = self.build_hub_map(graph,
                                                               float('inf'))
        distances[start.name] = 0
        prev: dict[str, str | Any] = self.build_hub_map(graph,
                                                        None)
        visited = self.build_hub_map(graph,
                                     False)

        while True:
            min_distance = float('inf')
            u: Hub | None = None

            for hub in graph.hubs:
                if (
                    not visited[hub.name]
                    and distances[hub.name] < min_distance
                ):
                    u = hub
                    min_distance = distances[hub.name]

            if u is None or min_distance == float('inf'):
                break
            if u.is_end:
                break

            visited[u.name] = True
            for v in u.connections:
                if visited[v.name]:
                    continue
                if v.zone == 'blocked':
                    continue

                base_cost: float = v.weight
                penalty = self.estimate_congestion(v, turn, reservations)
                alt = distances[u.name] + base_cost + penalty

                if alt < distances[v.name]:
                    distances[v.name] = alt
                    prev[v.name] = u.name

        return distances, prev

    def estimate_congestion(self, hub: Hub, turn: int,
                            reservations: dict) -> float:

        """Calculates path congestion in the next five turns.
        If the hub is out of capacity, it returns a high
        penalty cost.
        """

        penalty: float = 0.0

        for t in range(turn, turn + 5):
            occupied = reservations.get((hub.name, t), 0)
            if occupied >= hub.max_drones:
                penalty += 10.0
            elif occupied >= hub.max_drones * 0.7:
                penalty += 3.0

        return penalty

    def get_alternative_routes(self, start: Hub,
                               graph: Graph,
                               turn: int,
                               reservations: dict[tuple, int]
                               ) -> list[list[Hub]]:
        """Return several candidate routes from the current hub."""

        routes: list[list[Hub]] = []
        modified_graph: Graph

        for attempt in range(3):
            modified_graph = self.graph_with_random_weights(graph, attempt)
            route = self.reconstruct_path(start, modified_graph,
                                          turn, reservations)
            routes.append(route)

        return routes

    def graph_with_random_weights(self, graph: Graph, attempt: int) -> Graph:
        """Returns a copy of the original graph with modified weight values."""

        modified_graph: Graph = graph.model_copy(deep=True)

        for hub in modified_graph.hubs:
            num = random.uniform(-0.3, 0.3)
            n_weight = hub.weight * (1 + num + attempt * 0.1)
            hub.weight = max(1, n_weight)

        return modified_graph

    def build_hub_map(self, graph: Graph, type: Any) -> dict[str, Any]:
        """Create a mapping of every hub name to a default value."""
        map: dict[str, Any] = {}
        for h in graph.hubs:
            map[h.name] = type

        return map

    def reconstruct_path(self,
                         start: Hub,
                         graph: Graph,
                         turn: int,
                         reservations: dict[tuple, int]) -> list[Hub]:
        """Reconstruct the route from the given current hub to the end hub."""
        _, prev = self.build_path(start, graph, turn, reservations)
        end = graph.end_hub if graph.end_hub else None
        if not end:
            raise ValueError("No end hub in graph")

        hubs: dict[str, Hub] = {hub.name: hub for hub in graph.hubs}
        route: list[Hub] = [end]
        current: Hub = end

        while current.name != start.name:
            parent_name = prev[current.name]
            if parent_name is None:
                raise ValueError(
                    f"No path from {start.name} to {end.name}"
                )
            current = hubs[parent_name]
            route.append(current)

        route.reverse()

        return route

    def get_next_hub(self,
                     start: Hub,
                     graph: Graph,
                     turn: int,
                     reservations: dict[tuple, int]) -> Hub:
        """Returns the path's next hub"""
        route: list[Hub] = self.reconstruct_path(start, graph,
                                                 turn, reservations)

        if len(route) < 2:
            raise ValueError("No next hub available")

        return route[1]
