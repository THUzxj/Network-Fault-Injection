import time
from tcnetempy.Fault import *
from tcnetempy.TcNetem import TcNetem

# create an instance of Delay with time=100ms and jitter=20ms
delay = Delay(time="100ms", jitter="20ms")

# create an instance of Loss with rate=5%
loss = Loss(rate="5%")

# create an instance of Reorder with rate=5% and gap=2
reorder = Reorder(rate="5%", gap="2")

# get the command for each fault
delay_cmd = delay.build_command()
loss_cmd = loss.build_command()
reorder_cmd = reorder.build_command()

# print the commands
print(delay_cmd)   # "delay 100ms 20ms"
print(loss_cmd)    # "loss 5%"
print(reorder_cmd) # "reorder 5% gap 2"

# create a TcNetem instance for the "eth0" interface
tc_netem = TcNetem(interface="eth0")

tc_netem.add_faults([delay, loss, reorder])

# sleep for 10 seconds
time.sleep(10)

# delete the netem qdisc
tc_netem.delete()
