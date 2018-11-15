# -*- coding: utf8 -*-
from protected.models.FrontBaseModel import FrontBaseModel
from protected.libs.exceptions import ArgumentError, BaseError
import protected.libs.utils as utiles
from protected.libs.badwordfilter import DictFilter
import os, re, time
import jieba as cutChineesWord
from protected.libs.rankingAlgorithm import confidence

'''
反馈
'''
class Feedback(FrontBaseModel):

    def __init__(self):
        self._table = 'feedback'
        self.setPK('id')
        self._table_columns = [ 'id',
                                'uid',
                                'content',
                                'create_time',
                                'title',
                                'email',
                                'tag_ids',
                                'status',
                                'oppose_votes',     #反对票
                                'approval_votes',   #赞成票
                                'answers',
                                'views',
                                'rank_sort',
                                'summary'
                            ]
        self._table_columns_rule = {'email':['required'], 'content':['required'], 'title':['required'] }
        super(Feedback, self).__init__()

    def getListTotal(self, conds={}):
        args = [('status', 1)]
        if conds:
            if conds.has_key('tag') and conds['tag'].strip()!='':
                args.append(('tag_ids', ('like', conds['tag'])))

            if conds.has_key('keyword') and conds['keyword'].strip()!='':
                words = cutChineesWord.cut(conds['keyword'])
                words_list = []
                for word in words:
                    if word.strip()!='':
                        if utiles.validateOther(word):
                            word = '\\'+word
                        words_list.append(word)
                words_str = "|".join(words_list[0:] if len(words_list)<=10 else words_list[0:9])
                args.append(('content', ('regexp', words_str)))

        return self.queryOne(filterString=args, fields=['count(*) AS total'])

    def getList(self, conds, sorting, page, limit):
        tmp_conds = ['status=%s']
        tmp_args = [1]
        if conds.has_key('tag') and conds['tag']!='':
            tmp_conds.append(' tag_ids LIKE %s ')
            #获取标签id
            feedback_tag = FeedbackTags()
            tag_info = feedback_tag.getItemByName(conds['tag'])
            tmp_args.append('%,'+str(tag_info['id'])+',%')

        if conds.has_key('keyword'):
            words = cutChineesWord.cut(conds['keyword'])
            words_list = []
            for word in words:
                if word.strip()!='':
                    if utiles.validateOther(word):
                        word = '\\'+word
                    words_list.append(word)
            words = "|".join(words_list[0:] if len(words_list)<=10 else words_list[0:9])
            tmp_conds.append(' content REGEXP %s ')
            tmp_args.append(words)

        sorting_str = ' ORDER BY '
        if not sorting in ['create_time', 'rank_sort', 'views']:
            sorting_str += ' rank_sort DESC '
        if sorting=='views':
            sorting_str += ' views DESC, approval_votes ASC '
        if sorting=='create_time':
            sorting_str += ' create_time DESC '
        if sorting=='rank_sort':
            sorting_str += ' rank_sort DESC '

        sql = "SELECT {fields} FROM {table} WHERE {conds} {sorting} LIMIT {offset},{limit}".format(
                    fields=','.join(self._table_columns),
                    table=self._table,
                    conds=' AND '.join(tmp_conds),
                    sorting=sorting_str,
                    offset=(page-1)*limit,
                    limit=limit
        )
        return self.querySQL(sql, *tuple(tmp_args))

    #获取反馈信息详情
    def getFeedbackById(self, id):
        if not id:
            return {}
        info = self.queryOne(filterString=[('status', 1), ('id', id)])
        if not info:
            return {}
        return info

    #点赞操作
    def operateLike(self, id, uid, type):
        id = str(id)
        uid = str(uid)

        if type not in ['approval_votes', 'oppose_votes']:
            return False

        #获取feedback信息
        info = self.getItem(id)
        if not info:
            return False

        rank_sort = info['rank_sort']
        ups = info['approval_votes']
        downs = info['oppose_votes']

        #先判断是否已经点赞过
        fvu = FeedbackVoteUser()
        has_vote = fvu.getFeedbackVoteByFidAndUid(id, uid)
        if has_vote:
            if has_vote['approval_votes']==1 and type=='approval_votes':
                return -1
            elif has_vote['oppose_votes']==1 and type=='oppose_votes':
                return -1

            #如果已经点赞 现在操作是反对 那么总票数要-1
            if has_vote['approval_votes']==1 and type=='oppose_votes':
                ups = ups - 1
                downs = downs + 1
                rank_sort = confidence(ups, downs)
                sql = "UPDATE feedback SET oppose_votes=oppose_votes+1, approval_votes=approval_votes-1, rank_sort=%s WHERE id=%s"
                update_sql = "UPDATE feedback_vote_user SET vote_type=2 WHERE fid=%s AND uid=%s"

            elif has_vote['oppose_votes']==1 and type=='approval_votes':
                ups = ups + 1
                downs = downs - 1
                rank_sort = confidence(ups, downs)
                sql = "UPDATE feedback SET approval_votes=approval_votes+1, oppose_votes=oppose_votes-1, rank_sort=%s WHERE id=%s"
                update_sql = "UPDATE feedback_vote_user SET vote_type=1 WHERE fid=%s AND uid=%s"

            else:
                return -1
            update_res = self.runSQL4RowCount(update_sql, *(str(id), str(uid)))
            if update_res:
                res = self.runSQL4RowCount(sql, *(str(rank_sort), str(id)))
                if not res:
                    return -1
                else:
                    return 1
            else:
                return -1

        #用户投票关系表中插入数据
        item = {'fid':id, 'uid':uid, 'vote_type': 1 if type=='approval_votes' else 2}
        res = fvu.addItem(item)
        if not res:
            return -1

        if type=='approval_votes':
            rank_sort = confidence(ups+1, downs)
        else:
            rank_sort = confidence(ups, downs+1)

        sql = "UPDATE feedback SET {field}={field}+1, rank_sort=%s WHERE id=%s AND uid=%s".format(field=type)
        return self.runSQL4RowCount(sql, *(rank_sort, id, uid))

    #修改反馈表里的字段增值
    def updateFeedbackCount(self, id, field):
        if field not in self._table_columns:
            return False
        update_sql = 'UPDATE feedback SET {field}={field}+1  WHERE id=%s'.format(field=field)
        return self.runSQL4RowCount(update_sql, str(id))

'''
反馈标签model
'''
class FeedbackTags(FrontBaseModel):
    def __init__(self):
        self._table = 'feedback_tags'
        self.setPK('id')
        self._table_columns = ['id', 'name', 'status', 'create_time', 'creator_id']
        self._table_columns_rule = {'name':['required'] }
        super(FeedbackTags, self).__init__()

    #通过名称模糊匹配tag
    def getItemsByName(self, name, page=1):
        if not name:
            return []
        return self.queryMany(filterString=[('name', ('like', name+'%')), ('status', 1)], fields=['id', 'name'], orderBy=[('id', 'DESC')], limit=20, pageNo=page)

    #通过name获取标签信息
    def getItemByName(self, name):
        if not name:
            return None
        return self.queryOne(filterString=[('name', name)], fields=self._table_columns)

    #通过ids获取tag列表
    def getTagListByIds(self, ids=[]):
        ids = set(ids)
        if not ids:
            return {}
        list = self.queryMany(filterString=[('id', ('in', ids))], fields=self._table_columns)
        res = {}
        for item in list:
            res[item['id']] = item
        del list
        return res

'''
反馈评论model
'''
class FeedbackComment(FrontBaseModel):

    def __init__(self):
        self._table = 'feedback_comment'
        self.setPK('id')
        self._table_columns = [ 'id',
                                'comment',
                                'create_time',
                                'status',
                                'feedback_id',
                                'pid',
                                'uid',
                                'to_uid',
                                'rank_sort',
                                'oppose_votes',
                                'approval_votes',
                                'reply_count',
                                'ancestor_id',
                                'complaint_count',
                            ]
        self._table_columns_rule = {'comment':['required']}
        super(FeedbackComment, self).__init__()

    def getFeedbackCommentsByFid(self, fid, page, limit):
        if not fid:
            return []
        list = self.queryMany(filterString=[('feedback_id', fid), ('ancestor_id', 0)], fields=self._table_columns, orderBy=[('rank_sort', 'DESC')], limit=limit, pageNo=page)
        res = {}
        for item in list:
            res[item['id']] = item
        del list
        return res

    def getFeedbackCommentCountByFid(self, fid):
        return self.queryOne(filterString=[('status', 1), ('ancestor_id', 0), ('feedback_id', fid)], fields=['count(*) AS total'])

    def getSonFeedbackCommentByAncestorId(self, aids, page, limit):
        if not aids:
            return {}
        res = {}
        list = self.queryMany(filterString=[('ancestor_id', ('in', aids))], fields=self._table_columns, orderBy=[('create_time', 'DESC')], limit=limit, pageNo=page)
        for item in list:
            temp = res.get(item['ancestor_id'], None)
            if not temp:
                res[item['ancestor_id']] = [item]
            else:
                res[item['ancestor_id']].append(item)
        del list
        return res

    def getReplyCount(self, cids):
        if not cids:
            return {}
        list = self.queryMany(filterString=[('status', 1), ('ancestor_id', ('in', cids))], fields=['id', 'count(*) AS total'])
        res = {}
        for item in list:
            res[item['id']] = [item['total']]
        return res

    #点赞操作
    def operateLike(self, id, uid, type):

        id = str(id)
        uid = str(uid)

        if type not in ['approval_votes', 'oppose_votes']:
            return False

        #获取feedback信息
        info = self.getItem(id)
        if not info:
            return False

        rank_sort = info['rank_sort']
        ups = info['approval_votes']
        downs = info['oppose_votes']

        #先判断是否已经点赞过
        fcvu = FeedbackCommentVoteUser()
        has_vote = fcvu.getFeedbackCommentVoteByFcidAndUid(id, uid)
        if has_vote:
            if has_vote['approval_votes']==1 and type=='approval_votes':
                return -1
            elif has_vote['oppose_votes']==1 and type=='oppose_votes':
                return -1

            #如果已经点赞 现在操作是反对 那么总票数要-1
            if has_vote['approval_votes']==1 and type=='oppose_votes':
                ups = ups - 1
                downs = downs + 1
                rank_sort = confidence(ups, downs)
                sql = "UPDATE feedback_comment SET oppose_votes=oppose_votes+1, approval_votes=approval_votes-1, rank_sort=%s WHERE id=%s"
                update_sql = "UPDATE feedback_comment_vote_user SET vote_type=2 WHERE fcid=%s AND uid=%s"

            elif has_vote['oppose_votes']==1 and type=='approval_votes':
                ups = ups + 1
                downs = downs - 1
                rank_sort = confidence(ups, downs)
                sql = "UPDATE feedback_comment SET approval_votes=approval_votes+1, oppose_votes=oppose_votes-1, rank_sort=%s WHERE id=%s"
                update_sql = "UPDATE feedback_comment_vote_user SET vote_type=1 WHERE fcid=%s AND uid=%s"

            else:
                return False

            update_res = self.runSQL4RowCount(update_sql, *(str(id), str(uid)))
            if update_res:
                res = self.runSQL4RowCount(sql, str(id))
                if not res:
                    return False
                else:
                    return 1
            else:
                return False

        #用户投票关系表中插入数据
        item = {'fcid':id, 'uid':uid, 'vote_type': 1 if type=='approval_votes' else 2}
        res = fcvu.addItem(item)
        if not res:
            return -1

        if type=='approval_votes':
            rank_sort = confidence(ups+1, downs)
        else:
            rank_sort = confidence(ups, downs+1)

        sql = "UPDATE feedback_comment SET {field}={field}+1, rank_sort=%s WHERE id=%s".format(field=type)
        return self.runSQL4RowCount(sql, *(rank_sort, id))


    #检测评论的内容是否一样，不一样返回false
    def checkIsRepeatComment(self, comment, uid, feedback_id, pid):
        item = self.queryOne(filterString=[('uid', uid), ('feedback_id', feedback_id), ('pid', pid)], fields=self._table_columns, orderBy=[('create_time', 'DESC')])
        if item['comment'].strip()==comment.strip():
            return True
        return False


    #保存评论信息
    def addComment(self, settings, uid, pid, ancestor_id, comment, feedback_id, create_time, comment_uid, type='feedback'):
        #过滤评论
        comment, imgs = utiles.filterContent(settings, comment)
        #检查非法字符
        filter_obj = DictFilter()
        new_comment, bad_words = filter_obj.match_all(comment)
        item = {    'uid': int(uid),
                    'comment': new_comment,
                    'feedback_id': feedback_id,
                    'ancestor_id': ancestor_id,
                    'pid': pid,
                    'create_time': create_time,
                    'to_uid': comment_uid
                }
        id = self.addItem(item)
        if not id:
            for img in imgs:
                if os.path.isfile(img):
                    os.remove(img)
        else:
            if type=='feedback':
                feedback = Feedback()
                feedback.updateFeedbackCount(feedback_id, 'answers')
            elif type=='feedback_comment':
                self.updateFeedbackCommentCount(pid, 'reply_count', 'add')
        return id, new_comment


    #修改反馈评论表里的字段增值
    def updateFeedbackCommentCount(self, id, field, op='minus'):
        if field not in self._table_columns:
            return False
        op_code = '+'
        if op=='minus':
            op_code = '-'
        update_sql = 'UPDATE {table} SET {field}={field}{op}1  WHERE id=%s'.format(table=self._table , op=op_code, field=field)
        return self.runSQL4RowCount(update_sql, str(id))

'''
反馈评论和用户关系表
'''
class FeedbackCommentVoteUser(FrontBaseModel):
    def __init__(self):
        self._table = 'feedback_comment_vote_user'
        self.setPK('id')
        self._table_columns = [ 'id',
                                'fcid',
                                'uid',
                                'vote_type',
                                'create_time',
                            ]
        self._table_columns_rule = {'fcid':['required'], 'uid':['required'], 'create_time':['required']}
        super(FeedbackCommentVoteUser, self).__init__()

    def getFeedbackCommentVoteByFcidAndUid(self, fcid, uid):
        item = self.queryOne(filterString=[('fcid', fcid), ('uid', uid)], fields=self._table_columns)
        if not item:
            return None
        return {'approval_votes':1, 'oppose_votes':0} if int(item['vote_type'])==1 else {'approval_votes':0, 'oppose_votes':1}


'''
反馈和用户关系表
'''
class FeedbackVoteUser(FrontBaseModel):
    def __init__(self):
        self._table = 'feedback_vote_user'
        self.setPK('id')
        self._table_columns = [ 'id',
                                'fid',
                                'uid',
                                'vote_type',
                                'create_time',
                            ]
        self._table_columns_rule = {'fid':['required'], 'uid':['required'], 'create_time':['required']}
        super(FeedbackVoteUser, self).__init__()

    def getFeedbackVoteByFidAndUid(self, fid, uid):
        item = self.queryOne(filterString=[('fid', fid), ('uid', uid)], fields=self._table_columns)
        if not item:
            return None
        return {'approval_votes':1, 'oppose_votes':0} if int(item['vote_type'])==1 else {'approval_votes':0, 'oppose_votes':1}


'''
反馈评论投诉表
'''
class FeedbackCommentComplaint(FrontBaseModel):
    def __init__(self):
        self._table = 'feedback_comment_complaint'
        self.setPK('id')
        self._table_columns = [ 'id',
                                'fcid',
                                'reason',
                                'uid',
                                'create_time',
                            ]
        self._table_columns_rule = {'fcid':['required'], 'uid':['required'], 'create_time':['required'], 'reason':['required']}
        self._table_columns_autoload = {'create_time': time.time()}
        super(FeedbackCommentComplaint, self).__init__()
