# -*- coding: utf-8 -*-
from tornado.web import asynchronous, HTTPError
from tornado import escape
from tornado.options import options
from tornado import locale
from tornado import gen
from tornado.ioloop import IOLoop
from tornado.escape import json_encode
from handler import BaseHandler
from protected.models.user import User
from protected.models.sysConfig import SysConfig
from protected.libs.const import ErrorMessage, SuccessMessage
import sys, time, hashlib, re, urlparse, uuid, os, datetime
import protected.libs.utils as utiles

class recUsersHandler(BaseHandler):

    def post(self):
        pass

    def get(self):
        pass


handlers = [
]