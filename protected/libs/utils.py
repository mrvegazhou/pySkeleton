# -*- coding: utf-8 -*-
import datetime
from tornado.util import import_object
from tornado import gen, httpclient
from tornado.web import asynchronous
import datetime,time,os,re,sys,types,json,random,itertools,urllib,socket

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY3:
    string_types = str,
    integer_types = int,
    class_types = type,
    text_type = str
    binary_type = bytes

    MAXSIZE = sys.maxsize
else:
    string_types = basestring,
    integer_types = (int, long)
    class_types = (type, types.ClassType)
    text_type = unicode
    binary_type = str

def find_modules(modules_dir):
    try:
        return [f[:-3] for f in os.listdir(modules_dir)
                if not f.startswith('_') and f.endswith('.py')]
    except OSError:
        return []

#
def timeBefore(d):
    chunks = (
        (60 * 60 * 24 * 365, u'年'),
        (60 * 60 * 24 * 30, u'月'),
        (60 * 60 * 24 * 7, u'周'),
        (60 * 60 * 24, u'天'),
        (60 * 60, u'小时'),
        (60, u'分钟'),
    )
    #如果不是datetime类型转换后与datetime比较
    if not isinstance(d, datetime.datetime):
        d = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(d))
        d = datetime.datetime.strptime(d, "%Y-%m-%d %H:%M:%S")

    now = datetime.datetime.now()
    delta = now - d
    #忽略毫秒
    before = delta.total_seconds()
    #刚刚过去的1分钟
    if before <= 60:
        before = 1 if before < 1 else before
        return str(int(before)) + u'秒前'
    u = None
    c = 0
    for seconds, unit in chunks:
        count = before // seconds
        c = count
        u = unit
        if count != 0:
            break

    if c>6 and u==u'月':
        return d.strftime("%Y/%m/%d %H:%M:%S")
    return unicode(int(count)) + unit + u"前"

def dateRange(month):
    if month<3:
        return 1
    elif month>=3 and month<6:
        return 3
    elif month>=6 and month<9:
        return 6
    elif month>=9 and month<12:
        return 9
    elif month==12:
        return 12

def dict_to_list(d):
    a = []
    for key, value in d.iteritems():
        if (type(value) is dict):
            value = dict_to_list(value)
        a.append([key, value])
    return a

def safestr(obj, encoding='utf-8'):
    r"""
    Converts any given object to utf-8 encoded string.

        >>> safestr('hello')
        'hello'
        >>> safestr(u'\u1234')
        '\xe1\x88\xb4'
        >>> safestr(2)
        '2'
    """
    if isinstance(obj, unicode):
        return obj.encode(encoding)
    elif isinstance(obj, str):
        return obj
    elif hasattr(obj, 'next'):  # iterator
        return itertools.imap(safestr, obj)
    else:
        return str(obj)

def safeunicode(obj, encoding='utf-8'):
    """
    Converts any given object to unicode string.

        >>> safeunicode('hello')
        u'hello'
        >>> safeunicode(2)
        u'2'
        >>> safeunicode('\xe1\x88\xb4')
        u'\u1234'
    """
    t = type(obj)
    if t is unicode:
        return obj
    elif t is str:
        return obj.decode(encoding)
    elif t in [int, float, bool]:
        return unicode(obj)
    elif hasattr(obj, '__unicode__') or isinstance(obj, unicode):
        return unicode(obj)
    else:
        return str(obj).decode(encoding)

'''随机字符串'''
def generate_randsalt(list = '0123456789abcdefghijklmnopqrstuvwxyz', size = 8):
    salt = ''
    while (size > 0):
        salt = salt + random.choice(list)
        size = size - 1
    return salt

"""全角转半角"""
def strQ2B(ustring):
    rstring = ""
    for uchar in ustring:
        inside_code=ord(uchar)
        if inside_code == 12288:                              #全角空格直接转换
            inside_code = 32
        elif (inside_code >= 65281 and inside_code <= 65374): #全角字符（除空格）根据关系转化
            inside_code -= 65248
        rstring += unichr(inside_code)
    return rstring
"""半角转全角"""
def strB2Q(ustring):
    rstring = ""
    for uchar in ustring:
        inside_code=ord(uchar)
        if inside_code == 32:                                 #半角空格直接转化
            inside_code = 12288
        elif inside_code >= 32 and inside_code <= 126:        #半角字符（除空格）根据关系转化
            inside_code += 65248
        rstring += unichr(inside_code)
    return rstring

"""获取文件大小"""
def get_file_size(file):
    file.seek(0, 2)  # Seek to the end of the file
    size = file.tell()  # Get the position of EOF
    file.seek(0)  # Reset the file position to the beginning
    return size
"""判断图片类型"""
def checkImgType(type):
    IMAGE_TYPES = re.compile('image/(gif|p?jpeg|(x-)?png)')
    return IMAGE_TYPES.match(type)
'''验证邮箱'''
def validateEmail(email):
    if len(email) > 7:
        if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
            return True
    return False
'''验证手机号和座机号'''
def validateTel(tel):
    if re.match("^(010\d{8})|(0[2-9]\d{9})|(13\d{9})|(14[57]\d{8})|(15[0-35-9]\d{8})|(18[0-35-9]\d{8})$", tel) != None:
        return True
    return False
"""判断一个unicode是否是汉字"""
def validatChinese(uchar):
    if uchar >= u'\u4e00' and uchar<=u'\u9fa5':
        return True
    else:
        return False
"""判断一个unicode是否是数字"""
def validateNumber(uchar):
    try:
        float(uchar)
        return True
    except ValueError:
        pass
    try:
        import unicodedata
        unicodedata.numeric(uchar)
        return True
    except (TypeError, ValueError):
        pass
    return False

"""判断一个unicode是否是英文字母"""
def validateAlphabet(uchar):
    if (uchar >= u'\u0041' and uchar<=u'\u005a') or (uchar >= u'\u0061' and uchar<=u'\u007a'):
        return True
    else:
        return False
"""判断是否非汉字，数字和英文字符"""
def validateOther(uchar):
    if (not (validatChinese(uchar)) and (not validateNumber(uchar)) and (not validateAlphabet(uchar))):
        return True
    else:
        return False
"""判断值是否小于length"""
def validateLength(value, compare_str):
    compare_str = "{value}{compare}{length}".format(value=value, compare=re.search(r'\D+', compare_str).group(0), length=re.search(r'\d+', compare_str).group(0))
    if not eval(compare_str):
        return False
    return True
"""判断是否为日期格式"""
def validateDatetime(str):
    try:
        time.strptime(str, "%Y-%m-%d %H:%M:%S")
        return True
    except:
        return False

'''判断表字段'''
def checkColumnRules(rules, value):
    tmp = True
    for rule in rules:
        if isinstance(rule, dict):
            if rule.get('length'):
                if not validateLength(value, rule.get('length')):
                    tmp = False
        elif isinstance(rule, basestring):
            if rule=='required':
                if value=='' or value==None:
                    tmp = False
            if rule=='email':
                if not validateEmail(value):
                    tmp = False
            if rule=='tel':
                if not validateTel(value):
                    tmp = False
            if rule=='chinese':
                if not validatChinese(value):
                    tmp = False
            if rule=='number':
                if not validateNumber(value):
                    tmp = False
            if rule=='integer':
                if not validateNumber(value, 'int'):
                    tmp = False
            if rule=='float':
                if not validateNumber(value, 'float'):
                    tmp = False
            if rule=='alphabet':
                if not validateAlphabet(value):
                    tmp = False
            if rule=='datetime':
                if not validateDatetime(value):
                    tmp = False
    return tmp

'''指定的元组时间转时间戳'''
def dateToTimestamp(date=None):
    if not date:
        return time.time()
    time_array = time.strptime(date, "%Y-%m-%d %H:%M:%S")
    return int(time.mktime(time_array))

'''格式化好的日期转化为时间戳%Y-%m-%d %H:%M:%S'''
def formateDateToTimestamp(date):
    if not date:
        date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    return int(time.mktime(date.timetuple()))

'''时间戳转格式时间'''
def timestampToDate(timestamp, format="%Y-%m-%d %H:%M:%S"):
    if not timestamp:
        timestamp = time.time()
    time_array = time.localtime(timestamp)
    return time.strftime(format, time_array)

'''与当前时间(获取指定的时间)的时间差'''
def futureDateToTimestamp(now=None, d=0, s=60*60*3, m=0, timestamp=True):
    now_date = now if now else datetime.datetime.now()
    sdate = None
    if d==0 and s==0 and m==0:
        sdate = datetime.datetime.now()
    sdate = now_date + datetime.timedelta(seconds=s)
    if not timestamp:
        return sdate.strftime("%Y-%m-%d %H:%M:%S")
    return int(time.mktime(sdate.timetuple()))

'''检查文件类型'''
def checkFileType(file_type, ext):
    if file_type is 'img':
        type_list = ['image/gif', 'image/jpeg', 'image/pjpeg', 'image/bmp', 'image/png', 'image/x-png']
    elif file_type is 'file':
        type_list = ['.pdf','.doc','.docx','.xls']
    else:
        return False
    if ext not in type_list:
        return False
    return True

'''按长度截取字符串'''
def cutStr(str, length=150):
    """
    截取字符串，使得字符串长度等于length，并在字符串后加上省略号
    """
    is_encode = False
    try:
        str_encode = str.encode('gb18030') #为了中文和英文的长度一致（中文按长度2计算）
        is_encode = True
    except:
        pass
    if is_encode:
        l = length*2
        if l < len(str_encode):
            l = l - 3
            str_encode = str_encode[:l]
            try:
                str = str_encode.decode('gb18030') + '...'
            except:
                str_encode = str_encode[:-1]
                try:
                    str = str_encode.decode('gb18030') + '...'
                except:
                    is_encode = False
    if not is_encode:
        if length < len(str):
            length = length - 2
            return str[:length] + '...'
    return str

#替换内容中的上传图片
server_upload_tmp = os.path.sep+'server'+os.path.sep+'uploads'+os.path.sep+'tmp'+os.path.sep
upload_feedback = os.path.sep+'server'+os.path.sep+'uploads'+os.path.sep+'feedback'+os.path.sep
def filterContent(setting, content):
        sep = os.path.sep
        #保存内容中图片
        imgs = []
        ueditor_dir = setting['uploads_path']+sep+'ueditor'+sep
        #过滤文本，把文本内的图片转移到正式目录
        src_list = re.findall('[^_]src="(.*?)"', content, re.I)
        for src_item in src_list:
            if src_item.find(server_upload_tmp)==0:
                src_item_temp = src_item[16:len(src_item)]
                if os.path.isfile(ueditor_dir + src_item_temp):
                    src_dir = os.path.dirname(src_item_temp)
                    #获取存放的相对路径
                    des_dir = ueditor_dir + 'feedback' + sep + src_dir.split('/').pop()
                    #获取文件的正式存放路径
                    des_dir_temp = upload_feedback + src_dir.split('/').pop() + sep + src_item_temp.split('/').pop()

                    imgs.append(sep + ueditor_dir + src_dir.split('/').pop() + sep + src_item_temp.split('/').pop())

                    if not os.path.isdir(des_dir):
                        os.makedirs(des_dir)
                    des_item = des_dir + sep + src_item.split('/').pop()
                    os.rename(ueditor_dir + src_item_temp, des_item)
                    content = content.replace(src_item, des_dir_temp)
        return content, imgs

#获取表情
def getFaceImgs(idx=None):
    imgs = ['大笑', '江南style', '得意地笑', '转发', '挤火车', '泪流满面', '喜欢你',
            '去旅游', '晕', '鼓掌', '压力大', '小猫', '小绵羊', '神马',
            '浮云', '给力', '围观', '威武', '熊猫', '兔子', '奥特曼',
            '囧', '互粉', '礼物', '微笑', '嘻嘻', '哈哈', '可爱', '可怜', '挖鼻屎', '吃惊', '害羞', '挤眼', '闭嘴',
            '鄙视', '爱你', '泪', '偷笑', '亲亲', '生病', '太开心', '白眼', '右哼哼', '左哼哼', '嘘', '炸黑', '呕吐', '委屈', '抱抱',
            '再见', '疑问', '瞌睡', '钱', '酷', '色', 'OK', 'Good', 'NO', '赞', '弱', '猪', '心碎', '心']
    if idx:
        try:
            return imgs[idx]
        except:
            return None
    else:
        return imgs

########################################class###########################################################################

class LazyImport:
    """lazy import module"""
    def __init__(self, module_name):
        self.module_name = module_name
        self.module = None
    def __getattr__(self, func_name):
        if self.module is None:
            self.module = import_object(self.module_name)
        return getattr(self.module, func_name)
lazyimport = LazyImport

class CJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, obj)

class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.__str__()
        return json.JSONEncoder.default(self, obj)


class cachedProperty(object):
    """
    Decorator that converts a method with a single self argument into a
    property cached on the instance.
    """
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, type=None):
        if instance is None:
            return self
        res = instance.__dict__[self.func.__name__] = self.func(instance)
        return res

'''
ip地址查询
'''
class IPLocation(object):

    url = "http://ip.taobao.com/service/getIpInfo.php?ip="
    re_ipaddress = re.compile(r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
    re_domain = re.compile(r'[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})+\.?')

    @classmethod
    @gen.coroutine
    def callBack(cls, response):
        if response.error:
            raise gen.Return(False)
        else:
            res = {}
            datadict = json.loads(response.body)
            for item in datadict:
                if "code" == item:
                    if datadict[item] == 0:
                        res['country'] = datadict["data"]["country"]
                        res['region'] = datadict["data"]["region"]
                        res['city'] = datadict["data"]["city"]
                        res['isp'] = datadict["data"]["isp"]
            raise gen.Return(res)

    @classmethod
    @gen.coroutine
    def getLocationByIp(cls, ip):
        if not IPLocation.re_ipaddress.match(ip):
            raise gen.Return(False)
        #如果参数是域名
        if IPLocation.re_domain.match(ip):
            result = socket.getaddrinfo(ip, None)
            ip = result[0][4][0]
        client = httpclient.AsyncHTTPClient()
        client.fetch(IPLocation.url + ip, callback=IPLocation.callBack)