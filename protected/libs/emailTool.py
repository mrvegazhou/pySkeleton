# -*- coding: utf-8 -*-
import os, re, functools, csv
from smtplib import SMTP, SMTP_SSL
from tornado import gen
from multiprocessing import cpu_count
try:
    from concurrent.futures import ThreadPoolExecutor
except:
    from futures import ThreadPoolExecutor

class JumpEmail:
    EMAIL_URL = {
        '163.com': 'mail.163.com',
        'vip.163.com': 'vip.163.com',
        '126.com': 'mail.126.com',
        'qq.com': 'mail.qq.com',
        'vip.qq.com': 'mail.qq.com',
        'foxmail.com': 'mail.qq.com',
        'gmail.com': 'mail.google.com',
        'sohu.com': 'mail.sohu.com',
        'tom.com': 'mail.tom.com',
        'vip.sina.com': 'vip.sina.com',
        'sina.com.cn': 'mail.sina.com.cn',
        'sina.com': 'mail.sina.com.cn',
        'yahoo.com.cn': 'mail.cn.yahoo.com',
        'yahoo.cn': 'mail.cn.yahoo.com',
        'yeah.net': 'www.yeah.net',
        '21cn.com': 'mail.21cn.com',
        'hotmail.com': 'www.hotmail.com',
        'sogou.com': 'mail.sogou.com',
        '188.com': 'www.188.com',
        '139.com': 'mail.10086.cn',
        '189.cn': 'webmail15.189.cn/webmail',
        'wo.com.cn': 'mail.wo.com.cn/smsmail'
    }
    @classmethod
    def goEmailUrl(cls, email):
        if not re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
            return False
        temp = email.split('@')
        e = temp[1].lower()
        if e in cls.EMAIL_URL.keys():
            return cls.EMAIL_URL[e]
        return None

class SendEmail:
    def initialized_async(func):
        @functools.wraps(func)
        @gen.coroutine
        def wrapper(self, *args, **kwargs):
            if self._busy:
                self._smtp = yield self._busy
                self._busy = None

            result = yield func(self, *args, **kwargs)
            raise gen.Return(result)

        return wrapper

    def __init__(self, host='', port=25, use_ssl=False):
        self._pool = ThreadPoolExecutor(cpu_count or 1)
        self._busy = self._pool.submit(self._initialize, host, port, use_ssl)

    def _initialize(self, host='', port=25, use_ssl=False):
        return SMTP_SSL(host, port) if use_ssl else SMTP(host, port)

    @initialized_async
    def login(self, user, password):
        return self._pool.submit(self._smtp.login, user, password)

    @initialized_async
    def sendmail(self, from_addr, to_addrs, msg):
        return self._pool.submit(self._smtp.sendmail, from_addr, to_addrs, msg.as_string())

    @initialized_async
    def quit(self):
        return self._pool.submit(self._smtp.quit)

class CheckEmailAddressList(object):
    @classmethod
    def getEmail(cls, filename):
        array = []
        f = open(filename, 'r')
        ext = os.path.splitext(filename)[-1]
        if ext=='.vcf':
            for i in f:
                if "EMAIL;" in i:
                    str = i.strip("\n")
                    array.append(str.split(':')[1])
        elif ext=='.csv':
            f = csv.reader(open(filename))
            for item in f:
                array.append(item[2])
        f.close()
        return array

if __name__ == "__main__":
    pass