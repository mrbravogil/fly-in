from typing import Any
from models.models import Graph, Hub


class PathFinder():

    def build_path(self, start: Hub, graph: Graph) -> tuple[dict[str, Any],
                                                            dict[str, Any]]:
        size = len(graph.hubs)
        distances: dict[str, float | int] = self.build_hub_map(graph,
                                                               float('inf'))
        distances[start.name] = 0
        prev: dict[str, str | None] = self.build_hub_map(graph,
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
                    prev[v.name] = u

        return distances, prev

    def build_hub_map(self, graph: Graph, type: Any) -> dict[str, Any]:
        map: dict[str, Any] = {}
        for h in graph.hubs:
            map[h.name] = type

        return map
