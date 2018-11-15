# -*- coding: utf8 -*-
from protected.models.FrontBaseModel import FrontBaseModel
from protected.libs.exceptions import ArgumentError, BaseError
import sys

class CommonDistrict(FrontBaseModel):
    def __init__(self):
        self._table = 'common_district'
        self.setPK('id')
        self._table_columns = ['id', 'region_name', 'region_type', 'pid']
        super(CommonDistrict, self).__init__()

    def new(self, item):
        obj = self.initialize(item)
        if obj:
            return self.save()
        return None

    #通过pid获取子地区
    def getDistrict(self, pid=0):
        tmp = self._table_columns[:]
        tmp[1] = 'region_name as name'
        return self.queryMany([('pid', pid)], tmp)

    def getDistrictParents(self, id, res=[]):
        if id!=0:
            info = self.getItem(id)
            res.append(info['region_name'])
            if info:
                self.getDistrictParents(info['pid'], res)
        return res
