# -*- coding: utf8 -*-
from protected.models.admin.AdminBaseModel import AdminBaseModel
from protected.libs.exceptions import ArgumentError, BaseError
import sys,os,time,shutil
from tornado.options import options

class CmsAttachment(AdminBaseModel):
    def __init__(self):
        self._table  = 'cms_attachment'
        self.setPK('id')
        self._table_columns = ['id', 'create_time', 'content_id', 'filename', 'bytesize', 'url']
        super(CmsAttachment, self).__init__()

    #通过内容id获取详情
    def getInfoByContentId(self, content_id):
        return self.queryOne([('content_id',content_id)], self._table_columns)

    def deleteTmpFileByName(self, name):
        file = os.path.join(os.path.join(os.path.dirname(__file__), '../../../static/attachment/tmp/'), name)
        if os.path.isfile(file):
            os.remove(file)

    def moveTmpFileToFolder(self, file_name, node_id):
        file = os.path.join(os.path.join(os.path.dirname(__file__), '../../../static/attachment/tmp/'), file_name)
        if os.path.isfile(file):
            cms_attachment_folder = os.path.join(os.path.dirname(__file__), '../../../static/attachment/cms/')
            if not os.path.exists(cms_attachment_folder):
                os.makedirs(cms_attachment_folder)
            this_month = time.strftime('%Y-%m', time.localtime(time.time()))
            new_file_name = this_month+'_'+node_id+'_'+file_name
            cms_file_folder = os.path.join(cms_attachment_folder, new_file_name)
            shutil.move(file, cms_file_folder)
            new_file_size = os.path.getsize(cms_file_folder)
            return '/static/attachment/cms/'+new_file_name, new_file_name, new_file_size
        return False, False, False

    #删除表数据和文件
    def deleteFileByFileIds(self, delete_file_ids):
        if not delete_file_ids:
            raise ArgumentError("参数错误")
        if len(delete_file_ids)==1:
            list = self.queryMany(filterString=[('id', delete_file_ids)], fields=self._table_columns)
        else:
            list = self.queryMany(filterString=[('id', ('in', delete_file_ids))], fields=self._table_columns)
        if list:
            for item in list:
                #删除指定文件
                if item['url']!=0:
                    file_url = os.path.join(os.path.dirname(__file__), '../../../'+item['url'])
                    if os.path.isfile(file_url):
                        os.remove(file_url)
            if len(delete_file_ids)==1:
                res = self.deleteByCondition(filterString=[('id', delete_file_ids)])
            else:
                res = self.deleteByCondition(filterString=[('id', ('in', delete_file_ids))])
            if not res:
                return False
            else:
                return True
        else:
            return True