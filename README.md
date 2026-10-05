# Fly-in

Fly-in is a drone routing and traffic simulation project inspired by a graph-based pathfinding challenge. The program reads a map definition, builds a graph of zones and connections, schedules multiple drones simultaneously, and prints the movement sequence as a terminal simulation.

The project is designed around a routing problem with capacity constraints, zone types, and turn-based scheduling. It aims to move all drones from a start hub to an end hub while respecting movement limits, congestion, and route conflicts.

## Description

This project models a network of connected zones where each drone must find a valid route through the graph while respecting the rules described in the project brief:

- zones can be `normal`, `priority`, `restricted`, or `blocked`
- connections may have a maximum link capacity
- hubs may have a maximum drone capacity per turn
- drones move in discrete turns
- restricted zones add movement cost and require careful scheduling
- the simulation must keep all drones moving without deadlocks or invalid capacity usage

The solution combines:

- config parsing for map files
- graph validation and connection building
- pathfinding and alternative route selection
- planner logic for turn-by-turn movement scheduling
- terminal output for visual trace of the simulation

## Main Challenge

The challenge is not simply shortest-path finding. The real difficulty is planning traffic under constraints:

- several drones share the same network
- bottlenecks appear at narrow corridors and restricted hubs
- routes should avoid congestion and avoid dead-end loops
- the simulation should remain valid under the map rules

This becomes especially important in the optimized challenge map described in `docs/impossible_dream_optimization.md`, where the target is to push the solution toward a much lower total turn count.

## Project structure

| Path | Purpose |
| --- | --- |
| `src/__main__.py` | CLI entry point for running the simulation |
| `src/fly_in.py` | Main simulation engine and turn execution |
| `src/planner.py` | Route selection and movement scheduling logic |
| `src/pathfinding.py` | Path generation, congestion-aware route searching, and alternative paths |
| `src/config_parser.py` | Reads and validates map files |
| `src/models/graph.py` | Graph model and topology validation |
| `src/models/models.py` | Drone, hub, and connection models |
| `maps/` | Input maps for easy, medium, hard, and challenger scenarios |

## How to run

Install the project dependencies:

```bash
make install
```

Run the default simulation using the challenger map:

```bash
make run
```

You can also run a specific map directly:

```bash
uv run python -m src --map maps/easy/01_linear_path.txt
```

Or choose another available map from the `maps/` folder.

## Map format

Maps are plain text files with a simple declarative syntax. A typical example looks like this:

```text
nb_drones: 2
start_hub: start 0 0 [color=green]
end_hub: goal 3 0 [color=red]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

Zone metadata may include:

- `zone=<normal|priority|restricted|blocked>`
- `color=<value>`
- `max_drones=<number>`

Connection metadata may include:

- `max_link_capacity=<number>`


## Simulation rules

The implementation follows the challenge rules described in the projecct, including:

- exact start and end hub validation
- connection and zone validation
- capacity management per zone and edge
- priority and restricted-area handling
- turn-based scheduling and movement restrictions
- terminal output showing drone moves across the map

## Performance notes

This project evolved from a reactive, shortest-path approach into a more structured traffic-planning strategy. The key changes were made in the route selection and scheduling logic, not just in the static graph model.

In `src/pathfinding.py`, the route evaluation shifted from a simple shortest-path calculation toward a congestion-aware cost model. Instead of choosing the path solely by graph distance, the algorithm now penalizes crowded hubs and likely bottlenecks. This makes the system more resilient in dense maps, because drones avoid converging toward the same restricted section at the same time.

In `src/planner.py`, the planner was refined to group drones by urgency and to evaluate multiple candidate routes before committing to a movement. Rather than letting each drone decide independently in a greedy way, the planner selects the least congested valid route and reserves movement capacity in a way that reduces head-on collisions and queues near critical nodes.

This combination changes the behavior from local, turn-by-turn greediness to a more coordinated planning model: drones are scheduled with awareness of congestion, urgency, and the current state of the network. That is the main improvement behind the final version of the project, especially for harder maps where a naive route choice causes cascading delays.

## Summary

Fly-in is a small but interesting routing challenge: it turns a graph and capacity-constrained movement problem into a simulation where multiple drones compete for space, timing, and route choices. The implementation already covers the basic mechanics of parsing, graph building, planning, and movement, and it provides a useful base for optimizing the hardest challenge maps.
