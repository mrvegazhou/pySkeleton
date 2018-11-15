#!/usr/bin/python
# -*- coding: utf8 -*-
import socket
import struct
from tornado import ioloop
from tornado.options import options
import functools

multicast_addr = options.CHAT['multicast']['addr']
bind_addr = options.CHAT['multicast']['bind_addr']
port = options.CHAT['multicast']['port']

def make_sock():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((bind_addr, port))

    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)  #设置多播组数据的TTL的值 允许设置超时TTL，范围为0～255之间的任何值
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1) #禁止组播数据回送 参数loop设置为0禁止回送，设置为1允许回送。

    intf = socket.gethostbyname(socket.gethostname())
    sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF,
                    socket.inet_aton(intf) + socket.inet_aton('0.0.0.0'))

    membership = socket.inet_aton(multicast_addr) + socket.inet_aton(bind_addr)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)

    return sock

def add_callback(callback):
    def conn_callback(sock, fd, events):
        callback(sock)
    sock = make_sock()
    io_loop = ioloop.IOLoop.instance()
    handler = functools.partial(conn_callback, sock)
    #用于添加socket到主循环中, 接受三个参数: fd 是socket的文件描述符 handler 是处理此socket的 callback函数 * events 是此socket注册的事件
    io_loop.add_handler(sock.fileno(), handler, io_loop.READ)
    return io_loop
