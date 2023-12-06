#!/usr/bin/env python3

# This is adapted from the OR-Tools vrp_capacity.py example:
# ortools/constraint_solver/samples/vrp_capacity.py

from datetime import datetime
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from typing import Any, Dict
import argparse
import json
import math
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="Solve routing model.")
    parser.add_argument(
        "-duration",
        default=10,
        help="Max runtime duration (in seconds).",
        type=int,
    )
    args = parser.parse_args()

    input_data = json.load(sys.stdin)
    output = solve(input_data, args.duration)
    print(json.dumps(output, indent=2))


def solve(input_data: Dict[str, Any], duration: int) -> Dict[str, Any]:
    start = datetime.now()
    depot = 0

    distance_matrix = matrix(input_data)
    manager = pywrapcp.RoutingIndexManager(
        len(distance_matrix),
        len(input_data["vehicles"]),
        depot
    )
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback.
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Capacity constraint.
    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        if from_node == depot:
            return 0
        return -input_data["stops"][from_node-1]["quantity"]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)

    capacity = input_data["defaults"]["vehicles"]["capacity"]
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0, # null capacity slack
        [capacity] * len(input_data["vehicles"]), # vehicle maximum capacities
        True, # start cumul to zero
        "Capacity",
    )

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.FromSeconds(duration)

    solution, value = format_solution(
        input_data,
        manager,
        routing,
        routing.SolveWithParameters(search_parameters)
    )

    duration = (datetime.now() - start).total_seconds()

    return {
        "version": {"sdk": "v1.0.3"},
        "options": {},
        "solutions": [solution],
        "statistics": {
            "result": {
                "duration": duration,
                "value": value
            },
            "run": {
                "duration": duration
            },
            "schema": "v1"
        }
    }

def format_solution(input_data, manager, routing, solution):
    unplanned = [] # TODO: track this if necessary
    vehicles = []

    depot = input_data["defaults"]["vehicles"]["start_location"]

    total_distance = 0
    for v in range(len(input_data["vehicles"])):
        vehicle_id = input_data["vehicles"][v]["id"]
        index = routing.Start(v)
        route_distance = 0

        route = [{
            "stop": {
                "id": f"{vehicle_id}-start",
                "location": depot
            },
            "travel_duration": 0,
            "cumulative_travel_duration": 0
        }]

        while not routing.IsEnd(index):
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            stop_distance = routing.GetArcCostForVehicle(previous_index, index, v)
            route_distance += stop_distance

            node = manager.IndexToNode(index)
            if node == 0:
                stop = {
                    "id": f"{vehicle_id}-end",
                    "location": depot
                }
            else:
                stop = input_data["stops"][node-1]

            route.append({
                "stop": stop,
                "travel_duration": stop_distance,
                "cumulative_travel_duration": route_distance
            })

        total_distance += route_distance

        vehicles.append({
            "id": vehicle_id,
            "route": route,
            "route_travel_distance": total_distance
        })

    return {"unplanned": unplanned, "vehicles": vehicles}, total_distance


def matrix(input_data):
    locations = [input_data["defaults"]["vehicles"]["start_location"]]
    for s in input_data["stops"]:
        locations.append(s["location"])

    m = []
    for start in locations:
        row = []
        for end in locations:
            km = haversine(start["lon"], start["lat"], end["lon"], end["lat"])
            row.append(round(km, 2))
        m.append(row)
    return m


def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371

    return int(round(c * r))


if __name__ == "__main__":
    main()
