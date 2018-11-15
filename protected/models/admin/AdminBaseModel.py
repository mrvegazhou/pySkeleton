#-*- coding:utf-8 -*-
from protected.libs.db.BaseModel import BaseModel
from protected.libs.exceptions import ArgumentError, BaseError
from protected.libs.utils import checkColumnRules
from datetime import datetime
from tornado.options import options
import re,time
from protected.conf.debug import logger
num_compile = re.compile("^[0-9]*$")

class AdminBaseModel(BaseModel):
    def __init__(self):
        super(AdminBaseModel, self).__init__()

    #有层次的展示子父级别
    def showTree(self, list):
        last_id = 0
        list_last_id = []
        level = 0
        res = []
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
                    level = level + 1
                    continue
                elif item['pid']==last_id:
                    item['level'] = level
                    res.append(item)
                    list.remove(item)
                    if item['has_children']>0:
                        last_id = item['id']
                        list_last_id.append(last_id)
                        level = level + 1
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
        return res


     #获取所有非禁止状态的角色
    def getAllItems(self, has_children=None):
        #获取表字段
        fields = ','.join(['tb.'+item for item in self._table_columns])
        if has_children:
            sql = "SELECT %s," \
                  " (SELECT count(*) FROM %s tb2 WHERE tb2.pid=tb.id) AS has_children " \
                  "FROM %s tb " \
                  "WHERE tb.status=1  ORDER BY tb.pid" % (fields, self._table, self._table)
        else:
            sql = "SELECT  %s " \
                  "FROM %s tb " \
                  "WHERE tb.status=1  ORDER BY tb.id" % (fields, self._table)
        return self.querySQL(sql)

    #获取所有列表信息
    def getAll(self):
        fields = ','.join(self._table_columns)
        sql = "SELECT  %s " \
                  "FROM %s " \
                  "ORDER BY id" % (fields, self._table)
        return self.querySQL(sql)

    #通过id获取子孙ids
    def getChildrenIds(self, id):
        child_ids = [id]
        all_pid_id = {}
        lists = self.getAllItems()
        if not lists:
            return None
        for item in lists:
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

    #通过在主键获取信息
    def getItem(self, id):
        if not id:
            return None
        return self.queryOne([('id',id)], self._table_columns)

    def addItem(self, item={}):
        return self.saveOne(item)

    def addItems(self, items=[]):
        if not items:
            raise ArgumentError("参数不能为空")
        if not isinstance(items['parents'], list):
            raise ArgumentError("如果有父角色，parents类型为集合")
        lists = []
        for i in items['parents']:
            tmp = {'role_name':items['role_name'], 'pid':i}
            lists.append(tmp)
        return self.saveMany(lists)

    #通过主键修改信息
    def updateItem(self, item={}):
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
            if k=='status':
                if item['status']=='1':
                    if 'delete_time' in self._table_columns:
                        replace_list.append(('delete_time', '0'))
                elif item['status']=='-1':
                    if 'delete_time' in self._table_columns:
                        replace_list.append(('delete_time', time.time()))
        if replace_list:
            return self.updateInfo(filterString=replace_list, where=[('id', item['id'])])
        return False

    def deleteByIds(self, ids=[]):
        if ids==None:
            raise ArgumentError("参数不能为空")
        for id in ids:
            if not num_compile.match(str(id)):
                raise ArgumentError("ids中不能有非数字值")
        #获取此id的子孙信息
        tmp = []
        for id in ids:
            tmp = tmp + self.getChildrenIds(id)
        return self.updateInfo(filterString=[('status', 0)], where=[('id',('in',list(set(tmp))))])

    #删除单条数据 先获取子集一起删除
    def deleteById(self, id=None, type=1):
        if id==None:
            raise ArgumentError('参数不能为空')
        try:
            tmp = self.getChildrenIds(id)
            if len(tmp)==1:
                return self.updateInfo(filterString=[('status', 0)], where=[('id', tmp[0]), ('type', type)])
            else:
                return self.updateInfo(filterString=[('status', 0)], where=[('id', ('in', tmp)), ('type', type)])
        except Exception as e:
            return e
    #没有子父级别的删除
    def deleteByRowId(self, id=None):
        if not id:
            raise ArgumentError('参数不能为空')
        return self.updateInfo(filterString=[('status', 0)], where=[('id', id)])
    #没有子父级别的删除
    def deleteByRowIds(self, ids=[]):
        if not ids:
            raise ArgumentError('参数不能为空')
        return self.updateInfo(filterString=[('status', 0)], where=[('id', ('in', ids))])
    #真实删除
    def trueDeleteByRowId(self, id):
        return self.deleteByPK(id)
