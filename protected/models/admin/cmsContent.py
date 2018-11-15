# -*- coding: utf8 -*-
from protected.models.admin.AdminBaseModel import AdminBaseModel
from protected.libs.exceptions import ArgumentError, BaseError
import sys,time
from tornado.options import options

class CmsContent(AdminBaseModel):
    def __init__(self):
        self._table  = 'cms_content'
        self.setPK('id')
        self._table_columns = ['id', 'node_id', 'page_title', 'meta_title', 'meta_description', 'meta_keywords', 'content', 'file_ids']
        self._table_columns_rule = {'node_id':['required'], 'page_title':['required'], 'meta_title':['required'],'file_ids':['required']}
        super(CmsContent, self).__init__()

    #通过节点id获取详情
    def getInfoByNodeId(self, node_id):
        return self.queryOne([('node_id',node_id)], self._table_columns)

    #通过id修改属性
    def updateInfoById(self, item):
        if (not item) or (not isinstance(item, dict)) or (not item['id']):
            raise ArgumentError("参数错误")
        keys = item.keys()
        replace_list = []
        for k in keys:
            if k not in self._table_columns:
                del item[k]
                continue
            if k!='id' and item[k]!='':
                replace_list.append((k, item[k]))
        if replace_list:
            return self.updateInfo(filterString=replace_list, where=[('id', item['id'])])
        return False
