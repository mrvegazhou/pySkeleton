# -*- coding: utf-8 -*-
from tornado.options import options
from tornado import gen, web
from tornado.ioloop import IOLoop
from handler import BaseHandler, unblock, userAuthenticated
from protected.models.user import User
from protected.models.feedback import Feedback, FeedbackTags, FeedbackComment, FeedbackCommentComplaint
from protected.libs.const import ErrorMessage, SuccessMessage
import sys, time, re, urlparse, uuid, os, datetime, re, math, io
import protected.libs.utils as utiles
from protected.libs.pagenation import Page
from protected.libs.filterTags import filterTags
import protected.libs.captcha as captcha
from protected.libs.limitOperation import limitCaptcha, checkNeedCaptcha, rateLimited, delayPostLimit
from protected.libs.badwordfilter import DictFilter
from protected.extensions.autoMakeSummary import TextRank4Sentence

FEEDBACK_COMMENT_KEY = 'feedback_comment'


class GetTagsHandler(BaseHandler):
    tag = FeedbackTags()
    @unblock
    def get(self):
        name = self.get_argument('q', '')
        if name:
            tags_list = self.tag.getItemsByName(name)
            self.return_json({'value': tags_list}, finish=True)
            return
        else:
            self.return_json({'value': []}, finish=True)
            return
#提交反馈
class PublishHandler(BaseHandler):
    @unblock
    def get(self):
        _handler_template = 'feedback/feedback.html'
        #获取用户邮箱地址
        user_info = self.get_current_user()
        if not user_info:
            user_info = {'user_email':''}
        self._context.feedback_user_info = user_info
        self._context.r = time.time()
        self.render(_handler_template)
        return
    @unblock
    @userAuthenticated
    def post(self):
        uid = self.get_secure_cookie('uid')
        content = self.get_argument('content', '')
        title = self.get_argument('title', '')
        email = self.get_argument('email', '')
        tags = self.get_argument('tags', '')
        captcha = self.get_argument('captcha', '').lower()
        if not email:
            self.return_json({'msg': ErrorMessage.error_message['030'], 'code': 'error', 'num': '030'}, finish=True)
            return
        elif not title:
            self.return_json({'msg': ErrorMessage.error_message['028'], 'code': 'error', 'num': '028'}, finish=True)
            return
        elif not content:
            self.return_json({'msg': ErrorMessage.error_message['029'], 'code': 'error', 'num': '029'}, finish=True)
            return
        elif not captcha:
            self.return_json({'msg': ErrorMessage.error_message['033'], 'code': 'error', 'num': '033'}, finish=True)
            return
        else:
            if captcha!=self.session.get('captcha'):
                self.return_json({'msg': ErrorMessage.error_message['034'], 'code': 'error', 'num': '034'}, finish=True)
                return

            ueditor_dir = self.settings['uploads_path']+os.path.sep+'ueditor'+os.path.sep

            #验证是否是邮箱格式
            if not utiles.validateEmail(email):
                self.return_json({'msg': ErrorMessage.error_message['032'], 'code': 'error', 'num': '029'}, finish=True)
                return

            #过滤文本，把文本内的图片转移到正式目录
            src_list = re.findall('[^_]src="(.*?)"', content, re.I)
            for src_item in src_list:
                if src_item.find('/server/uploads/tmp/')==0:
                    src_item_temp = src_item[16:len(src_item)]
                    if os.path.isfile(ueditor_dir + src_item_temp):
                        src_dir = os.path.dirname(src_item_temp)
                        des_dir = ueditor_dir + 'feedback' + os.path.sep + src_dir.split('/').pop()
                        des_dir_temp = '/server/uploads/feedback' + os.path.sep + src_dir.split('/').pop() + os.path.sep + src_dir.split('/').pop()
                        if not os.path.isdir(des_dir):
                            os.makedirs(des_dir)
                        des_item = des_dir + os.path.sep + src_item.split('/').pop()
                        os.rename(ueditor_dir + src_item_temp, des_item)
                        content = content.replace(src_item, des_dir_temp)

            #检查非法字符
            filter_obj = DictFilter()
            new_content, bad_words = filter_obj.match_all(content)

            #保存tag标签
            tag_ids = []
            if tags:
                tag_obj = FeedbackTags()
                tag_names = tags.split(',')
                for name in tag_names:
                    tag_info = tag_obj.getItemByName(name)
                    if tag_info:
                        tag_ids.append(str(tag_info['id']))
                    else:
                        tag_id = tag_obj.addItem({'name': name, 'creator_id': self.get_current_user(False)})
                        tag_ids.append(str(tag_id))
                        del tag_id
            #保存信息
            feedback = Feedback()
            tag_ids = ','+','.join(tag_ids)+',' if tag_ids else 0

            #过滤html
            dr = re.compile(r'<[^>]+>', re.S)
            temp_new_content = dr.sub('', new_content)
            if len(temp_new_content)>500:
                #摘要
                tr4s = TextRank4Sentence()
                tr4s.analyze(text=temp_new_content, lower=True, source = 'all_filters')
                summary = []
                for item in tr4s.get_key_sentences(num=3):
                    summary.append(item.sentence)
                summary = ' '.join(summary)
                if len(summary)>300:
                    summary = utiles.cutStr(summary, 300)
            else:
                summary = utiles.cutStr(temp_new_content, 300)

            res = feedback.addItem(item={'uid': uid, 'title':title, 'content':new_content, 'email':email, 'tag_ids': tag_ids, 'summary': summary})
            if not res:
                self.return_json({'msg': ErrorMessage.error_message['031'], 'code': 'error', 'num': '031'}, finish=True)
                return
            else:
                if bad_words:
                    msg = '很抱歉，您的内容里有敏感字，它们会被*替换。'
                else:
                    msg = '谢谢您的反馈，我会认真阅读'

                self.return_json({'code': 'success', 'msg':msg, 'url':'/feedback'}, finish=True)
                return

'''
投诉操作
'''
class ComplaintHandler(BaseHandler):
    @unblock
    def post(self):
        uid = self.get_current_user(info=False)
        if not uid:
            self.return_json({'msg': ErrorMessage.error_message['037'], 'code': 'error', 'num': '037'}, finish=True)
            return

        f_c = FeedbackComment()
        fcid = self.get_argument('fcid', None)
        if not fcid:
            self.return_json({'msg': ErrorMessage.error_message['036'], 'code': 'error', 'num': '036'}, finish=True)
            return
        #检查反馈评论是否存在
        info = f_c.getItem(fcid)
        if not info:
            self.return_json({'msg': ErrorMessage.error_message['044'], 'code': 'error', 'num': '044'}, finish=True)
            return
        res = f_c.updateFeedbackCommentCount(fcid, 'complaint_count')
        if res:
            f_c_c = FeedbackCommentComplaint()
            reason = self.get_argument('reason', None)
            if not reason:
                self.return_json({'msg': ErrorMessage.error_message['046'], 'code': 'error', 'num': '046'}, finish=True)
                return
            item = {
                'fcid': fcid,
                'reason': filterTags(reason),
                'uid': uid
            }
            res = f_c_c.addItem(item)
            if not res:
                self.return_json({'msg': ErrorMessage.error_message['045'], 'code': 'error', 'num': '045'}, finish=True)
                return
            else:
                self.return_json({'msg': SuccessMessage.success_message['009'], 'code': 'success', 'num': '009'}, finish=True)
                return


'''
提交回复
'''
class ReplyHandler(BaseHandler):
    f_c = FeedbackComment()
    @unblock
    @userAuthenticated
    def post(self):
        user_info = self.get_current_user()
        if not user_info:
            self.return_json({'msg': ErrorMessage.error_message['037'], 'code': 'error', 'num': '037', 'is_need_cpatcha': 0}, finish=True)
            return

        uid = str(user_info['id'])

        pid = self.get_argument('pid', 0)
        ancestor_id = self.get_argument('ancestor_id', 0)
        comment = filterTags(self.get_argument('comment', ''))
        feedback_id = self.get_argument('feedback_id', 0)

        if not comment:
            self.return_json({'msg': ErrorMessage.error_message['035'], 'code': 'error', 'num': '035'}, finish=True)
            return
        if not feedback_id:
            self.return_json({'msg': ErrorMessage.error_message['036'], 'code': 'error', 'num': '036'}, finish=True)
            return

        #频率控制
        tmp = delayPostLimit('feedback-reply', uid, 0.5)
        if not tmp:
            self.return_json({'msg': ErrorMessage.error_message['043'], 'code': 'error', 'num': '043'}, finish=True)
            return

        #查询评论的信息
        comment_info = self.f_c.getItem(pid)
        if not comment_info:
            self.return_json({'msg': ErrorMessage.error_message['036'], 'code': 'error', 'num': '036'}, finish=True)
            return

        create_timestamp = time.time()
        create_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(create_timestamp))

        res, new_comment = self.f_c.addComment(self.settings, uid, pid, ancestor_id, comment, feedback_id, create_time, comment_info['uid'], type='feedback_comment')
        if not res:
            self.return_json({'msg': ErrorMessage.error_message['038'], 'code': 'error', 'num': '038'}, finish=True)
            return
        #获取被评论的用户姓名
        user = User()
        to_user_info = user.getItem(comment_info['uid'])
        res_data = {
            'fcid': res,
            'user_name': user_info['user_name'],
            'create_time': utiles.timeBefore(create_time),
            'avatar': user_info['avatar'],
            'uid': user_info['id'],
            'comment': new_comment,
            'p_comment_id': pid,
            'to_user_id': comment_info['uid'],
            'to_user_name': to_user_info['user_name'] if to_user_info else ''
        }
        self.return_json({'code': 'success', 'msg': SuccessMessage.success_message['006'], 'res': res_data}, finish=True)
        return



'''
提交反馈的评论
'''
class CommentHandler(BaseHandler):
    f_c = FeedbackComment()
    f = Feedback()
    @unblock
    def post(self):
        user_info = self.get_current_user()
        if not user_info:
            self.return_json({'msg': ErrorMessage.error_message['037'], 'code': 'error', 'num': '037', 'is_need_cpatcha': 0}, finish=True)
            return

        uid = str(user_info['id'])

        pid = self.get_argument('pid', 0)
        ancestor_id = self.get_argument('ancestor_id', 0)
        comment = filterTags(self.get_argument('editor_comment', ''))
        feedback_id = self.get_argument('feedback_id', 0)

        create_timestamp = time.time()
        create_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(create_timestamp))

        captcha = self.get_argument('captcha', '')

        #验证验证码次数和频率
        is_need_captcha, cache_count, cache_time, is_frequency, is_true_need_captcha = limitCaptcha(uid, 'feedback_comment')

        if not comment:
            self.return_json({'msg': ErrorMessage.error_message['035'], 'code': 'error', 'num': '035', 'is_need_captcha': is_need_captcha}, finish=True)
            return
        if not feedback_id:
            self.return_json({'msg': ErrorMessage.error_message['036'], 'code': 'error', 'num': '036', 'is_need_captcha': is_need_captcha}, finish=True)
            return

        #通过feedback_id查询反馈信息
        f_info = self.f.getItem(feedback_id)
        if not f_info:
            self.return_json({'msg': ErrorMessage.error_message['036'], 'code': 'error', 'num': '036', 'is_need_captcha': is_need_captcha}, finish=True)
            return

        #验证验证码是否正确
        if is_true_need_captcha==1:
            if not captcha:
                self.return_json({'msg': ErrorMessage.error_message['033'], 'code': 'error', 'num': '033', 'is_need_captcha': is_need_captcha}, finish=True)
                return
            else:
                #判断是否频繁操作
                if is_frequency==1 and captcha!=self.session['captcha']:
                    self.return_json({'msg': ErrorMessage.error_message['039'], 'code': 'error', 'num': '039', 'is_need_captcha': is_need_captcha}, finish=True)
                    return
                if captcha!=self.session['captcha']:
                    self.return_json({'msg': ErrorMessage.error_message['034'], 'code': 'error', 'num': '034', 'is_need_captcha': is_need_captcha}, finish=True)
                    return

        res, new_comment = self.f_c.addComment(self.settings, uid, pid, ancestor_id, comment, feedback_id, create_time, f_info['uid'])
        if not res:
            self.return_json({'msg': ErrorMessage.error_message['038'], 'code': 'error', 'num': '038', 'is_need_captcha': is_need_captcha}, finish=True)
            return
        #
        res_data = {
            'fcid': res,
            'user_name': user_info['user_name'],
            'create_time': utiles.timeBefore(create_time),
            'avatar': user_info['avatar'],
            'uid': user_info['id'],
            'comment': new_comment
        }

        self.return_json({'code': 'success', 'msg': SuccessMessage.success_message['006'], 'res': res_data, 'is_need_captcha': is_need_captcha}, finish=True)
        return


#问题详情页
class InfoHandler(BaseHandler):

    feedback = Feedback()
    feedback_tag = FeedbackTags()
    feedback_comment = FeedbackComment()
    user = User()

    #获取评论列表以及评论的回复列表
    def getComentsAndReplies(self, fid, page, limit):

        #获取评论总数
        comment_total = self.feedback_comment.getFeedbackCommentCountByFid(fid)

        #获取评论
        comments = self.feedback_comment.getFeedbackCommentsByFid(fid, page, limit)

        user_ids = []
        comment_ids = []
        for (k, v) in comments.items():
            user_ids.append(v['uid'])
            comment_ids.append(v['id'])
        #获取评论的回复列表
        reply_list = self.feedback_comment.getSonFeedbackCommentByAncestorId(comment_ids, 1, 100)

        for (k, v) in reply_list.items():
            for i in v:
                user_ids.append(i['uid'])
                user_ids.append(i['to_uid'])

        #评论者集合
        user_infos = self.user.getUsersByUids(user_ids)

        for (key, item) in comments.items():
            item['commenter'] = user_infos[item['uid']] if user_infos[item['uid']] else {'user_name':''}
            item['create_time'] = utiles.timeBefore(item['create_time'])
            temp_reply_list = reply_list.get(item['id'], [])
            temp_new_reply_list = []
            for i in temp_reply_list:
                i['commenter'] = user_infos[item['uid']] if user_infos[item['uid']] else {'user_name':''}
                i['create_time'] = utiles.timeBefore(i['create_time'])
                i['to_user_name'] = user_infos[item['to_uid']]['user_name'] if item['to_uid']!=0 and user_infos[item['to_uid']] else ''
                i['to_user_id'] = item['to_uid']
                temp_new_reply_list.append(i)
            item['reply_list'] = temp_new_reply_list
            del temp_new_reply_list, temp_reply_list
            comments[key] = item

        return comment_total, comments

    @unblock
    def get(self, id):
        if not id:
            self.render_404()

        #更新查看总数
        self.feedback.updateFeedbackCount(id, 'views')

        uid = self.get_current_user(info=False)

        page = self.get_argument('page', 1)
        limit = options.page_limit['feedback_limit']
        _handler_template = 'feedback/feedback_info.html'
        feedback_info = self.feedback.getFeedbackById(id)

        if not feedback_info:
            return self.render_404()

        feedback_info['tags'] = self.feedback_tag.getTagListByIds(feedback_info['tag_ids'].split(','))
        feedback_info['user_info'] = self.user.getItem(feedback_info['uid'])
        feedback_info['publish_time'] = utiles.timeBefore(feedback_info['create_time'])
        self._context.feedback_info = feedback_info

        comment_total, comments = self.getComentsAndReplies(feedback_info['id'], page, limit)

        self._context.comment_total = str(comment_total['total'])
        self._context.comments = comments

        #判断是否显示‘查看更多’
        show_more = None
        if comment_total['total']>limit:
            show_more = True
        self._context.show_more = show_more
        self._context.show_more_url = '/feedback/info/%d' % int(id)
        self._context.page = page
        self._context.relay_click_time = options.relay_click_time
        self._context.r = time.time()

        if checkNeedCaptcha(FEEDBACK_COMMENT_KEY, uid):
            self._context.is_need_captcha = 1
        else:
            self._context.is_need_captcha = None

        self.render(_handler_template)
        self.finish()

    @unblock
    def post(self, fid):
        #ajax请求获取评论的分页信息
        page = self.get_argument('page', 1)
        limit = options.page_limit['feedback_limit']
        if not fid:
            self.return_json({'res': None, 'code': 'error'})

        comment_total, comments = self.getComentsAndReplies(fid, page, limit)

        #判断是否显示‘查看更多’
        show_more = 0
        if int(math.ceil(comment_total['total']/limit))>=int(page):
            show_more = 1

        self.return_json({'res': {'comments': comments, 'fid': fid, 'show_more': show_more, 'page': page}, 'code': 'success'}, date_encoder=True, finish=True)
        return


'''
点赞功能
'''
class LikeHandler(BaseHandler):
    @unblock
    @userAuthenticated
    def post(self):
        uid = self.get_current_user(info=False)
        feedback_type = self.get_argument('feedback_type', '')
        operate_type = self.get_argument('type', '')
        fid = self.get_argument('fid', 0)
        vote_type = ''

        if operate_type=='unlike':
            vote_type = 'oppose_votes'
        elif operate_type=='like':
            vote_type = 'approval_votes'
        else:
            self.return_json({'code': 'error', 'msg': ErrorMessage.error_message['042'], 'type': operate_type}, finish=True)
            return

        if not uid:
            self.return_json({'code': 'error', 'msg': ErrorMessage.error_message['041'], 'type': operate_type}, finish=True)
            return

        res = rateLimited('feedback-like', uid, 30)
        if not res:
            self.return_json({'code': 'error', 'msg': ErrorMessage.error_message['039'], 'type': operate_type}, finish=True)
            return

        if feedback_type=='feedback':
            obj = Feedback()
        elif feedback_type=='feedback_comment':
            obj = FeedbackComment()
        else:
            self.return_json({'code': 'error', 'msg': ErrorMessage.error_message['042'], 'type': operate_type}, finish=True)
            return

        if vote_type and feedback_type:
            res = obj.operateLike(fid, uid, vote_type)
            if res and res!=-1:
                self.return_json({'code': 'success', 'msg': SuccessMessage.success_message['007' if operate_type=='like' else '008'], 'type': operate_type}, finish=True)
                return
            elif res==-1:
                self.return_json({'code': 'error', 'msg': ErrorMessage.error_message['047'], 'type': operate_type}, finish=True)
                return
            else:
                self.return_json({'code': 'error', 'msg': ErrorMessage.error_message['040'], 'type': operate_type}, finish=True)
                return

'''
反馈信息列表
'''
class IndexHandler(BaseHandler):
    #@unblock
    def get(self):
        _handler_template = 'feedback/index.html'
        sort_type = self.get_argument('sort', 'rank_sort')
        self._context.sort_type = sort_type

        page = self.get_argument('page', 1)
        limit = options.page_limit['feedback_limit']

        #分页url
        page_url = 'feedback/'
        args_url = ''

        #是否有tag参数
        tag = self.get_argument('tag', '')
        keyword = self.get_argument('keyword', '')
        self._context.keyword = keyword

        conds = {}
        if tag:
            page_url += '&tag='+tag if page_url.find('?')>=0 else '?tag='+tag
            args_url += '&tag='+tag
            conds['tag'] = tag

        if keyword:
            if page_url.find('?')>=0:
                page_url += '&keyword='+keyword
            else:
                page_url += '?keyword='+keyword
            args_url += '&keyword='+keyword
            conds['keyword'] = keyword

        #传递请求url
        self._context.form_url = page_url
        self._context.args_url = args_url

        feedback = Feedback()
        feedback_total = feedback.getListTotal(conds)
        #分页
        page_obj = Page(total_entries=int(feedback_total.total), entries_per_page=int(limit), current_page=page)
        page_obj.current_page(page)

        feedback_list = feedback.getList(conds=conds, sorting=sort_type, page=page_obj.current_page(), limit=limit)
        page_str = page_obj.getPageStr('/feedback')
        self._context.page_str = page_str
        #
        (list, res, tag_ids, uids) = ([], [], [], [])
        for item in feedback_list:
            item['votes'] = item['oppose_votes']+item['approval_votes']
            temp_tag_ids = item['tag_ids'].split(',')
            for t in temp_tag_ids:
                if t:
                    tag_ids.append(t)
            uids.append(item['uid'])
            item['title'] = filterTags(utiles.cutStr(item['title']), True)
            item['tag_ids'] = temp_tag_ids
            list.append(item)

        feedback_tag = FeedbackTags()
        tag_list = feedback_tag.getTagListByIds(tag_ids)
        del tag_ids

        #获取用户
        user = User()
        user_list = user.getUsersByUids(uids)

        for item in list:
            item['user_info'] = user_list[item['uid']] if user_list[item['uid']] else {'user_name':''}
            item.pop('uid')
            item['tags'] = []
            for i in item['tag_ids']:
                if i and tag_list.has_key(int(i)):
                    item['tags'].append(tag_list[int(i)])
            item['create_time'] = utiles.timeBefore(item['create_time'])
            if item['views']>9999:
                item['views'] = '9999+'
            res.append(item)
        del list
        self._context.feedback_list = res
        self.render(_handler_template)

class TestHandler(BaseHandler):
    @web.asynchronous
    @gen.coroutine
    def get(self):
        tmp = yield self.fuck()
        self.write('ssss'+str(tmp))
        self.finish()
    @gen.coroutine
    def fuck(self):
        user = User()
        res = user.queryBySql('select sleep(20);')
        raise gen.Return(res)

class Test2Handler(BaseHandler):
    def get(self, *args, **kwargs):
        f = FeedbackComment()
        print f.operateLike(1, 2, 'approval_votes')

handlers = [
    (r"/feedback", IndexHandler),
    (r"/feedback/info/(\d+)", InfoHandler),
    (r"/feedback/index", IndexHandler),
    (r"/feedback/like", LikeHandler),
    (r"/feedback/publish", PublishHandler),
    (r"/feedback/gettags", GetTagsHandler),
    (r"/feedback/complaint", ComplaintHandler),
    (r'/feedback/comment', CommentHandler),
    (r'/feedback/reply', ReplyHandler),
    (r"/feedback/test", TestHandler),
    (r"/feedback/test2", Test2Handler),
]