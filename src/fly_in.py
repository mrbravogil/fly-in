from .pathfinding import PathFinder
from .models.graph import Graph

COLOURS: dict[str, str] = {
    'red': '\x1b[91m',
    'green': '\x1b[92m',
    'yellow': '\x1b[93m',
    'blue': '\x1b[94m',
    'purple': '\x1b[95m',
    'cyan': '\x1b[96m',
    'white': '\x1b[97m'
}


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
        turns: int = 0
        x, y = 0, 1
        while self.all_drones_finished() is False:
            turn_print: str = ''
            for drone in self.graph.drones:
                if drone.current_hub:
                    colour: str = ''
                    if drone.path[y].name == 'goal':
                        colour = 'red'
                    else:
                        colour = drone.current_hub.colour
                    code: str = COLOURS[colour]

                    turn_print += (f'{code}[{drone.id}: {drone.path[x].name} '
                                   f'- {drone.path[y].name}] \x1b[0m')

                    drone.move_next_hub(drone.path[y])
                    turns += 1
            print(turn_print)
            turn_print = ''
            x += 1
            y += 1
        print(f'\n\x1b[40mTURNS: {turns}\x1b[0m\n')
