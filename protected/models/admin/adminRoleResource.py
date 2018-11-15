#-*- coding:utf-8 -*-
from protected.models.admin.AdminBaseModel import AdminBaseModel
from protected.models.admin.adminResource import AdminResource
from protected.libs.exceptions import ArgumentError, BaseError
from protected.extensions.rbac.operations import Ops

class AdminRoleResource(AdminBaseModel):
    def __init__(self):
        self._table  = 'admin_role_resource'
        self.setPK('id')
        self._table_columns = ['id', 'role_id', 'resource_id', 'operation_vals', 'create_time']
        super(AdminRoleResource, self).__init__()

    def addRoleResource(self, item):
        if (not item['role_id']) or (not item['resource_id']):
            raise ArgumentError("参数不能为空")
        if not item['operation_vals']:
            item['operation_vals'] = 0
        return self.saveOne({'role_id':item['role_id'], 'resource_id':item['resource_id'], 'operation_vals':item['operation_vals']})

    def updateRoleResourceById(self, item):
        return self.updateItem(item)

    def delRoleResource(self, role, resource, operation=None):
        if (not role) or (not resource):
            raise ArgumentError("参数不能为空")
        if operation:
            info = self.getOperationByRoleAndResource(role, resource)
            newOperation = Ops.delOperation(info['operation_vals'], operation)
            return self.updateInfo([('operation_vals',newOperation)], [('role_id',role), ('resource_id',resource)])
        else:
            return self.deleteByCondition([('role_id',role), ('resource_id',resource)])

    #通过角色和资源获取操作权限
    def getOperationByRoleAndResource(self, role, resource):
        if (not role) or (not resource):
            raise ArgumentError("参数不能为空")
        return self.queryOne([('role_id',role), ('resource_id',resource)], self._table_columns)

    #通过角色id获取资源
    def getResourcesByRoleId(self, role_id):
        if not role_id:
            raise ArgumentError("参数不能为空")
        sql = "SELECT arr.id, arr.operation_vals,ar.resource_name,ar.resource_url,ar.pid as res_pid,ar.id as res_id " \
              "FROM admin_role_resource arr " \
              "LEFT JOIN admin_resource ar ON ar.id=arr.resource_id " \
              "WHERE ar.type=1 AND ar.status=1 AND arr.role_id=%s"
        return self.querySQL(sql, *tuple(role_id))

    #展示子父级别的层级关系列表
    def showRoleResTree(self, list):
        res = []
        tmp = {}
        for item in list:
            tmp.setdefault(item['res_pid'], [])
            tmp[item['res_pid']].append(item)
        for item in list:
            if item['res_id'] in tmp.keys():
                if item in res:
                    res.remove(item)
                item['parent'] = 1
                res.append(item)
                for item2 in tmp[item['res_id']]:
                    if item2 in res:
                        res.remove(item2)
                    item2['parent'] = 0
                    res.append(item2)
            else:
                if not item in res:
                    item['parent'] = 0
                    res.append(item)
        return res

    #通过id获取详细信息
    def getRoleResInfoById(self, id):
        if not id:
            raise ArgumentError("参数不能为空")
        return self.queryOne([('id',id)], self._table_columns)

    #真删除
    def deleteTrueByRowId(self, id):
        sql = 'DELETE FROM '+self._table+' WHERE id=%s'
        return self.executeSQL(sql, *tuple(id))