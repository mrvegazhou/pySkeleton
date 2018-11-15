# -*- coding: utf-8 -*-
from tornado.web import asynchronous, HTTPError, StaticFileHandler
from tornado import escape
from tornado.options import options
from tornado import gen
from tornado.ioloop import IOLoop
from tornado.escape import json_encode
from handler import BaseHandler
import sys, time, hashlib, re, urlparse, uuid, os, datetime, base64
import protected.libs.utils as utiles

UEDITOR = {
    #/* 上传图片配置项 */
    "imageActionName": "uploadimage", #/* 执行上传图片的action名称 */
    "imageFieldName": "upfile", #/* 提交的图片表单名称 */
    "imageMaxSize": 2048000, #/* 上传大小限制，单位B */
    "imageAllowFiles": [".png", ".jpg", ".jpeg", ".gif", ".bmp"], #/* 上传图片格式显示 */
    "imageCompressEnable": True, #/* 是否压缩图片,默认是true */
    "imageCompressBorder": 1600, #/* 图片压缩最长边限制 */
    "imageInsertAlign": "none", #/* 插入的图片浮动方式 */
    "imageUrlPrefix": "", #/* 图片访问路径前缀 */
    "imagePathFormat": "/ueditor/php/upload/image/{yyyy}{mm}{dd}/{time}{rand:6}", #/* 上传保存路径,可以自定义保存路径和文件名格式 */
                                #/* {filename} 会替换成原文件名,配置这项需要注意中文乱码问题 */
                                #/* {rand:6} 会替换成随机数,后面的数字是随机数的位数 */
                                #/* {time} 会替换成时间戳 */
                                #/* {yyyy} 会替换成四位年份 */
                                #/* {yy} 会替换成两位年份 */
                                #/* {mm} 会替换成两位月份 */
                                #/* {dd} 会替换成两位日期 */
                                #/* {hh} 会替换成两位小时 */
                                #/* {ii} 会替换成两位分钟 */
                                #/* {ss} 会替换成两位秒 */
                                #/* 非法字符 \ : * ? " < > | */
                                #/* 具请体看线上文档: fex.baidu.com/ueditor/#use-format_upload_filename */

    #/* 涂鸦图片上传配置项 */
    "scrawlActionName": "uploadscrawl", #/* 执行上传涂鸦的action名称 */
    "scrawlFieldName": "upfile", #/* 提交的图片表单名称 */
    "scrawlPathFormat": "/ueditor/php/upload/image/{yyyy}{mm}{dd}/{time}{rand:6}", #/* 上传保存路径,可以自定义保存路径和文件名格式 */
    "scrawlMaxSize": 2048000, #/* 上传大小限制，单位B */
    "scrawlUrlPrefix": "", #/* 图片访问路径前缀 */
    "scrawlInsertAlign": "none",

    #/* 截图工具上传 */
    "snapscreenActionName": "uploadimage", #/* 执行上传截图的action名称 */
    "snapscreenPathFormat": "/ueditor/php/upload/image/{yyyy}{mm}{dd}/{time}{rand:6}", #/* 上传保存路径,可以自定义保存路径和文件名格式 */
    "snapscreenUrlPrefix": "", #/* 图片访问路径前缀 */
    "snapscreenInsertAlign": "none", #/* 插入的图片浮动方式 */

    #/* 抓取远程图片配置 */
    "catcherLocalDomain": ["127.0.0.1", "localhost", "img.baidu.com"],
    "catcherActionName": "catchimage", #/* 执行抓取远程图片的action名称 */
    "catcherFieldName": "source", #/* 提交的图片列表表单名称 */
    "catcherPathFormat": "/uploads/ueditor/image/{yyyy}{mm}{dd}/{time}{rand:6}", #/* 上传保存路径,可以自定义保存路径和文件名格式 */
    "catcherUrlPrefix": "", #/* 图片访问路径前缀 */
    "catcherMaxSize": 2048000, #/* 上传大小限制，单位B */
    "catcherAllowFiles": [".png", ".jpg", ".jpeg", ".gif", ".bmp"], #/* 抓取图片格式显示 */

    #/* 上传视频配置 */
    "videoActionName": "uploadvideo", #/* 执行上传视频的action名称 */
    "videoFieldName": "upfile", #/* 提交的视频表单名称 */
    "videoPathFormat": "/uploads/ueditor/video/{yyyy}{mm}{dd}/{time}{rand:6}", #/* 上传保存路径,可以自定义保存路径和文件名格式 */
    "videoUrlPrefix": "", #/* 视频访问路径前缀 */
    "videoMaxSize": 102400000, #/* 上传大小限制，单位B，默认100MB */
    "videoAllowFiles": [
        ".flv", ".swf", ".mkv", ".avi", ".rm", ".rmvb", ".mpeg", ".mpg",
        ".ogg", ".ogv", ".mov", ".wmv", ".mp4", ".webm", ".mp3", ".wav", ".mid"], #/* 上传视频格式显示 */

    #/* 上传文件配置 */
    "fileActionName": "uploadfile", #/* controller里,执行上传视频的action名称 */
    "fileFieldName": "upfile", #/* 提交的文件表单名称 */
    "filePathFormat": "/uploads/ueditor/file/{yyyy}{mm}{dd}/{time}{rand:6}", #/* 上传保存路径,可以自定义保存路径和文件名格式 */
    "fileUrlPrefix": "", #/* 文件访问路径前缀 */
    "fileMaxSize": 51200000, #/* 上传大小限制，单位B，默认50MB */
    "fileAllowFiles": [
        ".png", ".jpg", ".jpeg", ".gif", ".bmp",
        ".flv", ".swf", ".mkv", ".avi", ".rm", ".rmvb", ".mpeg", ".mpg",
        ".ogg", ".ogv", ".mov", ".wmv", ".mp4", ".webm", ".mp3", ".wav", ".mid",
        ".rar", ".zip", ".tar", ".gz", ".7z", ".bz2", ".cab", ".iso",
        ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".pdf", ".txt", ".md", ".xml"
    ], #/* 上传文件格式显示 */

    #/* 列出指定目录下的图片 */
    "imageManagerActionName": "listimage", #/* 执行图片管理的action名称 */
    "imageManagerListPath": "/uploads/ueditor/image/", #/* 指定要列出图片的目录 */
    "imageManagerListSize": 20, #/* 每次列出文件数量 */
    "imageManagerUrlPrefix": "", #/* 图片访问路径前缀 */
    "imageManagerInsertAlign": "none", #/* 插入的图片浮动方式 */
    "imageManagerAllowFiles": [".png", ".jpg", ".jpeg", ".gif", ".bmp"], #/* 列出的文件类型 */

    #/* 列出指定目录下的文件 */
    "fileManagerActionName": "listfile", #/* 执行文件管理的action名称 */
    "fileManagerListPath": "/uploads/ueditor/file/", #/* 指定要列出文件的目录 */
    "fileManagerUrlPrefix": "", #/* 文件访问路径前缀 */
    "fileManagerListSize": 20, #/* 每次列出文件数量 */
    "fileManagerAllowFiles": [
        ".png", ".jpg", ".jpeg", ".gif", ".bmp",
        ".flv", ".swf", ".mkv", ".avi", ".rm", ".rmvb", ".mpeg", ".mpg",
        ".ogg", ".ogv", ".mov", ".wmv", ".mp4", ".webm", ".mp3", ".wav", ".mid",
        ".rar", ".zip", ".tar", ".gz", ".7z", ".bz2", ".cab", ".iso",
        ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".pdf", ".txt", ".md", ".xml"
    ] #/* 列出的文件类型 */

}
UPLOAD_RES = {
        "SUCCESS" : "SUCCESS",
        "ERROR_FILESIZE" : "文件大小超出 upload_max_filesize 限制",
        "ERROR_MAX_FILE_SIZE" : "文件大小超出 MAX_FILE_SIZE 限制",
        "ERROR_NOT_COMPLETE_UPLOAD" : "文件未被完整上传",
        "ERROR_NOT_UPLOAD" : "没有文件被上传",
        "ERROR_NOT_FILE" : "上传文件为空",
        "ERROR_TMP_FILE" : "临时文件错误",
        "ERROR_TMP_FILE_NOT_FOUND" : "找不到临时文件",
        "ERROR_SIZE_EXCEED" : "文件大小超出网站限制",
        "ERROR_TYPE_NOT_ALLOWED" : "文件类型不允许",
        "ERROR_CREATE_DIR" : "目录创建失败",
        "ERROR_DIR_NOT_WRITEABLE" : "目录没有写权限",
        "ERROR_FILE_MOVE" : "文件保存时出错",
        "ERROR_FILE_NOT_FOUND" : "找不到上传文件",
        "ERROR_WRITE_CONTENT" : "写入文件内容错误",
        "ERROR_UNKNOWN" : "未知错误",
        "ERROR_DEAD_LINK" : "链接不可用",
        "ERROR_HTTP_LINK" : "链接不是http链接",
        "ERROR_HTTP_CONTENTTYPE" : "链接contentType不正确",
        "INVALID_URL" : "非法 URL",
        "INVALID_IP" : "非法 IP"
}
#上传地址
def setUrl(req, str_date):
    upload_url = req.settings['uploads_path'] + os.path.sep + 'ueditor' + os.path.sep + 'tmp' + os.path.sep + str_date
    if not os.path.isdir(upload_url):
        os.makedirs(upload_url)
    return upload_url

def uploadScrawl(req):
    str_date = str(datetime.date.today())
    scrawl = base64.decodestring(req.get_argument('upfile', ''))
    if scrawl:
        if len(scrawl) > UEDITOR['scrawlMaxSize']:
            req.write({'state': UPLOAD_RES['ERROR_MAX_FILE_SIZE']})
        dstname = 'scrawl_'+str(int(time.time()))+'.png'
        filepath = os.path.join(setUrl(req, str_date), dstname)
        with open(filepath, 'wb') as up:
            up.write(scrawl)
        req.write({'state':UPLOAD_RES['SUCCESS'], 'url': '/server/uploads/'+str_date+'/'+dstname})

def uploadImage(req, post_name, file_type):
    res = None
    str_date = str(datetime.date.today())
    if req.request.files:
        for f in req.request.files[post_name]:
            if len(f['body']) > UEDITOR['imageMaxSize']:
                res = UPLOAD_RES['ERROR_MAX_FILE_SIZE']
                req.write({'state':res})
            if utiles.checkFileType(file_type, f['content_type']):
                filename = f['filename']
                dstname = filename.split('.')[0] + '_' + str(int(time.time()))+'.'+filename.split('.').pop()
                filepath = os.path.join(setUrl(req, str_date), dstname)
                with open(filepath, 'wb') as up:
                    up.write(f['body'])
                res = UPLOAD_RES['SUCCESS']
            else:
                res = UPLOAD_RES['ERROR_TYPE_NOT_ALLOWED']
                req.write({'state':res})
        req.write({'state':res, 'url': '/server/uploads/tmp/'+str_date+'/'+dstname})

class RichEditorHandler(BaseHandler):
    def post(self):
        action = self.get_argument('action', '')
        #配置文件
        if action=='config':
            self.return_json(UEDITOR)
        #上传涂鸦
        elif action=='uploadscrawl':
            uploadScrawl(self)
        #上传照片
        elif action=='uploadimage':
            uploadImage(self, 'upfile', 'img')
        elif action=='':
            pass
        else:
            pass
    def get(self):
        action = self.get_argument('action', '')
        #配置文件
        if action=='config':
            self.return_json(UEDITOR)
        return

handlers = [
    (r"/server/editor", RichEditorHandler),
    (r"/server/uploads/(.*)", StaticFileHandler, {"path": "uploads/ueditor"}),
]