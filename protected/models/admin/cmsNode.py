# -*- coding: utf8 -*-
from protected.models.admin.AdminBaseModel import AdminBaseModel
from protected.libs.exceptions import ArgumentError, BaseError
import sys
from protected.conf.debug import logger
from tornado.options import options

class CmsNode(AdminBaseModel):
    def __init__(self):
        self._table  = 'cms_node'
        self.setPK('id')
        self._table_columns = ['id', 'name', 'create_time', 'publish_time', 'delete_time', 'type', 'tag_ids', 'update_time', 'status']
        super(CmsNode, self).__init__()

    #获取所有文章列表
    def getAllCmsNode(self, filters=[], page=None, limit=None, orderBy=()):
        if not page and not limit:
            return self.getAllItems()
        page_limit = limit if limit else options.admin_config['page_limit']
        filterString = []
        if filters:
            for key,val in filters.items():
                if key in self._table_columns and val!='':
                    if key=='name':
                        filterString.append(('name',('like', '%'+val+'%')))
                    elif key=='id':
                        del filters[key]
                    else:
                        filterString.append((key, val))
        return self.queryMany(filterString=filterString, fields=self._table_columns, orderBy=[('id', 'DESC')], limit=page_limit, pageNo=page)

    def getAllCmsNodeCount(self, filters=None):
        place = ' WHERE 1=1  '
        vals = []
        if filters:
            for key,val in filters.items():
                if key in self._table_columns:
                    if key=='admin_name':
                        place += " AND admin_name LIKE %s "
                        vals.append('%'+val+'%')
                    elif key=='admin_password':
                        del filters[key]
                    else:
                        place += 'AND %s=%s ' % (key, val)
                        vals.append(val)
        sql = 'SELECT COUNT(*) as total FROM '+self._table+' %s LIMIT 1' % (place)
        return self.queryOneSQL(sql, *tuple(vals))
