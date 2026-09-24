"""Pathfinding utilities for navigating hub graphs.

This module provides Dijkstra's algorithm for calculating the shortest
weighted paths between hubs in a graph.
"""
from typing import Any
from .models.graph import Graph
from .models.models import Hub


class PathFinder():
    """Finds the shortest path between hubs in a graph using Dijkstra's
    algorithm.

    The class builds distance, predecessor, and visited-node maps while
    traversing connected hubs based on their connection weights.
    """

    def build_path(self, start: Hub, graph: Graph) -> tuple[dict[str, Any],
                                                            dict[str, Any]]:
        """Build shortest-path data from a starting hub.

        Args:
            start: The hub from which pathfinding begins.
            graph: The graph containing the hubs and their connections.

        Returns:
            A tuple containing:
                - A dictionary of the shortest distance to each hub.
                - A dictionary mapping each hub to its previous hub.
        """
        size = len(graph.hubs)
        distances: dict[str, float | int] = self.build_hub_map(graph,
                                                               float('inf'))
        distances[start.name] = 0
        prev: dict[str, str | Any] = self.build_hub_map(graph,
                                                        None)
        visited = self.build_hub_map(graph,
                                     False)

        for _ in range(size):
            min_distance = float('inf')
            u: Hub
            for i in graph.hubs:
                if not visited[i.name] and distances[i.name] < min_distance:
                    min_distance = distances[i.name]
                    u = i

            if u.is_end or u is None:
                break

            visited[u.name] = True

            for v in u.connections:
                if visited[v.name]:
                    continue

                w: int = v.weight
                if w == 0:
                    continue

                alt: float = distances[u.name] + w

                if alt < distances[v.name]:
                    distances[v.name] = alt
                    prev[v.name] = u.name

        return distances, prev

    def build_hub_map(self, graph: Graph, type: Any) -> dict[str, Any]:
        """Create a dictionary containing every hub in the graph.

        Args:
            graph: The graph whose hubs should be included.
            value: The initial value assigned to each hub.

        Returns:
            A dictionary mapping each hub name to the provided value.
        """
        map: dict[str, Any] = {}
        for h in graph.hubs:
            map[h.name] = type

        return map

    def reconstruct_path(self, start: Hub, graph: Graph) -> dict[str, Any]:
        _, path = self.build_path(start, graph)

        return dict(reversed(list(path.items())))
