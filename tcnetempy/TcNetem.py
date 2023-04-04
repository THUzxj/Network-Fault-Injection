import subprocess

class TcNetem:
    def __init__(self, interface):
        self.interface = interface

    def build_command(self, faults):
        command = f"tc qdisc add dev {self.interface} root netem"
        for fault in faults:
            command += f" {fault.build_command()}"
        return command.strip()

    def add_faults(self, faults):
        command = self.build_command(faults)
        subprocess.run(command.split())

    def delete(self):
        subprocess.run(["tc", "qdisc", "del", "dev", self.interface, "root", "netem"])
