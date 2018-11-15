#encoding:UTF-8
import sys
from time import time
import logging
# logger = logging.getLogger("spam_application")
# logger.setLevel(logging.DEBUG)
# # create file handler which logs even debug messages
# fh = logging.FileHandler("../spam.log")
# fh.setLevel(logging.DEBUG)
# # create console handler with a higher log level
# ch = logging.StreamHandler()
# ch.setLevel(logging.ERROR)
# # create formatter and add it to the handlers
# formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# fh.setFormatter(formatter)
# ch.setFormatter(formatter)
# # add the handlers to the logger
# logger.addHandler(fh)
# logger.addHandler(ch)
class datfilter():
    def __init__(self):
        self.d = {}
        self.hash = {}
        self.DEF_LEN = 1024
        self.END_TAG = '#' #在CWC中的value=1
        self.base = [0]*self.DEF_LEN
        self.check = [0]*self.DEF_LEN
        self.tail = [0]*self.DEF_LEN
        self.tailPos = 1
        self.base[1] = 1
        self.hash = {}
        self.hash[self.END_TAG] = 1

    #查找一个词是否在Trie树结构中
    def retrieval(self, word):
        #执行查询操作
        pre = 1
        cur = 0
        for ch in word:
            cur = self.base[pre] + self.GetCode(ch)
            if self.check[cur] != pre:
                return False
            #到tail数组中去查询
            if self.base[cur] < 0:
                head = -self.base[cur]
                return self.MatchInTail(word, word.index(ch)+1, head)
        #这一句是关键，对于一个串是另一个字符串 子串的情况
        if self.check[self.base[cur]+self.GetCode(self.END_TAG)] == cur:
            return True
        return False

    def insert(self, word):
        word += self.END_TAG
        pre = 1
        for i in xrange(len(word)):
            cur = self.base[pre] + self.GetCode(word[i])
            #容量不够的时，扩容
            if cur>=len(self.base):
                self.extend()
            #空白位置，可以添加，这里需要注意的是如果check[cur]=0,则base[cur]=0成立
            if self.check[cur]==0:
                self.check[cur] = pre
                self.base[cur] = -self.tailPos
                self.toTail(word, i+1) #把剩下的字符串存储到tail数组中
                #当前词已经插入到DATire中
                return
            #公共前缀，直接走
            if self.check[cur]==pre and self.base[pre]>0:
                pre = cur
                continue
            #遇到压缩到tail中的字符串，有可能是公共前缀
            if self.check[cur]==pre and self.base[pre]<0:
                #是公共前缀，把前缀解放出来
                new_base_value = None
                head = -self.base[cur]
                #插入相同的字符串
                if self.tail[head]==self.END_TAG and word[i+1]==self.END_TAG:
                    return
                if self.tail[head]==word[i+1]:
                    ncode = self.GetCode(word[i+1])
                    new_base_value = self.x_check(ncode)
                    #解放当前结点
                    self.base[cur] = new_base_value
                    self.base[new_base_value] = -(head+1)
                    self.check[new_base_value] = cur
                    #把边推向前一步,继续
                    pre = cur
                    continue
                #两个字符不相等,这里需要注意"一个串是另一个串的子串的情况"
                tailH = self.GetCode(self.tail[head])
                nextW = self.GetCode(word[i+1])
                new_base_value = self.x_check([tailH, nextW])
                self.base[cur] = new_base_value
                #确定父子关系
                self.check[new_base_value+tailH] = cur
                self.check[new_base_value+nextW] = cur
                #处理原来tail的首字符
                if self.tail[head] == self.END_TAG:
                    self.base[new_base_value+tailH] = 0
                else:
                    self.base[new_base_value+tailH] = -(head+1)
                #处理新加进来的单词后缀
                if self.word[i+1] == self.END_TAG:
                    self.base[new_base_value+nextW] = 0
                else:
                    self.base[new_base_value+nextW] = -self.tailPos
                self.toTail(word,i+2)
                return
            #冲突:当前结点已经被占用，需要调整pre的base  这里也就是整个DATrie最复杂的地方了
            if self.check[cur] != pre:
                adjustBase = pre
                #父结点的所有孩子
                list = self.GetAllChild(pre)
                #产冲突结点的所有孩子
                tmp = self.GetAllChild(self.check[cur])
                new_base_value = None
                if len(tmp)>0 and len(tmp)<=(len(list)+1):
                    list = tmp
                    tmp = None
                    adjustBase = self.check[cur]
                    new_base_value = self.x_check(list)
                else:
                    #由于当前字符也是结点的孩子，所以需要把当前字符加上
                    list[len(list)] = None
                    list[len(list)-1] = self.GetCode(word[i])
                    new_base_value = self.x_check(list)
                    #但是当前字符 现在并不是他的孩子，所以暂时先需要去掉
                    list = list[0:len(list)-1]
                old_base_value = self.base[adjustBase]
                self.base[adjustBase] = new_base_value
                old_pos = None
                new_pos = None
                #处理所有节点的冲突
                for j in xrange(len(list)):
                    old_pos = old_base_value+list[j]
                    new_pos = new_base_value+list[j]
                    '''
                    if(old_pos==pre)pre=new_pos;
                     * 这句代码差不多花了我3天的时间，才想出来
                     * 其间，反复看论文，理解DATrie树的操作过程。
                     * 动手在纸上画分析DATrie可能的结构。最后找到
                     * 样例："ba","bac","be","bae" 解决问题
                    '''
                    if old_pos==pre:
                        pre=new_pos;
                    #把原来老结点的信息迁移到新节点上
                    self.base[new_pos] = self.base[old_pos]
                    self.check[new_pos] = self.check[old_pos]
                    #有后续,所有孩子都用新的父亲替代原来的父亲
                    if self.base[old_pos]>0:
                        tmp = self.GetAllChild(old_pos)
                        for k in xrange(len(tmp)):
                            self.check[self.base[old_pos]+tmp[k]] = new_pos
                    #释放废弃的节点空间
                    self.base[old_pos] = 0
                    self.check[old_pos] = 0
                #冲突处理完毕，把新的单词插入到DATrie中
                cur = self.base[pre]+self.GetCode(word[i])
                if self.check[cur]!=0:
                    print "collision exists~!"
                if word[i]==self.END_TAG:
                    self.base[cur] = 0
                else:
                    self.base[cur] =  -self.tailPos
                self.check[cur] = pre
                self.toTail(word,i+1)
                return



    #到Tail数组中进行比较
    def MatchInTail(self, word, start, head):
        word = word + self.END_TAG;
        while len(word)>start:
            if word[start] != self.tail[head]:
                return False
            start = start + 1
            head = head + 1
        return True

    def GetCode(self, ch):
        if False==self.hash.has_key(ch):
            self.hash[ch] = len(self.hash)+1
        return self.hash[ch]

    #将字符串的后缀存储到tail数组中
    def toTail(self, w, pos):
        #如果容量不足，就扩容
        tailLen = len(self.tail)-self.tailPos
        wLen = len(w)-pos
        if tailLen < wLen:
            self.tail.extend( [0]*(wLen-tailLen) )
        while pos<len(w):
            self.tail[self.tailPos] = w[pos]
            pos = pos+1
            self.tailPos = self.tailPos+1

    #寻找最小的q,q要满足的条件是：q>0 ,并且对于list中所有的元素都有check[q+c]=0
    def x_check(self, c=[]):
        i = 0
        cur = None
        q = 1
        while i<len(c)-1:
            cur = q + c[i]
            i = i+1
            if cur>=len(self.check):
                self.extend()
            if self.check[cur]!=0:
                i = 0
                q = q+1
        return q

    def extend(self):
        self.base[len(self.base)] = 0
        self.check[len(self.check)] = 0

    #寻找一个节点的所有子元素
    def GetAllChild(self, pos):
        if self.base[pos]<0:
            return None
        c = []
        for i in xrange(len(self.hash)):
            if self.base[pos] + i >= len(self.check):
                break
            if self.check[self.base[pos]+i] == pos:
                c.append(i)
        return c

if __name__=="__main__":
    def testInsert():
        s = ["bachelor","我爱你北京","abcdefg"]
        s2 = ["bachelor","北京","abcdefg"]
        dat = datfilter()
        for string in s:
            dat.insert(string)
        for string in s2:
            print dat.retrieval(string)
    testInsert()
