# -*- coding: utf-8 -*-
from tornado.web import UIModule
import time

class Entry(UIModule):
    def render(self):
        return self.render_string("modules/websites_index.html")

#聊天窗口
class Chat(UIModule):
    def render(self):
        return self.render_string("modules/chat.html")

'''
通用评论模块
'''
class Comments(UIModule):
    def render(self, comments, uid, id, is_need_captcha=None):
        if (not type) or (not uid) or (not id):
            return self.render_string("modules/404.html")
        self.handler._context.is_need_captcha = is_need_captcha
        self.handler._context.r = time.time()

        return self.render_string("modules/comments.html")