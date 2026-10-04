from .pathfinding import PathFinder
from .models.graph import Graph
from .models.models import Drone, Hub

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

        for drone in self.graph.drones:
            drone.current_hub = self.graph.start_hub

    def assign_path(self, drone: Drone, current_hub: Hub) -> None:
        if drone.current_hub:
            drone.path = self.path_finder.reconstruct_path(
                    drone.current_hub, self.graph
                )

    def all_drones_finished(self) -> bool:
        for drones in self.graph.drones:
            if drones.current_hub != self.graph.end_hub:
                return False

        return True

    def _assign_colour_code(self, next_hub: Hub, drone: Drone) -> str:
        colour: str = ''
        if next_hub.is_end is True:
            colour = 'red'
        elif drone.current_hub:
            colour = drone.current_hub.colour
        code: str = ''
        if colour in COLOURS:
            code = COLOURS[colour]
        else:
            code = COLOURS['white']

        return code

    def _turn_validation(self, drone: Drone, next_hub: Hub) -> bool:
        if not drone.current_hub:
            return False

        connection = self.graph.find_connection(drone.current_hub.name,
                                                next_hub.name)
        if connection is None:
            return False

        return drone.can_move(connection) is True


    def _record_move(self, drone_movements: list[Drone]) -> str:
        turn_print: str = ''

        for drone in drone_movements:
            if not drone.current_hub:
                continue

            next_hub = drone.next_hub()
            if next_hub is None:
                continue

            connection = self.graph.find_connection(
                drone.current_hub.name,
                next_hub.name
            )
            if connection is None:
                continue

            if next_hub.zone == 'restricted' and drone.status == 'normal':
                if drone.can_move(connection) is False:
                    continue
                connection.enter(drone)
                drone.status = 'restricted'
                continue

            if next_hub.zone == 'restricted' and drone.status == 'restricted':
                if drone.current_connection is not None:
                    drone.current_connection.leave(drone)
                drone.status = 'normal'

            if drone.can_move(connection) is True:
                code: str = self._assign_colour_code(next_hub, drone)
                turn_print += (
                    f'{code}[{drone.id}: '
                    f'{drone.current_hub.name} - {next_hub.name}] \x1b[0m'
                )
                drone.move_next_hub(next_hub)

        return turn_print

    def run(self) -> None:
        turns: int = 0
        max_turns: int = 10000

        while self.all_drones_finished() is False:
            if turns >= max_turns:
                raise RuntimeError(
                    'Simulation stalled: no progress was made after '
                    f'{max_turns} turns.'
                )

            drone_movements: list[Drone] = []

            for drone in self.graph.drones:
                if drone.current_hub:
                    self.assign_path(drone, drone.current_hub)
                    next_hub: Hub | None = drone.next_hub()
                    if next_hub is None:
                        continue

                    connection = self.graph.find_connection(
                        drone.current_hub.name,
                        next_hub.name
                    )
                    if connection is None:
                        continue

                    if (
                        next_hub.zone == 'restricted'
                        and drone.status == 'normal'
                    ):
                        if drone.can_move(connection) is True:
                            drone_movements.append(drone)
                        continue

                    if (
                        next_hub.zone == 'restricted'
                        and drone.status == 'restricted'
                    ):
                        drone_movements.append(drone)
                        continue

                    if self._turn_validation(drone, next_hub) is True:
                        drone_movements.append(drone)

            turn_print = self._record_move(drone_movements)
            if turn_print:
                print(turn_print)
            turns += 1

        print(f'\n\x1b[40mTURNS: {turns}\x1b[0m\n')
