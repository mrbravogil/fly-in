from .pathfinding import PathFinder
from .models.graph import Graph

COLOURS: dict[str, str] = {
    'red': '\x1b[38;5;196m',
    'green': '\x1b[38;5;40m',
    'yellow': '\x1b[38;5;190m',
    'blue': '\x1b[38;5;39m',
    'purple': '\x1b[38;5;57m',
    'cyan': '\x1b[96m',
    'orange': '\x1b[38;5;208m',
    'brown': '\x1b[38;5;95m',
    'maroon': '\x1b[38;5;88m',
    'darkred': '\x1b[38;5;52m',
    'crimson': '\x1b[38;5;124m',
    'gold': '\x1b[38;5;178m',
    'white': '\x1b[97m',
    'black': '\n\x1b[40m',
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

    def _record_move(self) -> str:
        turn_print: str = ''
        for drone in self.graph.drones:
            if drone.current_hub:
                next_hub = drone.next_hub()
                if next_hub:
                    colour: str = ''
                    if next_hub.name == 'goal':
                        colour = 'red'
                    else:
                        colour = drone.current_hub.colour
                    code: str = COLOURS[colour]

                    if (
                        next_hub.max_drone_capacity() is False
                        and drone.has_finished() is False
                    ):
                        turn_print += (f'{code}[{drone.id}: '
                                       f'{drone.current_hub.name} '
                                       f'- {next_hub.name}] \x1b[0m')

                        drone.move_next_hub(next_hub)
                    else:
                        continue

        return turn_print

    def run(self) -> None:
        turns: int = 0

        while self.all_drones_finished() is False:
            turn_print = self._record_move()
            print(turn_print)
            turns += 1

        print(f'\n\x1b[40mTURNS: {turns}\x1b[0m\n')
