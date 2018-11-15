# -*- coding: utf-8 -*-
import logging
from tornado.options import options
from tornado.web import asynchronous, HTTPError, StaticFileHandler
from tornado import gen, httpclient, escape
from handler import BaseHandler, unblock, userAuthenticated
from protected.models.user import User
from protected.models.userNewsfeed import UserNewsfeed
from protected.models.userActivity import UserActivity
import protected.libs.utils as utiles
from protected.libs.const import ErrorMessage, SuccessMessage
from protected.libs.tempFileManger import TempFileManager
from protected.libs.badwordfilter import DictFilter
from protected.libs.limitOperation import rateLimited
from protected.libs.pagenation import Page
import sys, time, uuid, datetime, re, math, json

dr = re.compile(r'<[^>]+>', re.S)

class IndexHandler(BaseHandler):
    #@unblock
    @gen.coroutine
    def get(self):
        userinfo = self.get_current_user()
        if not userinfo:
            self.render('not_found.html')

        page = self.get_argument('page', 1)

        newsfeed = UserNewsfeed()
        #获取表情图片
        img_str = newsfeed.getFaceImgs()
        self._context.faceimgs = img_str
        #根据ip获取地理位置
        ip = self.request.remote_ip
        addr = yield utiles.IPLocation.getLocationByIp('123.121.72.84')
        if not addr:
            addr = {'city': '北京'}

        #动态列表
        newsfeed_list = newsfeed.getNewsFeedList(userinfo['id'], page)

        self._context.selected_menu = 'news_feed'
        self._context.city = addr['city']
        self._context.center_user_info = userinfo
        self._context.newsfeed_list = newsfeed_list
        self.render('ucenter/index.html')

    def post(self):
        pass

'''
对动态进行排序
'''
class SortNewsFeedHandler(BaseHandler):
    def post(self):
        uid = self.get_current_user(info=False)
        page = self.get_argument('page', 1)
        order_by = self.get_argument('order_by', 'time')
        if order_by=='time':
            order_by = 'create_time'
        elif order_by=='hot':
            order_by = 'rank_num'
        newsfeed = UserNewsfeed()
        list = newsfeed.getNewsFeedList(uid, page, order=[order_by, 'DESC'])
        self.return_json({'res': list, 'code': 'success'}, finish=True)
        return

'''
发表newsfeed
'''
class PublicNewsfeedHandler(BaseHandler):
    @asynchronous
    @gen.coroutine
    def post(self):
        uid = self.get_current_user()
        #当前用户没有登录
        if not uid:
            self.return_json({'msg': ErrorMessage.error_message['037'], 'code': 'error', 'num': '037'}, finish=True)
            return

        #提交频率限制
        if not rateLimited('PublicNewsfeed', uid, 2):
            self.return_json_by_num('039', finish=True)

        content = self.get_argument('content', '')
        if not content:
            self.return_json({'msg': ErrorMessage.error_message['052'], 'code': 'error', 'num': '052'}, finish=True)
            return

        news_feed = UserNewsfeed()

        #检查非法字符
        filter_obj = DictFilter()
        content, bad_words = filter_obj.match_all(content)
        #过滤html
        content = dr.sub('', content)

        #获取图片url
        newsfeed_img_urls = self.get_argument('newsfeed_img_urls', '')
        coordinate = self.get_argument('coordinate', '')
        isopen = self.get_argument('isopen', 1)
        #活动
        activity_ids = self.get_argument('newsfeed_activity_ids', 0)

        item = {
            'content': content,
            'coordinate': coordinate,
            'is_open': isopen,
            'urls': newsfeed_img_urls,
            'uid': uid['id'],
            'activity_ids': activity_ids
        }
        ua = self.request.headers["User-Agent"]
        ip = '123.121.72.84'#self.request.remote_ip
        news_feed_res = yield news_feed.addContent(item, self.settings['uploads_path'], ua_string=ua, ip=ip)
        if news_feed_res:
            content = '<span class="feed-content">' + news_feed.showContent(content, activity_ids.split(',')) + '</span>'
            if news_feed_res[1].has_key('img_paths'):
                content = content + '<div class="feed-list-img">'
                for item in news_feed_res[1]['img_paths']:
                    content = content + '''<a class='imgZoom' href='javascript:;' data-href='/ucenter/feedimg/%s' data-width='%s' data-height='%s'>
                                            <img src='/ucenter/feedimg/%s' style='max-width:150px; max-height:100px;'/>
                                           </a>''' % (item['file'], item['width'], item['height'], item['file'])
                del item
                content = content + '</div>'
            self.return_json({'res': {'content':content,
                                      'from_source':news_feed_res[1]['from_source'],
                                      'coordinate':news_feed_res[1]['coordinate'],
                                      'create_time': utiles.timeBefore(news_feed_res[1]['create_time']),
                                      },
                              'code': 'success'}, finish=True)
        return

'''
通过ip获取坐标
'''
class GetLocationByIpHandler(BaseHandler):
    baidu_url = "http://api.map.baidu.com/location/ip?ak=DF0d2c938ce2f578eb317fc45a8342b3&coor=bd09ll&ip="
    @asynchronous
    @gen.coroutine
    def post(self):
        ip = '123.121.72.84'#self.request.remote_ip
        client = httpclient.AsyncHTTPClient()
        resp = yield client.fetch(self.baidu_url+ip)
        if resp.code == 200:
            resp = {'code': 'success', 'res': escape.json_decode(resp.body)}
            self.write(json.dumps(resp, indent=4, separators=(',', ':')))
        else:
            resp = {"code": "error"}
            self.write(json.dumps(resp, indent=4, separators=(',', ':')))
        self.finish()
        return

'''
获取用户的计划活动
'''
class GetUserActsHandler(BaseHandler):
    def post(self):
        uid = self.get_current_user(info=False)
        if not uid:
            self.return_json_by_num('002', finish=True)
            return

        page = self.get_argument('page', 1)
        user_activity = UserActivity()

        total = user_activity.getActivityTotalByUid(uid)

        #分页
        page_obj = Page(total_entries=int(total), entries_per_page=int(options.page_limit['activity_limit']), current_page=page)
        page_obj.current_page(page)
        user_activity_list = user_activity.getActivities(uid, page_obj.current_page())
        if not user_activity_list:
            self.return_json_by_num('054', finish=True)
            return

        page_str = page_obj.getPageStr('/ucenter/userActs')

        self._context.page_str = page_str
        self._context.page_class = 'pagination pagination-sm'
        self._context.page_style = 'margin:0px;'

        user_activities = {'code': 'success'}
        user_activities["res"] = escape.to_basestring(self.render_string("ucenter/include/activity_list.html", user_activity_list=user_activity_list))
        self.write(user_activities)
        self.finish()
        return

'''
删除发布状态的上传图片
'''
class DelFeedImgHandler(BaseHandler):
    def post(self):
        img_id = self.get_argument('img_id', None)

        self.finish({'code': 'success'})
        return

'''
删除动态信息
'''
class DelNewsFeedHandler(BaseHandler):
    def post(self):
        feed_id = self.get_argument('id', None)
        if not feed_id:
            self.finish({'code': 'error'})
        user_news_feed = UserNewsfeed()
        res = user_news_feed.delNewsFeed(feed_id)
        if res:
            self.finish({'code': 'success'})
        else:
            self.finish({'code': 'error'})
        return

'''
获取更多状态信息列表
'''
class GetMoreItemFeedsHandler(BaseHandler):
    @asynchronous
    @gen.coroutine
    def post(self):
        uid = self.get_current_user(False)
        page = self.get_argument('page', 1)
        newsfeed = UserNewsfeed()
        list = newsfeed.getNewsFeedList(uid, page)
        resp = {'code': 'success', 'res': list, 'page': page}
        self.write(json.dumps(resp, separators=(',', ':')))
        self.finish()

'''
上传图片
'''
class UploadImgHandler(BaseHandler):

    image_max_size = 2048000

    def post(self):
        uid = self.get_current_user(info=False)
        if self.request.files:
            feed_img = self.request.files['feed_img'][0]
            if utiles.checkFileType('img', feed_img['content_type']):
                if len(feed_img['body']) > self.image_max_size:
                    self.return_json({'res': {}, 'code': 'error', 'num': '050'}, finish=True)
                    return
                #生成临时存储路径
                temp_file_dir, temp_file_name = TempFileManager.getTempFileDir(self.settings['uploads_path'], UserNewsfeed.ucent_feed_img, feed_img['filename'], uid)
                with open(temp_file_dir, 'wb') as up:
                    up.write(feed_img['body'])
                self.return_json({'res': {'id': str(uuid.uuid4()), 'url': '/ucenter/feedimg/'+temp_file_name, 'filename': temp_file_name}, 'code': 'success'}, finish=True)
                return
            else:
                self.return_json({'res': {}, 'code': 'error', 'num': '051'}, finish=True)
                return

handlers = [
    (r"/ucenter", IndexHandler),
    (r"/ucenter/public", PublicNewsfeedHandler),
    (r"/ucenter/mapLocation", GetLocationByIpHandler),
    (r"/ucenter/delNewsfeed", DelNewsFeedHandler),
    (r"/ucenter/delFeedImg", DelFeedImgHandler),
    (r"/ucenter/userActs", GetUserActsHandler),
    (r"/ucenter/getMoreItems", GetMoreItemFeedsHandler),
    (r"/ucenter/sortNewsFeed", SortNewsFeedHandler),
    (r"/ucenter/uploadImg", UploadImgHandler),
    (r"/ucenter/feedimg/(.*)", StaticFileHandler, {"path": "uploads/ucenter-feed-img"}),
    (r"/ucenter/avatar/(.*)", StaticFileHandler, {"path": "uploads/avatar"}),
    (r"/ucenter/js/(.*)", StaticFileHandler, {"path": "templates/ucenter/js"}),
    (r"/ucenter/js/extend/(.*)", StaticFileHandler, {"path": "static/ucenter/js/extend"}),
]