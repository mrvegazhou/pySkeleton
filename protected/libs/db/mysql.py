from tornado.options import options
from tornado.ioloop import PeriodicCallback
from torndb import Connection
import MySQLdb
import threading

class MysqlConn(Connection):
    database = options.mysql["database"]
    def __DBUtilInit(self):
        self.host = options.mysql["host"] + ":" + options.mysql["port"]
        self.database = self.database
        self.user = options.mysql["user"]
        self.password = options.mysql["password"]
        super(MysqlConn, self).__init__(host=self.host, database=self.database, user=self.user, password=self.password)

    __instance = None
    __lock = threading.Lock()

    def __new__(cls, *args, **kargs):
        if not cls.__instance:
            cls.__instance = MysqlConn.getInstance()
        return cls.__instance

    @staticmethod
    def getInstance():
        if not MysqlConn.__instance:
            MysqlConn.__lock.acquire()
            if not MysqlConn.__instance:
                MysqlConn.__instance = Connection.__new__(MysqlConn)
                MysqlConn.__instance.__DBUtilInit()
            MysqlConn.__lock.release()
        return MysqlConn.__instance

    # def reconnect(self):
    #     """Closes the existing database connection and re-opens it."""
    #     self.close()
    #     try:
    #         from DBUtils import PooledDB
    #         pool_con = PooledDB.PooledDB(creator=MySQLdb, **self._db_args)
    #         self._db = pool_con.connection()
    #     except:
    #         self._db = MySQLdb.connect(**self._db_args)
    #         self._db.autocommit(True)


