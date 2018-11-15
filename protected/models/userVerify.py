# -*- coding: utf8 -*-
from protected.models.FrontBaseModel import FrontBaseModel
import protected.libs.utils as utiles
from protected.libs.exceptions import ArgumentError, BaseError
import sys, time, datetime
from protected.conf.debug import logger
class UserVerify(FrontBaseModel):
    def __init__(self):
        self._table = 'user_verify'
        self.setPK('uid')
        self._table_columns = ['uid', 'token', 'verify_expire_time']
        self._table_columns_rule = {'uid': ['required'], 'token': ['required'], 'verify_expire_time': ['required']}
        super(UserVerify, self).__init__()

    def saveToken(self, uid, token):
        if (not uid) or (not token):
            return None
        #查询是否插入成功
        tmp = self.queryOne([('uid', uid)], self._table_columns)
        now = datetime.datetime.now()
        expire = utiles.futureDateToTimestamp(now=now, s=60*60*3, timestamp=False)

        if tmp:
            #判断失效时间
            if utiles.formateDateToTimestamp(tmp['verify_expire_time']) < int(time.mktime(now.timetuple())):
                res = self.updateInfo(filterString=[('token', token), ('verify_expire_time', expire)], where=[('uid', uid)])
                if res>0:
                    return True
                else:
                    return False
            return tmp
        else:
            try:
                tmp = self.saveOne({'uid': uid, 'token': token, 'verify_expire_time': expire})
                return True
            except Exception, e:
                return False


    def getVerifyInfo(self, uid):
        if not uid:
            return None
        return self.queryOne([('uid', uid)], self._table_columns)