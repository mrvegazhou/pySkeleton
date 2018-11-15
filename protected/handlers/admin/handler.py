# -*- coding: utf8 -*-
import re
import urllib
import json
from protected.conf.debug import logger
from tornado.web import RequestHandler, HTTPError
from tornado.options import options
from tornado import template, ioloop, escape
from protected.libs.exceptions import TemplateContextError
from tornado import locale
import protected.libs.sessionCache as session
import functools
import urlparse
from protected.libs.const import AdminErrorMessage
from protected.models.admin.adminResource import AdminResource
from protected.libs.db.memDB import MemDB
from protected.handlers.handler import BaseHandler, _Context, ErrorHandler, _remove_slash_re
from protected.libs.utils import CJsonEncoder
import os,sys

class AdminBaseHandler(BaseHandler):
    session = None
    def __init__(self, application, request, **kwargs):
        try:
            #设置session
            super(AdminBaseHandler, self).__init__(application, request, **kwargs)
            self.session = session.Session(self.application.session_manager, self)
        except Exception as e:
            print e

    #获取系统菜单
    def get_menus(self):
        user_info = self.session.get("admin_user")
        if user_info:
            try:
                mc = MemDB()
                self._context.menus = mc.memGet('menus')
                if not self._context.menus:
                    ar = AdminResource()
                    mc.memSet('menus', ''.join(ar.showTreeMenus(role_id=user_info['role']['id'], id=0, menus=[])))
                    self._context.menus = mc.memGet('menus')
            except Exception as e:
                self._context.menus = ''.join(ar.showTreeMenus(role_id=user_info['role']['id'], id=0, menus=[]))
        else:
            self._context.menus = ''

    def prepare(self):
        self._prepare_context()

    def _prepare_context(self):
        self._context = _Context()
        self._context.options = options
        #从缓存中获取菜单
        self.get_menus()

    def render_string(self, template_name, **kwargs):
        assert "context" not in kwargs, "context is a reserved word for template context valuable."
        kwargs['context'] = self._context
        kwargs['url_escape'] = escape.url_escape
        return super(BaseHandler, self).render_string(template_name, **kwargs)

    @property
    def is_admin(self):
        pass

    def json_encode(self, value):
        return json.dumps(value, cls=CJsonEncoder).replace("</", "<\\/")

#后台验证用户是否登录
def adminAuthenticated(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if (not self.session.get('admin_user')) or (not self.get_secure_cookie('session_id')):
            self.set_cookie("admin_next", self.request.path)
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                self.set_header('Content-Type', 'application/json; charset=UTF-8')
                self.write(json.dumps({'success': False, 'msg': AdminErrorMessage.error_message['004']}))
                return
            if self.request.method in ("GET", "HEAD"):
                url = options.admin_login_url
                if "?" not in url:
                    if urlparse.urlsplit(url).scheme:
                        # if login url is absolute, make next absolute too
                        next_url = self.request.full_url()
                    else:
                        next_url = self.request.uri
                    url += "?" + urllib.urlencode(dict(next=next_url))
                self.redirect(url)
                return
            raise HTTPError(403)
        return method(self, *args, **kwargs)
    return wrapper

_remove_slash_re = re.compile(".+/$")