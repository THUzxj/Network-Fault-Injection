#!/usr/bin/env python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import time
import argparse
from datetime import datetime
import itertools
import logging
import shutil
import json
import random

from collections import namedtuple

import ansible.constants as C
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.module_utils.common.collections import ImmutableDict
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.plugins.callback import CallbackBase
from ansible.vars.manager import VariableManager
from ansible import context

from tcnetempy.TcNetem import TcNetem
from tcnetempy.Fault import *
from tcnetempy.Event import FaultEvent
from tcnetempy.StressNg import StressNg
from tcnetempy.utils import get_interfaces, calculate_time

# Create a callback plugin so we can capture the output
class ResultsCollectorJSONCallback(CallbackBase):
    """A sample callback plugin used for performing an action as results come in.

    If you want to collect all results into a single object for processing at
    the end of the execution, look into utilizing the ``json`` callback plugin
    or writing your own custom callback plugin.
    """

    def __init__(self, *args, **kwargs):
        super(ResultsCollectorJSONCallback, self).__init__(*args, **kwargs)
        self.host_ok = {}
        self.host_unreachable = {}
        self.host_failed = {}

    def v2_runner_on_unreachable(self, result):
        host = result._host
        self.host_unreachable[host.get_name()] = result

    def v2_runner_on_ok(self, result, *args, **kwargs):
        """Print a json representation of the result.

        Also, store the result in an instance attribute for retrieval later
        """
        host = result._host
        self.host_ok[host.get_name()] = result
        print(json.dumps({host.name: result._result}, indent=4))

    def v2_runner_on_failed(self, result, *args, **kwargs):
        host = result._host
        self.host_failed[host.get_name()] = result


DEFAULT_LOG_PATH = "../logs"

# Fault Injection Campaign

def get_args():
    parser = argparse.ArgumentParser(description='Process args for retrieving arguments')

    # log file
    parser.add_argument('-l', "--log", help="log file", default=None, type=str)
    parser.add_argument("--log_dir", help="log directory", default=DEFAULT_LOG_PATH, type=str)

    # schedule
    parser.add_argument("-pmin", "--padding_min", help="padding_time (second)", type=int)
    parser.add_argument("-pmax", "--padding_max", type=int)
    parser.add_argument("-d", "--duation", help="fault injection duation (second)", required=True, type=int)
    # parser.add_argument("-dmin", "--duation_min", help="fault injection duation (second)", type=int)
    # parser.add_argument("-dmax", "--duation_max", type=int)

    parser.add_argument("--dry", action="store_true", help="dry run")

    parser.add_argument("--interface_num", help="number of interfaces", type=int, )

    parser.add_argument("-g", "--group", type=str)
    parser.add_argument("-H", "--hosts", type=str)
    parser.add_argument("-i", "--inventory", required=True, type=str)
    # parser.add_argument("-m", "--mode", required=True)

    return parser.parse_args()

CPU_FAULTS = reversed(["2", "4", "8", "16", "32"])

MEMORY_FAULTS = reversed([1, 2, 4, 6, 8])

DISK_FAULTS = reversed([1, 2, 4, 8, 16])

NETWORK_FAULTS = [(1000, 0), (1000, 25), (1000, 50), (0, 25), (0, 50)]

# FAULTS = [
#     {
#         "type": "delay",
#         "values": [0, 1000, 5000],
#         "unit": "ms",
#         "args": "20ms"
#     },
#     {
#         "type": "loss",
#         "values": [0, 15, 30],
#         "unit": "%",
#         "args": "25%"
#     },
#     # {
#     #     "type": "duplicate",
#     #     "values": [0],
#     #     "unit": "%",
#     #     "args": ""
#     # }
# ]


if __name__ == "__main__":
    args = get_args()

    if args.log is None:
        os.makedirs(DEFAULT_LOG_PATH, exist_ok=True)
        args.log = f"{args.log_dir}/{args.mode}_{datetime.now().strftime('%Y-%m-%d-%H:%M:%S')}.log"
        print("log file: ", args.log)

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler(args.log),
                            logging.StreamHandler()
                        ])
    
    context.CLIARGS = ImmutableDict(connection='smart', module_path=['/to/mymodules', '/usr/share/ansible'], forks=10, become=True,
                                    become_method="sudo", become_user="root", check=False, diff=False, verbosity=0)

    loader = DataLoader()

    passwords = dict(vault_pass='secret')

    results_callback = ResultsCollectorJSONCallback()

    inventory = InventoryManager(loader=loader, sources = [args.inventory, ])

    variable_manager = VariableManager(loader=loader, inventory=inventory)

    if args.group:
        host_list = inventory.get_groups_dict()[args.group]
    elif args.hosts:
        host_list = args.hosts.split(",")
    else:
        raise Exception
    
    print("host_list:", host_list)

    stressNg = StressNg()

    devices = get_interfaces()
    devices = [ device for device in devices if device != "lo" and not device.startswith("v") and not device.startswith("b")]
    if args.interface_num:
        devices = devices[:args.interface_num]
    # logging.info(f"Devices: {devices}")
    print(f"Devices: {devices}")
    network_commands = [TcNetem(interface=device, faults=[
        Delay(time=f"{fault_values[0]}ms", jitter="20ms"),
        Loss(rate=f"{fault_values[1]}%", correlation="25%"),
    ]).build_campaign_command(args.duation) for device in devices for fault_values in NETWORK_FAULTS]

    all_commands = []
    all_commands.extend(network_commands)
    all_commands.extend([stressNg.cpu(fault, args.duation) for fault in CPU_FAULTS])
    all_commands.extend([stressNg.memory(vm=fault, vm_bytes="1G", vm_hang=args.duation, timeout=args.duation) for fault in MEMORY_FAULTS])
    all_commands.extend([stressNg.disk(io=fault, hdd=fault, timeout=args.duation) for fault in DISK_FAULTS])

    print(all_commands)
    
    if args.dry:
        exit(0)

    while True: 
        tqm = TaskQueueManager(
            inventory=inventory,
            variable_manager=variable_manager,
            loader=loader,
            passwords=passwords,
            stdout_callback=results_callback,  # Use our custom callback instead of the ``default`` callback plugin, which prints to stdout
        )

        # choose a command randomly
        command = all_commands[random.randint(0, len(all_commands) -1)]

        play_source = dict(
            name="Ansible Play",
            hosts=host_list,
            gather_facts='no',
            tasks=[
                # dict(action=dict(module='shell', args='ls'), register='shell_out'),
                # dict(action=dict(module='debug', args=dict(msg='{{shell_out.stdout}}'))),
                # dict(action=dict(module='command', args=dict(cmd='/usr/bin/uptime'))),
                dict(
                    action=dict(module='command',
                                args=dict(
                                    cmd= command,
                                    chdir="/root"
                                ),
                            ), register="shell_out"
                ),
                # dict(
                #     action=dict(module='debug', args=dict(msg='{{shell_out.stdout}}'))
                # )
            ],
            # become="true",
            # become_user="root"
        )
        print(play_source)
        logging.info(f"Start_fault_injection, {host_list}, {command}")
        play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

        # Actually run it
        try:
            result = tqm.run(play)  # most interesting data for a play is actually sent to the callback's methods
        except Exception as e:
            print(e)
        finally:
            # we always need to cleanup child procs and the structures we use to communicate with them
            tqm.cleanup()
            if loader:
                loader.cleanup_all_tmp_files()

        # Remove ansible tmpdir
        shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)

        print("UP ***********")
        for host, result in results_callback.host_ok.items():
            print('{0} >>> {1}'.format(host, result._result['stdout']))

        print("FAILED *******")
        for host, result in results_callback.host_failed.items():
            print('{0} >>> {1}'.format(host, result._result['msg']))

        print("DOWN *********")
        for host, result in results_callback.host_unreachable.items():
            print('{0} >>> {1}'.format(host, result._result['msg']))

        time.sleep(random.randint(args.padding_min, args.padding_max))

    # devices = get_interfaces()
    # if args.interface_num:
    #     devices = devices[:args.interface_num]
    # logging.info(f"Devices: {devices}")

    # fault_values_sets = list(itertools.product(devices, *[fault["values"] for fault in FAULTS]))

    # fault_values_sets = [fault_values for fault_values in fault_values_sets if sum(fault_values[1:]) != 0]

    # print("The fault injection will take about", calculate_time(args.padding, args.duation, len(fault_values_sets)), "seconds.")

    # try:
    #     for fault_values in fault_values_sets:
    #         device = fault_values[0]
    #         faults = [
    #             Delay(time=f"{fault_values[1]}ms", jitter="20ms"),
    #             Loss(rate=f"{fault_values[2]}%", correlation="25%"),
    #             # Duplicate(rate=f"{fault_values[3]}%")
    #         ]
    #         tc_netem = TcNetem(interface=device, faults=faults)
    #         if args.dry:
    #             tc_netem.dry_run()
    #         else:
    #             fault_event = FaultEvent(tc_netem=tc_netem, duation=args.duation)
    #             fault_event.run()
    #             time.sleep(args.padding)
    # except KeyboardInterrupt:
    #     logging.info("KeyboardInterrupt")
    #     tc_netem.delete()
    #     exit(0)
