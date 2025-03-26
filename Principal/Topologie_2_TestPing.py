#!/usr/bin/env python3
"""
This module creates a topology with a row of routers and FED (end device) nodes,
using the OTNS library.
"""

import os
import math
import time
import datetime
import sys

sys.path.insert(0, '/home/jbonn/ot-ns/pylibs')

from otns.cli import OTNS


def generate_row_topology(ns, row_y, num_routers, fed_total, delta_x, start_x=500,
                          pattern_first=None, pattern_intermediate=None, pattern_last=None):
    """
    Generate a row of routers at the given y-coordinate.
    For each router, based on its position (first, intermediate, or last),
    add FED (end device) nodes according to the provided pattern (None means no FEDs).
    Each FED is placed on a circle of fixed radius (150) around the router,
    with an angle computed as: angle = 2π * position / fed_total.
    
    :param ns: an instance of OTNS.
    :param row_y: the y-coordinate for the row.
    :param num_routers: number of routers to add.
    :param fed_total: total positions to consider on the circle.
    :param delta_x: horizontal distance between adjacent routers.
    :param start_x: starting x-coordinate (default 500).
    :param pattern_first: list of FED positions for the first router.
    :param pattern_intermediate: list of FED positions for intermediate routers.
    :param pattern_last: list of FED positions for the last router.
    :return: tuple (fed_ids, router_ids) where fed_ids is a dict with marked FED IDs and router_ids is a list.
    """
    radius = 150
    router_ids = []
    fed_ids = {'left_bottom': None, 'right_top': None}

    # Store first router ID to later check network stability
    first_router_id = None

    for i in range(num_routers):
        center_x = start_x + i * delta_x
        center_y = row_y

        # Add a router using the OTNS API
        router_id = ns.add("router", x=center_x, y=center_y)
        router_ids.append(router_id)
        if i == 0:
            first_router_id = router_id

        time.sleep(1)  # brief pause between additions

        # Select FED pattern based on router position
        if i == 0:
            fed_positions = pattern_first
        elif i == num_routers - 1:
            fed_positions = pattern_last
        else:
            fed_positions = pattern_intermediate

        if fed_positions is None:
            continue

        # Add FED nodes around the router
        for pos in fed_positions:
            angle = 2 * math.pi * pos / fed_total
            fed_x = int(center_x + radius * math.cos(angle))
            fed_y = int(center_y + radius * math.sin(angle))

            print(f"Adding FED at x={fed_x}, y={fed_y}")
            fed_id = ns.add("fed", x=fed_x, y=fed_y)
            if fed_id:
                print(f"Successfully added FED with ID: {fed_id} at position {pos}")
                if i == 0 and pos == 4:
                    fed_ids['left_bottom'] = fed_id
                    print(f"Marked FED {fed_id} as left_bottom")
                elif i == num_routers - 1 and pos == 2:
                    fed_ids['right_top'] = fed_id
                    print(f"Marked FED {fed_id} as right_top")
            else:
                print(f"WARNING: Failed to add FED at position {pos}")

    # Wait for network stabilization after the row is added
    if first_router_id:
        wait_for_network_stability(ns, duration=30, speedup_factor=32)
        state = ns.get_state(first_router_id)
        print(f"[Network] State of the first router after stabilization: {state}")

    print(f"FED IDs: {fed_ids} and Router IDs: {router_ids}")
    return fed_ids, router_ids


def wait_for_network_stability(ns, duration, speedup_factor):
    """
    Wait for network stability by running the simulation for a given duration with a specified speedup factor.
    
    :param ns: an instance of OTNS.
    :param duration: simulation time duration to run.
    :param speedup_factor: simulation speed.
    """
    ns.go(duration, speed=speedup_factor)
    time.sleep(1)  # small delay to ensure processing


def ping_nodes(ns, source_id, dest_id, count=3):
    """
    Perform a ping from the source node to the destination node.
    
    :param ns: an instance of OTNS.
    :param source_id: the source node ID.
    :param dest_id: the destination node ID.
    :param count: number of pings.
    :return: list of ping result tuples.
    """
    ns.ping(source_id, dest_id, count=count)
    time.sleep(2)  # wait for ping results
    return ns.pings()


def log_to_file(message, filename="log_file.txt"):
    """
    Append a message with a timestamp to the specified log file.
    
    :param message: the message to log.
    :param filename: the log file name.
    :return: True if successful, False otherwise.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(filename, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
        return True
    except Exception as e:
        print(f"ERROR: Unable to write to log file {filename}: {e}")
        return False


def log_and_print(message, filename="log_file.txt"):
    """
    Print a message to the console and log it to a file.
    
    :param message: the message to log and print.
    :param filename: the log file name.
    """
    print(message)
    log_to_file(message, filename)


def main():
    log_directory = os.path.dirname(os.path.abspath(__file__))
    log_filename = f"topology_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    log_file = os.path.join(log_directory, log_filename)

    ns = None
    try:
        # Instantiate OTNS with the desired arguments.
        ns = OTNS(otns_args=["-log", "critical"])
        log_and_print(f"Starting OTNS simulation... (Log file: {log_file})", log_file)

        num_routers = 3
        fed_total = 6
        delta_x = 150
        base_y = 250

        log_and_print("Generating initial row topology...", log_file)
        initial_fed_ids, initial_router_ids = generate_row_topology(
            ns,
            row_y=base_y,
            num_routers=num_routers,
            fed_total=fed_total,
            delta_x=delta_x,
            pattern_first=[2, 4],
            pattern_intermediate=[2, 4],
            pattern_last=[2, 4]
        )

        log_and_print("Base topology generated. Waiting for full network stabilization...", log_file)
        wait_for_network_stability(ns, duration=60, speedup_factor=32)

        left_bottom_id = initial_fed_ids['left_bottom']

        log_and_print("\nInitial routers' states:", log_file)
        for router_id in initial_router_ids:
            state = ns.get_state(router_id)
            log_and_print(f"  - Router {router_id}: {state}", log_file)

        # Slow down simulation for interactive operations.
        ns.speed = 1

        for i in range(1, 2):  # 1 extension
            log_and_print(f"\n=== Adding topology section {i+1} ===", log_file)
            start_x = 500 + i * num_routers * delta_x
            extension_fed_ids, extension_router_ids = generate_row_topology(
                ns,
                row_y=base_y,
                num_routers=num_routers,
                fed_total=fed_total,
                delta_x=delta_x,
                start_x=start_x,
                pattern_first=[2, 4],
                pattern_intermediate=[2, 4],
                pattern_last=[2, 4]
            )

            log_and_print("Waiting for new nodes to join the network...", log_file)
            wait_for_network_stability(ns, duration=60, speedup_factor=32)

            log_and_print("\nExtension routers' states:", log_file)
            for router_id in extension_router_ids:
                state = ns.get_state(router_id)
                log_and_print(f"  - Router {router_id}: {state}", log_file)

            ns.speed = 1

            right_top_id = extension_fed_ids['right_top']
            if right_top_id and left_bottom_id:
                log_and_print(f"\nConnectivity test: Pinging from node {right_top_id} (top-right) "
                              f"to {left_bottom_id} (bottom-left)", log_file)
                ping_results = ping_nodes(ns, right_top_id, left_bottom_id, count=5)
                log_and_print("Ping results:", log_file)
                log_and_print(str(ping_results), log_file)
            else:
                log_and_print("FEDs for source or destination not available for ping test", log_file)

        log_and_print("\nEnd of program. The OTNS simulation remains active for further interaction.", log_file)
        log_and_print("You can now interact with the network (perform pings, check states, etc.)", log_file)

        # Simple interactive loop for further commands (optional).
        try:
            while True:
                user_input = input("Enter command (or 'exit' to quit): ")
                if user_input.strip().lower() == "exit":
                    break
                print("Command not recognized.")
        except KeyboardInterrupt:
            pass
    finally:
        log_and_print("Program terminated.", log_file)
        if ns is not None:
            ns.close()


if __name__ == "__main__":
    main()
