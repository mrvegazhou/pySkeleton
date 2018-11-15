# -*- coding: utf8 -*-
from protected.models.admin.AdminBaseModel import AdminBaseModel
from tornado.options import options
from protected.conf.debug import logger
from protected.libs.exceptions import ArgumentError
import sys

class AdminUser(AdminBaseModel):
    def __init__(self):
        self._table  = 'admin_user'
        self.setPK('id')
        self._table_columns = ['id','admin_name','admin_password','update_time','register_ip','login_times','register_time', 'status']
        super(AdminUser, self).__init__()

    #通过用户名获取信息
    def getByUserName(self, admin_name):
        return self.queryOne([('admin_name',admin_name)], self._table_columns)

    #通过id获取后台用户信息
    def getUserById(self, id):
        return self.queryOne([('id',id)], self._table_columns)

    #获取所有用户
    def getAllAdminUsers(self, filters=[], page=None, limit=None, orderBy=()):
        if not page and not limit:
            return self.getAllItems()
        page_limit = limit if limit else options.admin_config['page_limit']
        filterString = []
        if filters:
            for key,val in filters.items():
                if key in self._table_columns:
                    if key=='admin_name':
                        filterString.append(('admin_name',('like', '%'+val+'%')))
                    elif key=='admin_password':
                        del filters[key]
                    else:
                        filterString.append((key, val))
        return self.queryMany(filterString=filterString, fields=self._table_columns, orderBy=[('id', 'DESC')], limit=page_limit, pageNo=page)

    def getAllAdminUsersCount(self, filters=None):
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

    #添加管理员 并判断admin_name是否有重复
    def addAdminUser(self, item):
        if not item['admin_name']:
            raise ArgumentError("参数错误")
        tmp = self.getByUserName(item['admin_name'])
        if tmp:
            return 'admin_same_error'
        return self.addItem(item)