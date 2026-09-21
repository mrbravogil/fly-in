import argparse


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments and return their defaulted values."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--map',
        default='maps/easy/01_linear_path.txt'
    )

    return parser.parse_args()


def main() -> None:
    print('\nWELCOME TO FLY-IN ✈️ ✈️ ✈️\n')
    args = parse_args()
    from . import config_parser
    config = config_parser.parse_config(args.map)
    print(config)


if __name__ == '__main__':
    main()
