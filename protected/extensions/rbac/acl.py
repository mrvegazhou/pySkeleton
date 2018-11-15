#-*- coding:utf-8 -*-
import itertools
from protected.models.admin.adminRoleUser import AdminRoleUser
from protected.models.admin.adminRole import AdminRole
from protected.models.admin.adminResource import AdminResource
from protected.models.admin.adminRoleResource import AdminRoleResource
from protected.models.admin.adminRoleUser import AdminRoleUser
from protected.extensions.rbac.operations import Ops
from protected.libs.exceptions import ArgumentError,BaseError
__all__ = ["Registry"]

class Registry(object):
    adminRole = None
    adminResource = None
    adminRoleResource = None
    adminRoleUser = None
    def __init__(self):
        self.adminRole = AdminRole()
        self.adminResource = AdminResource()
        self.adminRoleResource = AdminRoleResource()
        self.adminRoleUser = AdminRoleUser()

    #获取用户的角色信息
    def get_role(self, uid):
        role_info = self.adminRoleUser.getRoleByUserId(uid)
        if not role_info:
            return  None
        return self.adminRole.getRoleById(role_info['role_id'])

    def add_role(self, role_id, parents=[0]):
        return self.adminRole.addRoles({'role_name':role_id, 'parents':parents})

    def add_resource(self, uid, resource_name, resource_url=None, parents=[0]):
        return self.AdminResource.addResources({'resource_name':resource_name, 'resource_url':resource_url, 'creator':uid, 'parents':parents})

    def allow(self, role, resource, operation=None):
        if not role:
            raise ArgumentError(u'角色id不能为空'.encode("GBK"))
        if not resource:
            raise ArgumentError(u'资源不能为空'.encode("GBK"))
        item = {'role_id':role, 'resource_id':resource}
        if operation!=None and type(operation)==int:
            item['operation_vals'] = operation
        return self.adminRoleResource.addRoleResource(item)

    def deny(self, role_id, resource_id, operation=None):
        if not operation:
            return self.adminRoleResource.delRoleResource(role_id, resource_id)
        else:
            return self.adminRoleResource.delRoleResource(role_id, resource_id, operation)

    def is_allowed(self, role_id, resource, operation):
        #获取资源id
        resource_info = self.adminResource.getResourceInfoByUrl(resource)
        info = self.adminRoleResource.getOperationByRoleAndResource(role_id, resource_info['id'])
        if info and operation:
            if Ops.checkOperation(info['operation_vals'], operation):
                return True
            else:
                return None
        elif not info:
            return None
        elif info and (not operation):
            return True
        else:
            return None

    def is_user_allowed(self, uid, resource, operation):
        role = self.adminRoleUser.getRoleByUserId(uid)
        if not role:
            raise BaseError(u'用户角色不存在'.encode("GBK"))
        return self.is_allowed(role['id'], resource, operation)





