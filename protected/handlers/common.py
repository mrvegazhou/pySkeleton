# -*- coding: utf-8 -*-
from tornado.web import HTTPError, asynchronous
from tornado import gen
from tornado.options import options
from handler import BaseHandler, unblock
from protected.models.user import User
from protected.libs.const import ErrorMessage, SuccessMessage
import sys, time, re, urlparse, uuid, os, datetime, re, math, io, base64
import protected.libs.utils as utiles
import protected.libs.captcha as captcha

class FlushCattchaHandler(BaseHandler):
    @asynchronous
    @gen.coroutine
    def get(self):
        s = yield self.getCaptcha()
        self.return_json({'res': base64.b64encode(s)})

    @gen.coroutine
    def getCaptcha(self):
        code_img = captcha.create_validate_code()
        #验证码值保存到session中
        self.session['captcha'] = code_img[1].lower()
        self.session.save()
        o = io.BytesIO()
        code_img[0].save(o, format="GIF")
        code_img[0].close()
        raise gen.Return(o.getvalue())

#验证码输出
class CaptchaHandler(BaseHandler):
    @unblock
    def get(self, filename):
        code_img = captcha.create_validate_code()
        #验证码值保存到session中
        self.session['captcha'] = code_img[1].lower()
        self.session.save()
        o = io.BytesIO()
        code_img[0].save(o, format="JPEG")
        code_img[0].close()
        s = o.getvalue()
        self.set_header('Content-type', 'image/gif')
        self.set_header('Content-length', len(s))
        self.write(s)
        self.finish()

handlers = [
    (r"/common/captcha", FlushCattchaHandler),
    (r'/show/captcha/(?P<filename>.+\.gif)?', CaptchaHandler),
]