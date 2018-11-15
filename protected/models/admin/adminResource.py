#-*- coding:utf-8 -*-
from protected.models.admin.AdminBaseModel import AdminBaseModel
from protected.libs.exceptions import ArgumentError, BaseError
import re
import sys
from protected.conf.debug import logger
num_compile = re.compile("^[0-9]*$")

class AdminResource(AdminBaseModel):
    def __init__(self):
        self._table  = 'admin_resource'
        self.setPK('id')
        self._table_columns = ['id', 'resource_name', 'resource_url', 'creator', 'update_time', 'pid', 'type', 'icon', 'status']
        super(AdminResource, self).__init__()

    def addResource(self, item):
        if (not item) or (not isinstance(item, dict)):
            raise ArgumentError("参数错误")
        keys = item.keys()
        for k in keys:
            if k not in self._table_columns:
                del item[k]
        return self.saveOne(item)

    def addResources(self, items):
        if not items:
            raise ArgumentError("参数不能为空")
        if not isinstance(items['parents'], list):
            raise ArgumentError("如果有父资源，parents类型为集合")
        lists = []
        for i in items['parents']:
            tmp = {'resource_name':items['resource_name'], 'resource_url':items['resource_url'], 'creator':items['creator'], 'pid':i}
            lists.append(tmp)
        return self.saveMany(lists)

    #通过id修改信息
    def updateResource(self, item={}):
        if (not item) or (not isinstance(item, dict)) or (not item['id']):
            raise ArgumentError("参数错误")
        keys = item.keys()
        replace_list = []
        for k in keys:
            if k not in self._table_columns:
                del item[k]
                continue
            if k!='id':
                replace_list.append((k, item[k]))
        if replace_list:
            return self.updateInfo(filterString=replace_list, where=[('id', item['id'])])
        return False

    #获取单个信息
    def getResourceById(self, id):
        if not id:
            raise ArgumentError("参数错误")
        return self.queryOne([('id', id)], self._table_columns)

    #通过资源url获取id
    def getResourceInfoByUrl(self, url):
        return self.queryOne([('resource_url', url)], self._table_columns)

    #通过id获取子菜单
    def getChildrenMenus(self, pid):
        return self.queryMany(filterString=[('type',1), ('pid',pid)], fields=self._table_columns)

    #获取所有的菜单 可以选择是否包含has_children
    def getAllByType(self, type=1, has_children=None):
        if has_children:
            sql = "SELECT ar.id, ar.resource_name, ar.resource_url, ar.creator, ar.update_time, ar.pid, ar.type, ar.icon, ar.status," \
                  " (SELECT count(*) FROM admin_resource ar2 WHERE ar2.pid=ar.id) AS has_children " \
                  "FROM admin_resource ar " \
                  "WHERE ar.type=%s  ORDER BY ar.pid"
        else:
            sql = "SELECT ar.id, ar.resource_name, ar.resource_url, ar.creator, ar.update_time, ar.pid, ar.type, ar.icon, ar.status " \
                  "FROM admin_resource ar " \
                  "WHERE ar.type=%s  ORDER BY ar.id"
        return self.querySQL(sql, type)

    #展示菜单
    def showMens(self, list):
        last_id = 0
        list_last_id = []
        level = 0
        res = []
        level_array  = {}
        while list:
            for item in list:
                if last_id==0 and item['pid']==0:
                    item['level'] = level
                    res.append(item)
                    list.remove(item)
                    if item['has_children']==0:
                        continue
                    last_id = item['id']
                    list_last_id.append(item['id'])
                    level += 1
                    level_array[last_id] = level
                    continue
                elif item['pid']==last_id:
                    item['level'] = level
                    res.append(item)
                    list.remove(item)
                    if item['has_children']>0:
                        last_id = item['id']
                        list_last_id.append(last_id)
                        level += 1
                        level_array[last_id] = level
                    else:
                        last_id = list_last_id[-1]
                elif item['pid']>last_id:
                    break
            count = len(list_last_id)
            if count>1:
                last_id = list_last_id.pop()
            elif count==1:
                if last_id!=list_last_id[0]:
                    last_id = list_last_id[0]
                else:
                    last_id = 0
                    level = 0
                    continue
            if last_id and level_array[last_id]:
                level = level_array[last_id]
            else:
                level = 0
        return res

    #获取树形菜单
    def showTreeMenus(self, role_id=0, id=0, menus=[]):
        list = self.querySQL("""SELECT ar.id, ar.resource_name, ar.resource_url, ar.creator, ar.update_time, ar.pid, ar.type, ar.icon
                               FROM admin_resource ar
                               LEFT JOIN admin_role_resource arr ON arr.resource_id=ar.id
                               WHERE ar.type=1 AND pid=%s AND arr.role_id=%s
                            """, id, role_id)
        for item in list:
            menus.append('<li>')
            clist = self.getChildrenMenus(item['id'])
            if clist:
                menus.append('<a href="#" class="dropdown-toggle">')
            else:
                url = item['resource_url'] if item['resource_url'] else '#'
                menus.append('<a href="'+url+'">')
            icon = item['icon'] if item['icon'] else ''
            menus.append('<i class="'+icon+'"></i>')
            if item['pid']==0:
                menus.append('<span class="menu-text">'+item['resource_name']+'</span>')
            else:
                menus.append(item['resource_name'])
            if clist:
                menus.append('<b class="arrow icon-angle-down"></b>')
            menus.append('</a>')
            if clist:
                menus.append('<ul class="submenu">')
                self.showTreeMenus(role_id, item['id'], menus)
                menus.append('</ul>')
            menus.append('</li>')
        return menus

    #通过id获取子孙ids
    def getChildrenIds(self, id):
        child_ids = [id]
        all_pid_id = {}
        menus = self.getAllByType()
        for item in menus:
            all_pid_id.setdefault(item['pid'], [])
            if all_pid_id[item['pid']]:
                all_pid_id[item['pid']].append(item['id'])
            else:
                all_pid_id[item['pid']] = [item['id']]
        flag = True
        try:
            while flag:
                inters = list(set(child_ids).intersection(set(all_pid_id.keys())))
                if inters:
                    for i in inters:
                        child_ids = child_ids + all_pid_id[i]
                        del all_pid_id[i]
                else:
                    flag = False
        except Exception as e:
            print e
        return child_ids


    #删除菜单
    def deleteByIds(self, ids=[], type=1):
        if ids==None:
            raise ArgumentError("参数不能为空")
        for id in ids:
            if not num_compile.match(str(id)):
                raise ArgumentError("ids中不能有非数字值")
        #获取此id的子孙信息
        tmp = []
        for id in ids:
            tmp = tmp + self.getChildrenIds(id)
        return self.updateInfo(filterString=[('status', 0)], where=[('id',('in',list(set(tmp)))), ('type', type)])

    #删除单条数据
    def deleteById(self, id=None, type=1):
        if id==None:
            raise ArgumentError('参数不能为空')
        try:
            tmp = self.getChildrenIds(id)
            print tmp
            return self.updateInfo(filterString=[('status', 0)], where=[('id', ('in', tmp)), ('type', type)])
        except Exception as e:
            return e