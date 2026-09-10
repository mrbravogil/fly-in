from typing import Any
from models import Graph, Hub


class PathFinder():

    def build_path(self, start: Hub, graph: Graph) -> tuple[dict[str, Any],
                                                            dict[str, Any]]:
        size = len(graph.hubs)
        distances: dict[str, float | int] = self.build_hub_map(graph,
                                                               [float('inf')])
        distances[start] = 0
        prev: dict[str, str | None] = self.build_hub_map(graph,
                                                         None)
        visited = [False] * size

        for _ in range(size):
            min_distance = float('inf')
            u: Hub
            for i in graph.hubs:
                if not visited[i] and distances[i] < min_distance:
                    min_distance = distances[i]
                    u = i

            if u.is_end:
                break

            visited[u] = True

            for v in u.connections:
                if visited[v]:
                    continue

                w: int = self.get_weights(u, v, graph)
                alt: float = distances[u] + w

                if alt < distances[v]:
                    distances[v] = alt
                    prev[v] = u

        return distances, prev

    def build_hub_map(self, graph: Graph, type: Any) -> dict[str, Any]:
        map: dict[str, Any] = {}
        for h in graph.hubs:
            map[h.name] = type

        return map

    def get_weights(self, n1: Hub, n2: Hub, graph: Graph) -> int:
        weight = 0
        connections = graph.connections
        for v in connections.values():
            if n1 in v['connection'] and n2 in v['connection']:
                weight = v['weight']

        return weight
