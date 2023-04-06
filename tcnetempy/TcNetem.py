import logging
import subprocess
from typing import List
from tcnetempy.Fault import Fault

class TcNetem:
    def __init__(self, interface: str, faults: List[Fault] = []):
        self.interface = interface
        self.faults = faults

    def build_command(self) -> str:
        command = f"tc qdisc add dev {self.interface} root netem"
        for fault in self.faults:
            command += f" {fault.build_command()}"
        return command.strip()

    def add_faults(self, faults: List[Fault]):
        self.faults.extend(faults)

    def start(self):
        logging.info(f"Start fault injection: {self.build_command()}")
        command = self.build_command()
        subprocess.run(command.split())

    def delete(self):
        command = ' '.join(["tc", "qdisc", "del", "dev", self.interface, "root", "netem"])
        logging.info(f"Stop fault injection: {command}")
        subprocess.run(["tc", "qdisc", "del", "dev", self.interface, "root", "netem"])

    def _log(self):
        log = subprocess.run(["tc", "qdisc", "show", "dev", self.interface], stdout=subprocess.PIPE)
        print(log.stdout.decode('utf-8'))

    def dry_run(self):
        command = self.build_command()
        print(command)
