# -*- coding: utf-8 -*-
import time, os
import hashlib

class TempFileManager(object):
    @staticmethod
    #生成临时存储路径
    def getTempFileDir(uploads_path, temp_name, filename, uid):
        uid = str(uid)
        sep = os.path.sep
        temp_name = temp_name + sep + 'tmp'
        temp_upload_url = uploads_path + sep + temp_name
        if not os.path.isdir(temp_upload_url):
            os.makedirs(temp_upload_url)
        dstname = hashlib.md5(filename.split('.')[0] + '_' + uid + '_' + str(int(time.time()))).hexdigest()+'.'+filename.split('.').pop()
        return os.path.join(temp_upload_url, dstname), dstname

    '''
    uploads_path: 服务器文件地址
    dir_name: 模块保存图片文件的名称
    temp_filename: 临时性文件名称
    '''
    @staticmethod
    def moveTempFileToRealDir(uploads_path, dir_name, temp_filename, type='week'):
        sep = os.path.sep
        temp_upload_file_url = uploads_path + sep + dir_name + sep + 'tmp' + sep + temp_filename
        if not os.path.isfile(temp_upload_file_url):
            return False, False
        today_date = time.localtime()
        #按照年月周的方式存储路径
        if type=='week':
            today_year_month_str = '%s-%02d-w%s' % (today_date.tm_year, int(today_date.tm_mon), time.strftime("%W"))
        elif type=='day':
            today_year_month_str = time.strftime("%Y-%m-d%d", time.localtime())
        elif type=='month':
            today_year_month_str = time.strftime("%Y-%m", time.localtime())
        real_path = uploads_path + sep + dir_name + sep + today_year_month_str + sep
        if not os.path.isdir(real_path):
           os.makedirs(real_path)
        real_file_path = real_path + temp_filename
        os.rename(temp_upload_file_url, real_file_path)
        return today_year_month_str + sep + temp_filename, real_file_path
