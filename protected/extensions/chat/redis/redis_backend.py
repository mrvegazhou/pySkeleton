#!/usr/bin/python
# -*- coding: utf8 -*-
import time, tornadoredis, json
from tornado import gen, web
from tornado.concurrent import Future

room_prefix = "room:"
chat_queue_prefix = "chat:queue:"
userlist_prefix = "userlist:"
chat_history_user = "chat:last:"


def connect_redis():
    c = tornadoredis.Client()
    c.connect()
    return c

def connect_redis_pipeline():
    c = tornadoredis.Client()
    #pipe = c.pipeline()
    return pipe

try:
    c = connect_redis()
    #c_pipe = connect_redis_pipeline()
except Exception, e:
    raise

@gen.coroutine
def key_exists(key):
    exists = yield c.exists(key)
    if exists:
        raise gen.Return(True)
    else:
        raise gen.Return(False)

@gen.coroutine
def h_key_exists(name, key):
    exists = yield c.exists(name, key)
    if exists:
        raise gen.Return(True)
    else:
        raise gen.Return(False)

class UserManager(object):
    def __init__(self):
        pass

    @staticmethod
    @gen.coroutine
    def is_user_online(user):
        online = yield gen.Task(c.hget, user, "offline")
        if online == None:
            raise gen.Return(False)
        else:
            raise gen.Return(True)

    @staticmethod
    @gen.coroutine
    def set_user_offline(user):
        yield gen.Task(c.hdel, user, "offline")


    @staticmethod
    @gen.coroutine
    def user_del_from_list(user, chat_user):
        userlist_set = userlist_prefix + room_prefix + str(user)
        yield gen.Task(c.srem, userlist_set, chat_user)
        raise gen.Return(True)

    @staticmethod
    @gen.coroutine
    def get_user_from_list(user, page=1, size=30):
        userlist_set = userlist_prefix + room_prefix + str(user)
        offset = (page-1)*size
        res = yield gen.Task(c.lrange, userlist_set, offset, size)
        raise gen.Return(res)

    @staticmethod
    @gen.coroutine
    def user_add_to_list(user, chat_user):
        if user!=chat_user['id']:
            userlist_set = userlist_prefix + room_prefix + str(user)
            res = yield gen.Task(c.lpush, userlist_set, json.dumps(chat_user))
            raise gen.Return(res)

    @staticmethod
    @gen.coroutine
    def set_history_user(user, chat_user):
        yield gen.Task(c.set, chat_history_user+str(user), chat_user)
        raise gen.Return(True)

    @staticmethod
    @gen.coroutine
    def get_history_user(user):
        to_user_id = yield gen.Task(c.get, chat_history_user+str(user))
        raise gen.Return(to_user_id)

    @staticmethod
    @gen.coroutine
    def del_chat_user(self_chat_user, chat_user, room_id):
        res = yield gen.Task(c.lrem, userlist_prefix + room_prefix + str(self_chat_user['id']), json.dumps(chat_user))
        #判断两个用户都是否存在，不存在则删除聊天记录
        user_list = yield gen.Task(c.lrange, userlist_prefix + room_prefix + str(chat_user['id']), 0, -1)
        is_exist = False
        for item in user_list:
            if json.dumps(self_chat_user)==item:
                is_exist = True
        if not is_exist:
            MessageCacheManager.del_msg_by_room_id(room_id)
        raise gen.Return(res)


# settings for default chat room
default_room_id = 1

room_list = dict()

class WaiterManager(object):
    def __init__(self):
        pass

    @staticmethod
    def add_waiter(callback, room_id, tab_index):
        if room_id:
            if not (room_id in room_list):
                room_list[room_id] = []
            room_list[room_id].append({tab_index: callback})

    @staticmethod
    def get_waiters_for_room_id(room_id):
        if not (room_id in room_list.keys()):
            room_list[room_id] = set()
        return room_list[room_id]

    @staticmethod
    def empty_waiter(room_id):
        """
        clear all the suspended callback(client) for the room
        """
        room_list[room_id] = []

    @staticmethod
    def remove_waiter(room_id):
        """
        delete a suspended callback(client) for a room
        """
        try:

            room_list.pop(room_id)
        except Exception, e:
            pass

    @staticmethod
    def remove_waiter_by_tabindex(room_id, tab_index):
        try:
            for room in room_list[room_id]:
                if room.has_key(tab_index):
                    room_list.remove(room)
            if len(room_list[room_id])==0:
                WaiterManager.remove_waiter(room_id)
        except Exception, e:
            pass

    @staticmethod
    def remove_other_waiter(room_id):
        for k, v in room_list.items():
            if room_id!=k:
                del room_list[k]

    @staticmethod
    def remove_all_waiter():
        room_list.clear()

class ChatroomManager(object):
    def __init__(self):
        pass

    @staticmethod
    def add_local_chat_room(room_id):
        room_custom = dict(
            room_id = room_id,
            room_waiter_list = dict()
        )
        room_list.append(room_custom)
        return True

    @staticmethod
    @gen.coroutine
    def check_room_id(room_id):
        room_key = room_prefix + str(room_id)
        tmp = yield key_exists(room_key)
        if tmp:
            raise gen.Return(True)
        else:
            raise gen.Return(False)


class MessageCacheManager(object):
    def __init__(self):
        pass

    @staticmethod
    @gen.coroutine
    def get_room_cache_size(room_id):
        room_key = room_prefix + str(room_id)
        temp = yield key_exists(room_key)
        if temp:
            room_cache_size = yield gen.Task(c.hget, room_key, "room_cache_size")
            if room_cache_size:
                raise gen.Return(room_cache_size)
        raise gen.Return(False)

    @staticmethod
    def get_max_length():
        return 1000

    @staticmethod
    @gen.coroutine
    def add_msg_cache(messages, room_id):
        chat_queue_name = chat_queue_prefix + str(room_id)
        chat_msg_len = yield gen.Task(c.llen, chat_queue_name)
        if chat_msg_len >= MessageCacheManager.get_max_length():
            yield c.lpop(chat_queue_name)
        if isinstance(messages, list):
            for item in messages:
                msg = json.dumps({'msg': item['body'], 'uid': item['from'], 'time': item['time'], 'name': item['user_name'], 'id': item['id']})
                yield gen.Task(c.rpush, chat_queue_name, msg)
            del item, msg
        elif isinstance(messages, str):
            msg = json.dumps({'msg': messages['body'], 'uid': messages['from'], 'time': messages['time'], 'name': messages['user_name'], 'id': messages['id']})
            yield gen.Task(c.rpush, chat_queue_name, msg)
            del msg
        raise gen.Return(True)

    @staticmethod
    @gen.coroutine
    def get_msg_for_room_id(room_id):
        chat_queue_name = chat_queue_prefix + str(room_id)
        queue_len = yield gen.Task(c.llen, chat_queue_name)
        if not queue_len:
            raise gen.Return(list())
        msg_list = yield gen.Task(c.lrange, chat_queue_name, 0, -1)
        lists = []
        for msg in msg_list:
            lists.append(json.loads(msg))
        del msg
        raise gen.Return(lists)

    @staticmethod
    @gen.coroutine
    def del_msg_by_room_id(room_id):
        chat_queue_name = chat_queue_prefix + str(room_id)
        res = yield gen.Task(c.delete, chat_queue_name)
        raise gen.Return(res)

class SignalHandlerManager(object):
    def __init__(self):
        pass

    @staticmethod
    @gen.coroutine
    def on_server_exit():
        room_userlist_all = userlist_prefix + room_prefix + "[0-9]*"
        keys = yield c.keys(room_userlist_all)
        for key in keys:
            users = c.smembers(key)
            for user in users:
                yield c.delete(user)
            yield c.delete(key)

    @staticmethod
    @gen.coroutine
    def on_single_chat_server_exit(key):
        yield c.delete(key)