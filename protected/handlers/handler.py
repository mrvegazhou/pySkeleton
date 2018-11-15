# -*- coding: utf8 -*-
import logging as logger
from tornado.escape import json_encode
from tornado.web import RequestHandler, HTTPError, asynchronous
from tornado import gen
from tornado.options import options
from tornado import template, ioloop, escape
from protected.libs.exceptions import TemplateContextError
from protected.libs.const import ErrorMessage, SuccessMessage
from tornado import locale
from tornado.ioloop import IOLoop
from protected.models.user import User
from protected.libs.utils import DateEncoder
import os, sys, functools, urlparse, json, traceback, httplib, re, urllib, uuid, time, datetime
from protected.libs.MyCrypt import MyCrypt
from functools import partial, wraps
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import cpu_count
import protected.libs.sessionCache as session

class BaseHandler(RequestHandler):
    _first_running = True
    _locale = None

    def __init__(self, application, request, **kwargs):
        if BaseHandler._first_running:
            self._after_prefork()
            BaseHandler._first_running = False
        #国际化
        locale.load_translations("./protected/translations")
        locale.set_default_locale("zh_CN")
        self._locale = locale.get()
        super(BaseHandler, self).__init__(application, request, **kwargs)
        self.session = session.Session(self.application.session_manager, self)


    def _after_prefork(self):
        pass

    def json_encode(self, value):
        return json.dumps(value, cls=DateEncoder)

    def render_string(self, template_name, **kwargs):
        """Override default render_string, add context to template."""
        assert "context" not in kwargs, "context is a reserved word for template context valuable."
        kwargs['context'] = self._context
        kwargs['url_escape'] = escape.url_escape
        return super(BaseHandler, self).render_string(template_name, **kwargs)

    def is_ajax(self):
        return "X-Requested-With" in self.request.headers and \
            self.request.headers['X-Requested-With'] == "XMLHttpRequest"

    def return_json(self, data_dict, date_encoder=False, finish=False):
        """
        acessory method to return json objects
        """
        self.set_header('Content-Type', 'application/json')
        if date_encoder:
            json_ = self.json_encode(data_dict)
        else:
            json_ = json_encode(data_dict)
        self.write(json_)
        if finish:
            self.finish()
        return

    def return_json_by_num(self, num, type=False, date_encoder=False, finish=False):
        if not type:
            self.return_json({'msg': ErrorMessage.error_message[num], 'code': 'error', 'num': str(num)}, finish=finish)
        else:
            self.return_json({'msg': SuccessMessage.success_message[num], 'code': 'success', 'num': str(num)}, finish=finish)
        return

    def get_json_argument(self, name, default=None):
        """Find and return the argument with key 'name' from JSON request data.
        Similar to Tornado's get_argument() method.
        """
        if default is None:
            default = self._ARG_DEFAULT
        if not self.request.arguments:
            self.load_json()
        if name not in self.request.arguments:
            if default is self._ARG_DEFAULT:
                msg = "Missing argument '%s'" % name
                logger.debug(msg)
                raise HTTPError(400, msg)
            logger.debug("Returning default argument %s, as we couldn't find "
                    "'%s' in %s" % (default, name, self.request.arguments))
            return default
        arg = self.request.arguments[name]
        logger.debug("Found '%s': %s in JSON arguments" % (name, arg))
        return arg

    #获取上一页面
    def get_next_url(self):
        next = self.get_argument("next", '')
        if not next:
            next = self.request.headers.get('Referer')
        else:
            if next.startswith(options.login_url):
                next = '/index'
        return next if next is not None else '/index'

    def get_current_user(self, info=True):
        uid = self.get_secure_cookie("uid")
        if not uid:
            return None
        if info:
            user = User()
            user_info = user.getItem(uid)
            user_info['avatar'] = '/avatar/'+user_info['avatar']
            return user_info
        else:
            return uid

    def prepare(self):
        self._prepare_context()
        self._remove_slash()

    def _remove_slash(self):
        if self.request.method == "GET":
            if _remove_slash_re.match(self.request.path):
                # remove trail slash in path
                uri = self.request.path.rstrip("/")
                if self.request.query:
                    uri += "?" + self.request.query
                self.redirect(uri)

    def _prepare_context(self):
        self._context = _Context()
        #self._context.css = ['base.css', ]
        #self._context.js = ['base.js', ]
        self._context.title = options.title
        self._context.domain_name = options.domain_name
        #self._context.keywords = options.keywords
        #self._context.description = options.description
        #self._context.project_name = options.sitename
        #self._context.project_slogan = options.project_slogan
        #self._context.current_project = None
        #self._context.current_logo = options.logo
        self._context.options = options
        user_info = self.get_current_user()
        if user_info:
            self._context.user_info = self.get_current_user()
        else:
            self._context.user_info = {'id': ''}


    def get_error_html(self, status_code, **kwargs):
        """Override to implement custom error pages.
        It will send email notification to admins if debug is off when internal
        server error happening.
        """
        code = status_code
        message = httplib.responses[status_code]
        try:
            # add stack trace information
            exception = "%s\n\n%s" % (kwargs["exception"], traceback.format_exc())

            if options.debug:
                template = "%s_debug.html" % code
            else:
                template = "%s.html" % code

                ## comment send email for ec2 smtp limit
                if code == 500:
                    fr = options.email_from
                    to = options.admins

                    subject = "[%s]Internal Server Error" % options.sitename
                    body = self.render_string("500_email.html",
                                          code=code,
                                          message=message,
                                          exception=exception)
                elif code==404:
                    return self.send_error(404)

            return self.render_string(template,
                                      code=code,
                                      message=message,
                                      exception=exception)
        except Exception:
            return super(BaseHandler, self).get_error_html(status_code, **kwargs)

    def render_404(self):
        return self.send_error(404)

    #生成session token
    def saveToken(self):
        self.set_cookie('form_token', uuid.uuid1(), expires=60)
    #销毁session token
    def destroyToken(self):
        self.clear_cookie('form_token')
    #验证session token
    def verifyToken(self, val):
        return True if val==self.getToken else False
    #获取session token
    def getToken(self):
        return self.get_cookie('form_token')

EXECUTOR = ThreadPoolExecutor(max_workers=cpu_count())
def unblock(f):
    @asynchronous
    @wraps(f)
    def wrapper(*args, **kwargs):
        self = args[0]

        def callback(future):
            #self.write(future.result())
            #self.finish()
            pass

        EXECUTOR.submit(
            partial(f, *args, **kwargs)
        ).add_done_callback(
            lambda future: IOLoop.instance().add_callback(
                partial(callback, future)))
    return wrapper


class _Context(dict):
    def __setattr__(self, key, value):
        self[key] = value

    def __str__(self):
        return str(self)

    def __iter__(self):
        return iter(self.items())

    def __getattr__(self, key):
        if key in self:
            return self[key]
        elif options.debug:
            raise TemplateContextError("'%s' does not exist in context" % key)
        else:
            return ""

    def __hasattr__(self, key):
        if key in self:
            return True
        else:
            return False

class ErrorHandler(BaseHandler):
    def prepare(self):
        super(ErrorHandler, self).prepare()
        raise HTTPError(404)

def userAuthenticated(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        print 'i ama here----------2222'
        if not self.get_secure_cookie('uid'):
            if self.get_secure_cookie('token') and self.get_secure_cookie('token_time'):
                if self.verifyIsRemember(self, self.get_secure_cookie('token'), self.get_secure_cookie('token_time')):
                    return
            self.set_cookie("next", self.request.path)
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                print 'i ama here----------'
                self.set_header('Content-Type', 'application/json; charset=UTF-8')
                self.write(json.dumps({'code': 'error', 'msg': ErrorMessage.error_message['041']}))
                return
            if self.request.method in ("GET", "HEAD"):
                url = options.login_url
                if "?" not in url:
                    if urlparse.urlsplit(url).scheme:
                        next_url = self.request.full_url()
                    else:
                        next_url = self.request.uri
                    url += "?" + urllib.urlencode(dict(next=next_url))
                self.redirect(url)
                return
            raise HTTPError(403)
        return method(self, *args, **kwargs)
    return wrapper

#判断记住密码
def verifyIsRemember(self, token, token_time):
    fp = self.get_argument('fp', '')
    ec = MyCrypt(options.login_key)
    token = eval(ec.decrypt(token))
    token_time = ec.decrypt(token_time)
    ip = self.request.remote_ip
    if (token.has_key('fp') and token['fp']==fp) and (token.has_key('date') and token['date']==token_time) and (token.has_key('ip') and token['ip']==ip):
        if token.has_key('salt') and token.has_key('uid'):
            #通过uid查询salt是否相等
            user = User()
            info = user.queryOne([('uid', token['uid'])], ['salt'])
            if token['salt']==info['salt']:
                self.set_secure_cookie("uid", str(info.id),
                                   #domain=options.cookie_domain,
                                   #httponly=True,
                                   #secure=True,
                                   #expires_days=None,
                                   expires=options.remember_time_out+token_time)
                return True
    return False

def sync_loop_call(delta=60 * 1000):
  """
  Wait for func down then process add_timeout
  """
  def wrap_loop(func):
      @wraps(func)
      @gen.coroutine
      def wrap_func(*args, **kwargs):
          options.logger.info("function %r start at %d" %
                              (func.__name__, int(time.time())))
          try:
              yield func(*args, **kwargs)
          except Exception, e:
              options.logger.error("function %r error: %s" %
                                   (func.__name__, e))
          options.logger.info("function %r end at %d" %
                              (func.__name__, int(time.time())))
          IOLoop.instance().add_timeout(
              datetime.timedelta(milliseconds=delta),
              wrap_func)
      return wrap_func
  return wrap_loop

_remove_slash_re = re.compile(".+/$")