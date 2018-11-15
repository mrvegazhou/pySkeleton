#encoding:UTF-8
import codecs
import time
import sys

class TrieNode:
    def __init__ (self):
        self.val = 0
        self.trans = {}

class Trie(object):
    def __init__ (self):
        self.root = TrieNode()

    def __walk (self, trienode, ch):
        if ch in trienode.trans:
            trienode = trienode.trans[ch]
            return trienode, trienode.val
        else:
            return None, 0

    def add (self, word, value=1):
        curr_node = self.root
        for ch in word:
            try:
                curr_node = curr_node.trans[ch]
            except:
                curr_node.trans[ch] = TrieNode()
                curr_node = curr_node.trans[ch]

        curr_node.val = value

    def _find_ch(self,curr_node,ch,word,start,limit):
        curr_node, val = self.__walk (curr_node, ch)
        tmp_index = 0
        if val:
            return val
        while curr_node is not None and start<(limit-1):
            start = start+1
            ch = word[start]
            if not (self.is_chinese(ch) or self.is_number(ch) or self.is_alphabet(ch)):
                tmp_index = tmp_index+1
                continue
            curr_node, val = self.__walk (curr_node, ch)
            if val:
                tmp = ''
                if tmp_index!=0:
                    tmp = u'*'*tmp_index
                    tmp_index = 0
                return val + tmp

    def match_all (self, word):
        ret = []
        bad_word_ret = []
        curr_node = self.root
        index = 0
        j = 0
        size = len(word)
        while index<size:
            val = self._find_ch(curr_node,word[index], word, index, size)
            if val:
                j = len(val)
                ret.append(u'*'*j)
                bad_word_ret.append(word[index:index+j])
                index=index+j-1
            else:
                ret.append(word[index])
            index=index+1
        return ''.join(ret), bad_word_ret

    def is_chinese(self, uchar):
        #判断一个unicode是否是汉字
        if uchar>=u'\u4e00' and uchar<=u'\u9fa5':
            return True
        else:
            return False

    def is_number(self, uchar):
        #判断一个unicode是否是数字
        if uchar >= u'\u0030' and uchar<=u'\u0039':
            return True
        else:
            return False

    def is_alphabet(self, uchar):
        #判断一个unicode是否是英文字母
        if (uchar >= u'\u0041' and uchar<=u'\u005a') or (uchar >= u'\u0061' and uchar<=u'\u007a'):
            return True
        else:
            return False

class DictFilter(Trie):
    def __init__(self, fname='protected/conf/badwords'):
        super(DictFilter, self).__init__()
        self.load(fname)

    def load(self, fname):
        file = codecs.open(fname, 'r', 'utf-8')
        for line in file:
            word = line.strip()
            self.add(word, unicode(word))
        file.close()
if __name__=="__main__":
    d = DictFilter('../conf/badwords')
    print d.match_all(u'毛泽东SSS习近平天啊家里的肌肤带来ajdkjdk aaa')