import socket

from ansible.plugins.callback import CallbackBase
import json

def get_interfaces():
    return [iface[1] for iface in socket.if_nameindex()]

def calculate_time(padding, duation, number_of_faults):
    return (padding + duation) * number_of_faults
