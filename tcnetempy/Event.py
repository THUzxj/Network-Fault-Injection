import time
import logging

from tcnetempy.TcNetem import TcNetem

class FaultEvent:
    def __init__(self, tc_netem: TcNetem, duation):
        self.tc_netem = tc_netem
        self.duation = duation
    
    def run(self):
        self.tc_netem.start()
        time.sleep(self.duation)
        self.tc_netem.delete()
