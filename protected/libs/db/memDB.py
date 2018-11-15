# -*- coding: utf-8 -*-
import redis
import memcache
from tornado.options import options

def singleton(cls, *args, **kw):
    instances = {}
    def _singleton():
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]
    return _singleton

@singleton
class RedisDB(object):
    def __init__(self):
        self.r = redis.StrictRedis(host=options.redis["host"], port=options.redis["port"], db=options.redis["db"])

    def getRedis(self):
        return self.r

    def set(self, key, val):
        return self.r.set(key, val)

    def get(self, key):
        return self.r.get(key)

    #批量set
    def mSet(self, n, list):
        for i in range(n):
            self.r.mset(list[i])
    #批量get
    def mGet(self, list):
        post_list = []
        for i in range(10):
            post = self.r.mget(','.join(list))
            if post:
                post_list.append(post)
        return post_list

    #hashed类型的操作
    def hSet(self, key, objKey, objVal):
        self.r.hset(key, objKey, objVal)
    def hGet(self, key, objKey):
        self.r.hget(key, objKey)
    def hGetAll(self, key):
        self.r.hgetall(key)

    #hmset批量操作
    def hMSet(self, key, dicts):
         self.r.hmset(key, dicts)
    def hMGet(self, key, objs):
        return self.r.hmget(key, *tuple([k for k in objs]))

    #lists类型的操作  对应的还有rpush，lpop，rpop
    def lList(self, key, val):
        self.r.lpush(key, val)
    def lRange(self, key, begin=0, end=-1):
        return self.r.lrange(key, begin, end)

    #sets类型的操作
    '''
    #4、sets类型的操作
    print u'====sets操作：'
    cache.sadd('blog:category:python', '001')
    cache.sadd('blog:category:python', '002')
    #cache.sadd('blog:category:python', '001', '002')

    print cache.smembers('blog:category:python')
    cache.srem('blog:category:python', '001')
    print cache.smembers('blog:category:python')
    '''

@singleton
class MemDB(object):
    def __init__(self):
        self.mc = memcache.Client(options.memcache["host"], debug=0)
    #set
    def memSet(self, key, val, expire=None):
        if expire:
            self.mc.set(key, val, time=expire)
        else:
            self.mc.set(key, val)
    #get
    def memGet(self, key):
        return self.mc.get(key)

    #delete
    def memDel(self, key, timeout=None):
        if not timeout:
            return self.mc.delete(key, timeout)
        return self.mc.delete(key)
