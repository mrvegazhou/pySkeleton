# -*- coding: utf-8 -*-
from protected.handlers.admin.handler import AdminBaseHandler, adminAuthenticated
from protected.models.admin.adminResource import AdminResource
from protected.models.admin.adminUser import AdminUser
from protected.models.admin.adminRole import AdminRole
from protected.models.admin.adminRoleUser import AdminRoleUser
from protected.models.admin.adminRoleResource import AdminRoleResource
from protected.extensions.rbac.operations import Ops
from protected.libs.const import AdminErrorMessage
#分页工具
from protected.libs.pagenation import Pageset
from tornado.escape import json_decode
from tornado import gen, options
from tornado.web import asynchronous, authenticated
from protected.conf.debug import logger
import math
import time
import sys
import datetime

class IndexHandler(AdminBaseHandler):
    #@adminAuthenticated
    def get(self):
        ar = AdminRole()
        print ar.getTotalRoles()
        print '%%%%'
        sys.exit()
        self.render('admin/system_menus.html')

#菜单管理
class MenusHandler(AdminBaseHandler):
    ar = AdminResource()
    #@adminAuthenticated
    def get(self):
        list = self.ar.getAllByType(has_children=True)
        self._context.menu_list = self.ar.showMens(list)
        au = AdminUser()
        def getUser(id):
            user = au.getUserById(id)
            if not user:
                return '暂无'
            else:
                return user['admin_name']
        def showBlank(level, name):
            return "%s%s" % (level*"&nbsp;&nbsp;&nbsp;", name)
        self._context.getUser = getUser
        self._context.showBlank = showBlank
        self.render('admin/system_menus.html')

    #@adminAuthenticated
    def post(self):
        act = self.get_argument('act', '')
        if act=='delete':
            ids = self.get_argument('ids', '')
            res = self.ar.deleteByIds(ids.split(','))
            if not res:
                ret = { 'msg': res, 'code':'005'}
            else:
                ret = { 'msg': '删除成功', 'code':'success'}
            self.finish(self.write(self.json_encode(ret)))
        elif act=='delete-one':
            id = self.get_argument('id', '')
            res = self.ar.deleteById(id)
            if not res:
                ret = { 'msg': res, 'code':'005'}
            else:
                ret = { 'msg': '删除成功', 'code':'success'}
            self.finish(self.write(self.json_encode(ret)))
        elif act=='fresh':
            self.redirect('/admin/system/menus')
        elif act=='add':
            item = {}
            item['resource_name'] = self.get_argument('resource_name', '')
            item['resource_url'] = self.get_argument('resource_url', '')
            item['pid'] = self.get_argument('pid', 0)
            item['icon'] = self.get_argument('icon', '')
            item['status'] = self.get_argument('status', '')
            res = self.ar.addResource(item)
            if res:
                ret = { 'msg': '添加成功', 'code':'success'}
            else:
                ret = { 'msg': '添加失败', 'code':'006'}
            self.finish(self.write(self.json_encode(ret)))
        elif act=='edit-info':
            id = self.get_argument('id', '')
            info = self.ar.getResourceById(id)
            self.finish(self.write(self.json_encode(info)))
        elif act=='edit':
            item = {}
            item['resource_name'] = self.get_argument('resource_name', '')
            item['resource_url'] = self.get_argument('resource_url', '')
            item['pid'] = self.get_argument('pid', 0)
            item['icon'] = self.get_argument('icon', '')
            item['status'] = self.get_argument('status', '')
            item['id'] = self.get_argument('id', '')
            res = self.ar.updateResource(item)
            if res:
                ret = { 'msg': '修改成功', 'code':'success', 'new_data':item}
            else:
                ret = { 'msg': '修改失败', 'code':'007'}
            self.finish(self.write(self.json_encode(ret)))

#权限管理
class RoleHandler(AdminBaseHandler):
    role = AdminRole()
    limit = options.options.admin_config['page_limit']
    #@adminAuthenticated
    def get(self):
        page = self.get_argument('page', 1)
        roles = self.role.getAllRolesByPage(page=page, limit=self.limit)
        roles_total = self.role.getTotalRoles()
        total = roles_total['total']
        self._context.role_total = total
        self._context.role_list = roles
        #分页
        page_set = Pageset(total_entries=total, entries_per_page=self.limit, current_page=page, pages_per_set=None)
        last_page = page_set.last_page()
        page_set.pages_per_set(last_page)
        self._context.last_page = last_page
        #获取父角色
        def getParentRoleInfo(pid):
            pinfo = self.role.getRoleById(pid)
            if not pinfo:
                return '无'
            return pinfo['role_name']
        self._context.getParentRoleInfo = getParentRoleInfo
        self._context.show_pages = page_set.pages_in_set()
        self._context.page = page
        #父级角色
        self._context.parent_role_list = self.role.showRoles()
        def showBlank(level, name):
            return "%s%s" % (level*"&nbsp;&nbsp;&nbsp;", name)
        self._context.showBlank = showBlank
        self.render('admin/system_role.html')

    #@adminAuthenticated
    def post(self):
        act = self.get_argument('act', '')
        if act=='list':
            page = self.get_argument('page', 1)
            roles = self.role.getAllRolesByPage(page=page, limit=self.limit)
            i = 0
            for r in roles:
                pinfo = self.role.getRoleById(r['pid'])
                if pinfo:
                    r['pid'] = pinfo['role_name']
                else:
                    r['pid'] = '无'
                r['role_name'] = '<a href="/admin/system/roleuser/?role_id='+r['id']+'">'+r['role_name']+'</a>'
                roles[i] = r
                i += 1
            del i
            self.finish(self.write(self.json_encode(roles)))
        elif act=='add':
            item = {}
            item['role_name'] = self.get_argument('role_name', '')
            item['pid'] = self.get_argument('pid', 0)
            item['update_time'] = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
            item['status'] = self.get_argument('status', '')
            res = self.role.addRole(item)
            if res:
                ret = { 'msg': '添加成功', 'code':'success'}
            else:
                ret = { 'msg': '添加失败', 'code':'006'}
            self.finish(self.write(self.json_encode(ret)))
        elif act=='edit-info':
            id = self.get_argument('id', '')
            info = self.role.getRoleById(id)
            self.finish(self.write(self.json_encode(info)))
        elif act=='edit':
            item = {}
            item['role_name'] = self.get_argument('role_name', '')
            item['pid'] = self.get_argument('pid', 0)
            item['status'] = self.get_argument('status', '')
            item['id'] = self.get_argument('id', '')
            item['update_time'] = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
            res = self.role.updateRole(item)
            if res:
                ret = { 'msg': '修改成功', 'code':'success', 'new_data':item}
            else:
                ret = { 'msg': '修改失败', 'code':'007'}
            self.finish(self.write(self.json_encode(ret)))
        elif act=='delete':
            ids = self.get_argument('ids', '')
            res = self.role.deleteByIds(ids.split(','))
            if not res:
                ret = { 'msg': res, 'code':'005'}
            else:
                ret = { 'msg': '删除成功', 'code':'success'}
            self.finish(self.write(self.json_encode(ret)))
        elif act=='delete-one':
            id = self.get_argument('id', '')
            res = self.role.deleteByRoleId(id)
            if not res:
                ret = { 'msg': res, 'code':'005'}
            else:
                ret = { 'msg': '删除成功', 'code':'success'}
            self.finish(self.write(self.json_encode(ret)))

#角色和管理员关系
class RoleUserHandler(AdminBaseHandler):
    role_user = AdminRoleUser()
    limit = options.options.admin_config['page_limit']
    #@adminAuthenticated
    def get(self):
        admin_user = AdminUser()
        role = AdminRole()
        role_id = self.get_argument('role_id', '1')
        self._context.role_id = role_id
        self._context.admin_users = admin_user.getAllAdminUsers()
        self._context.roles = role.showRoles()
        self.render('admin/system_role_user.html')
    #@adminAuthenticated
    def post(self):
        act = self.get_argument('act', '')
        role_id = self.get_argument('role_id', 1)
        if act=='list':
            page = self.get_argument('page', 1)
            search = self.get_argument('_search', False)
            user_id = None
            if search=='true':
                filters = json_decode(self.get_argument('filters', ''))
                user_id = filters['user_id'] if filters['user_id'] else None
                role_id = filters['role_id'] if filters['role_id'] else None
            res = self.role_user.getAllRoleUsersByRoleId(role_id=role_id, user_id=user_id, page=page, limit=self.limit)
            records = self.role_user.getAllRoleUsersCount(role_id, user_id)
            total = math.ceil(records['total']/(self.limit*1.0))
            ret = { "page": page,
                    "total": total,
                    "records": records['total'],
                    "rows": res }
            self.finish(self.write(self.json_encode(ret)))
        elif act=='add':
            role_id = self.get_argument('role_id', 1)
            user_id = self.get_argument('user_id', 1)
            item = {'role_id':role_id, 'user_id':user_id, 'create_time':time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))}
            res = self.role_user.addRoleUser(item)
            if not res:
                ret = { 'msg': '添加失败', 'code':'006'}
            else:
                if res=='admin_same_error':
                    ret = { 'msg': '存在相同记录', 'code':'008'}
                else:
                    ret = { 'msg': '添加成功', 'code':'success'}
            self.finish(self.write(self.json_encode(ret)))
        elif act=='edit':
            post_data = self.get_argument('postData', '')
            res = self.role_user.updateItem(json_decode(post_data))
            if not res:
                ret = { 'msg': '修改失败', 'code':'007'}
            else:
                ret = { 'msg': '修改成功', 'code':'success'}
            self.finish(self.write(self.json_encode(ret)))
        elif act=='delete':
            post_data = self.get_argument('postData', '')
            post_data = json_decode(post_data)
            ids = post_data['ids']
            res = self.role_user.deleteByIds(ids.split(','))
            if not res:
                ret = { 'msg': res, 'code':'005'}
            else:
                ret = { 'msg': '删除成功', 'code':'success'}
            self.finish(self.write(self.json_encode(ret)))
        elif act=='delete-one':
            post_data = self.get_argument('postData', '')
            post_data = json_decode(post_data)
            id = post_data['id']
            res = self.role_user.deleteById(id)
            if not res:
                ret = { 'msg': res, 'code':'005'}
            else:
                ret = { 'msg': '删除成功', 'code':'success'}
            self.finish(self.write(self.json_encode(ret)))

#管理员列表管理
class AdminUserHandler(AdminBaseHandler):
    admin_user = AdminUser()
    limit = options.options.admin_config['page_limit']
    #@adminAuthenticated
    def get(self):
        self.render('admin/system_admin_user.html')
    #@adminAuthenticated
    def post(self):
        act = self.get_argument('act', '')
        if act=='list':
            page = self.get_argument('page', 1)
            search = self.get_argument('_search', '')
            if search=='true':
                filters = json_decode(self.get_argument('filters', ''))
            else:
                filters = []
            admin_users = self.admin_user.getAllAdminUsers(filters=filters, page=page, limit=self.limit, orderBy=('id', 'DESC'))
            admin_users_count = self.admin_user.getAllAdminUsersCount(filters=filters)
            self._context.admin_users = admin_users
            total = math.ceil(admin_users_count['total']/(self.limit*1.0))
            ret = { "page": page,
                    "total": total,
                    "records": admin_users_count['total'],
                    "rows": admin_users }
            self.finish(self.write(self.json_encode(ret)))
        elif act=='add':
            admin_name = self.get_argument('admin_name', '')
            admin_password = self.get_argument('admin_password', '')
            admin_email = self.get_argument('admin_email', '')
            status = self.get_argument('status', '')
            register_ip = self.request.remote_ip#self.request.headers['X-Real-Ip']
            register_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
            item = {'admin_name':admin_name,
                    'admin_password':admin_password,
                    'status':status,
                    'register_ip':register_ip,
                    'register_time':register_time,
                    'admin_email':admin_email
            }
            res = self.admin_user.addAdminUser(item)
            if not res:
                ret = { 'msg': '添加失败', 'code':'006'}
            else:
                if res=='admin_same_error':
                    ret = { 'msg': '存在相同记录', 'code':'008'}
                else:
                    ret = { 'msg': '添加成功', 'code':'success'}
            self.finish(self.write(self.json_encode(ret)))
        elif act=='delete-one':
            post_data = self.get_argument('postData', '')
            post_data = json_decode(post_data)
            id = post_data['id']
            res = self.admin_user.deleteByRowId(id)
            if not res:
                ret = { 'msg': res, 'code':'005'}
            else:
                ret = { 'msg': '删除成功', 'code':'success'}
            self.finish(self.write(self.json_encode(ret)))
        elif act=='delete':
            post_data = self.get_argument('postData', '')
            post_data = json_decode(post_data)
            ids = post_data['ids']
            res = self.admin_user.deleteByRowIds(ids.split(','))
            if not res:
                ret = { 'msg': res, 'code':'005'}
            else:
                ret = { 'msg': '删除成功', 'code':'success'}
            self.finish(self.write(self.json_encode(ret)))
        elif act=='edit':
            post_data = self.get_argument('postData', '')
            item = json_decode(post_data)
            if ''!=item['admin_password']:
                import hashlib
                hash = hashlib.md5()
                hash.update(item['admin_password'])
                item['admin_password'] = hash.hexdigest()
            else:
                del item['admin_password']
            res = self.admin_user.updateItem(item)
            if not res:
                ret = { 'msg': '修改失败', 'code':'007'}
            else:
                ret = { 'msg': '修改成功', 'code':'success'}

#为角色分配资源
class RoleResourceHandler(AdminBaseHandler):
    role_resource = AdminRoleResource()
    role = AdminRole()
    def get(self):
        role_id = self.get_argument('role_id', '1')
        role_page = self.get_argument('page', 1)
        self._context.error = ''
        self._context.role_page = role_page
        if not role_id:
            self._context.error = '请先分配角色!'
        else:
            list = self.role_resource.getResourcesByRoleId(role_id)
            trees = self.role_resource.showRoleResTree(list)
            #获取角色信息
            role_info = self.role.getRoleById(role_id)
            self._context.role_info = role_info
            #获取角色列表
            role_list = self.role.getAllItems()
            self._context.role_list = role_list
            #获取资源(菜单)
            def showBlank(level, name):
                return "%s%s" % (level*"&nbsp;&nbsp;&nbsp;", name)
            ar = AdminResource()
            list = ar.getAllByType(has_children=True)
            self._context.menu_list = ar.showMens(list)
            self._context.showBlank = showBlank

            def showOperations(opts):
                tmp = Ops.getOperations(opts)
                res = []
                for item in tmp:
                    if item in Ops.opes_names.keys():
                        res.append(Ops.opes_names[item])
                return ','.join(res)
            self._context.trees = trees
            self._context.showOperations = showOperations
            self._context.opes = Ops.opes_names
            self._context.role_id = role_id
        self.render('admin/system_role_resource.html')
    def post(self):
        act = self.get_argument('act', '')
        id = self.get_argument('id', '')
        if act=='delete-one':
            id = self.get_argument('id', None)
            res = self.role_resource.deleteTrueByRowId(id)
            if not res:
                ret = { 'msg': res, 'code':'005'}
            else:
                ret = { 'msg': '删除成功', 'code':'success'}
            self.finish(self.write(self.json_encode(ret)))
        elif act=='add':
            role_id = self.get_argument('role_id', None)
            resource_id = self.get_argument('resource_id', None)
            opes = self.get_argument('opes', None)
            operation_vals = Ops.getOpesValues(opes.split(','))
            item = {'role_id':role_id, 'resource_id':resource_id, 'operation_vals':operation_vals}
            #添加之前先判断是否存在记录
            tmp = self.role_resource.getOperationByRoleAndResource(role_id, resource_id)
            if tmp:
                ret = { 'msg': '已经存在记录！', 'code':'error'}
                self.finish(self.write(self.json_encode(ret)))
            res = self.role_resource.addRoleResource(item)
            ret = { 'msg': '添加成功', 'code':'success'}
            self.finish(self.write(self.json_encode(ret)))
        elif act=='edit':
            id = self.get_argument('id', None)
            role_id = self.get_argument('role_id', None)
            resource_id = self.get_argument('resource_id', None)
            opes = self.get_argument('opes', None)
            operation_vals = Ops.getOpesValues(opes.split(','))
            item = {'id':id, 'role_id':role_id, 'resource_id':resource_id, 'operation_vals':operation_vals}
            res = self.role_resource.updateRoleResourceById(item)
            ret = { 'msg': '修改成功', 'code':'success'}
            self.finish(self.write(self.json_encode(ret)))
        elif act=='edit-info':
            info_id = self.get_argument('id')
            if not info_id:
                ret = { 'msg': '缺少唯一标识错误！', 'code':'error'}
                self.finish(self.write(self.json_encode(ret)))
            else:
                info = self.role_resource.getRoleResInfoById(info_id)
                if not info:
                    ret = { 'msg': '没有相关数据！', 'code':'error'}
                    self.finish(self.write(self.json_encode(ret)))
                tmp = Ops.getOperations(info['operation_vals'])
                res = []
                for item in tmp:
                    if item in Ops.opes_names.keys():
                        res.append(item)
                info['opes'] = ','.join(res)
                self.finish(self.write(self.json_encode(info)))

handlers = [
    (r"/admin/system/index", IndexHandler),
    (r"/admin/system/menus", MenusHandler),
    (r"/admin/system/role", RoleHandler),
    (r"/admin/system/roleuser", RoleUserHandler),
    (r"/admin/system/adminuser", AdminUserHandler),
    (r"/admin/system/roleresource", RoleResourceHandler)
]


