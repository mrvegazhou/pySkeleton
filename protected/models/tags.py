# -*- coding: utf8 -*-
from protected.models.FrontBaseModel import FrontBaseModel
from tornado.options import options
from protected.conf.debug import logger
from protected.libs.exceptions import ArgumentError
import protected.libs.utils as utiles
import sys

class Tags(FrontBaseModel):

    note_type = 1
    types = {note_type: '日记'}

    def __init__(self):
        self._table  = 'tags'
        self.setPK('id')
        self._table_columns = ['id', 'name', 'create_time', 'type', 'click_num', 'use_num', 'rank_num']
        self._table_columns_autoload = {'create_time': utiles.dateToTimestamp()}
        super(Tags, self).__init__()

    def getTagsBySearch(self, name, limit):
        return self.querySQL('SELECT id,name,create_time FROM '+self._table+' WHERE name like %s LIMIT %s', '%'+name+'%', limit)

    def getTagsByIds(self, ids):
        if len(ids)==1:
            return self.querySQL('SELECT id,name,create_time FROM '+self._table+' WHERE id=%s', ids)
        return self.queryMany(filterString=[('id', ('in', ids))], fields=self._table_columns, orderBy=[('id', 'DESC')])

    def getAllTagsByType(self, type):
        if not isinstance(type, int):
            return None
        return self.queryMany(filterString=[('type', type)], fields=self._table_columns, orderBy=[('rank_num', 'DESC')])

    def getTagByNames(self, names, type):
        if not names:
            return None
        if not type:
            return None
        if isinstance(names, list) or isinstance(names, set):
            tags = self.queryMany(filterString=[('name', ('in', names)), ('type', int(type))], fields=self._table_columns)
            if not tags:
                return None
            res_list = {}
            for tag in tags:
                res_list[tag['id']] = tag
            return res_list
        else:
            return self.queryOne(filterString=[('name', names), ('type', int(type))], fields=self._table_columns)
