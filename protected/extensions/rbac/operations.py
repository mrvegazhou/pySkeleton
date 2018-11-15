#-*- coding:utf-8 -*-
class Ops(object):
    opes = {
        'view': 1<< 0,
        'add': 1<< 1,
        'update': 1<< 2,
        'delete': 1<< 3,
        'upload': 1<< 4
    }
    opes_names = {
        'view': '查看',
        'add': '添加',
        'update': '修改',
        'delete': '删除',
        'upload': '更新'
    }
    @classmethod
    def getAll(cls):
        all = 0
        for v in cls.opes.values():
            all |= v
        return all

    #通过标识返回权限值
    @classmethod
    def getOpesValues(cls, opes_names):
        res = 0
        for item in opes_names:
            res |= cls.opes[item]
        return res

    #操作权限的修改
    @classmethod
    def checkOperationByAll(cls, permission):
        if hasattr(cls, permission):
            #(userrolevalue & oprolevalue) != 0表示拥有oprolevalue所表示权限
            if cls.all & permission==permission:
                return True
        return None

    @classmethod
    def checkOperation(cls, operations, operation):
        if operations & operation==operation:
            return True
        else:
            return None

    @classmethod
    def delOperation(cls, old_val, operation):
        if hasattr(cls, operation):
           old_val &= ~cls.operation
           return old_val
        else:
            return None

    #添加操作权限
    @classmethod
    def addOperation(cls, old_val, operation):
        return old_val | operation

    #包括哪些操作权限
    @classmethod
    def getOperations(cls, operations):
        res = []
        if not operations:
            return res
        for k,v in cls.opes.items():
            if operations&v==v:
                res.append(k)
        return res