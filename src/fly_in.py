"""Simulation engine for moving drones through the graph."""

from .pathfinding import PathFinder
from .models.graph import Graph
from .models.models import Drone, Hub
from .planner import Planner

COLOURS: dict[str, str] = {
    'red': '\x1b[38;5;196m',
    'green': '\x1b[38;5;40m',
    'yellow': '\x1b[38;5;190m',
    'blue': '\x1b[38;5;39m',
    'purple': '\x1b[38;5;90m',
    'violet': '\x1b[38;5;57m',
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

RAINBOW: list[str] = [
    '\x1b[38;5;196m',
    '\x1b[38;5;190m',
    '\x1b[38;5;40m',
    '\x1b[96m',
    '\x1b[38;5;39m',
    '\x1b[38;5;90m',
]


class Fly_in():
    """Runs the drone simulation turn by turn.

    It schedules moves, validates capacity, records each action, and
    prints the resulting route updates.
    """

    path_finder: PathFinder = PathFinder()
    graph: Graph
    planner: Planner
    reservations: dict[tuple, int] = {}

    def __init__(self, graph: Graph) -> None:
        """Initialize the simulation with a graph and its drones."""
        self.graph = graph
        self.graph.create_drones()

        for drone in self.graph.drones:
            drone.current_hub = self.graph.start_hub

        self.planner = Planner(graph)
        self.reservations = {}

    def _assign_path(self, drone: Drone, current_hub: Hub,
                     turn: int, reservations: dict[tuple, int]) -> None:
        """Assign the drone's current route using the graph state."""
        if drone.current_hub:
            drone.path = self.path_finder.reconstruct_path(
                    drone.current_hub, self.graph, turn, reservations
                )

    def _all_drones_finished(self) -> bool:
        """Return True when every drone has reached the end hub."""
        for drones in self.graph.drones:
            if drones.current_hub != self.graph.end_hub:
                return False

        return True

    def _assign_colour_code(self, from_hub: Hub,
                            to_hub: Hub, drone: Drone) -> str:
        """Return the ANSI colour code used for the movement print."""
        colour: str = ''
        if to_hub.is_end is True:
            colour = 'red'
        elif from_hub:
            if from_hub.is_start is True:
                colour = 'green'
            else:
                colour = from_hub.colour
        code: str = ''
        if colour in COLOURS:
            code = COLOURS[colour]
        else:
            code = COLOURS['white']

        return code

    def _rainbow_text(self, text: str) -> str:
        """Return the text with a rainbow-style ANSI colour cycle."""
        colored: list[str] = []

        for i, ch in enumerate(text):
            colour = RAINBOW[i % len(RAINBOW)]
            colored.append(f'{colour}{ch}')

        return ''.join(colored) + '\x1b[0m'

    def _turn_validation(self, drone: Drone, next_hub: Hub, turn: int) -> bool:
        """Validate whether a move is legal for the current turn."""
        if not drone.current_hub:
            return False

        connection = self.graph.find_connection(drone.current_hub.name,
                                                next_hub.name)
        if connection is None:
            return False

        return drone.can_move(connection, turn) is True

    def _record_move(
        self,
        drone_movements: list[tuple[Drone, Hub, Hub]],
    ) -> str:
        """Build the terminal output for all moves in a turn."""
        turn_print: str = ''

        for drone, from_hub, to_hub in drone_movements:
            connection = self.graph.find_connection(
                from_hub.name,
                to_hub.name
            )
            if connection is None:
                continue

            code: str = self._assign_colour_code(from_hub, to_hub, drone)
            if to_hub.is_end is True and to_hub.name == 'impossible_goal':
                label = f'[{drone.id}: {from_hub.name} - {to_hub.name}]'
                turn_print += self._rainbow_text(label)
            else:
                turn_print += (
                                f'{code}[{drone.id}: '
                                f'{from_hub.name} - {to_hub.name}] \x1b[0m'
                )

        return turn_print

    def run(self) -> None:
        """Run the simulation until every drone reaches the end hub."""
        turns: int = 0
        max_turns: int = 10000

        while self._all_drones_finished() is False:
            if turns >= max_turns:
                raise RuntimeError(
                    'Simulation stalled: no progress was made after '
                    f'{max_turns} turns.'
                )

            schedule: list[tuple] = self.planner.plan(self.graph.drones,
                                                      turns,
                                                      self.reservations)

            drone_movements = self._execute_schedule(schedule, turns)

            turn_print = self._record_move(drone_movements)
            if turn_print:
                print(turn_print)
            turns += 1

        print(f'\n\x1b[40mTURNS: {turns}\x1b[0m\n')

    def _execute_schedule(self,
                          schedule: list[tuple],
                          turn: int) -> list[tuple[Drone, Hub, Hub]]:
        """Execute the scheduled moves and record successful ones."""
        drone_movements: list[tuple[Drone, Hub, Hub]] = []

        for action in schedule:
            drone, next_hub, t = action

            if self._turn_validation(drone, next_hub, t):
                if drone.current_hub is None:
                    continue
                from_hub: Hub = drone.current_hub
                drone.path = self.path_finder.reconstruct_path(
                    drone.current_hub, self.graph, turn, self.reservations
                )
                drone.move_next_hub(next_hub, t)

                if drone.current_hub is None:
                    continue
                if drone.current_hub.name != next_hub.name:
                    continue

                drone_movements.append((drone, from_hub, next_hub))
                self._reserve_capacity(drone, next_hub, turn + 1)

        return drone_movements

    def _reserve_capacity(self, drone: Drone, hub: Hub, turn: int) -> None:
        """Reserve the destination hub and connection for this turn."""
        if drone.current_hub is None:
            return

        connection = self.graph.find_connection(drone.current_hub.name,
                                                hub.name)
        if connection is None:
            return

        key_hub = (hub.name, turn)
        self.reservations[key_hub] = self.reservations.get(key_hub, 0) + 1
        hub.reserve_turn(turn)

        key_conn = (hub.name, turn)
        self.reservations[key_conn] = self.reservations.get(key_conn, 0) + 1
        connection.reserve_turn(turn)

        drone.reserved_turn = turn
        drone.reserved_hub = hub.name
