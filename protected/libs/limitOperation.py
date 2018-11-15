# -*- coding: utf-8 -*-
'''
此类为限制操作的文件，包括验证码的限制
'''
import time
from tornado import gen, web
from tornado.ioloop import IOLoop
from protected.libs.cache import cache
from protected.libs.const import ErrorMessage, SuccessMessage

def limitCaptcha(uid, key, max_count=4, period=500):
    uid = str(uid)
    key = key+'_captcha_'
    now_time = time.time()
    is_frequency = 0
    is_need_captcha = 0
    cache_count = 0
    cache_time = now_time

    if (not cache.get(key+'_count_'+uid)) or (not cache.get(key+'_time_'+uid)):
        is_need_captcha = 0
        cache.set(key+'_is_need_captcha_'+uid, is_need_captcha)

        cache.set(key+'_count_'+uid, 1)
        cache.set(key+'_time_'+uid, now_time)
        cache_count = 1

    else:
        cache_count = cache.get(key+'_count_'+uid)
        cache_time = cache.get(key+'_time_'+uid)

        #小于5秒 次数+1
        if (now_time-float(cache_time))<=period:
            cache.set(key+'_count_'+uid, int(cache_count)+1)

        #等于4的时候显示验证码
        if cache.get(key+'_count_'+uid)==max_count:
            is_need_captcha = 1
            cache.set(key+'_is_need_captcha_'+uid, 0)

        #大于4的时候对验证码进行验证
        if cache.get(key+'_count_'+uid)>max_count:
            is_need_captcha = 1
            cache.set(key+'_is_need_captcha_'+uid, 1)

    #操作太频繁
    if cache.get(key+'_count_'+uid)>8 and (now_time-float(cache.get(key+'_time_'+uid)))<=period:
        is_frequency = 1

    return is_need_captcha, cache.get(key+'_count_'+uid), cache_time, is_frequency, cache.get(key+'_is_need_captcha_'+uid)

#验证是否需要验证码
def checkNeedCaptcha(key, uid):
    uid = str(uid)
    key = key+'_captcha_'
    if not cache.get(key+'_is_need_captcha_'+uid):
        return False
    elif cache.get(key+'_is_need_captcha_'+uid)==1:
        return True

#清除验证码的判断
def clearNeedCaptcha(key, uid):
    key = key+'_captcha_'
    cache.delete(key+'_count_'+uid)
    cache.delete(key+'_time_'+uid)
    cache.delete(key+'_is_need_captcha_'+uid)
    return

def clearActionNameOperateCache(uid):
    cache.delete(uid+'-'+'feedback-like')  #反馈模块点赞操作频率限制
    cache.delete(uid+'-'+'feedback-reply'+'-'+'d')  #提交回复
    return

'''
操作频率的限制
'''
def rateLimited(action, uid, maxPerSecond=5):
    uid = str(uid)
    action = str(action)
    lastTimeCalled = [0.0 if not cache.get(uid+'-'+action) else cache.get(uid+'-'+action)]
    minInterval = 1.0 / float(maxPerSecond)
    elapsed = time.clock() - lastTimeCalled[0]
    leftToWait = minInterval - elapsed
    if leftToWait>0:
        return False
    cache.set(uid+'-'+action, time.clock())
    return True

'''
如果频繁操作，延迟5分钟请求
'''
def delayPostLimit(action, uid, maxPerSecond):
    uid = str(uid)
    key = uid+'-'+action+'-'+'d'
    key_time = uid+'-'+action+'-'+'t'
    lastTimeCalled = [0.0 if not cache.get(key_time) else cache.get(key_time)]
    minInterval = 1.0 / float(maxPerSecond)
    elapsed = time.time() - lastTimeCalled[0]
    leftToWait = minInterval - elapsed
    if not cache.get(key):
        cache.set(key, 0)
    if leftToWait>0:
        delay = int(cache.get(key)) + 1
        cache.set(key, delay)
    if cache.get(key)>=3 and (time.time()-float(cache.get(key_time))<600):
        cache.set(key, 0)
        return False
    cache.set(key_time, time.time())
    return True


if __name__ == "__main__":
    start = time.clock()
    minInterval = 1.0 / float(0.5)
    time.sleep(0.01)
    elapsed = time.clock() - start
    leftToWait = minInterval - elapsed
    print minInterval