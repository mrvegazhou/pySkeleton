#-*- coding:utf-8 -*-
import functools
import urllib
from protected.extensions.rbac.acl import Registry
from tornado.web import HTTPError

def checkPermission(operation, resource):
    def dec(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            if not self.current_user:
                if self.request.method == "GET":
                    url = self.get_login_url()
                    if "?" not in url:
                        url += "?" + urllib.urlencode(dict(next=self.request.full_url()))
                    self.redirect(url)
                    return
            checked = Registry().is_user_allowed(self.current_user.id, operation, resource)
            if not checked:
                raise HTTPError(403)
            return method(self, *args, **kwargs)
        return wrapper
    return dec


