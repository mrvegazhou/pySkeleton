# -*- coding: utf8 -*-
from protected.models.FrontBaseModel import FrontBaseModel
from protected.models.groupActivity import GroupActivity
from protected.models.user import User
from protected.libs.exceptions import ArgumentError, BaseError
import protected.libs.utils as utiles
from tornado import gen
from tornado.web import asynchronous
import os

class UserActivity(FrontBaseModel):

    user_activity_status_normal = 1
    user_activity_status_stop = 0


    def __init__(self):
        self._table = 'user_activity'
        self.setPK('id')
        self._table_columns = [ 'id',
                                'uid',
                                'activity_id',
                                'create_time',
                                'status'
                            ]
        self._table_columns_rule = {'uid':['required'], 'activity_id':['required'], 'create_time':['required'], 'status':['required'] }
        self._table_columns_autoload = {'create_time': utiles.dateToTimestamp(), 'status': 1}
        super(UserActivity, self).__init__()

    def new(self, item):
        obj = self.initialize(item)
        if obj:
            return self.save()
        return None

    '''
    获取用户的计划活动
    '''
    def getActivities(self, uid, page=1, limit=15):
        if not uid:
            return None
        user_act_list = self.queryMany(filterString=[('uid', uid), ('status', 1)], limit=limit, pageNo=page)
        ids = []
        for item in user_act_list:
            ids.append(item['activity_id'])

        ids = set(ids)
        act = GroupActivity()
        act_list = act.getGroupActivityListById(ids)
        if not act_list:
            return []

        res = []
        #获取组织活动的发起人
        group_leader_ids = []
        for item in user_act_list:
            if act_list.has_key(item['activity_id']):
                group_leader_ids.append(act_list[item['activity_id']]['group_leader'])

        user = User()
        user_list = user.getUsersByUids(group_leader_ids)

        for item in user_act_list:
            if act_list.has_key(item['activity_id']):
                item['activity_info'] = act_list[item['activity_id']]
                item['activity_info']['create_time'] = item['activity_info']['create_time'].strftime("%Y/%m/%d %H:%M:%S")
                item['activity_info']['dead_time'] = item['activity_info']['dead_time'].strftime("%Y/%m/%d %H:%M:%S")
                item['activity_info']['group_leader_name'] = user_list[act_list[item['activity_id']]['group_leader']]['user_name']
                res.append(item)
        return res

    '''
    获取用户活动计划的总数
    '''
    def getActivityTotalByUid(self, uid):
        if not uid:
            return None
        count = self.getCount(filterString=[('uid', uid), ('status', 1)])
        return count