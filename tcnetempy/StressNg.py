

class StressNg:
    def __init__(self):
        self.exe_path = "./stress-ng"

    def cpu(self, cpu_num, timeout):
        return f"{self.exe_path} --cpu {cpu_num} --timeout {timeout}"

    def memory(self, vm, vm_bytes, vm_hang, timeout):
        return f"{self.exe_path} --vm {vm} --vm-bytes {vm_bytes} --vm-hang {vm_hang} --timeout {timeout}"

    def disk(self, io, hdd, timeout):
        return f"{self.exe_path} --io {io} --hdd {hdd} --timeout {timeout}"
