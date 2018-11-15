# -*- coding: utf-8 -*-
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.gen
import tornado.httpclient
import tornado.concurrent
import tornado.ioloop
from tornado.web import RequestHandler
from handler import BaseHandler
from protected.models.userNewsfeed import UserNewsfeed
import sys, time, re, urlparse, uuid, os, datetime, re

class SleepHandler(BaseHandler):
    @tornado.web.asynchronous
    def get(self):
        tornado.ioloop.IOLoop.instance().add_timeout(time.time() + 5, callback=self.on_response)
    def on_response(self):
        self.write("when i sleep 5s")
        self.finish()

class TestHandler(BaseHandler):
    def get(self):
        uf = UserNewsfeed()
        uf.test()
        self.finish()

from protected.libs.dispatcher.dispatcher import Signal, receiver
from protected.libs.middleware.signal import call_started, call_finished, handler_started, handler_render, SignalMiddleware
signal_done = Signal(providing_args=["toppings", "size"])
def callback(**kwargs):
    print kwargs['sender'].get_argument('t')
    print '00000000'
    return 'return'
# 通过调用信号connect方法注册事件回调
signal_done.connect(callback)

class Test2(BaseHandler):
    def get(self):
        signal_done.send(sender=self, toppings=111, size=222)
        self.render('test2.html')




handlers = [
    (r"/test22", Test2),
    (r"/ttt", TestHandler),
]