from .models.graph import Graph
from .models.models import Drone, Hub
from .pathfinding import PathFinder


class Planner():

    def __init__(self, graph: Graph):
        self.graph = graph
        self.path_finder = PathFinder()

    def plan(self, drones: list[Drone], turn: int,
             reservations: dict[tuple, int]) -> list[tuple]:
        """Return the drones's movements for the current turn"""

        schedule: list[tuple] = []
        groups: list[list[Drone]] = self.group_drones(drones,
                                                      turn, reservations)
        original_hubs = {hub.name: hub for hub in self.graph.hubs}

        for group in groups:
            for drone in group:
                routes: list[list[Hub]] = self.get_alt_routes(
                    drone, turn, reservations
                )

                best_route: list[Hub] = self.select_best_route(
                    routes, turn, reservations)

                if best_route is not None:
                    next_hub = original_hubs[best_route[1].name]

                    if self.has_capacity(next_hub, turn, reservations):
                        schedule.append((drone, next_hub, turn + 1))
                    else:
                        continue

        return schedule

    def group_drones(self, drones: list[Drone],
                     turn: int, reservations: dict[tuple, int]
                     ) -> list[list[Drone]]:
        """Returns groups of drones sorted by urgency."""
        groups: list[list[Drone]] = [[], [], []]

        for drone in drones:
            if drone.current_hub is None:
                continue
            if drone.current_hub.is_end:
                continue

            distance_to_end = self.distance_to_end(drone, turn, reservations)
            if distance_to_end <= 3:
                groups[0].append(drone)
            elif distance_to_end <= 8:
                groups[1].append(drone)
            else:
                groups[2].append(drone)

        return groups

    def distance_to_end(self, drone: Drone,
                        turn: int, reservations: dict[tuple, int]) -> int:
        """Return distance between drone's current hub to
        end hub."""
        if drone.current_hub is None:
            return 999

        route = self.path_finder.reconstruct_path(drone.current_hub,
                                                  self.graph,
                                                  turn, reservations)
        return len(route)

    def get_alt_routes(self,
                       drone: Drone,
                       turn: int,
                       reservations: dict[tuple, int]) -> list[list[Hub]]:
        """Returns three possible routes using pathfinder."""

        if drone.current_hub is None:
            return []

        routes: list[list[Hub]] = self.path_finder.get_alternative_routes(
            drone.current_hub, self.graph, turn, reservations
        )

        return routes

    def select_best_route(self, routes: list[list[Hub]], turn: int,
                          reservations: dict[tuple, int]) -> list[Hub]:
        """Returns the best route from the given list of routes."""

        best_route: list[Hub] = []
        best_score = float('inf')

        for route in routes:
            if len(route) < 2:
                continue

            score = 0.0
            for t in range(1, 6):
                for hub in route[1:4]:
                    occupation: int = reservations.get((hub.name, turn+t), 0)
                    congestion: float = occupation / hub.max_drones
                    score += congestion

            if score < best_score:
                best_score = score
                best_route = route

        return best_route

    def has_capacity(self, hub: Hub, turn: int,
                     reservations: dict[tuple, int]) -> bool:
        """Verifies hub's capacity for the current turn."""
        occupied: int = reservations.get((hub.name, turn), 0)

        return occupied < hub.max_drones

    def validate_move(self, drone: Drone, next_hub: Hub,
                      turn: int, reservations: dict[tuple, int]) -> bool:
        """Validates drone's movement."""

        if drone.current_hub is None:
            return False

        connection = self.graph.find_connection(
            drone.current_hub.name, next_hub.name)
        if connection is False:
            return False

        if not self.has_capacity(next_hub, turn, reservations):
            return False

        if connection:
            conn_occupation = reservations.get((connection.id, turn), 0)
            if conn_occupation >= connection.max_link_capacity:
                return False

        if next_hub.zone == 'blocked':
            return False

        return True
