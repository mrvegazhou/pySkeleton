# -*- coding: utf8 -*-
from protected.models.FrontBaseModel import FrontBaseModel
from protected.models.tags import Tags
from protected.libs.decorators import preSave, postSave
from protected.models.groupActivity import GroupActivity
from protected.libs.exceptions import ArgumentError, BaseError
import protected.libs.utils as utiles
from protected.libs.tempFileManger import TempFileManager
from tornado import gen
import os,re,logging,json
from PIL import Image

class UserNewsfeed(FrontBaseModel):
    ucent_feed_img = 'ucenter-feed-img'

    public_status = 1
    group_status = 2
    friend_status = 3
    self_status = 4

    #公开状态
    is_open = {public_status:'所有人', group_status:'仅群组', friend_status:'仅朋友', self_status:'仅自己'}

    map_regex = re.compile(r'(\[@(.*?)@\])', re.S|re.M)
    emotion_regex = re.compile(r'(\[&(.*?)&\])', re.S|re.M)
    event_regex = re.compile(r'(\[#(.*?)#\])', re.S|re.M)


    def __init__(self):
        self._table = 'user_newsfeed'
        self.setPK('id')
        self._table_columns = [ 'id',
                                'uid',
                                'content',
                                'imgs',
                                'create_time',
                                'from_source',
                                'coordinate',
                                'status',
                                'is_open',
                                'rank_num',
                                'focus_num',
                                'activity_ids'
                            ]
        self._table_columns_rule = {'uid':['required'], 'content':['required'], 'create_time':['required'], 'status':['required'] }
        self._table_columns_autoload = {'create_time': utiles.dateToTimestamp(), 'status': 1}
        super(UserNewsfeed, self).__init__()

    def new(self, item):
        obj = self.initialize(item)
        if obj:
            return self.save()
        return None

    #获取动态列表
    def getNewsFeedList(self, uid, page, order=['create_time', 'DESC']):
        if not uid:
            return None
        list = self.queryMany(filterString=[('uid', int(uid)), ('status', 1)],
                              fields=self._table_columns,
                              orderBy=[(order[0], order[1])],
                              limit=self._page_size,
                              pageNo=page)
        img_ids = []   #存储图片id
        for item in list:
            if item['imgs'] and item['imgs']!='0':
                for i in item['imgs'].split(','):
                    img_ids.append(i)

        img_dict = {}
        if img_ids:
            feed_img = UserNewsfeedImgs()
            img_list = feed_img.getImgsById(img_ids)
            for img in img_list:
                img_dict.setdefault(img['feed_id'], [])
                img_dict[img['feed_id']].append(img)

        res = []
        for item in list:
            item['create_time'] = utiles.timeBefore(item['create_time'])
            #通过标签展示内容
            item['content'] = self.showContent(item['content'], item['activity_ids'].split(','))
            if img_dict.has_key(item['id']):
                img_item_tmp = []
                for tmp in img_dict[item['id']]:
                    tmp['ext_info'] = json.loads(tmp['ext_info'])
                    img_item_tmp.append(tmp)
                item['img_urls'] = img_item_tmp
                del img_item_tmp
            else:
                item['img_urls'] = None
            item['is_open'] = self.is_open[int(item['is_open'])]
            res.append(item)
        return res

    #根据标签显示内容（地图，活动，表情）
    def showContent(self, content, activity_ids=None):
        content = self.map_regex.sub(r'<ins><a href="javascript:;" onclick="showMapByAddr(%s\2%s);">\2</a></ins>' % ("'", "'"), content)
        emotion = self.emotion_regex.findall(content)
        if emotion:
            for item in emotion:
                tmp = self.getFaceImgs(item[1])
                content = content.replace(item[0], tmp)
            del item
        if self.event_regex.search(content):
            events = self.event_regex.findall(content)
            i = 0
            for item in events:
                if activity_ids[i]!='0':
                    content = content.replace(item[0], '<a href="/activity-info/%d" class="event">%s</a>' % (int(activity_ids[i]), item[1]))
                i = i+1
            del item
            content = self.event_regex.sub(r'<a href="#" class="event">\2</a>', content)
        return content


    @gen.coroutine
    def addContent(self, item, upload_url, ua_string=None, ip=None):
        if not item.has_key('content'):
            raise gen.Return(False)
        elif not item.has_key('uid'):
            raise gen.Return(False)
        else:
            if int(item['is_open']) not in [self.public_status, self.self_status, self.friend_status]:
                item['is_open'] = 1
            if ua_string:
                user_agent = parse(ua_string)
                item['from_source'] = user_agent.os.family + ' ' + user_agent.browser.family
            else:
                item['from_source'] = ''
            addr = yield utiles.IPLocation.getLocationByIp(ip)
            item['coordinate'] = addr['city'] if addr else ''
            urls = item['urls'] if item['urls'] else None
            feed_id = self.addItem(item)

            if not feed_id:
                raise gen.Return(False)

            if feed_id and urls:
                feed_img = UserNewsfeedImgs()
                img_ids = []
                urls = urls.split(',')
                real_file_path_list = []
                #判断url是否存在 存在则移动到真实路径并保存数据库
                for url in urls:
                    real_file, real_path = TempFileManager.moveTempFileToRealDir(upload_url, self.ucent_feed_img, url.split('/').pop())
                    if real_file:
                        #使用PIL获取图片大小 长宽
                        try:
                            img_info = Image.open(real_path)
                        except IOError, error:
                            logging.error(error)
                        img_width_height = img_info.size
                        img_size = os.path.getsize(real_path)
                        ext_info_json = json.dumps({'width': img_width_height[0], 'height':img_width_height[1], 'size':img_size})
                        real_file_path_list.append({'file':real_file, 'width':img_width_height[0], 'height':img_width_height[1]})
                        img_ids.append(feed_img.addImg({'feed_id': feed_id, 'url': real_file, 'ext_info':ext_info_json}))
                if img_ids:
                    item['img_paths'] = real_file_path_list
                    img_ids = ','.join(map(str, img_ids))
                    self.updateInfo(filterString=[('imgs', img_ids)], where=[('id', feed_id)])
            raise gen.Return([feed_id, item])

    #获取表情
    def getFaceImgs(self, one_img_name=None):
        img_dir = os.path.dirname(__file__)+'/../../static/img/face'
        img_str = ''
        if os.path.isdir(img_dir):
            if not one_img_name:
                for img in os.listdir(img_dir):
                    img_idx = img.split('.')
                    if img_idx[1]=='gif':
                        img_name = utiles.getFaceImgs(int(img_idx[0]))
                        temp_str = '<li><a href="javascript:void(0)" title="%s"><img src="/static/img/face/%s" face="[&%s&]"/></a></li>' % (img_name, img, img_name)
                        img_str = img_str + temp_str
                return img_str
            else:
                img_names = utiles.getFaceImgs()
                if img_names.index(one_img_name):
                    return '<img src="/static/img/face/%s.gif" class="face-img"/>' % str(img_names.index(one_img_name))
                else:
                    return None


    #删除动态信息
    def delNewsFeed(self, id):
        id = int(id)
        item = {'id':id, 'status':0}
        return self.updateItem(item)

class UserNewsfeedImgs(FrontBaseModel):
    def __init__(self):
        self._table = 'user_newsfeed_imgs'
        self.setPK('id')
        self._table_columns = [ 'id',
                                'url',
                                'feed_id',
                                'ext_info'
                            ]
        self._table_columns_rule = {'url':['required'], 'feed_id':['required']}
        super(UserNewsfeedImgs, self).__init__()

    def addImgs(self, items):
        for item in items:
            if (not item.has_key('url')) or (not item .has_key('feed_id')):
                items.remove(item)
        return self.addItems(items)

    def getImgs(self, feed_id):
        return self.queryMany(filterString=[('feed_id', int(feed_id))], fields=self._table_columns)

    def addImg(self, item):
        if (not item.has_key('url')) or (not item.has_key('feed_id')):
            return False
        return self.addItem(item)

    def getImgsById(self, id):
        if isinstance(id, list):
            filterString = [('id', ('in', set(id)))]
            return self.queryMany(filterString=filterString, fields=self._table_columns)
        else:
            filterString=[('id', id)]
            return self.queryOne(filterString=filterString, fields=self._table_columns)

'''
用户日记
'''
class UserNote(FrontBaseModel):
    ucenter_note_img = 'ucenter-note-img'

    public_status = 1
    group_status = 2
    friend_status = 3
    self_status = 4
    #公开状态
    is_open = {public_status:'所有人', group_status:'仅群组', friend_status:'仅朋友', self_status:'仅自己'}

    def __init__(self):
        self._table = 'user_note'
        self.setPK('id')
        self._table_columns = [ 'id',
                                'title',
                                'content',
                                'create_time',
                                'update_time',
                                'view_num',
                                'is_open',
                                'is_comment',
                                'tag_ids',
                                'detete_time',
                                'create_uid'
                                ]
        self._table_columns_rule = {'title':['required'], 'content':['required'], 'create_time':['required']}
        self._table_columns_autoload = {'create_time': utiles.dateToTimestamp()}
        super(UserNote, self).__init__()

    @gen.coroutine
    def saveNote(self, item):
        if (not isinstance(item, dict)) \
                or (not item.has_key('create_uid')) \
                or (not item.has_key('title')) \
                or (not item.has_key('content')):
            raise gen.Return(False)
        else:
            note_item = item.copy()
            if int(item['is_open']) not in self.is_open.keys():
                note_item['is_open'] = 1
            else:
                note_item['is_open'] = int(item['is_open'])

            if item['tags']:
                #检查tag是否存在
                note_item['tag_ids'] = yield self.getNoteTags(set(item['tags']))

            res = self.saveOne(note_item)
            if not res:
                raise gen.Return(False)
            else:
                note_item['id'] = res
                raise gen.Return(note_item)

    @gen.coroutine
    def getNoteTags(self, tag_names):
        tag_obj = Tags()
        tag_list = tag_obj.getTagByNames(tag_names, Tags.note_type)
        if not tag_list:
            return None
        exist_names = []
        for key, value in tag_list.items():
            exist_names.append(value['name'])
        del key, value
        #找出数据库没有的tag
        diff_names = list(set(tag_names).difference(set(exist_names)))
        #插入新的tag
        ids = []
        for item in diff_names:
            res = tag_obj.saveOne({'name': item, 'type': Tags.note_type})
            if res:
                ids.append(res)
        return tag_list.keys()+ids

'''
用户日志评论
'''
class userNoteComment(FrontBaseModel):

    def __init__(self):
        self._table = 'user_note_comment'
        self.setPK('id')
        self._table_columns = [ 'id',
                                'note_id',
                                'content',
                                'create_time',
                                'create_uid',
                                'status'
                                ]
        self._table_columns_rule = {'content':['required'], 'note_id':['required'], 'create_time':['required'], 'create_uid':['required']}
        self._table_columns_autoload = {'create_time': utiles.dateToTimestamp()}
        super(userNoteComment, self).__init__()

    def getNoteComments(self, note_id, page):
        comment_list = self.queryMany(filterString=[('note_id', int(note_id)), ('status', 1)],
                                      fields=self._table_columns,
                                      orderBy=[('create_time', 'DESC')],
                                      limit=self._comment_page_size,
                                      pageNo=page)
        cids = []
        for item in comment_list:
            cids.append(item['id'])
        del item

        cids = set(cids)
        reply_obj = userNoteReply()
        reply_list = reply_obj.getNoteCommentsByCommentId(cids, 1)

        res = []
        for item in comment_list:
            if reply_list.has_key(item['id']):
                item['reply_list'] = reply_list[item['id']]
            else:
                item['reply_list'] = []
            res.append({item['id']: item})

        return res


'''
评论回复列表
'''
class userNoteReply(FrontBaseModel):

    def __init__(self):
        self._table = 'user_note_reply'
        self.setPK('id')
        self._table_columns = [ 'id',
                                'comment_id',
                                'content',
                                'create_time',
                                'from_uid',
                                'to_uid',
                                'status'
                                ]
        self._table_columns_rule = {'content':['required'], 'comment_id':['required'], 'create_time':['required'], 'from_uid':['required'], 'to_uid':['required']}
        self._table_columns_autoload = {'create_time': utiles.dateToTimestamp()}
        super(userNoteReply, self).__init__()

    def getNoteCommentsByCommentId(self, cid, page=1):
        filterString = None
        if isinstance(cid, set):
            filterString = ('comment_id', ('in', cid))
        elif isinstance(cid, int):
            filterString = ('comment_id', cid)
        else:
            return []
        reply_list = self.queryMany(  filterString=[filterString, ('status', 1)],
                                      fields=self._table_columns,
                                      orderBy=[('create_time', 'DESC')],
                                      limit=self._reply_page_size,
                                      pageNo=page)
        if isinstance(cid, set):
            res = {}
            for item in reply_list:
                res.setdefault(item['comment_id'], [])
                res[item['comment_id']].append(item)
        else:
            res = []
            for item in reply_list:
                res[item['id']] = item
        del item
        return res