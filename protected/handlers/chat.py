# -*- coding: utf-8 -*-
import logging
from tornado import gen, web
from tornado import ioloop
import tornado.escape
from handler import BaseHandler
import json, os, uuid, signal, functools, time
import protected.extensions.chat.redis.redis_backend as redis_backend
from protected.libs.utils import timestampToDate
from protected.extensions.chat.multicast.multicast_processor import multicast_sender
from protected.models.user import User
from protected.libs.const import ErrorMessage, SuccessMessage
from tornado.web import RequestHandler

node_name = str(uuid.uuid4())

# def handler_signal(signum):
#     # if process receive SIGNINT/SITTERM/SIGQUIT
#     # stop the server
#     if signum == 2 or signum == 3 or signum ==15:
#         logging.error("Receive signal: %s" % signum)
#         logging.error("Server quit.")
#         server_stop()
#     elif signum == 14:  # ignore SIGALARM
#         pass
#
# def server_stop():
#     '''
#     停止服务器并做一些清理工作
#     '''
#     ioloop.IOLoop.instance().stop()
#     redis_backend.SignalHandlerManager.on_server_exit()

def get_node_id(node_id):
    pid = os.getpid()
    return node_id + ":" + str(pid)

# signal.signal(signal.SIGTERM, handler_signal)
# signal.signal(signal.SIGINT, handler_signal)
# signal.signal(signal.SIGQUIT, handler_signal)
# signal.signal(signal.SIGALRM, handler_signal)

# local_node_id = get_node_id(node_name)
# multicast_sender = functools.partial(multicast_sender, local_node_id=local_node_id)

def get_node_id(node_id):
    pid = os.getpid()
    return node_id + ":" + str(pid)

def get_key(from_uid, to_uid):
    min = from_uid
    max = to_uid
    if min>max:
        max = from_uid
        min = to_uid
    return str(min)+"_"+str(max)


class MessageMixin(object):
    @gen.coroutine
    def wait_for_messages(self, callback, room_id, tab_index, cursor=None):
        if cursor:
            index = 0
            msg_cache = yield gen.Task(redis_backend.MessageCacheManager.get_msg_for_room_id, room_id)
            for i in xrange(len(msg_cache)):
                index = len(msg_cache) - i - 1
                if msg_cache[index]["id"] == cursor:
                    break

            recent = msg_cache[index + 1:]
            if recent:
                temp_recent = {'messages': recent}
                try:
                    callback(temp_recent)
                except Exception, e:
                    logging.error("Error in waiter callback", exc_info=True)
                    logging.exception(e)

        redis_backend.WaiterManager.add_waiter(callback, room_id, tab_index)

    def cancel_wait(self, room_id, tab_index):
        redis_backend.WaiterManager.remove_waiter_by_tabindex(room_id, tab_index)

    @gen.coroutine
    def new_messages(self, messages, room_id):
        room_waiters = redis_backend.WaiterManager.get_waiters_for_room_id(room_id)
        msg_list = {'messages': messages}
        for callback_item in room_waiters:
            try:
                callback_item.values()[0](msg_list)
            except Exception, e:
                logging.error("Error in waiter callback", exc_info=True)
                logging.exception(e)

        yield gen.Task(redis_backend.MessageCacheManager.add_msg_cache, messages, room_id)

        # send messages to multicast channel
        #multicast_sender(messages, "message")

class MessagesNewHandler(BaseHandler, MessageMixin):
    @web.asynchronous
    def post(self):
        to_user_id = self.get_argument("to_user_id")
        self_user_info = self.get_current_user(info=True)

        if not self_user_info:
            self.finish({"status": "logout"})
            return

        room_id = get_key(self_user_info['id'], to_user_id)
        body = self.get_argument("body")

        msg_id = str(uuid.uuid4())
        message = {
            "id": msg_id,
            "from": self_user_info['id'],
            "to_user_id": to_user_id,
            "user_name": self_user_info['user_name'],
            "body": body,
            "room_id": room_id,
            "time": timestampToDate(time.time()),
            "status": 'success',
        }
        message["html"] = tornado.escape.to_basestring(self.render_string("chat/message.html", message=message))
        self.write(message)
        self.finish()
        self.new_messages([message], room_id)

        #记录最近一次与谁聊天
        # if to_user_id!=self_user_info['id']:
        #     yield gen.Task(redis_backend.UserManager.set_history_user, self_user_info['id'], to_user_id)

        return

class MessagesUpdatesHandler(RequestHandler, MessageMixin):
    @web.asynchronous
    def post(self):
        to_user_id = self.get_argument("to_user_id", None)
        self.tab_index = self.get_argument("tab_index", 0)

        self.user = self.get_secure_cookie("uid")
        if (not to_user_id) or (not self.user):
            return
        self.room_id = get_key(self.user, to_user_id)

        if not redis_backend.UserManager.is_user_online(self.user):
            redis_backend.UserManager.user_add_to_list(self.room_id, self.user)

        cursor = self.get_argument("cursor", None)

        self.wait_for_messages(self.on_new_messages, self.room_id, self.tab_index, cursor)


    def on_new_messages(self, messages):
        if self.request.connection.stream.closed():
            return
        self.finish(messages)
        #返回了消息之后才清理的会话，这时候客户端拿到了返回值，就可以再发一次update的请求
        redis_backend.WaiterManager.empty_waiter(self.room_id)
        return

    def on_connection_close(self):
        #删除tab下得聊天实例
        self.cancel_wait(self.room_id, self.tab_index)

'''
删除聊天人和聊天内容
'''
class MessagesCloseHandler(RequestHandler, MessageMixin):
    @gen.coroutine
    def post(self):
        uid = self.get_secure_cookie("uid")
        to_user_id = self.get_argument("to_user_id", None)
        tab_index = self.get_argument('tab_index', None)
        if (not to_user_id) or (not uid):
            self.finish({'code': 'error'})
            return
        room_id = get_key(uid, to_user_id)
        redis_backend.WaiterManager.remove_waiter_by_tabindex(room_id, tab_index)
        yield gen.Task(redis_backend.MessageCacheManager.del_msg_by_room_id, room_id)
        self.finish({'code': 'success'})
        return

'''
显示默认
'''
class MainHandler(RequestHandler):
    @gen.coroutine
    def post(self):
        uid = self.get_secure_cookie("uid")
        if not uid:
            self.finish({'user_list': [], 'default_user': 0})
            return
        self.set_cookie('from_uid', uid)
        page = self.get_argument('page', 1)
        #获取已经对话过的列表
        res = yield gen.Task(redis_backend.UserManager.get_user_from_list, uid, page=page)
        user_list = {}
        for item in res:
            item = json.loads(item)
            user_list[item['id']] = item
        #获取最近的聊天用户
        to_user_id = yield gen.Task(redis_backend.UserManager.get_history_user, uid)
        #给tab赋值
        tab_index = str(uuid.uuid4())
        self.finish({'user_list': user_list, 'default_user': to_user_id if to_user_id else 0, 'tab_index': tab_index})
        return


'''
显示对话内容列表
'''
class ChatContentListHandler(RequestHandler):
    @gen.coroutine
    def post(self):
        uid = self.get_secure_cookie("uid")
        to_user_id = self.get_argument('to_user_id', None)
        room_id = get_key(uid, to_user_id)
        res = yield gen.Task(redis_backend.MessageCacheManager.get_msg_for_room_id, room_id)
        msgs = {}
        idx = 0
        for item in res:
            msgs[idx] = item
            idx += 1
        del res
        self.finish(msgs)
        #删除其他的room_id的对话
        room_id = get_key(uid, to_user_id)
        redis_backend.WaiterManager.remove_other_waiter(room_id)
        return

'''
关闭对话框中的用户显示
'''
class ChatUserCloseHandler(BaseHandler):
    def get_chat_user_info(self, info):
        return {
                    'user_name': info['user_name'],
                    'id': info['id'],
                    'user_email': info['user_email'],
                    'avatar': info['avatar']
                }

    @gen.coroutine
    def post(self):
        to_user_id = self.get_argument('to_user_id', None)
        if not to_user_id:
            self.finish({'code': 'error', 'msg': ErrorMessage.error_message['048']})
            return
        chat_user_info = User.getItem(to_user_id)
        if not chat_user_info:
            self.finish({'code': 'error', 'msg': ErrorMessage.error_message['049']})
            return
        self_user_info = self.get_current_user(info=True)
        chat_user = self.get_chat_user_info(chat_user_info)
        self_user = self.get_chat_user_info(self_user_info)
        room_id = get_key(chat_user_info['id'], self_user_info['id'])
        res = yield gen.Task(redis_backend.UserManager.del_chat_user, self_user, chat_user, room_id)
        self.finish({'code': 'success', 'msg': res})
        return


handlers = [
    (r"/chat/index", MainHandler),
    (r"/chat/msglist", ChatContentListHandler),
    (r"/chat/new", MessagesNewHandler),
    (r"/chat/updates", MessagesUpdatesHandler),
    (r"/chat/closeuser", MessagesCloseHandler),
]