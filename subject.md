Let the drone fly
Attached to this subject, you’ll find multiple files that represent the network of zones in
the following format:
Example:
nb_drones: 5
start_hub: hub 0 0 [color=green]
end_hub: goal 10 10 [color=yellow]
hub: roof1 3 4 [zone=restricted color=red]
hub: roof2 6 2 [zone=normal color=blue]
hub: corridorA 4 3 [zone=priority color=green max_drones=2]
hub: tunnelB 7 4 [zone=normal color=red]
hub: obstacleX 5 5 [zone=blocked color=gray]
connection: hub-roof1
connection: hub-corridorA
connection: roof1-roof2
connection: roof2-goal
connection: corridorA-tunnelB [max_link_capacity=2]
connection: tunnelB-goal
Interesting, right? To be more precise:
• The first line defines the number of drones using nb_drones:
<number>.
• Zone definition on each line using type prefixes:
◦ start_hub:
◦ end_hub:
◦ hub:
<name> <x> <y> [metadata] marks the starting zone.
<name> <x> <y> [metadata] marks the end zone.
<name> <x> <y> [metadata] defines a regular zone.
◦ The connection syntax forbids dashes in zone names (see below).
• All metadata is optional and enclosed in brackets [...] with default values:
◦ zone=<type> (default: normal)
◦ color=<value> (default: none)
◦ max_drones=<number> (default: 1) - Maximum drones that can occupy this
zone simultaneously
◦ Tags inside brackets can appear in any order.
• Zone types:
◦ normal – Standard zone with 1 turn movement cost (default)
◦ blocked – Inaccessible zone. Drones must not enter or pass through this zone.
Any path using it is invalid.
◦ restricted – A sensitive or dangerous zone. Movement to this zone costs 2
turns.
◦ priority – A preferred zone. Movement to this zone costs 1 turn but should
be prioritized in pathfinding.
• Colors:
◦ Colors are optional and can be used for visual representation (terminal output
or graphical display).
◦ Accepted values for color are any valid single-word strings (e.g., red, blue,
gray). There is no fixed list of allowed colors.
◦ When colors are specified, the implementation should provide visual feedback
through colored terminal output or graphical representation.
• Connections are defined using connection:
<name1>-<name2> [metadata]:
◦ Define a bidirectional connection (edge) between two zones.
◦ The connection syntax forbids dashes in zone names.
◦ Optional metadata can be specified in brackets [...]:
∗ max_link_capacity=<number> (default: 1) - Maximum drones that can
traverse this connection simultaneously
• Comments start with ’#’ and are ignored.
The zones coordinates will always be integers, and there will always
be a unique start and a unique end zone.

VII.1
Pathfinding and Algorithm Requirements
• Drones may move simultaneously. The algorithm must schedule paths to maximize
throughput and avoid unnecessary delays.
• Your implementation must handle:
◦ Distribution of drones across multiple paths.
◦ Strategic waiting when movement is not possible.
◦ Avoidance of path conflicts and deadlocks.
• The algorithm must take into account:
◦ Path lengths, including movement costs associated with zone types (e.g., re-
stricted or priority).
◦ Turn scheduling, to prevent drones from colliding or blocking each other.
◦ Graph structure, to determine available disjoint or overlapping paths.
◦ Zone capacity constraints (max_drones) and connection capacity (max_link_capacity).
• Your algorithm should be adaptable: different maps may require different routing
strategies, depending on the topology and zone types.
• Visual Representation: Your implementation must provide visual feedback of
the simulation, either through:
◦ Colored terminal output showing drone movements and zone states
◦ A graphical interface displaying the network and drone positions
◦ Both options for enhanced user experience

VII.2
Zone Occupancy Rules
• By default, a zone may contain at most one drone at any given simulation turn.
• Zones with max_drones=N metadata can contain up to N drones simultaneously.
• The only special exceptions to occupancy rules are:
◦ The start zone: all drones begin here and may share the space initially.
◦ The end zone: multiple drones can arrive here and are considered delivered.
• Two drones may not enter the same zone on the same turn unless the zone’s capacity
allows it.
• A drone may not move into a zone that would exceed its maximum capacity.
• Connection capacity (max_link_capacity) defined on connections limits how many
drones can traverse the same connection simultaneously.
• Drones may move simultaneously, as long as all capacity constraints are respected.
VII.3
Movement and Turn Mechanics
The simulation proceeds in discrete turns. At each turn, every drone may:
• Move to an adjacent connected zone (if capacity allows).
• Move to a connection towards a restricted zone (that requires 2 turns to be reached).
In this case, the drone MUST reach its destination during the next turn. It can’t
wait extra turns on the connection.
• Stay in place (e.g., to wait, or if movement is blocked).
The simulation must prevent conflicts and ensure valid movement scheduling based on
turn-by-turn state evaluation:
• Drones moving out of a zone free up capacity for that same turn.
• A zone must have available capacity for a drone to move into it (after all drones
moving out have freed up space).

• For multi-turn movements (restricted zones), the drone occupies the connection
during transit and MUST arrive at the destination after the specified number of
turns. It cannot wait on the connection for an empty space in the destination zone.
Each movement between zones has a cost in turns, based on the zone=type of the
destination:
• normal: 1 turn (default)
• restricted: 2 turns
• priority: 1 turn (but should be preferred in pathfinding algorithms)
• blocked: Inaccessible — cannot be entered
VII.4
Parser Constraints
The input file must respect the expected structure and syntax:
• The first line must define the number of drones using nb_drones:
<positive_integer>.
• The program must be able to handle any number of drones.
• There must be exactly one start_hub: zone and one end_hub: zone.
• Each zone must have a unique name and valid integer coordinates.
• Zone names can use any valid characters except dashes and spaces.
• Connections must link only previously defined zones using connection:
[metadata].
<zone1>-<zone2>
• The same connection must not appear more than once (e.g., a-b and b-a are con-
sidered duplicates).
• Any metadata block (e.g., [zone=... color=...] for zones, [max_link_capacity=...]
for connections) must be syntactically valid.
• Zone types must be one of: normal, blocked, restricted, priority. Any invalid
type must raise a parsing error.
• Capacity values (max_drones for zones, max_link_capacity for connections) must
be positive integers.
• The max_drones capacity is ignored on the start_hub and end_hub zones: these
have no capacity limit (all drones may start in the start zone, and any number of
drones may be delivered to the end zone). If such metadata is present on those two
zones, it is ignored and is not a validation error.
• Any other parsing error must stop the program and return a clear error message
indicating the line and cause.

VII.5
Simulation Output Format
• The simulation must output the step-by-step movement of drones from the start to
the end zone.
• Each simulation turn is represented by a line.
• A line must list all the drone movements that occur during that turn, space-
separated. Each movement must follow the format: D<ID>-<zone>, or D<ID>-<connection>
in case of drones still in flight toward restricted zones.
◦ D<ID> refers to the unique drone identifier (e.g., D1, D2).
◦ <zone> is the name of the destination zone.
◦ <connection> is the name of the connection toward a restricted zone.
• Drones that do not move in a given turn are omitted from that line.
• Drones that reach the end zone are considered delivered and are no longer tracked.
• The simulation ends when all drones have reached the end zone.
• Example:
D1-roof1 D2-corridorA
D1-roof2 D2-tunnelB
D1-goal D2-goal
VII.6
Scoring System
• The performance of a solution is evaluated based on the total number of simu-
lation turns required to route all drones from the start zone to the end zone.
• The fewer the number of turns, the better the score.
• A valid simulation must:
◦ Comply with all movement and occupancy rules.
◦ Correctly handle movement costs associated with zone types.
◦ Respect all capacity constraints (zone and connection limits).
◦ Avoid all conflicts (e.g., exceeding zone or connection capacity).
Secondary (optional) evaluation metrics may include:
• The number of drones moved per turn (efficiency of path allocation).
• The average number of turns per drone.
• The total path cost (sum of weighted movement costs across all drones).
• Quality and usefulness of visual representation.
In case of identical turn counts, solutions may be compared based on secondary metrics
or code quality.
These secondary metrics are not mandatory to compute automatically,
but learners are encouraged to display them in their simulation
output or documentation to help peers evaluate performance.


VII.7
Performance Benchmarks
The following performance targets define the expected optimization level your implemen-
tation must achieve.
• Expected performance:
◦ Easy maps should be solved in less than 10 turns
◦ Medium maps should be solved in 10–30 turns
◦ Hard maps should be solved in less than 60 turns
◦ Challenger map (optional) should aim to beat the reference record of 45 turns
This level is purely optional and does not affect your grade.
To help you evaluate your algorithm’s efficiency, here are reference performance targets
based on the provided test maps:
• Easy Maps:
◦ Linear path with 2 drones: Target ≤ 6 turns
◦ Simple fork with 4 drones: Target ≤ 8 turns
◦ Basic capacity with 4 drones: Target ≤ 6 turns
• Medium Maps:
◦ Dead end trap with 5 drones: Target ≤ 12 turns
◦ Circular loop with 6 drones: Target ≤ 15 turns
◦ Priority puzzle with 5 drones: Target ≤ 12 turns
• Hard Maps:
◦ Maze nightmare with 8 drones: Target ≤ 30 turns
◦ Capacity hell with 12 drones: Target ≤ 35 turns
◦ Ultimate challenge with 15 drones: Target ≤ 45 turns
• Challenger Map (optional — for exceptional implementations):
◦ The Impossible Dream with 25 drones: Reference record: 45 turns
◦ This quasi-unsolvable challenge is designed for algorithmic research and opti-
mization
◦ Solving this map demonstrates exceptional pathfinding and optimization skills
◦ Note: This level is purely optional and does not affect your grade
These benchmarks are provided as optimization targets to help you
evaluate your algorithm’s performance. Meeting these targets
demonstrates a well-optimized implementation and will be assessed
during peer evaluation.

