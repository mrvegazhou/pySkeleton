# -*- coding: utf8 -*-
from protected.models.admin.AdminBaseModel import AdminBaseModel, num_compile
from tornado.options import options
from protected.libs.exceptions import ArgumentError
import re
class AdminRole(AdminBaseModel):
    def __init__(self):
        self._table  = 'admin_role'
        self.setPK('id')
        self._table_columns = ['id', 'role_name', 'create_time', 'pid', 'status', 'update_time']
        super(AdminRole, self).__init__()

    #通过id查询Role
    def getRoleById(self, role_id):
        return self.queryOne([('id', role_id)], self._table_columns)

    #获取所有非禁止状态的角色
    def getAllRoles(self, has_children=None):
        return self.getAllItems(has_children)

    #展示菜单
    def showRoles(self):
        list = self.getAllRoles(has_children=True)
        return self.showTree(list)


    #分页获取所有roles
    def getAllRolesByPage(self, page=1, limit=None):
        page_limit = limit if limit else options.admin_config['page_limit']
        return self.queryMany(fields=self._table_columns, orderBy=[('id', 'DESC')], limit=page_limit, pageNo=page)

    #获取角色列表总数
    def getTotalRoles(self):
        return self.queryOneSQL("SELECT COUNT(*) as total FROM %s LIMIT 1" % (self._table))

    #多条数据插入
    def addRoles(self, items):
        return self.addItems(items)

    def addRole(self, item={}):
        return self.addItem(item)

    #通过id修改信息
    def updateRole(self, item={}):
        return self.updateItem(item)

    #多条id删除
    def deleteByRoleIds(self, ids=[]):
        return self.deleteByIds(ids)

    #删除单条数据
    def deleteByRoleId(self, id):
        return self.deleteById(id)