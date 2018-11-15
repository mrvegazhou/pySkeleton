# -*- coding: utf-8 -*-
from tornado.web import UIModule
from handler import BaseHandler
from protected.models.user import User
from protected.libs import cache
import sys

class IndexHandler(BaseHandler):
    _handler_template = "index.html"
    def get(self):
        print self.get_current_user()
        print '====-=-=-=-='
        self.render(self._handler_template)


handlers = [
    (r"/", IndexHandler),
    (r"/index", IndexHandler)
]