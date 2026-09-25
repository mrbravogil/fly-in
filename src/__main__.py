import argparse
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


def write_map(map: str) -> None:
    with open(map, "r", encoding="utf-8") as f:
        map_print: list[str] = f.readlines()

    for line in map_print:
        if line.startswith('#') is False and line[0] != '\n':
            print(line)


def main() -> None:

    print('\nWELCOME TO FLY-IN ✈️ ✈️ ✈️\n')
    args = parse_args()
    try:
        graph: Graph = parse_config(args.map)
        fly_in = Fly_in(graph)
        fly_in.run()
    except Exception as e:
        print(e)
    
    # write_map(args.map)
    # # print(graph, '\n')
    # path_finder = PathFinder()
    # path, prev = path_finder.build_path(start=graph.start_hub, graph=graph)
    # print(prev)
    # rev = path_finder.reconstruct_path(graph.start_hub, graph)
    # print(rev)


if __name__ == '__main__':
    try:
        main()

    except Exception as e:
        print(e)
