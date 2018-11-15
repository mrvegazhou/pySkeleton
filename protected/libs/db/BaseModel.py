# -*- coding: utf8 -*-
from protected.libs import db
from tornado.options import options
from protected.libs.utils import checkColumnRules
from protected.libs.exceptions import ArgumentError, BaseError
import sys

#https://github.com/martez81/SimpleModel
class BaseModel(object):
    _db_name = None
    _table_columns = []
    _columns_data = []
    __db = None
    _table = None
    _pk_name = []
    _properties = {}
    _exclude_columns = []
    _first_running = True
    _debug = False

    def __init__(self):
        if BaseModel._first_running:
            database = options.mysql["database"]
            BaseModel.__db = db.connetion("mysql", database)
            BaseModel._first_running = False
        self.getDbName()

    def getDbInstance(self):
		return self.__db

    def getDbName(self):
        if not self._db_name:
            self._db_name = options.mysql["database"]
        return self._db_name

    #获取表字段
    def getAttribute(self):
        if not self._table:
            return None
        if self._table_columns:
            return {'columns':self._table_columns, 'columns_data':None, 'pk_name':self._pk_name[0]}
        query = """
            SELECT
                `COLUMN_NAME`,
                `DATA_TYPE`,
                `CHARACTER_MAXIMUM_LENGTH`,
                `NUMERIC_PRECISION`,
                `COLUMN_KEY`
            FROM
                `information_schema`.`columns`
            WHERE
                `TABLE_SCHEMA` = "{dbName}"
                AND `TABLE_NAME` = "{tableName}"
		"""
        query = query.format(dbName=self.__db_name, tableName=self._table)
        columns = self.__db.query(query)
        if not columns:
			raise SimpleModelError('No columns found for table %s. Does this table exist?' % (self._table,))
        for column in columns:
			self._table_columns.append(column.get('COLUMN_NAME'))
			self._columns_data.append({
				'DATA_TYPE': column['DATA_TYPE'],
				'CHARACTER_MAXIMUM_LENGTH': column['CHARACTER_MAXIMUM_LENGTH']
			})
			if column.get('COLUMN_KEY') == 'PRI':
				self._pk_name.append(column.get('COLUMN_NAME'))
        return {'columns':self._table_columns, 'columns_data':self._columns_data, 'pk_name':self._pk_name}

    def validateData(self, data):
		types = {
			'char' : 'string',
			'varchar' : 'string',
			'text' : 'string',
			'tinytext' : 'string',
			'mediumtext' : 'string',
			'longtext' : 'string',
			'int' : 'int',
			'tinyint' : 'int',
			'smallint' : 'int',
			'mediumint' : 'int',
			'bigint' : 'int',
			'float' : 'float',
			'decimal' : 'float',
			'double' : 'float',
			'real' : 'real'
		}
		for key, value in data.items():
			if key not in self._table_columns or key in self._exclude_columns:
				del data[key]
				continue
			columnKey = self._table_columns.index(key)
			if not value:
				continue
			elif types.get(self._columns_data[columnKey].get('DATA_TYPE')):
				type = types.get(self._columns_data[columnKey].get('DATA_TYPE'))
			else:
				type = 'string'

			if type == 'string' and isinstance(value, basestring):
				continue
			elif type == 'int' and isinstance(value, (int, long)):
				continue
			elif type == 'float' and isinstance(value, (float)):
				continue
			elif type == 'real' and isinstance(value, (int, long, float)):
				continue
			else:
				raise RecordError('Data type of field "{column}" does not match column data type in "{tableName}" table.'.format(tableName=self._table, column=key))
		return data

    def save(self, res=False):
        limit = ''
        where = ''
        valueToString = []
        insertOrUpdate = ''
        if len(self._pk_name) > 1:
            insertOrUpdate = 'REPLACE INTO'
        elif len(self._pk_name) and self._properties.get(self._pk_name[0]):
            insertOrUpdate = 'UPDATE'
            limit = 'LIMIT 1'
            where = 'WHERE `{column}` = %s'.format(
                    column = self._pk_name[0]
				)
        else:
            insertOrUpdate = 'INSERT INTO'

        if len(self._pk_name) == 1:
			self.excludeColumns(self._pk_name[0])
        columnsToStringTmp = []
        for k,v in self._properties.items():
            if k not in self._exclude_columns:
                columnsToStringTmp.append( '`'+k+'` = %s')
                valueToString.append(v)
        columnsToString = ','.join(columnsToStringTmp)
        if where:
            valueToString.append(self._properties.get(self.pk_name[0]))
        query = """
            {insertOrUpdate} `{dbName}`.`{tableName}`
            SET
                {columns}
            {where}
            {limit}
            """
        query = query.format(
                insertOrUpdate 	= insertOrUpdate,
                dbName 			= self._db_name,
                tableName 		= self._table,
                columns 		= columnsToString,
                where 			= where,
                limit 			= limit
			)
        last_id = self.__db.execute(str(query), *tuple(valueToString))
        if not res:
            return last_id
        self._exclude_columns = []
        _filters = {}
        if len(self._pk_name) == 1:
			_filters.append({self._pk_name[0]: last_id})
        else:
			for pk in self._pk_name:
				_filters.append({pk: self._properties.get(pk)})
        self.setColumnProperties(self.queryOne(_filters, self._properties.items()))

    def new(self, item):
        obj = self.initialize(item)
        if obj:
            return self.save()
        return None

    #通过主键删除信息
    def deleteByPK(self, pk=[]):
        if (not self._pk_name[0]):
            raise RecordError('This table has compound primary key but one or more it\'s values are not set')
        args = []
        where = ' 1=1 '
        for item in pk:
            for i in self._pk_name:
                if not i in item:
                     raise RecordError('pk error')
            args.append(item[1])
            where = 'AND %s=%s' % (item[0], item[1])
        query = """
                DELETE FROM `{dbName}`.`{tableName}`
                WHERE
                    {where}
                """
        query = query.format(
			dbName 		= self._db_name,
			tableName 	= self._table,
			where 		= where
			)
        self.__db.execute_rowcount(query, *tuple(args))

    #通过条件删除数据
    def deleteByCondition(self, filterString=[]):
        if not filterString:
            raise RecordError('参数为空')
        conds,vals = self.conditionStr(filterString)
        sql = "DELETE FROM `%s`.`%s` WHERE %s" % (self._db_name, self._table, conds)
        return self.__db.execute(sql, *tuple(vals))

    def excludeColumns(self, toExclude):
		self._exclude_columns.append(toExclude)

    def setColumnProperties(self, data):
        if not self._table_columns:
            self.getAttribute()
        data = self.validateData(data)
        for key, value in data.items():
            self._properties[key] = value

    #获取表总数
    def getCount(self, filterString=[]):
        if not filterString:
            raise RecordError('not exist filterString')
        conds, vals = self.conditionStr(filterString)
        count_sql = """
                        SELECT COUNT(1) AS total FROM `{dbName}`.`{tableName}` {filters} LIMIT 1;
                    """
        count_sql = count_sql.format(
            dbName=self._db_name,
            tableName=self._table,
            filters=' WHERE '+conds if conds else '',
        )
        res = self.__db.get(count_sql, *tuple(vals))
        print res
        print 'resresresres'
        return res['total']

    #通过主键获取一条信息
    def queryOne(self, filterString=[], fields=[], orderBy=[]):
        if not filterString:
            raise RecordError('not exist filterString')
        conds, vals = self.conditionStr(filterString)
        query = """
                    SELECT
                        {fields}
                    FROM `{dbName}`.`{tableName}`
                       {filters}
                       {orderBy}
                       LIMIT 1;
                    """
        orders = ''
        if orderBy:
            for o in orderBy:
                orders += o[0]+' '+o[1]+','
            orders = orders[0:-1]

        query = query.format(
            fields= ','.join([v for v in fields]) if fields else '*',
            dbName=self._db_name,
            tableName=self._table,
            filters=' WHERE '+conds if conds else '',
            orderBy = ' ORDER BY %s '% (orders) if orders else ' ORDER BY '+self._pk_name[0]+' DESC'
        )
        return self.__db.get(query, *tuple(vals))

    def queryBySql(self, sql, *vals):
        if not sql:
            raise RecordError('not exist sql')
        return self.__db.query(sql, *vals)

    #通过条件获取多条信息
    def queryMany(self, filterString=[], fields=[], orderBy=[], limit=None, pageNo=None):
        conds, vals = self.conditionStr(filterString)
        query = """SELECT {fields} FROM `{dbName}`.`{tableName}` {filters} {orderBy} {limit};"""
        offset = (int(pageNo)-1)*int(limit) if limit and pageNo else ""
        orders = ""
        if orderBy:
            for o in orderBy:
                orders += o[0]+" "+o[1]+","
            orders = orders[0:-1]
        query = query.format(
            fields = ",".join(fields) if fields else ",".join(self._table_columns),
            dbName = self._db_name,
            tableName = self._table,
            filters = " WHERE "+conds if conds else "",
            orderBy = " ORDER BY %s " % (orders) if orders else " ORDER BY "+self._pk_name[0]+" DESC",
            limit = " LIMIT %s, %s " % (offset, limit) if limit and pageNo else ""
        )
        self.showSQL(query, tuple(vals), True)
        return self.__db.query(query, *tuple(vals))

    #通过条件修改数据
    def updateInfo(self, filterString=[], where=[]):
        if (not filterString) or (not where):
            raise RecordError('not exist filterString or where')
        filters = ','.join(['`%s` = %s' % (item[0], '%s') for item in filterString])
        wheres, vals = self.conditionStr(where)
        query = """
                    UPDATE
                     `{dbName}`.`{tableName}`
                     SET {fields}
                    WHERE
                       {filters};
                    """
        query = query.format(
            dbName = self._db_name,
            tableName = self._table,
            fields = filters,
            filters = wheres
        )
        tmp = []
        for item in filterString:
            tmp.append(item[1])
        tmp = tmp + vals
        #self.showSQL(query, tuple(tmp), True)
        return self.__db.execute_rowcount(query, *tuple(tmp))

    #返回条件语句
    def conditionStr(self, where):
        if not where:
            return '', []
        wheres = "1=1 "
        vals = []
        for item in where:
            if isinstance(item[1], tuple):
                if 'in' in item[1]:
                    l = len(item[1][1])
                    fields = ''
                    for i in range(0, l):
                        fields += '%s,'
                    fields = fields[0: len(fields)-1]
                    wheres += " AND ({str1} IN ({str2})) ".format(str1=item[0], str2=fields)
                    for i in item[1][1]:
                        vals.append(i)
                elif 'or'==item[1][0]:
                    wheres += " OR (%s=%s) " % (item[0], '%s')
                    vals.append(item[1][1])
                elif '>'==item[1][0]:
                    wheres += " AND (%s>%s) " % (item[0], '%s')
                    vals.append(item[1][1])
                elif '<'==item[1][0]:
                    wheres += " AND (%s<%s) " % (item[0], '%s')
                    vals.append(item[1][1])
                elif '<>'==item[1][0]:
                    wheres += " AND (%s<>%s) " % (item[0], '%s')
                    vals.append(item[1][1])
                elif 'like'==item[1][0]:
                    wheres += " AND (%s like %%s) " % (item[0])
                    vals.append(item[1][1])
                elif 'regexp'==item[1][0]:
                    wheres += " AND (%s REGEXP %%s) " % (item[0])
                    vals.append(item[1][1])
                else:
                    wheres += " AND (%s=%s)" % (item[0], '%s')
                    vals.append(item[1])
            else:
                wheres += " AND (%s=%s)" % (item[0], '%s')
                vals.append(item[1])
        return wheres, vals

    #多条数据保存
    def saveMany(self, lists=[]):
        if not lists:
            raise RecordError('参数为空')
        if hasattr(self, '_table_columns_rule'):
            for item in lists:
                for key in item:
                    if self._table_columns_rule.has_key(key):
                        rules = self._table_columns_rule[key]
                        if not checkColumnRules(rules, item[key]):
                            return False
        for i in range(len(lists)):
            keys = lists[i].keys()
            for k in keys:
                if k not in self._table_columns:
                    del lists[i][k]
                else:
                    if hasattr(self, '_table_columns_autoload'):
                        for (autoload_key, autoload_val) in self._table_columns_autoload.items():
                            if autoload_key not in keys:
                                lists[i][autoload_key] = autoload_val
        vals = []
        keys_placeholder = []
        fields = []
        if isinstance(lists[0], dict):
            fields = lists[0].keys()
            for i in xrange(len(fields)):
                keys_placeholder.append('%s')
        else:
            raise RecordError('参数错误')

        for item in lists:
            if isinstance(item, dict):
                tmp_vals = []
                for key in fields:
                    tmp_vals.append(item[key])
                vals.append(tuple(tmp_vals))
        sql = "INSERT INTO `%s`.`%s` (%s) VALUES (%s)" % (self._db_name, self._table, ','.join(fields), ','.join(keys_placeholder))
        return self.__db.executemany(sql, tuple(vals))

    #保存一条数据
    def _saveOne(self, item={}):
        if not item:
            raise RecordError('参数为空')
        keys = []
        vals = []
        keys_placeholder = []
        for k,v in item.items():
            keys.append(k)
            vals.append(v)
            keys_placeholder.append('%s')
        sql = "INSERT INTO `%s`.`%s` (%s) VALUES (%s)" % (self._db_name, self._table, ','.join(keys), ','.join(keys_placeholder))
        print self.showSQL(sql, tuple(vals), True)
        return self.__db.execute(sql, *tuple(vals))

    def saveOne(self, item={}):
        if (not item) or (not isinstance(item, dict)):
            raise ArgumentError("参数错误")
        if hasattr(self, '_table_columns_rule'):
            for key in item:
                if self._table_columns_rule.has_key(key):
                    rules = self._table_columns_rule[key]
                    res = checkColumnRules(rules, item[key])
                    if res==False:
                        return False
        keys = item.keys()
        for k in keys:
            if k not in self._table_columns:
                del item[k]
        if hasattr(self, '_table_columns_autoload'):
            for (autoload_key, autoload_val) in self._table_columns_autoload.items():
                if autoload_key not in keys:
                    item[autoload_key] = autoload_val
        return self._saveOne(item)

    #执行sql语句 查询语句
    def querySQL(self, sql, *args):
        #self.showSQL(sql, list(args))
        return self.__db.query(sql, *args)

    def queryOneSQL(self, sql, *args):
        return self.__db.get(sql, *args)

    #执行语句 update delete insert
    def executeSQL(self, sql, *args):
        return self.__db.execute(sql, *args)

    def runSQL4RowCount(self, sql, *args):
        return self.__db.execute_rowcount(sql, *args)

    #初始化类对象 赋予对象属性 _properties赋值
    def initialize(self, item):
        if not item:
            return None
        attrs = self.getAttribute()
        for attr in attrs['columns']:
            setattr(self, attr, None)
        self.setColumnProperties(item)
        return self

    #设置主键字段
    def setPK(self, pk):
        if not pk:
            raise RecordError('参数为空')
        else:
            self._pk_name.append(pk)

    #显示sql日志
    def showSQL(self, sql, vals, flag=False):
        if flag or self._debug:
            print sql % vals

    def getExecutedSQL(self):
        return self.__db._cursor()._executed

    # def getLastSQL(self):
    #     return self.__db._cursor()._last_executed

    #事务
    def startCommit(self):
        self.__db


class SimpleModelError(Exception):
	pass
class RecordError(Exception):
	pass
