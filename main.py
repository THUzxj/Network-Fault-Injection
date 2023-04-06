import os
import time
import argparse
from datetime import datetime
import itertools
import logging

from tcnetempy.TcNetem import TcNetem
from tcnetempy.Fault import *
from tcnetempy.Event import FaultEvent
from tcnetempy.utils import get_interfaces

# Fault Injection Campaign

def get_args():
    parser = argparse.ArgumentParser(description='Process args for retrieving arguments')

    # log file
    parser.add_argument('-l', "--log", help="log file", default=None, type=str)

    # schedule
    parser.add_argument("-p", "--padding", help="padding_time (second)", required=True, type=int)
    parser.add_argument("-d", "--duation", help="fault injection duation (second)", required=True, type=int)

    parser.add_argument("--dry", action="store_true", help="dry run")

    parser.add_argument("--interface_num", help="number of interfaces", type=int)
    return parser.parse_args()

FAULTS = [
    {
        "type": "delay",
        "values": [0, 500],
        "unit": "ms",
        "args": "20ms"
    },
    {
        "type": "loss",
        "values": [0, 15],
        "unit": "%",
        "args": "25%"
    },
    {
        "type": "duplicate",
        "values": [0],
        "unit": "%",
        "args": ""
    }
]


if __name__ == "__main__":
    args = get_args()

    if args.log is None:
        os.makedirs("logs", exist_ok=True)
        args.log = f"logs/{datetime.now().strftime('%Y-%m-%d-%H:%M:%S')}.log"
        print("log file: ", args.log)

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler(args.log),
                            logging.StreamHandler()
                        ])
    
    devices = get_interfaces()
    if args.interface_num:
        devices = devices[:args.interface_num]
    logging.info(f"Devices: {devices}")

    try:
        for fault_values in itertools.product(devices, *[fault["values"] for fault in FAULTS]):
            if sum(fault_values[1:]) == 0:
                continue
            device = fault_values[0]
            faults = [
                Delay(time=f"{fault_values[1]}ms", jitter="20ms"),
                Loss(rate=f"{fault_values[2]}%", correlation="25%"),
                Duplicate(rate=f"{fault_values[3]}%")
            ]
            tc_netem = TcNetem(interface=device, faults=faults)
            if args.dry:
                tc_netem.dry_run()
            else:
                fault_event = FaultEvent(tc_netem=tc_netem, duation=args.duation)
                fault_event.run()
                time.sleep(args.padding)
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt")
        tc_netem.delete()
        exit(0)
