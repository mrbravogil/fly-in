import argparse
import sys
from pydantic import ValidationError
from .fly_in import Fly_in
from .config_parser import parse_config
from .models.graph import Graph


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments and return their defaulted values."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--map',
        default='maps/easy/01_linear_path.txt'
    )

    return parser.parse_args()


if __name__ == '__main__':

    print('\n\x1b[40mWELCOME TO FLY-IN ✈️ ✈️ ✈️ \x1b[0m\n')
    args = parse_args()
    try:

        graph: Graph = parse_config(args.map)
        print(f'DRONES: {graph.n_drones}')
        start = graph.start_hub
        print(f'START HUB: {start.name} {start.x}, {start.y}')
        end = graph.end_hub
        print(f'END HUB: {end.name} {end.x}, {end.y}')
        print(f'HUBS: {len(graph.hubs)}')
        print(f'CONNECTIONS: {len(graph.connections)}\n')

        fly_in = Fly_in(graph)
        fly_in.run()

    except FileNotFoundError as e:
        print(f"\nFile not found: {e.filename}")
        sys.exit(1)
    except PermissionError as e:
        print(f"\nPermission denied in this file {e.filename}",
              file=sys.stderr)
        sys.exit(1)
    except ValidationError as e:
        print("\nValidation error:")
        print(e.errors())
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error ocurred: {str(e)}")
        sys.exit(1)
    finally:
        print("\x1b[40m⚙️ Programme finished...\x1b[0m\n")
