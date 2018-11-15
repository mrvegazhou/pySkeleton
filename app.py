#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
import tornado
from tornado import web
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
import tornado.autoreload
from tornado.options import options
from protected.conf.conf import parse_config_file
import protected.libs.sessionCache as session
import os, sys
from protected.handlers import uimodules

class Application(web.Application):
    def __init__(self):
        from protected.urls import handlers, sub_handlers, ui_modules
        settings = dict(
            debug = options.debug,
            template_path = os.path.join(os.path.dirname(__file__), "templates"),
            static_path = os.path.join(os.path.dirname(__file__), "static"),
            uploads_path = os.path.join(os.path.dirname(__file__), "uploads"),
            xsrf_cookies = options.xsrf_cookies,
            cookie_secret = options.cookie_secret,
            login_url = options.login_url,
            #static_url_prefix = options.static_url_prefix,
            ui_modules = uimodules
        )
        super(Application, self).__init__(handlers, **settings)
        # 初始化该类的 session_manager
        self.session_manager = session.SessionManager(options.session['session_secret'], options.session['session_memcache'], options.session['session_timeout'])
        for sub_handler in sub_handlers:
            self.add_handlers(sub_handler[0], sub_handler[1])

def main():
    dir = os.path.dirname(__file__)
    #加载配置文件
    parse_config_file(dir+"protected/conf/main.conf")
    tornado.options.parse_command_line()
    http_server = HTTPServer(Application(), xheaders=True)
    port = options.port
    num_processes = options.num_processes

    if options.debug:
        num_processes = 1
    if options.chat_app:
        port = getattr(options, "chat_app_port", options.port + 1)
        num_processes = 1

    #add_callback(multicast_receiver)

    http_server.bind(int(port))
    http_server.start(int(num_processes))
    IOLoop.instance().start()

if __name__ == "__main__":
    main()