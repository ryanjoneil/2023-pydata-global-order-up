#!/usr/bin/env python3
from datetime import datetime, timedelta
from dateutil.parser import parse
from itertools import groupby
from operator import itemgetter
from ortools.linear_solver import pywraplp
from typing import Any, Dict
import argparse
import json
import math
import sys

STATUS = {
    pywraplp.Solver.FEASIBLE: "suboptimal",
    pywraplp.Solver.INFEASIBLE: "infeasible",
    pywraplp.Solver.OPTIMAL: "optimal",
    pywraplp.Solver.UNBOUNDED: "unbounded",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Solve scheduling model.")
    parser.add_argument(
        "-input",
        default="",
        help="Path to input file. Default is stdin.",
    )
    parser.add_argument(
        "-output",
        default="",
        help="Path to output file. Default is stdout.",
    )
    parser.add_argument(
        "-duration",
        default=30,
        help="Max runtime duration (in seconds). Default is 30.",
        type=int,
    )
    args = parser.parse_args()

    input_data = read_input(args.input)
    solution = solve(input_data)
    write_output(args.output, solution)


def solve(input_data: Dict[str, Any]) -> Dict[str, Any]:
    provider = "SCIP"
    solver = pywraplp.Solver.CreateSolver(provider)

    big = 10**6 # solver.infinity() fails on arm64

    # shifts[w] = 1 if worker w's shift is assigned
    shifts = []
    for worker in input_data["workers"]:
        shifts.append({
            "worker_id": worker["id"],
            "start": worker["availability"][0]["start"],
            "end": worker["availability"][0]["end"],
            "var": solver.BoolVar(name=f"shifts[{worker['id']}]")
        })

    # supply[h] = scheduled supply per hour
    supply = []
    ub = len(shifts)
    for req in input_data["required_workers"]:
        t = parse(req["start"])
        end = parse(req["end"])

        while t < end:
            hour = str(t).replace(' ', 'T')
            supply.append({
                "hour": hour,
                "demand": req["count"],
                "var": solver.NumVar(lb=0, ub=ub, name=f"supply[{hour}]")
            })
            t += timedelta(hours=1)

    # supply = sum of matching, selected shifts.
    for s in supply:
        x = [t["var"] for t in shifts if t["start"] <= s["hour"] <= t["end"]]
        solver.Add(s["var"] == sum(x))

    # Objective = sum of oversupply and undersupply penalties.
    obj = []
    for s in supply:
        over = solver.NumVar(lb=0, ub=ub, name=f"over[{s['hour']}")
        under = solver.NumVar(lb=0, ub=ub, name=f"under[{s['hour']}")
        solver.Add(over >= s["var"] - s["demand"])
        solver.Add(under >= s["demand"] - s["var"])
        obj.extend((
            input_data["penalties"]["oversupply"] * over,
            input_data["penalties"]["undersupply"] * under
        ))

    # Minimize sum of penalties.
    solver.Minimize(sum(obj))
    status = solver.Solve()

    # Pull out shift assignments from solution.
    assigned_shifts = []
    for sh in shifts:
        if sh["var"].solution_value() > 0.5:
            assigned_shifts.append({
                "start": sh["start"],
                "end": sh["end"],
                "worker_id": sh["worker_id"]
            })

    return {
        "solutions": [
            {
                "assigned_shifts": assigned_shifts,
                "number_assigned_workers": len(assigned_shifts),
                "demand": [s["demand"] for s in supply],
                "supply": [int(s["var"].solution_value()) for s in supply]
            }
        ],
        "statistics": {
            "result": {
                "custom": {
                    "constraints": solver.NumConstraints(),
                    "provider": provider,
                    "status": STATUS.get(status, "unknown"),
                    "variables": solver.NumVariables(),
                },
                "duration": solver.WallTime() / 1000,
                "value": solver.Objective().Value(),
            },
            "run": {
                "duration": solver.WallTime() / 1000,
            },
            "schema": "v1",
        },
    }


def log(message: str) -> None:
    """Logs a message. We need to use stderr since stdout is used for the solution."""

    print(message, file=sys.stderr)


def read_input(input_path) -> Dict[str, Any]:
    """Reads the input from stdin or a given input file."""

    input_file = {}
    if input_path:
        with open(input_path, "r", encoding="utf-8") as file:
            input_file = json.load(file)
    else:
        input_file = json.load(sys.stdin)

    return input_file


def write_output(output_path, output) -> None:
    """Writes the output to stdout or a given output file."""

    content = json.dumps(output, indent=2)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(content + "\n")
    else:
        print(content)


if __name__ == "__main__":
    main()
