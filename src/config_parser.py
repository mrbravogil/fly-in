"""Configuration parser for the Fly-in project.

This module provides the Parser class to read and validate
maze generation configuration files in KEY:VALUE format.

Example configuration file:

    nb_drones: 2
    start_hub: start 0 0 [color=green]
    hub: waypoint1 1 0 [color=blue]
    hub: waypoint2 2 0 [color=blue]
    end_hub: goal 3 0 [color=red]
    connection: start-waypoint1
    connection: waypoint1-waypoint2
    connection: waypoint2-goal

"""

import os
from dataclasses import dataclass
from typing import Any


@dataclass
class Config:
    """Holds parsed graph generation configuration values.

    Attributes:

    drones: Number of drones used in the simulation
    start_hub: Coordinates and color of start hub
    hubs: Coordinates of different hubs
    end_hub: Coordinates and color of end hub
    connections: Connections between hubs

    """

    drones: int
    start_hub: dict[str, dict[str, Any]]
    end_hub: dict[str, dict[str, Any]]
    hubs: dict[str, dict[str, Any]]
    connections: tuple[tuple[str, str]]


class ConfigParser:

    """Parser for Fly-in configuration files.

    Reads a plain text file containing KEY:VALUE pairs, validates
    required fields, and returns a Config dataclass instance.
    """
    REQUIRED_KEYS = {"nb_drones", "start_hub", "hub", "end_hub",
                     "connection"}

    def __init__(self, file_path: str) -> None:
        """Initialize the parser with a configuration file path.

        Raises ValueError: If filepath is empty or not a string.
        """

        if not file_path or not isinstance(file_path, str):
            raise ValueError(
                    "Configuration file path must be a non-empty string.")

        self.filepath = file_path

    def _read_file(self) -> list[str]:
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(
                f"Configuration file not found: '{self.filepath}'")

        if not os.path.isfile(self.filepath):
            raise ValueError(
                f"Configuration path is not a file: '{self.filepath}'")

        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except OSError as e:
            raise OSError(
                f"Cannot read configuration file "
                f"'{self.filepath}': {e}") from e

        processed_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                processed_lines.append(line)

        if not processed_lines:
            raise ValueError(
                f"Configuration file '{self.filepath}' "
                f"is empty or contains only comments.")

        return processed_lines

    def _parse_lines(self, lines: list[str]) -> dict[str, str]:
        """Parse configuration lines into a key-value dictionary.

        Returns a Dictionary mapping lowercase keys to their string values.

        Raises ValueError: If a line has invalid format, empty key/value,
        or duplicate key.
        """

        config = {}

        for line in lines:
            if '#' in line:
                line = line.split('#', 1)[0].strip()
                if not line:
                    continue

            if ':' not in line:
                raise ValueError(
                    f"Invalid line in configuration file: '{line}'. "
                    f"Expected format: KEY:VALUE")

            k, v = line.split(':', 1)
            key = k.strip().lower()
            value = v.strip()

            if not key:
                raise ValueError(f"Empty key in configuration line: '{line}'")
            if not value:
                raise ValueError(
                    f"Empty value for key '{key}' in configuration file.")
            if key in config:
                raise ValueError(
                    f"Duplicate key '{key}' in configuration file.")

            config[key] = value

        return config

    def _validate_required_keys(self, config: dict[str, str]) -> None:
        """Check that all required configuration keys are present.

        Raises ValueError: If any required key is missing.
        """
        missing = self.REQUIRED_KEYS - config.keys()
        if missing:
            missing_list = ', '.join(sorted(missing))
            raise ValueError(
                f"Missing required configuration keys: {missing_list}")

    def _parse_drones(self, value: str) -> int:
        """Parse and validate the nb_drones value.

        Returns a positive integer drones.

        Raises ValueError: If value is not a positive integer.
        """

        try:
            drones = int(value)
        except ValueError:
            print(
                f"nb_drones must be an integer, got: '{value}'")
        if drones <= 0:
            raise ValueError(
                f"nb_drones must be a positive integer, got: {drones}")

        return drones

    def _parse_hubs(self, value: str) -> dict[str, dict[str, Any]]:
        required_values = 'color'

        name, v = value.strip().split(' ', 1)
        if not name.isalpha():
            raise ValueError('hub must have a name')

        if 'color=' not in v:
            raise ValueError(f'hub is missing value: {required_values}')
        if '[' not in v or ']' not in v:
            raise ValueError('hub configuration format error. Try:'
                             'hub_name: name 0 0 [color=color '
                             'zone=zone max_drones=2]')

        c, e_v = v.split('[', 1)
        coordinates: list[int] = self._validate_hub_coordinates(
            list(c.split(' ')))

        add_values: list[str] = e_v.strip(']').split()
        if not add_values:
            raise ValueError('hub must have at least one additional'
                             ' values like "color"')
        p_values: dict[str, str] = self._validate_hub_add_values(
            add_values)

        return {
            name: {
                'coordinates': coordinates,
                'color': p_values['color'],
                'zone': [p_values['zone']
                         if p_values['zone'] else 'none'],
                'max_drones': [int(p_values['max_drones'])
                               if p_values['max_drones'] else 0]
            }
        }

    def _validate_hub_coordinates(self, coord: list[str]) -> list[int]:
        new_cords: list[int] = []
        for c in coord:
            try:
                coordinate = int(c)
                if coordinate < 0:
                    raise ValueError('all coordinates must be positive numbers'
                                     f'. Error: {c}')
            except (Exception, ValueError) as e:
                print(e)
            new_cords.append(coordinate)

        return new_cords

    def _validate_hub_add_values(self,
                                 add_values: list[str]) -> dict[str, str]:
        processed_values = {}
        valid_keys = ['color', 'zone', 'max_drones']
        valid_colors = ['red', 'green', 'blue', 'orange', 'yellow',
                        'black', 'white', 'maroon', 'darkred', 'cyan']
        for value in add_values:
            k, v = value.split('=', 1)
            k = k.strip()
            v = v.strip()

            if k not in valid_keys:
                raise ValueError(f'provided an invalid value: {k}. '
                                 f'Valid keys: {valid_keys}')
            if k == 'color':
                if not v.isalpha():
                    raise ValueError('you must provide a valid color name. '
                                     f'Example: {valid_colors}')

            if k == 'zone':
                if not v.isalpha():
                    raise ValueError('you must provide a valid zone name: '
                                     'priority, restricted')
                if v != 'restricted' or v != 'priority':
                    raise ValueError('you must provide a valid zone name: '
                                     'priority, restricted')

            if k == 'max_drones':
                try:
                    max = int(v)
                    if max <= 0:
                        raise ValueError('max_drones must be a number'
                                         ' higher than 0.')
                except (ValueError, Exception) as e:
                    print(e)

            processed_values[k] = v

        return processed_values

    def _parse_connections(self, value: str) -> dict[str, Any]:
        if '[' in value and ']' not in value:
            raise ValueError(f'connections format error: connection: {value}'
                             'Try: connection: maze_a1-maze_a2 or'
                             ' connection: start-maze_a1'
                             ' [max_link_capacity=2]')
        c1, c2 = value.strip().split('-')
        c3 = ''
        if '[' in c2:
            c2, c3 = c2.strip().strip(']').split('[', 1)
            if '[' in c3 or ']' in c3:
                raise ValueError('connections format error: connection: '
                                 f'{value}'
                                 'Try: connection: maze_a1-maze_a2 or'
                                 ' connection: start-maze_a1'
                                 ' [max_link_capacity=2]')
            k, v = c3.strip().split('=')
            if k != 'max_link_capacity':
                raise ValueError(f'cannot recognise this key: {k}')
            try:
                max = int(v)
                if max < 0:
                    raise ValueError(' ')
            except (Exception, ValueError):
                print('max_link_capacity must be a valid '
                      'positive number.')

        connection: list[str] = [c1, c2]

        return {
            'connection': connection,
            'max_link_capacity': [int(c3) if c3 else 0]
        }
