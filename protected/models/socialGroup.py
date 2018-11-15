# -*- coding: utf8 -*-
from protected.models.FrontBaseModel import FrontBaseModel
from protected.libs.exceptions import ArgumentError, BaseError
import sys

class SocialGroup(FrontBaseModel):
    def __init__(self):
        self._table = 'social_group'
        self.setPK('id')
        self._table_columns = ['id', 'name', 'create_time', 'delete_time', 'update_time', 'description', 'creater', 'limit_number', 'status', 'icon']
        self._table_columns_rule = {    'name':['required', {'length':'<=150'}],
                                        'create_time':['datetime'],
                                        'creater':['required'],
                                        'limit_number':['number']
                                    }
        super(SocialGroup, self).__init__()

    def new(self, item):
        obj = self.initialize(item)
        if obj:
            return self.save()
        return None

    #获取列表
    def getSocialGroupList(self, page_num):
        return self.queryMany(filterString=[], fields=self._table_columns, orderBy=[('id', 'DESC')], limit=self._page_size, pageNo=page_num)

    #通过ids获取组列表
    def getSocialGroupsByIds(self, ids=[]):
        if not ids:
            return {}
        group_list = self.queryMany(filterString=[('id', ('in' ,list(set(ids))))])
        res = {}
        for item in group_list:
            res[item['id']] = item
        return res