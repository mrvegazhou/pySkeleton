# -*- coding: utf8 -*-
from protected.models.FrontBaseModel import FrontBaseModel
from protected.libs.exceptions import ArgumentError, BaseError
from protected.libs.utils import dateToTimestamp
import sys

class SysConfig(FrontBaseModel):
    def __init__(self):
        self._table = 'sys_config'
        self.setPK('id')
        self._table_columns = ['id', 'name', 'en_name', 'val']
        super(SysConfig, self).__init__()

    def updateConfig(self, en_name, val, cn_name=''):
        info = self.queryOne(filterString=[('en_name', en_name)], fields=self._table_columns)
        if info:
            #如果是人格测试总数
            if en_name=='bfi_total':
                (N, E, O, A, C) = (0, 0, 0, 0, 0)
                ubt = info['val'].split(',')
                for item in ubt:
                    tmp = item.split(':')
                    if tmp[0]=='N':
                        N = int(tmp[1]) + int(val['N'])
                    elif tmp[0]=='E':
                        E = int(tmp[1]) + int(val['E'])
                    elif tmp[0]=='O':
                        O = int(tmp[1]) + int(val['O'])
                    elif tmp[0]=='A':
                        A = int(tmp[1]) + int(val['A'])
                    elif tmp[0]=='C':
                        C = int(tmp[1]) + int(val['C'])
                val = 'N:%d,E:%d,O:%d,A:%d,C:%d' % (N, E, O, A, C)
            return self.updateInfo(filterString=[('val', val)], where=[('id', info['id'])])
        else:
            if (not cn_name) or (not en_name) or (not val):
                raise ArgumentError("参数错误")
            return self.addItem({'name':cn_name, 'en_name':en_name, 'val':val})

    def incConfig(self, en_name):
        return self.executeSQL("UPDATE %s SET val=val+1 WHERE en_name=%s", *(self._table, en_name))

    def getConfig(self, en_name):
        info = self.queryOne(filterString=[('en_name', en_name)], fields=self._table_columns)
        if en_name=='bfi_total':
            N, E, O, A, C = 0, 0, 0, 0, 0
            ubt = info['val'].split(',')
            for item in ubt:
                tmp = item.split(':')
                if tmp[0]=='N':
                    N = int(tmp[1])
                elif tmp[0]=='E':
                    E = int(tmp[1])
                elif tmp[0]=='O':
                    O = int(tmp[1])
                elif tmp[0]=='A':
                    A = int(tmp[1])
                elif tmp[0]=='C':
                    C = int(tmp[1])
            return {'N':int(N), 'E':int(E), 'O':int(O), 'A':int(A), 'C':int(C)}
        return info