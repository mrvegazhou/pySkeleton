# -*- coding: utf8 -*-
from protected.models.FrontBaseModel import FrontBaseModel
import protected.libs.utils as utiles
from protected.libs.exceptions import ArgumentError, BaseError
import sys, time

class FriendEmails(FrontBaseModel):
    def __init__(self):
        self._table = 'friend_emails'
        self.setPK('id')
        self._table_columns = ['id', 'email', 'uid', 'create_time']
        self._table_columns_rule = {'email': ['required', 'email'], 'uid': ['required']}
        super(FriendEmails, self).__init__()

    def saveEmailsByUid(self, uid, list):
        if not list:
            return None
        now = utiles.timestampToDate(time.time())
        tmp_list = []
        for item in list:
            info = self.getEmailByUidAndEmail(uid, item)
            if info:
                continue
            tmp = {'email': item, 'uid': uid, 'create_time': now}
            tmp_list.append(tmp)
        return self.saveMany(tmp_list)

    def getEmailByUidAndEmail(self, uid, email):
        if (not uid) or (not email):
            return None
        return self.queryOne([('uid', uid), ('email', email)], self._table_columns)