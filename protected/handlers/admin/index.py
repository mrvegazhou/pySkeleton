# -*- coding: utf-8 -*-
from tornado.web import UIModule
from protected.handlers.admin.handler import AdminBaseHandler, adminAuthenticated
from protected.models.admin.adminUser import AdminUser
from protected.extensions.rbac.context import checkPermission
from protected.libs.const import AdminErrorMessage
from tornado.escape import json_encode
from tornado import gen
from tornado.web import asynchronous, authenticated
from tornado.ioloop import IOLoop
from protected.extensions.rbac.acl import Registry
from protected.conf.debug import logger
import time
import sys
import hashlib

class IndexHandler(AdminBaseHandler):
    _handler_template = "admin/index.html"
    @adminAuthenticated
    def get(self):
        admin_user_info = self.session.get('admin_user')
        self.render(self._handler_template)

#https://github.com/vfasky/QcoreCMS/blob/master/app/handlers/admin/__init__.py
#https://github.com/qloog/PyCMS-Tornado/blob/master/handlers/admin/login.py
class LoginHandler(AdminBaseHandler):
    def get(self):
        self.render("admin/login.html")

    @gen.coroutine
    @asynchronous
    def post(self):
        hash = hashlib.md5()
        username = self.get_argument('admin_user', '')
        password = self.get_argument('admin_password', '')
        #self.set_header("Content-Type", "application/json")
        if not (username and password):
            ret = {'msg': AdminErrorMessage.error_message['110'], 'code':'110'}
            self.finish(self.write(json_encode(ret)))

        # 防止穷举
        yield gen.Task(IOLoop.instance().add_timeout, time.time() + 2)

        adminUser = AdminUser()
        user_info = adminUser.getByUserName(username)

        if not user_info:
            ret = { 'msg': AdminErrorMessage.error_message['002'], 'code':'002'}
            self.finish(self.write(json_encode(ret)))

        hash.update(password)
        if user_info['admin_password']!=hash.hexdigest():
            ret = { 'msg': AdminErrorMessage.error_message['003'], 'code':'003'}
            self.finish(self.write(json_encode(ret)))
        #获取角色
        acl = Registry()
        role = acl.get_role(user_info['id'])
        if role:
            user_info['role'] = role
        #保存session
        self.session["admin_user"] = user_info
        self.session.save()
        next_url = self.get_argument('next', '')
        if not next_url:
            next_url = self.get_cookie('admin_next') if self.get_cookie('admin_next') else '/admin/index'
            if next_url=='/admin/login':
                next_url = '/admin/index'
        ret = {'msg': '登录成功', 'url': '/admin/index', 'code':'success', 'next':next_url}
        self.finish(self.write(json_encode(ret)))

class LogoutHandler(AdminBaseHandler):
    _handler_template = "admin/login.html"
    def get(self):
        self.session.delete()
        self.render(self._handler_template)


handlers = [
    (r"/admin/index", IndexHandler),
    (r"/admin/login", LoginHandler),
    (r"/admin/logout", LogoutHandler)
]