import os
import sys
import mysql

def connetion(name, database):
    if name=="mysql":
        mysql.MysqlConn.database = database
        return mysql.MysqlConn.getInstance()
    elif name=="mongodb":
        return None
    else:
        return mysql.mysqlConn()

class _Connection(dict):
    def __init__(self):
        self["_db"] = {"mysql":None, "mongodb":None}

    def __getattr__(self, key):
        if key in self["_db"]:
            return self["_db"][key]
        else:
            raise AttributeError

    def __setattr__(self, key, value):
        if key in self["_db"]:
            self["_db"][key] = value
        else:
            raise AttributeError

conn = _Connection()