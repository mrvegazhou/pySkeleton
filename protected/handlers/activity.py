# -*- coding: utf-8 -*-
from tornado.web import asynchronous, HTTPError, StaticFileHandler
from tornado import escape
from tornado.options import options
from tornado import locale
from tornado import gen
from tornado.ioloop import IOLoop
from tornado.escape import json_encode
from handler import BaseHandler
from protected.models.user import User
from protected.models.groupActivity import GroupActivity
from protected.models.socialGroup import SocialGroup
from protected.models.sysConfig import SysConfig
from protected.libs.const import ErrorMessage, SuccessMessage
import sys, time, hashlib, re, urlparse, uuid, os, datetime
import protected.libs.utils as utiles

class indexHandler(BaseHandler):
    _handler_template = 'activity/index.html'
    ga = GroupActivity()
    g = SocialGroup()
    def post(self):
        pass

    def get(self, page=1):
        #获取当前用户活动被评论的信息

        page = page if page else 1
        #分页获取所有活动列表信息
        activity_list = self.ga.getGroupActivityList(page)
        res = []
        group_ids = []
        for item in activity_list:
            group_ids.append(item['group_id'])
        #通过组ids获取组列表信息
        group_list = self.g.getSocialGroupsByIds(group_ids)
        for item in activity_list:
            item['from_group_name'] = group_list[item['group_id']]['name']
            if not item['icon']:
                item['icon_width'] = None
                item['icon_height'] = None
            else:
                icon_img = item['icon'].split("_")
                item['icon_width'] = int(icon_img[1])
                item['icon_height'] = int(icon_img[2].split(".")[0])
            res.append(item)
        self._context.activity_list = res
        self.render(self._handler_template)

class infoHandler():
    _handler_template = 'activity/info.html'
    def post(self):

        pass
    def get(self):
        pass

handlers = [
    (r"/activity", indexHandler),
    (r"/activity/page/(\d+)", indexHandler),
    (r"/activity-info/(\d+)", infoHandler),
    (r"/uploads/(.*)", StaticFileHandler, {"path": "uploads/activities"})
]