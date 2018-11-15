# -*- coding: utf-8 -*-
import functools
import urllib
import json
from tornado.web import HTTPError
from tornado.options import options
from protected.models.user import User
from protected.libs.exceptions import ArgumentError, BaseError
from protected.libs.const import ErrorMessage, SuccessMessage

def admin(method):
    """Decorate with this method to restrict to site admins."""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.current_user:
            if self.request.method == "GET":
                url = self.get_login_url()
                if "?" not in url:
                    url += "?" + urllib.urlencode(dict(next=self.request.full_url()))
                self.redirect(url)
                return
            raise HTTPError(403)
        elif not self.is_admin:
            if self.request.method == "GET":
                self.redirect(options.home_url)
                return
            raise HTTPError(403)
        else:
            return method(self, *args, **kwargs)
    return wrapper

def staff(method):
    """Decorate with this method to restrict to site staff."""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.current_user:
            if self.request.method == "GET":
                url = self.get_login_url()
                if "?" not in url:
                    url += "?" + urllib.urlencode(dict(next=self.request.full_url()))
                self.redirect(url)
                return
            raise HTTPError(403)
        elif not self.is_staff:
            if self.request.method == "GET":
                self.redirect(options.home_url)
                return
            raise HTTPError(403)
        else:
            return method(self, *args, **kwargs)
    return wrapper


def authenticated(method):
    """Decorate methods with this to require that the user be logged in.
    Fix the redirect url with full_url.
    Tornado use uri by default.
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.current_user:
            if self.request.method == "GET":
                url = self.get_login_url()
                if "?" not in url:
                    url += "?" + urllib.urlencode(dict(next=self.request.full_url()))
                self.redirect(url)
                return
            raise HTTPError(403)
        return method(self, *args, **kwargs)
    return wrapper

'''
重复的子调用过程取消
@cache
def fib(n):
    if n < 2:
        return 1
    return fib(n-1) + fib(n-2)
'''
def cacheSub(func):
    caches = {}
    @functools.wraps(func)
    def wrap(*args):
        if args not in caches:
            caches[args] = func(*args)
        return caches[args]
    return wrap

#检查用户是否已经验证邮箱地址
def checkVerify(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        uid = self.get_secure_cookie('uid')
        if not uid:
            self.write(json.dumps({'code': 'error', 'msg': ErrorMessage.error_message['019'], 'num': '019'}))
            self.finish()
        user = User()
        info = user.getItem(uid)
        if info['is_verify']==1:
            self.write(json.dumps({'code': 'error', 'msg': ErrorMessage.error_message['018'], 'num': '018'}))
            self.finish()
        return method(self, *args, **kwargs)
    return wrapper


'''
保存前装饰器
'''
def preSave(f):
    @functools.wraps(f)
    def wrap_func(self, *args, **kargs):
        try:
            if callable(self._preSave):
                if not self._preSave(self, *args, **kargs):
                    return False
                else:
                    return f(self, *args, **kargs)
            else:
                 return False
        except BaseError, e:
            print e
            return False
    return wrap_func
'''
保存后运行的
'''
def postSave(f):
    @functools.wraps(f)
    def wrap_func(self, *args, **kargs):
        try:
            if callable(self._postSave):
                if not f:
                    return False
                else:
                    self.postSave(self, *args, **kargs)
                    f(self, *args, **kargs)
            else:
                 return False
        except BaseError, e:
            print e
            return False
    return wrap_func



