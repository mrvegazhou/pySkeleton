# -*- coding: utf8 -*-
from protected.models.FrontBaseModel import FrontBaseModel
from protected.libs.exceptions import ArgumentError, BaseError
import sys
"""
https://github.com/daydayfree/diggit/ 参考model
"""
class User(FrontBaseModel):
    def __init__(self):
        self._table = 'user'
        self.setPK('id')
        self._table_columns = [ 'id',
                                'user_name',
                                'pass_word',
                                'user_email',
                                'user_ip',
                                'salt',
                                'area_id',
                                'create_time',
                                'login_time',
                                'gender',
                                'is_verify',
                                'avatar'
                            ]
        self._table_columns_rule = {'pass_word':['required'], 'user_email':['required', 'email'], 'area_id':['required'], 'gender':['required'] }
        super(User, self).__init__()

    def new(self, item):
        obj = self.initialize(item)
        if obj:
            return self.save()
        return None

    #登录
    def login(self, user_email):
        info = self.queryOne([('user_email', user_email)], self._table_columns)
        if info:
            return info
        return False

    #判断用户名和邮箱是否唯一 包括not_id参数就是排除自己
    def checkUserOrEmail(self, val, type='', not_id=''):
        if not val:
            raise ArgumentError("参数不能为空")
        conds = []
        if type=='email':
            condition = ('user_email', val)
        else:
            condition = ('user_name', val)
        conds.append(condition)
        if not_id:
            conds.append(('id', ('<>', not_id)))
        res = self.queryOne(conds, self._table_columns)
        if res:
            return True
        return False

    #通过uid集合获取用户列表
    def getUsersByUids(self, uids):
        if not uids:
            return {}
        uids = set(uids)
        list = self.queryMany(filterString=[('id', ('in', uids))])
        res = {}
        for item in list:
            res[item['id']] = item
        del list
        return res

    #通过用户属性获取用户信息
    def getUserInfoByAttr(self, key, val):
        if not key:
            return None
        if not val:
            val = ''
        return self.queryOne([('status', 1), (key, val)], self._table_columns)