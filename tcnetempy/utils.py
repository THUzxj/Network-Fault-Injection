import socket

def get_interfaces():
    return [iface[1] for iface in socket.if_nameindex()]
