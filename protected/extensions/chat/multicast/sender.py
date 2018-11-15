#!/usr/bin/python
# -*- coding: utf8 -*-
import socket
import struct
from tornado.options import options

multicast_addr = options.CHAT['multicast']['addr']
port = options.CHAT['multicast']['port']

def sender(message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ttl = struct.pack('b', 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)

    sock.sendto(message, (multicast_addr, port))
    sock.close()
    return True
