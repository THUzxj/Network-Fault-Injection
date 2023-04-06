from typing import Optional

class Fault:
    def __init__(self):
        pass

    def build_command(self):
        raise NotImplementedError

class Delay:
    def __init__(self, time: str, jitter: Optional[str] = None, correlation: Optional[str] = None):
        self.time = time
        self.jitter = jitter
        self.correlation = correlation

    def build_command(self) -> str:
        cmd = f"delay {self.time}"
        if self.jitter:
            cmd += f" {self.jitter}"
        if self.correlation:
            cmd += f" {self.correlation}"
        return cmd

class Loss:
    def __init__(self, rate: str, correlation: Optional[str] = None, random: bool = False) -> None:
        self.rate = rate
        self.correlation = correlation
        self.random = random

    def build_command(self) -> str:
        cmd = f"loss {self.rate}"
        if self.correlation:
            cmd += f" {self.correlation}"
        if self.random:
            cmd += " random"
        return cmd

class Corruption:
    def __init__(self, rate: str, correlation: Optional[str] = None):
        self.rate = rate
        self.correlation = correlation

    def build_command(self) -> str:
        cmd = f"corrupt {self.rate}"
        if self.correlation:
            cmd += f" {self.correlation}"
        return cmd

class Duplicate:
    def __init__(self, rate: int, correlation: Optional[int] = None):
        self.rate = rate
        self.correlation = correlation

    def build_command(self) -> str:
        cmd = f"duplicate {self.rate}"
        if self.correlation:
            cmd += f" {self.correlation}"
        return cmd

class Reorder:
    def __init__(self, rate: int, correlation: Optional[int] = None, gap: Optional[int] = None):
        self.rate = rate
        self.correlation = correlation
        self.gap = gap

    def build_command(self) -> str:
        cmd = f"reorder {self.rate}"
        if self.correlation:
            cmd += f" {self.correlation}"
        if self.gap:
            cmd += f" gap {self.gap}"
        return cmd

class Rate:
    def __init__(self, rate: int, packet_overhead: Optional[int] = None, cell_size: Optional[int] = None, cell_overhead: Optional[int] = None):
        self.rate = rate
        self.packet_overhead = packet_overhead
        self.cell_size = cell_size
        self.cell_overhead = cell_overhead

    def build_command(self) -> str:
        cmd = f"rate {self.rate}"
        if self.packet_overhead:
            cmd += f" {self.packet_overhead}"
        if self.cell_size:
            cmd += f" {self.cell_size}"
        if self.cell_overhead:
            cmd += f" {self.cell_overhead}"
        return cmd

class Slot:
    def __init__(self, min_delay: int, max_delay: Optional[int]=None, packets: Optional[int]=None, bytes: Optional[int]=None, distribution: Optional[str]=None, jitter: Optional[int]=None):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.packets = packets
        self.bytes = bytes
        self.distribution = distribution
        self.jitter = jitter

    def build_command(self) -> str:
        cmd = f"slot {self.min_delay}"
        if self.max_delay:
            cmd += f" {self.max_delay}"
        if self.packets:
            cmd += f" packets {self.packets}"
        if self.bytes:
            cmd += f" bytes {self.bytes}"
        if self.distribution:
            cmd += f" distribution {self.distribution}"
        if self.jitter:
            cmd += f" {self.jitter}"
        return cmd
    