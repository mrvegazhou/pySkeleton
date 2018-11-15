# -*- coding: utf8 -*-
from protected.models.admin.AdminBaseModel import AdminBaseModel,num_compile
from protected.libs.exceptions import ArgumentError
from tornado.options import options

class AdminRoleUser(AdminBaseModel):
    def __init__(self):
        self._table  = 'admin_role_user'
        self.setPK('id')
        self._table_columns = ['id', 'user_id', 'role_id', 'create_time', 'update_time', 'status']
        super(AdminRoleUser, self).__init__()

    #通过用户id获取角色
    def getRoleByUserId(self, uid):
        return self.queryOne(filterString=[('user_id',uid)], fields=self._table_columns)

    #通过用户和角色id查询
    def getRoleUserByUserIdAndRoleId(self, role_id, user_id):
        return self.queryOne(filterString=[('role_id', int(role_id)), ('user_id', int(user_id))], fields=self._table_columns)

    #添加用户角色关系
    def addRoleUser(self, item={}):
        if (not item['role_id']) or (not item['user_id']):
            raise ArgumentError("参数错误")
        #判断是否存在关系
        tmp = self.getRoleUserByUserIdAndRoleId(item['role_id'], item['user_id'])
        if tmp:
            return 'admin_same_error'
        return self.addItem(item)

    #获取所有用户角色
    def getAllRoleUsersByRoleId(self, role_id=None, user_id=None, page=1, limit=None):
        page_limit = limit if limit else options.admin_config['page_limit']
        place = []
        vals = []
        if role_id:
            place.append(' ru.role_id=%s ')
            vals.append(role_id)
        if user_id:
            place.append(' ru.user_id=%s ')
            vals.append(user_id)
        place = ' AND '.join(place)
        sql = "SELECT ru.id,ru.role_id,ru.user_id,ru.create_time,ru.update_time,ru.status,r.role_name,u.admin_name " \
              "FROM "+self._table+" AS ru " \
              "LEFT JOIN admin_role AS r ON r.id=ru.role_id " \
              "LEFT JOIN admin_user AS u ON u.id=ru.user_id " \
              "WHERE 1=1 AND %s" \
              "ORDER BY ru.id DESC " \
              "LIMIT %s,%s" \
              % (place, '%s', '%s')
        offset = (int(page)-1)*int(limit)
        vals = vals+[offset,page_limit]
        return self.querySQL(sql, *tuple(vals))

    #通过角色id获取总记录数
    def getAllRoleUsersCount(self, role_id=None, user_id=None):
        if not role_id and not user_id:
            return 0
        place = ' WHERE 1=1 '
        vals = []
        if role_id:
            place += 'AND role_id=%s '
            vals.append(role_id)
        if user_id:
            place += 'AND user_id=%s '
            vals.append(user_id)
        sql = 'SELECT COUNT(*) as total FROM '+self._table+' %s' % (place)
        return self.queryOneSQL(sql, *tuple(vals))