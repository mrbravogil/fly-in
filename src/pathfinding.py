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
        """Build shortest-path data from a starting hub."""
        size = len(graph.hubs)
        # distances keeps the current best known cost from start to each hub.
        # Every hub starts as unreachable (infinity) except the starting hub.
        distances: dict[str, float | int] = self.build_hub_map(graph,
                                                               float('inf'))
        distances[start.name] = 0
        # prev stores the predecessor hub used to reach each hub with
        # the best known cost; this is later used to reconstruct routes.
        prev: dict[str, str | Any] = self.build_hub_map(graph,
                                                        None)
        # visited marks hubs whose minimum distance is already finalized.
        visited = self.build_hub_map(graph,
                                     False)

        for _ in range(size):
            # Pick the next hub to process: the unvisited hub with the
            # smallest temporary distance. In Dijkstra, this choice is safe
            # because all edge weights are non-negative.
            min_distance = float('inf')
            u: Hub
            for i in graph.hubs:
                if not visited[i.name] and distances[i.name] < min_distance:
                    min_distance = distances[i.name]
                    u = i

            # Stop early if we reached the destination hub, or if there is no
            # valid next hub to process.
            if u.is_end or u is None:
                break

            visited[u.name] = True

            # Try to improve the best known distance for each neighbor
            # connected to the current hub.
            for v in u.connections:
                # Skip neighbors that are already finalized.
                if visited[v.name]:
                    continue

                w: int = v.weight
                # Ignore blocked/non-usable connections.
                if w == 0:
                    continue

                # Candidate distance to neighbor through the current hub.
                alt: float = distances[u.name] + w

                # If this path is better, store the new distance and parent.
                if alt < distances[v.name]:
                    distances[v.name] = alt
                    prev[v.name] = u.name

        return distances, prev

    def build_hub_map(self, graph: Graph, type: Any) -> dict[str, Any]:
        """Create a dictionary containing every hub in the graph."""
        map: dict[str, Any] = {}
        for h in graph.hubs:
            map[h.name] = type

        return map

    def reconstruct_path(self, start: Hub, graph: Graph) -> list[Hub]:
        """Reconstruct path from end_hub to start_hub and returns
        a list of indexed hubs.
        """
        _, prev = self.build_path(start, graph)
        end = graph.end_hub if graph.end_hub else None
        if not end:
            raise ValueError("No end hub in graph")

        hubs: dict[str, Hub] = {hub.name: hub for hub in graph.hubs}
        route: list[Hub] = [end]
        current: Hub = end

        while current.name != graph.start_hub.name:
            parent_name = prev[current.name]
            if parent_name is None:
                raise ValueError("No path from start to end")
            current = hubs[parent_name]
            route.append(current)

        route.reverse()

        return route

    def get_next_hub(self, start: Hub, graph: Graph) -> Hub:
        """Returns the path's next hub"""
        route: list[Hub] = self.reconstruct_path(start, graph)

        if len(route) < 2:
            raise ValueError("No next hop available")

        return route[1]
