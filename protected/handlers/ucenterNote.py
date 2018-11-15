# -*- coding: utf-8 -*-
import logging
from tornado.options import options
from tornado.web import asynchronous, HTTPError, StaticFileHandler
from tornado import gen, httpclient, escape
from handler import BaseHandler, unblock, userAuthenticated
from protected.models.user import User
from protected.models.userNewsfeed import UserNote, userNoteComment
from protected.models.tags import Tags
import protected.libs.utils as utiles
from protected.libs.const import ErrorMessage, SuccessMessage
from protected.libs.tempFileManger import TempFileManager
from protected.libs.badwordfilter import DictFilter
from protected.libs.limitOperation import limitCaptcha, checkNeedCaptcha, rateLimited, delayPostLimit
from protected.libs.pagenation import Page
import sys, time, re, urlparse, uuid, os, datetime, re, math, io, json

script_re = re.compile(r'<script[\s\S]+</script *>')
style_re = re.compile(r'<style[\s\S]+</style *>')
head_re = re.compile(r'<head [^>]>.*</head>(?im)')
src_re = re.compile(r'<img.+src="(.*?)"', re.I)
FILTERS = frozenset((script_re, style_re, head_re))

class IndexHandler(BaseHandler):
    #@unblock
    @gen.coroutine
    def get(self):
        user_info = self.get_current_user()
        if not user_info:
            self.render('not_found.html')
        #获取标签列表
        tag_obj = Tags()
        tags = tag_obj.getAllTagsByType(1)
        self._context.tags = tags

        self._context.selected_menu = 'note'
        self.render('ucenter/index.html')

    @gen.coroutine
    def post(self):
        uid = self.get_current_user(info=False)
        if not uid:
            self.return_json_by_num('037')
        is_open = self.get_argument('is_open', 1)
        is_comment = self.get_argument('is_comment', 1)
        tags = self.get_argument('tags', None)
        content = self.get_argument('content', '')
        title = self.get_argument('title', '')
        if not title:
            self.return_json_by_num('055')
        if not content:
            self.return_json_by_num('056')

        #过滤content中的js标签
        for regex in FILTERS:
            content = regex.sub(u'', content)
        #过滤非法字符
        filter_obj = DictFilter()
        new_content, bad_words = filter_obj.match_all(content)
        if bad_words:
            self.return_json_by_num('057')

        #替换图片
        src_list = src_re.findall(new_content)
        for src_item in src_list:
            if re.match('/ucenter/noteimgtmp/', src_item):
                temp_name = src_item.split('/').pop()
                real_name, real_file_path = TempFileManager.moveTempFileToRealDir(self.settings['uploads_path'], UserNote.ucenter_note_img, temp_name)
                if real_file_path:
                    new_content = new_content.replace(src_item, '/ucenter/noteimg/'+temp_name)

        item = {'uid': uid,
                'title': title,
                'content': new_content,
                'tags':tags.split(','),
                'is_comment': is_comment,
                'is_open': is_open,
                'create_uid': uid}
        note_obj = UserNote()
        res = yield note_obj.saveNote(item)
        if res:
            self.return_json({'code': 'success', 'res':res}, finish=True)
        else:
            self.return_json_by_num('048')
            return

'''
日志列表
'''
class ListHandler(BaseHandler):
    def get(self):
        uid = self.get_current_user(info=False)
        if not uid:
            self.render('not_found.html')
'''
预览
'''
class PreviewHandler(BaseHandler):

    NOTE_COMMENT_KEY = 'note_comment'

    def get(self):
        uid = self.get_current_user(info=False)
        self._context.uid = uid
        self._context.selected_menu = 'preview_note'
        if checkNeedCaptcha(self.NOTE_COMMENT_KEY, uid):
            self._context.is_need_captcha = 1
        else:
            self._context.is_need_captcha = None
        #获取日志的评论信息列表
        comment_obj = userNoteComment()

        self.render('ucenter/index.html')

    def post(self):
        uid = self.get_current_user(info=False)
        if not uid:
            self.render('not_found.html')
        content = self.get_argument('content', '')
        title = self.get_argument('title', '')
        if not title:
            self.return_json_by_num('055')
        if not content:
            self.return_json_by_num('056')

        self._context.content = content
        self._context.selected_menu = 'preview_note'
        self.render('ucenter/index.html')

class UploadImgHandler(BaseHandler):
    image_max_size = 2048000

    def post(self):
        uid = self.get_current_user(info=False)
        if not uid:
            self.return_json_by_num('041')
            return
        if self.request.files:
            note_img = self.request.files['note_img'][0]
            if utiles.checkFileType('img', note_img['content_type']):
                if len(note_img['body']) > self.image_max_size:
                    self.return_json_by_num('050')
                    return
                #生成临时存储路径
                temp_file_dir, temp_file_name = TempFileManager.getTempFileDir(self.settings['uploads_path'], UserNote.ucenter_note_img, note_img['filename'], uid)
                with open(temp_file_dir, 'wb') as up:
                    up.write(note_img['body'])
                self.return_json({'res': {'id': str(uuid.uuid4()), 'url': '/ucenter/noteimgtmp/'+temp_file_name, 'filename': temp_file_name}, 'code': 'success'}, finish=True)
                return
            else:
                self.return_json_by_num('051')
                return

class DeleteImgHandler(BaseHandler):
    @userAuthenticated
    def post(self):
        url = self.get_argument('url', '')
        if not url:
            self.return_json_by_num('058')
            return
        filename = url.split('/').pop()
        sep = os.path.sep
        tmp_url = self.settings['uploads_path'] + sep + UserNote.ucenter_note_img + sep + 'tmp' + sep
        if not os.path.isdir(tmp_url):
            self.return_json_by_num('058')
            return
        if os.path.isfile(tmp_url+filename):
            os.remove(tmp_url+filename)
            self.return_json({'code': 'success'}, finish=True)
        else:
            self.return_json_by_num('058')
        return

handlers = [
    (r"/ucenter/note", IndexHandler),
    (r"/ucenter/previewnote", PreviewHandler),
    (r"/ucenter/notelist", ListHandler),
    (r"/ucenter/uploadimg", UploadImgHandler),
    (r"/ucenter/deleteimg", DeleteImgHandler),
    (r"/ucenter/js/(.*)", StaticFileHandler, {"path": "templates/ucenter/js"}),
    (r"/ucenter/noteimgtmp/(.*)", StaticFileHandler, {"path": "uploads/"+UserNote.ucenter_note_img+'/tmp'}),
    (r"/ucenter/noteimg/(.*)", StaticFileHandler, {"path": "uploads/"+UserNote.ucenter_note_img}),
]