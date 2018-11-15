# -*- coding: utf-8 -*-
from tornado.web import asynchronous, HTTPError, StaticFileHandler
from tornado import escape
from tornado.options import options
from tornado import locale
from tornado import gen
from tornado.ioloop import IOLoop
from tornado.escape import json_encode
from handler import BaseHandler
from protected.models.user import User
from protected.models.socialGroup import SocialGroup
from protected.models.commonDistrict import CommonDistrict
from protected.models.characterTest import BfiCharacterTest, UserBfiTest
from protected.models.friendEmails import FriendEmails
from protected.models.userVerify import UserVerify
from protected.models.sysConfig import SysConfig
from protected.libs.const import ErrorMessage, SuccessMessage
import sys, time, hashlib, re, urlparse, uuid, os, datetime
import pygal
from pygal import Config
from protected.libs.MyCrypt import MyCrypt
import protected.libs.utils as utiles
from protected.libs.emailTool import SendEmail, JumpEmail, CheckEmailAddressList
from email.mime.text import MIMEText
from email.header import Header
from protected.libs.decorators import checkVerify
from protected.libs.pydenticon import genarateAvatar
#_chinese_character_re = re.compile(u"[\u4e00-\u9fa5]")

class LoginHandler(BaseHandler):
    user = User()
    def get(self):
        self._context.next = self.get_next_url()
        self._context.title = self._locale.translate('login_name').encode("utf-8")
        self.render("user/login.html", url_escape=escape.url_escape)

    def post(self):
        ip = self.request.remote_ip
        user_password = self.get_argument('user_password', None)
        user_email = self.get_argument('user_email', None)
        info = self.user.login(user_email)

        if info:
            hash = hashlib.md5()
            hash.update(str(info['salt'])+str(user_password))
            if info['pass_word']!=hash.hexdigest():
                ret = {'msg': ErrorMessage.error_message['004'], 'code': 'error'}
                self.finish(self.write(json_encode(ret)))
            #当前时间戳
            now = time.time()
            if info['user_ip']!=ip:
                self.user.updateInfo([('user_ip', ip), ('login_time', utiles.timestampToDate(now))], [('id', info.id)])
            else:
                #更新登录时间
                self.user.updateInfo([('login_time', utiles.timestampToDate(now))], [('id', info.id)])
            self.set_secure_cookie("uid", str(info.id), expires=time.time()+options.reg_time_out)
            #判断记住帐号
            remember = self.get_argument('remember', '')
            if remember==1:
                #加密免登录
                fp = self.get_argument('fp', '')
                ec = MyCrypt(options.login_key)
                data = '{"fp": %s, "date": %s, "salt": %s, "ip": %s, "uid": %s}' % (fp, now, info['salt'], ip, info.id)
                self.set_secure_cookie('token', str(ec.encrypt(data)), expires=now+options.remember_time_out)
                self.set_secure_cookie('token_time', str(ec.encrypt(now)), expires=now+options.remember_time_out)
            ret = {'msg': SuccessMessage.success_message['001'], 'code': 'success', 'res': info, 'next': self.get_next_url()}
            self.finish(self.write(self.json_encode(ret)))
        else:
            ret = {'msg': ErrorMessage.error_message['003'], 'code': 'error'}
            self.finish(self.write(json_encode(ret)))

class LogoutHandler(BaseHandler):
    def post(self):
        pass
    def get(self):
        self.clear_cookie("uid")
        self.redirect('/')

#消除本地账号缓存
class ClearaccountHandler(BaseHandler):
    def post(self):
        self.clear_cookie("token")
        self.clear_cookie("token_time")
        url = self.get_next_url()
        self.return_json({'msg': SuccessMessage.success_message['002'], 'code': 'success', 'next': url})
    def get(self):
        self.clear_cookie("token")
        self.clear_cookie("token_time")
        url = self.get_next_url()
        self.redirect(url)

#注册
from protected.conf.debug import logger
class RegHandler(BaseHandler):

    d = CommonDistrict()

    #地区赋值
    def assignDirection(self):
        items = self.d.getDistrict(0)
        self._context.district = items

    #生成密码
    def generatePwd(self, reg_password, salt):
        hash = hashlib.md5()
        hash.update(salt+str(reg_password))
        return hash.hexdigest()

    #到邮箱验证用户注册url
    def checkTokenUrl(self, uid):
        ret = {'code': 'success', 'is_send': True}
        ret_017 = {'msg': ErrorMessage.error_message['017'], 'code': 'error', 'num': '017', 'is_send': False}
        ret_016 = {'msg': ErrorMessage.error_message['016'], 'code': 'error', 'num': '016', 'is_send': True}
        ret_019 = {'msg': ErrorMessage.error_message['019'], 'code': 'error', 'num': '019', 'is_send': False}
        ret_022 = {'msg': ErrorMessage.error_message['022'], 'code': 'error', 'num': '022', 'is_send': False}
        u = User()
        u_info = u.getItem(uid)
        if not u_info:
            return ret_022
        else:
            if u_info['is_verify']==0:
                return ret_016
            else:
                return ret
        #获取用户验证信息
        uv = UserVerify()
        uv_info = uv.getVerifyInfo(uid)
        if not uv_info:
            return ret_017
        if utiles.formateDateToTimestamp(uv_info['verify_expire_time']) < int(time.mktime(datetime.datetime.now().timetuple())):
            return ret_019
        #需要发送邮件 code=error不需要发送邮件
        return ret

    #保存推荐的朋友和活动信息
    def saveRecommend(self):
        rec_friends = self.get_argument('rec_friends', None)
        rec_activities = self.get_argument('rec_activities', None)

    #生成头像
    def generateAvatar(self, email):
        if not email:
            return False
        identicon_png = genarateAvatar(email)
        now = datetime.datetime.now()
        #存储头像的路径
        avatar_url = self.settings['uploads_path'] + os.path.sep + 'avatar' + os.path.sep + now.year + '-' + utiles.dateRange(now.month)
        if not os.path.isdir(avatar_url):
            os.makedirs(avatar_url)
        avatar_img_name = hashlib.sha256(str(uuid.uuid4())) + '_' + str(int(time.time())) + '.png'
        avatar = avatar_url + os.path.sep + avatar_img_name
        with open(avatar, 'wb') as f:
            f.write(identicon_png)
        return now.year + '-' + utiles.dateRange(now.month) + os.path.sep + avatar_img_name

    _handler_template = "user/reg.html"

    user = User()

    @gen.coroutine
    @asynchronous
    def post(self):
        update = int(self.get_argument('reg_update', 0))
        next_step = self.get_argument("next_step", 1)
        # 防止穷举
        yield gen.Task(IOLoop.instance().add_timeout, time.time() + 2)
        error = []
        #获取用户uid
        uid = self.get_secure_cookie('uid', None)
        if next_step == '1':
            item = {}
            reg_email = self.get_argument("reg_email", '')
            reg_password = self.get_argument("reg_password", '')
            reg_again_password = self.get_argument("reg_again_password", '')
            reg_agree = self.get_argument("reg_agree", '')
            reg_area = self.get_argument('h_reg_area', '')
            reg_gender = self.get_argument('reg_gender', 0)
            reg_user_name = self.get_argument('reg_user_name', '')
            salt = str(utiles.generate_randsalt(size=5))

            if update == '1':
                #当uid失效 页面进入注册空页面
                if not uid:
                    self.assignDirection()
                    self._handler_template = 'user/reg.html'
                    self._context.next = self.get_next_url()
                    self._context.error = []
                    self.render(self._handler_template)
                    return
                if reg_email:
                    if not utiles.validateEmail(reg_email):
                        error.append(ErrorMessage.error_message['005'])
                    else:
                        item['user_email'] = reg_email
                if reg_password and reg_again_password:
                    if len(reg_password) < 6:
                        error.append(ErrorMessage.error_message['006'])
                    elif reg_password != reg_again_password:
                        error.append(ErrorMessage.error_message['007'])
                    else:
                        item['pass_word'] = self.generatePwd(reg_password, salt)
                #判断邮箱和用户名是否重复
                if self.user.checkUserOrEmail(reg_email, 'email', uid):
                    error.append(ErrorMessage.error_message['011'])
                if self.user.checkUserOrEmail(reg_user_name, '', uid):
                    error.append(ErrorMessage.error_message['012'])

                if reg_gender:
                    item['gender'] = reg_gender
                if reg_area:
                    item['area_id'] = reg_area
                if reg_user_name:
                    item['user_name'] = reg_user_name
                item['salt'] = salt
                item['id'] = uid
            else:
                #判断用户名是否重复
                if self.user.checkUserOrEmail(reg_user_name):
                    error.append(ErrorMessage.error_message['012'])
                #判断用户邮箱是否重复
                if self.user.checkUserOrEmail(reg_email, 'email'):
                    error.append(ErrorMessage.error_message['011'])
                if not utiles.validateEmail(reg_email):
                    error.append(ErrorMessage.error_message['005'])
                if len(reg_password) < 6:
                    error.append(ErrorMessage.error_message['006'])
                if reg_password != reg_again_password:
                    error.append(ErrorMessage.error_message['007'])
                if not reg_agree:
                    error.append(ErrorMessage.error_message['008'])
                if not reg_area:
                    error.append(ErrorMessage.error_message['009'])
                if not reg_gender:
                    error.append(ErrorMessage.error_message['013'])

            if error:
                self.assignDirection()
                self._context.error = ','.join(error)
                self._handler_template = 'user/reg.html'
                self._context.next = self.get_next_url()
                if uid:
                    user_info = self.user.getItem(uid)
                    self._context.user_info = user_info
                    self._context.area = ','.join(self.d.getDistrictParents(user_info['area_id'], res=[]))
                self.render(self._handler_template)
                return

            #保存注册信息
            ip = self.request.remote_ip
            now = time.time()
            #修改用户注册信息
            if update==1:
                if not item:
                    self.redirect("/reg/?step=1")
                    return
                count = self.user.updateItem(item)
                if count==0:
                    self.assignDirection()
                    self._context.error = ErrorMessage.error_message['014']
                    self._handler_template = 'user/reg.html'
                    self.render(self._handler_template)
                res = uid
            else:
                avatar = self.generateAvatar(reg_email)
                res = self.user.addItem(item={
                                            'area_id': reg_area,
                                            'user_name': reg_user_name if reg_user_name else '',
                                            'user_email': reg_email,
                                            'pass_word': self.generatePwd(reg_password, salt),
                                            'user_ip': ip,
                                            'salt': salt,
                                            'gender': reg_gender,
                                            'create_time': utiles.timestampToDate(now),
                                            'avatar': avatar
                                        })
            if res:
                self.set_secure_cookie("uid", str(res), expires=time.time()+options.reg_time_out)
                self.redirect("/reg/?step=1")
            else:
                self.assignDirection()
                self._context.error = ErrorMessage.error_message['010']
                self._handler_template = "user/reg.html"
            self.render(self._handler_template)
            self.finish()
        elif next_step == '2':
            #获取用户验证信息
            ret = self.checkTokenUrl(uid)
            if ret['code']=='error':
                if uid:
                    #获取用户信息
                    user_info = self.user.getItem(uid)
                    self._context.user_info = user_info
                    self._context.user_email = user_info['user_email']
                self._context.error = ret['msg']
                self._context.is_send = ret['is_send']
                self._handler_template = 'user/reg_step_1.html'
                self.render(self._handler_template)
                return
            self.redirect("/reg/?step=2")
            return
        elif next_step == '3':
            self.redirect("/reg/?step=3")
        elif next_step == 'end':
            #保存推荐的朋友和活动信息

            self.redirect("/activity")
        else:
            self._handler_template = "user/reg_step_end.html"
        self._context.error = error
        self.render(self._handler_template)

    #获取性格列表
    def getChaList(self):
        bfi = BfiCharacterTest()
        return bfi.getAll()

    #活动推荐
    def getSocialGroups(self):
        group = SocialGroup()
        page_num = self.get_argument("stpage_numep", 1)
        group_list = group.getSocialGroupList(page_num)
        self._context.group_list = group_list

    def get(self):
        self._context.error = ''
        step = self.get_argument("step", 0)
        self._context.next = self.get_next_url()
        #获取用户uid
        user_info = None
        uid = self.get_secure_cookie('uid', None)
        if (step=='1' or step=='2' or step=='3' or step=='end') and (not uid):
            self.redirect('/reg/?step=0')
            return
        else:
            #获取用户信息
            user_info = self.user.getItem(uid)
        if urlparse.urlparse(self._context.next).path == '/reg':
            self._context.next = '/index'
        if step == '0':
            self.assignDirection()
            if uid:
                self._context.user_info = user_info
                self._context.area = ','.join(self.d.getDistrictParents(user_info['area_id'], res=[]))
            else:
                self._context.user_info = None
            self._handler_template = 'user/reg.html'
        elif step == '1':
            #判断用户是否保存到cookie中
            if not uid:
                self.redirect('/reg/?step=0')
            #获取用户信息
            user_info = self.user.getItem(uid)
            self._context.user_info = user_info
            self._context.user_email = user_info['user_email']
            #判断是否给用户发送了邮件
            self._context.is_send = True
            uv = UserVerify()
            uv_info = uv.getVerifyInfo(uid)
            if uv_info:
                #不需要发送邮件
                self._context.is_send = False
                #验证url没有过期
                now = int(time.mktime(datetime.datetime.now().timetuple()))
                if user_info['is_verify']!=1 and utiles.formateDateToTimestamp(uv_info['verify_expire_time']) > now:
                    self._context.error = ErrorMessage.error_message['016']
                elif user_info['is_verify']!=1 and utiles.formateDateToTimestamp(uv_info['verify_expire_time']) <= now:
                    self._context.is_send = True
            self._handler_template = 'user/reg_step_1.html'

        elif step == '2':
            #判断是否给用户发送了邮件
            ret = self.checkTokenUrl(uid)
            self._context.is_send = True if ret['code']=='success' else False
            if ret['code']=='error':
                self._context.error = ret['msg']
                self._handler_template = 'user/reg_step_1.html'
            else:
                list = self.getChaList()
                self._context.list = list
                self._context.ids = ','.join([str(item['id']) for item in list])
                self._handler_template = 'user/reg_step_2.html'

        elif step == '3':
            ut = UserBfiTest()
            ut_info = ut.queryOne(filterString=[('uid', uid)], fields=ut._table_columns)
            if ut_info:
                #获取性格测试平均值
                sysconfig = SysConfig()
                bfi_vals = sysconfig.getConfig('bfi_total')
                bfi_user_total = int(sysconfig.getConfig('bfi_user_total')['val'])

                #建立雷达图
                config = Config()
                config.explicit_size = True
                config.width = 500
                config.height = 450
                config.label_font_size = 14
                config.x_label_rotation = 1
                radar_chart = pygal.Radar(config)
                radar_chart.title = u'人格初测结果'
                radar_chart.x_labels = [u'开放性O', u'神经质N', u'宜人性A', u'外向型E', u'尽职性C']
                radar_chart.add(user_info['user_name'], [int(ut_info['O_val']), int(ut_info['N_val']), int(ut_info['A_val']), int(ut_info['E_val']), int(ut_info['C_val'])])
                radar_chart.add(u'平均值', [bfi_vals['O']/bfi_user_total, bfi_vals['N']/bfi_user_total, bfi_vals['A']/bfi_user_total, bfi_vals['E']/bfi_user_total, bfi_vals['C']/bfi_user_total])
                self._context.radar = radar_chart.render()
                #评价
                self._context.N_msg = BfiCharacterTest.transform('N', int(ut_info['N_val']))[0]
                self._context.O_msg = BfiCharacterTest.transform('O', int(ut_info['O_val']))[0]
                self._context.A_msg = BfiCharacterTest.transform('A', int(ut_info['A_val']))[0]
                self._context.E_msg = BfiCharacterTest.transform('E', int(ut_info['E_val']))[0]
                self._context.C_msg = BfiCharacterTest.transform('C', int(ut_info['C_val']))[0]
                #从人格特点推荐好友

                #活动推荐

            else:
                self._context.radar = None

            self._handler_template = 'user/reg_step_3.html'

        #跳转到活动列表页
        elif step == 'end':
            self.redirect('/activity')

        self.render(self._handler_template)
        return

class CharacterTestHandler(BaseHandler):
    ct = BfiCharacterTest()
    ubt = UserBfiTest()
    _handler_template = 'user/reg_step_3.html'
    def post(self, *args, **kwargs):
        uid = self.get_secure_cookie('uid', None)
        if not uid:
            self.redirect('/reg/?step=0')
        list = self.ct.getAll()
        tmp = []
        #适应性 第1排＋第6排＋第11排＋第16排＋第21排＝
        N = 0
        #社交性 第2排＋第7排＋第12排＋第17排＋第22排＝
        E = 0
        #开放性 第3排＋第8排＋第13排＋第18排＋第23排＝
        O = 0
        #利他性 第4排＋第9排＋第14排＋第19排＋第24排＝
        A = 0
        #道德感 第5排＋第10排＋第15排＋第20排＋第25排＝
        C = 0
        for item in list:
            id = str(item['id'])
            bfi_val = self.get_argument('bfi_'+id, 0)
            if bfi_val!=0:
                tmp.append(id+':'+bfi_val)
            val = int(bfi_val)
            id = int(id)
            if id in [1,6,11,16,21]:
                N += val
            elif id in [2,7,12,17,22]:
                E += val
            elif id in [3,8,13,18,23]:
                O += val
            elif id in [4,9,14,19,24]:
                A += val
            elif id in [5,10,15,20,25]:
                C += val
        #大五性格测试结果
        vals = {}
        vals['N'] = N
        vals['E'] = E
        vals['O'] = O
        vals['A'] = A
        vals['C'] = C
        ret = self.ubt.saveCharacterTest(uid, ','.join(tmp), vals)
        self._context.error = None
        if ret>0:
            self.redirect('/reg/?step=3')
            return
        else:
            self._context.error = ErrorMessage.error_message['023']
            self.render(self._handler_template)

    def get(self, *args, **kwargs):
        pass

class SendEmailHandler(BaseHandler):
    @checkVerify
    @gen.coroutine
    @asynchronous
    def post(self, *args, **kwargs):
        email_opt = options.email
        email_addr = self.get_argument('email')
        #token|uid|email
        ec = MyCrypt(options.login_key)
        uid = self.get_secure_cookie('uid', None)
        if not uid:
            self.return_json({'msg': ErrorMessage.error_message['024'], 'code': 'error', 'num': '024'})

        token = ec.encrypt("%s|%s|%s" % (uuid.uuid1(), uid, email_addr))

        content = '验证邮件'
        msg = MIMEText(content, _subtype='html', _charset='UTF-8')
        msg['Subject'] = Header('中文的标题22', charset='UTF-8')
        msg['To'] = email_addr
        msg['From'] = email_opt['FROM_ADDR']

        smtp = SendEmail(email_opt['SMTP_SERVER'], email_opt['SMTP_PORT'])
        yield smtp.login(email_opt['SMTP_USER'], email_opt['SMTP_PASSWORD'])
        try:
            uv = UserVerify()
            #修改用户的验证码
            tmp = uv.saveToken(uid=uid, token=token)
            if tmp and isinstance(tmp, bool):
                yield smtp.sendmail(email_opt['FROM_ADDR'], email_addr, msg)
            elif tmp and (not isinstance(tmp, bool)):
                self.return_json({'msg': ErrorMessage.error_message['018'], 'code': 'success', 'num': '018'})
            else:
                self.return_json({'msg': ErrorMessage.error_message['015'], 'code': 'error', 'num': '015'})
        except Exception, e:
            self.return_json({'msg': ErrorMessage.error_message['015'], 'code': 'error', 'num': '015', 'e': str(e)})

        jump = JumpEmail.goEmailUrl(email_addr)
        self.return_json({'msg': SuccessMessage.success_message['003'], 'code': 'success', 'res': jump if jump else '', 'host':options.domain_name})
        return

    @checkVerify
    def get(self, *args, **kwargs):
        email = self.get_argument('email', '')
        jump = JumpEmail.goEmailUrl(email)
        self._context.jump = jump
        self.render('user/reg_email.html')

#到邮箱确认用户验证
class VerifyEmailHandler(BaseHandler):
    def get(self, *args, **kwargs):
        token = self.get_argument('token', None)
        if token:
            now = int(time.mktime(datetime.datetime.now().timetuple()))
            ec = MyCrypt(options.login_key)
            decrpt_data = ec.decrypt(token)
            decrpt_data = decrpt_data.split('|')

            #修改用户的验证标识
            uv = UserVerify()
            uv_info = uv.queryOne(filterString=[('token', decrpt_data[0])])
            if not uv_info:
                self._context.error = ErrorMessage.error_message['025']
            else:
                if uv_info['uid']!=decrpt_data[1]:
                    self._context.error = ErrorMessage.error_message['025']
                elif utiles.formateDateToTimestamp(uv_info['verify_expire_time']) < now:
                    self._context.error = ErrorMessage.error_message['026']
                else:
                    user = User()
                    u_info = user.queryOne(filterString=[('id', decrpt_data[1])])
                    if u_info['user_email']!=decrpt_data[2]:
                        self._context.error = ErrorMessage.error_message['025']
                    else:
                        if u_info['is_verify']==1:
                            self._context.error = ErrorMessage.error_message['027']
                        user.updateInfo(filterString=[('is_verify', 1)], where=[('id', decrpt_data[1])])
                        #修改用户总数
                        config = SysConfig()
                        config.incConfig('user_total')
                        self._context.msg = SuccessMessage.success_message['005']
        else:
            self._context.error = ErrorMessage.error_message['025']
        self.render('./msg.html')

#读取邮件列表信息
class ReadEmailListHandler(BaseHandler):
    @gen.coroutine
    @asynchronous
    def post(self):
        uid = self.get_secure_cookie('uid')
        email_name = self.get_argument('email_name', '')
        email_name = email_name.replace('.', '_')
        now = datetime.datetime.now()
        date = now.strftime("%Y-%m-%d")
        UPLOAD_FILE_PATH = self.settings['uploads_path'] + os.path.sep + date + os.path.sep + 'email' + os.path.sep
        if not os.path.isdir(UPLOAD_FILE_PATH):
            os.makedirs(UPLOAD_FILE_PATH)
        #获取文件
        if self.request.files.get('email_list', None):
            email_list = self.request.files['email_list'][0]
            filename = email_list['filename']
            ext = os.path.splitext(filename)[-1]
            if ext not in ['.vcf', '.csv']:
                self.return_json({'msg': '文件格式不正确', 'code': 'error'})
            dir = UPLOAD_FILE_PATH + uid + '_' + email_name + '_' + filename
            fileObj = open(dir, 'wb')
            fileObj.write(email_list['body'])
            fileObj.close()
            list = CheckEmailAddressList.getEmail(dir)
            fe = FriendEmails()
            if not list:
                self.return_json({'msg': ErrorMessage.error_message['020'], 'code': 'error', 'num': '020'})
            res = yield fe.saveEmailsByUid(uid, list)
            if res<=0 or (not res):
                self.return_json({'msg': ErrorMessage.error_message['021'], 'code': 'error', 'num': '021'})
            else:
                self.return_json({'msg': SuccessMessage.success_message['004'], 'code': 'success'})

#获取联动地区
class DistrictHandler(BaseHandler):
    def post(self):
        district = CommonDistrict()
        pid = self.get_argument('pid', 0)
        list = district.getDistrict(pid)
        self.finish(self.write(json_encode(list)))

#判断用户名和邮箱是否唯一
class CheckUserHandler(BaseHandler):
    def post(self):
        val = self.get_argument('val', '')
        type = self.get_argument('type', '')
        user = User()
        if user.checkUserOrEmail(val, type)==False:
            ret = {'msg': '', 'code': 'success'}
        else:
            ret = {'msg': ErrorMessage.error_message['012' if type=='email' else '011'], 'code': 'error'}
        self.return_json(ret)


class TestHandler(BaseHandler):
    def get(self):
        wd = self.get_argument('wd', '')
        if wd:
            self.return_json({'value': [{"word": "fuck1", "id":1}, {"word": "fuck2", 'id':2}]})
        self.render("test.html", url_escape=escape.url_escape)
        pass

from tornado import gen,web
from concurrent.futures import ThreadPoolExecutor
from tornado.concurrent import run_on_executor
class Test2Handler(BaseHandler):
    executor = ThreadPoolExecutor(2)
    @gen.coroutine
    def get(self):
        #调用下层API
        str1 = self.api_1()
        self.write(str(str1))
        self.write('<br/>ssss')
        self.finish()
    @run_on_executor
    def api_1(self):
        #time.sleep(10)
        return "Hello Word"


handlers = [
    (r"/login", LoginHandler),
    (r"/logout", LogoutHandler),
    (r"/reg", RegHandler),
    (r"/checkuser", CheckUserHandler),
    (r"/district", DistrictHandler),
    (r"/clearaccount", ClearaccountHandler),
    (r"/sendemail", SendEmailHandler),
    (r"/reademail", ReadEmailListHandler),
    (r"/verifyemail", VerifyEmailHandler),
    (r"/character", CharacterTestHandler),
    (r"/avatar/(.*)", StaticFileHandler, {"path": "uploads/avatar"}),
    (r"/test", TestHandler),
    (r"/test2", Test2Handler),
]