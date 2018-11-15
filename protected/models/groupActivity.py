# -*- coding: utf8 -*-
from protected.models.FrontBaseModel import FrontBaseModel
import protected.libs.utils as utiles
from protected.libs.exceptions import ArgumentError, BaseError
import sys

class GroupActivity(FrontBaseModel):

    NORMAL_STATUS = 1
    DELETE_STATUS = 0

    def __init__(self):
        self._table = 'group_activity'
        self.setPK('id')
        self._table_columns = [ 'id',
                                'name',
                                'create_time',
                                'delete_time',
                                'update_time',
                                'content',
                                'group_leader',
                                'limit_number',
                                'status',
                                'icon',
                                'photo_albums',
                                'dead_time',
                                'group_id'
                                ]
        self._table_columns_rule = {    'name':['required', {'length':'<=150'}],
                                        'create_time':['datetime'],
                                        'update_time':['datetime'],
                                        'dead_time':['datetime'],
                                        'delete_time':['datetime'],
                                        'group_leader':['required'],
                                        'limit_number':['number'],
                                        'group_id':['required']
                                    }
        self._base_photo_url = '/uploads/activities/'
        super(GroupActivity, self).__init__()

    def new(self, item):
        obj = self.initialize(item)
        if obj:
            return self.save()
        return None

    @property
    def photoAlbums(self):
        return self._base_photo_url

    #获取列表
    def getGroupActivityList(self, page_num):
        return self.queryMany(filterString=[('status', self.NORMAL_STATUS)], fields=self._table_columns, orderBy=[('id', 'DESC')], limit=self._page_size, pageNo=page_num)

    #通过活动id获取活动列表
    def getGroupActivityListById(self, id, page=None, limit=None):
        if not id:
            return None
        filterString = [('status', self.NORMAL_STATUS)]
        res = {}
        if isinstance(id, int):
            filterString.append(('id', id))
            item_info = self.queryOne(filterString=filterString)
            res[item_info['id']] = item_info
        elif isinstance(id, set):
            filterString.append(('id', ('in', id)))
            filterString.append(('dead_time', ('>', utiles.timestampToDate(None))))
            act_list = self.queryMany(filterString=filterString, orderBy=[('id', 'DESC')], limit=limit, pageNo=page)
            res = {}
            for item in act_list:
                res[item['id']] = item
        return res