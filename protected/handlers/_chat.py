# -*- coding: utf-8 -*-
import logging
import tornado.escape
from tornado.escape import json_decode
import tornado.ioloop
from tornado.concurrent import Future
from tornado import gen
from handler import BaseHandler
import json
import redis
#https://github.com/leporo/tornado-redis
import tornadoredis

db = redis.Redis(host='localhost', port=6379)

class MessageBuffer(object):

    def __init__(self):
        self.chats = dict()

    def get_key(self, from_uid, to_uid):
        min = from_uid
        max = to_uid
        if min>max:
            max = from_uid
            min = to_uid
        return str(min)+"_"+str(max)

    def wait_for_messages(self, key, cursor=None):
        if not (key in self.chats):
            self.chats[key] = []

        result_future = Future()
        if cursor:
            new_count = 0
            for msg in db.lrange(key, 0, -1):
                msg = json_decode(msg)
                if msg["id"] == cursor:
                    break
                new_count += 1
            if new_count:
                result_future.set_result(db.lrange(key, -new_count, -1))
                return result_future

        self.chats[key].append(result_future)

        return result_future

    def cancel_wait(self, key, future):
        if key in self.chats:
            self.chats[key].remove(future)

    def new_messages(self, key, messages):
        if not (key in self.chats):
            self.chats[key] = set()

        for chat in self.chats[key]:
            chat.set_result(messages)

        self.chats = dict()
        for msg in messages:
            db.rpush(key, json.dumps(msg))

global_message_buffer = MessageBuffer()

class MainHandler(BaseHandler):
    def get(self):
        uid = self.get_current_user(info=False)
        to_user_id = self.get_argument('to_user_id', None)
        key = global_message_buffer.get_key(uid, to_user_id)
        messages = [json_decode(m) for m in db.lrange(key, 0, -1)]
        self.render("chat/index.html", messages=messages)


class MessageNewHandler(BaseHandler):
    def post(self):
        uid = self.get_current_user(info=False)
        uid = uid if uid else 12
        to_user_id = self.get_argument('to_user_id', None)
        key = global_message_buffer.get_key(uid, to_user_id)
        message_index = db.llen(key)
        message = {
            "id": str(message_index if message_index else 0),
            "to_user_id": str(to_user_id),
            "body": self.get_argument("body"),
        }
        message["html"] = tornado.escape.to_basestring(self.render_string("chat/message.html", message=message))
        self.write(message)
        global_message_buffer.new_messages(key, [message])


class MessageUpdatesHandler(BaseHandler):
    key = None
    @gen.coroutine
    def post(self):
        uid = self.get_current_user(info=False)
        uid = uid if uid else 12
        to_user_id = self.get_argument('to_user_id', None)
        cursor = self.get_argument("cursor", None)
        self.key = global_message_buffer.get_key(uid, to_user_id)
        # Save the future returned by wait_for_messages so we can cancel
        # it in wait_for_messages
        self.future = global_message_buffer.wait_for_messages(self.key, cursor)
        messages = yield self.future
        if self.request.connection.stream.closed():
            return
        self.write(dict(messages=messages))

    def on_connection_close(self):
        global_message_buffer.cancel_wait(self.key, self.future)




handlers = [
    (r"/chat", MainHandler),
    (r"/chat/new", MessageNewHandler),
    (r"/chat/update", MessageUpdatesHandler),
]