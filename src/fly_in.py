from .pathfinding import PathFinder
from .models.graph import Graph


class Fly_in():
    path_finder: PathFinder = PathFinder()
    graph: Graph

    def __init__(self, graph: Graph) -> None:
        self.graph = graph
        self.graph.create_drones()
        self.assign_path()

    def assign_path(self) -> None:
        for drones in self.graph.drones:
            drones.path = self.path_finder.reconstruct_path(
                self.graph.start_hub, self.graph
            )

    def all_drones_finished(self) -> bool:
        for drones in self.graph.drones:
            if drones.current_hub != self.graph.end_hub:
                return False

        return True

    def run(self) -> None:
        x, y = 0, 1
        while self.all_drones_finished() is False:
            for drone in self.graph.drones:
                print(f'[{drone.id}: {drone.path[x].name} - '
                      f'{drone.path[y].name}]')
                drone.move_next_hub(drone.path[y])
            x += 1
            y += 1
