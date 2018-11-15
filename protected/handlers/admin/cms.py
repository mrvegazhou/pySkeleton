# -*- coding: utf-8 -*-
#分页工具
from protected.libs.pagenation import Pageset
from tornado.escape import json_decode
from tornado import gen, options
from protected.handlers.admin.handler import AdminBaseHandler, adminAuthenticated
from tornado.web import asynchronous, authenticated
from protected.models.admin.cmsNode import CmsNode
from protected.models.admin.cmsContent import CmsContent
from protected.models.admin.cmsAttachment import CmsAttachment
from protected.models.tags import Tags
import time,sys,os,datetime

class IndexHandler(AdminBaseHandler):
    cms = CmsNode()
    tag = Tags()
    limit = options.options.admin_config['page_limit']
    #@adminAuthenticated
    def get(self):
        self.render('admin/cms_node_list.html')

    def post(self):
        act = self.get_argument('act', 'list')
        now = time.localtime(time.time())
        if act=='list':
            page = self.get_argument('page', 1)
            search = self.get_argument('_search', '')
            if search=='true':
                filters = json_decode(self.get_argument('filters', ''))
            else:
                filters = []
            list = self.cms.getAllCmsNode(filters=filters, page=page, limit=self.limit, orderBy=('id', 'DESC'))
            for item in list:
                if item['tag_ids'] and item['tag_ids']!=0:
                    ids = item['tag_ids'].split(',')
                    tmp = self.tag.getTagsByIds(ids)
                    item['tag_names'] = ','.join([i['name'] for i in tmp])
                    item['tag_vals'] = self.json_encode([{'name':i['name'], 'id':i['id']} for i in tmp])
                else:
                    item['tag_names'] = '无'
                    item['tag_vals'] = []
                if item['delete_time'] and item['delete_time']!=0:
                    item['delete_time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(item['delete_time']))
                else:
                    item['delete_time'] = ''
            self.finish(self.write(self.json_encode(list)))
        elif act=='search_tags':
            limit = self.get_argument('limit', 10)
            if limit>10:
                limit = 10
            q = self.get_argument('q', '')
            tag_list = self.tag.getTagsBySearch(q, limit)
            self.finish(self.write(self.json_encode(tag_list)))
        elif act=='edit':
            post_data = self.get_argument('postData', '')
            item = json_decode(post_data)
            if not item['publish_time']:
                item['publish_time'] = time.strftime('%Y-%m-%d %H:%M:%S', now)
            else:
                item['publish_time'] = item['publish_time'][0:10] + time.strftime(' %H:%M:%S', now)
            item['create_time'] = time.strftime('%Y-%m-%d %H:%M:%S', now)
            item['type'] = 1
            item['tag_ids'] = item['tag_vals']
            res = self.cms.updateItem(item)
            if not res:
                ret = { 'msg': '修改失败', 'code':'007'}
            else:
                ret = { 'msg': '修改成功', 'code':'success'}
        elif act=='add':
            item = {}
            item['name'] = self.get_argument('name', '')
            item['status'] = self.get_argument('status', '')
            publish_time = self.get_argument('publish_time', '')
            if not publish_time:
                item['publish_time'] = time.strftime('%Y-%m-%d %H:%M:%S', now)
            else:
                tmp = publish_time[0:10].split('/')
                tmp = tmp[2]+'-'+tmp[0]+'-'+tmp[1]
                item['publish_time'] = tmp + time.strftime(' %H:%M:%S', now)
            item['tag_ids'] = self.get_argument('tag_ids', '')
            #item['delete_time'] = self.get_argument('delete_time', '0000-00-00 00:00:00')
            item['create_time'] = time.strftime('%Y-%m-%d %H:%M:%S', now)
            res = self.cms.addItem(item)
            if res:
                ret = { 'msg': '添加成功', 'code':'success'}
            else:
                ret = { 'msg': '添加失败', 'code':'006'}
            self.finish(self.write(self.json_encode(ret)))
        elif act=='delete':
            post_data = self.get_argument('postData', '')
            item = json_decode(post_data)
            res = self.cms.deleteByRowIds(item['id'].split(','))
            if not res:
                ret = { 'msg': res, 'code':'005'}
            else:
                ret = { 'msg': '删除成功', 'code':'success'}
            self.finish(self.write(self.json_encode(ret)))
        elif act=='delete-one':
            post_data = self.get_argument('postData', '')
            item = json_decode(post_data)
            res = self.cms.deleteByRowId(item['id'])
            if not res:
                ret = { 'msg': res, 'code':'005'}
            else:
                ret = { 'msg': '删除成功', 'code':'success'}
            self.finish(self.write(self.json_encode(ret)))

class CmsinfoHandler(AdminBaseHandler):
    cms = CmsNode()
    tag = Tags()
    content = CmsContent()
    attachment = CmsAttachment()
    @asynchronous
    def get(self):
        node_id = self.get_argument('node_id', '')
        if node_id:
            #获取文章详情
            info = self.content.getInfoByNodeId(node_id)
            if not info:
                self._context.info = {}
            else:
                info['content_id'] = info.pop('id')
                node_info = self.cms.getItem(node_id)
                node_info.update(info)
                if node_info['tag_ids']:
                    tags = self.tag.getTagsByIds(node_info['tag_ids'].split(','))
                    tags_tmp = []
                    for item in tags:
                        tags_tmp.append({'name':item['name'], 'id':item['id']})
                    node_info['tags'] = self.json_encode(tags_tmp)
                node_info['attachment'] = []
                if node_info['file_ids'] and node_info['file_ids']!='0':
                    for item in node_info['file_ids'].split(','):
                        file_info = self.attachment.getItem(item)
                        if file_info:
                            file_info['name'] = file_info['filename'].split('.')[0]
                            node_info['attachment'].append(file_info)
                self._context.info = node_info
        self.render('admin/cms_node_info.html')
        self.finish()
    @asynchronous
    def post(self):
        now = time.localtime(time.time())
        formate_time = time.strftime('%Y-%m-%d %H:%M:%S', now)
        node_id = self.get_argument('node_id', '')
        content_id = self.get_argument('content_id', '')
        node_name = self.get_argument('node_name', '')
        node_tag_ids = self.get_argument('tag_ids', '')
        node_status = self.get_argument('node_status', '0')
        node_publish_time = self.get_argument('node_publish_time', formate_time)
        page_title = self.get_argument('page_title', '')
        meta_title = self.get_argument('meta_title', '')
        meta_description = self.get_argument('meta_description', '')
        meta_keywords = self.get_argument('meta_keywords', '')
        node_content = self.get_argument('node_content', '')
        if not node_status:
            ret = { 'msg': '状态不能为空', 'code':'error'}
        if not page_title:
            ret = { 'msg': 'page_title不能为空', 'code':'error'}
        if not meta_title:
            ret = { 'msg': 'meta_title不能为空', 'code':'error'}
        if not node_content:
            ret = { 'msg': '编辑内容不能为空', 'code':'error'}
        if 'ret' in locals().keys():
            self.finish(self.write(self.json_encode(ret)))
        #判断是修改还是新增
        node_item = {
            'name':node_name,
            'create_time':formate_time,
            'publish_time':node_publish_time,
            'type':1,
            'tag_ids':node_tag_ids,
            'status':node_status
        }
        content_item = {
            'page_title':page_title,
            'meta_title':meta_title,
            'meta_description':meta_description,
            'meta_keywords':meta_keywords,
            'content':node_content
        }

        if node_id:
            #判断node是否存在
            cms_info = self.cms.getItem(node_id)
            if not cms_info:
                ret = { 'msg': 'cms_node不存在', 'code':'error'}
                self.finish(self.write(self.json_encode(ret)))
            #判断content_id是否存在库里
            old_content_files = ''
            if content_id:
                content_info = self.content.getItem(content_id)
                if content_info:
                    content_item['id'] = content_info['id']
                    old_content_files = content_info['file_ids']
                    content_item['node_id'] = node_id
                    content_res = self.content.updateInfoById(content_item)
                    if type(content_res)=='bool' and content_res==False:
                        ret = { 'msg': 'cms_content修改失败', 'code':'error'}
                        self.finish(self.write(self.json_encode(ret)))
                else:
                    ret = { 'msg': 'cms_content不存在', 'code':'error'}
                    self.finish(self.write(self.json_encode(ret)))
            else:
                content_item['node_id'] = node_id
                content_res = self.content.addItem(content_item)
                if not content_res:
                    ret = { 'msg': 'cms_content添加失败', 'code':'error'}
                    self.finish(self.write(self.json_encode(ret)))
        else:
            #添加node表
            res = self.cms.addItem(node_item)
            if not res:
                ret = { 'msg': 'cms_node添加失败', 'code':'error'}
                self.finish(self.write(self.json_encode(ret)))
            #添加content表
            content_item['node_id'] = res
            content_res = self.content.addItem(content_item)
            if not content_res:
                ret = { 'msg': 'cms_content添加失败', 'code':'error'}
                self.finish(self.write(self.json_encode(ret)))
        #处理附件
        imgs_url = self.get_argument('imgs_url', '')
        attachment_item = {
            'create_time':formate_time
        }
        if content_res==0:
            content_res = content_id
        imgs_url = imgs_url.split(',')
        imgs_tmp = ''
        for item in imgs_url:
            file_url, new_file_name, new_file_size = self.attachment.moveTmpFileToFolder(item, node_id)
            if file_url!=False:
                attachment_item['url'] = file_url
                attachment_item['content_id'] = content_res
                attachment_item['filename'] = new_file_name
                attachment_item['bytesize'] = new_file_size
                #保存附件表
                img_id = self.attachment.addItem(attachment_item)
                imgs_tmp += str(img_id)+','
        if imgs_tmp:
            imgs_tmp = imgs_tmp[0:len(imgs_tmp)-1]

        #修改文章中的附件信息
        delete_file_ids = self.get_argument('old_files_url', '')#获取需要删除的旧的附件id
        delete_file_ids = set(delete_file_ids.split(','))
        if delete_file_ids:
            old_content_files = set(old_content_files.split(','))#content表的file_ids内容
            #获取要删除的附件id
            old_tmp_files = delete_file_ids & old_content_files
            for i in old_tmp_files:
                old_content_files.remove(i)
            imgs_tmp = imgs_tmp+','.join(old_content_files) if imgs_tmp else ','.join(old_content_files)

            #通过content_id, file_ids删除附件信息
            res = self.attachment.deleteFileByFileIds(old_tmp_files)
            if not res:
                ret = { 'msg': 'attachment删除附件信息失败', 'code':'error'}
                self.finish(self.write(self.json_encode(ret)))

        if imgs_tmp:
            res = self.content.updateItem({'id':content_res, 'file_ids':imgs_tmp})
            if not res:
                ret = { 'msg': '修改文章中的附件信息失败', 'code':'error'}
                self.finish(self.write(self.json_encode(ret)))

        ret = { 'msg': '操作成功！', 'code':'success'}
        self.finish(self.write(self.json_encode(ret)))

#上传附件
class CmsfileuploadHandler(AdminBaseHandler):
    @asynchronous
    def post(self):
        #admin_user = self.session.get('admin_user')
        upload_path = os.path.join(os.path.dirname(__file__), '../../../static/attachment/tmp/')
        file_metas = self.request.files['file'][0]
        filename = file_metas['filename']
        filepath = os.path.join(upload_path, filename)
        # 限制上传文件的大小，通过len获取字节数
        if len(file_metas['body']) > 4 * 1024 * 1024:
            ret = ret = { 'msg': '文件超出规定大小', 'code':'error'}
            self.finish(self.write(self.json_encode(ret)))

        with open(filepath, 'wb') as up:      #有些文件需要以二进制的形式存储，实际中可以更改
            up.write(file_metas['body'])
        #此时用PIL再处理进行存储，PIL打开不是图片的文件会出现IOERROR错误，这就可以识别后缀名虽然是图片格式，但内容并非是图片。
        try:
            import Image
            image_one = Image.open( filepath )
        except IOError, error:
            ret = { 'msg': '上传失败', 'code':'error'}
            self.finish(self.write(self.json_encode(ret)))
        ret = { 'msg': '上传成功', 'code':'success', 'res':{'file_name':filename, 'url':'http://'+self.request.headers.get('host')+'/static/attachment/tmp/'+filename}}
        self.write(self.json_encode(ret))
        self.finish()

#删除图片
class CmsdeleteimgHandler(AdminBaseHandler):
    @asynchronous
    def post(self):
        attachment = CmsAttachment()
        file_name = self.get_argument('file_name', '')
        attachment.deleteTmpFileByName(file_name)
        self.finish()

class CmstestHandler(AdminBaseHandler):
    def get(self):
        ts = set([3,5,9,10])
        ts2 = set([1,2])
        print ts & ts2
        sys.exit()
        str = '\u4fee\u6539\u5931\u8d25'
        print str.decode("unicode_escape")
        sys.exit()
        cms = CmsNode()
        now = time.localtime(time.time())
        formate_time = time.strftime('%Y-%m-%d %H:%M:%S', now)
        node_item = {
            'name':'test',
            'create_time':formate_time,
            'publish_time':formate_time,
            'type':1,
            'tag_ids':1,
            'status':1
        }
        print cms.addItem(node_item)
        sys.exit()

handlers = [
    (r"/admin/cms/index", IndexHandler),
    (r"/admin/cms/info", CmsinfoHandler),
    (r"/admin/cms/fileupload", CmsfileuploadHandler),
    (r"/admin/cms/deleteupload", CmsdeleteimgHandler),
    (r"/admin/cms/test", CmstestHandler)
]
