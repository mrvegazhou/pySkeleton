# -*- coding: utf8 -*-
from protected.models.FrontBaseModel import FrontBaseModel
from protected.libs.exceptions import ArgumentError, BaseError
from protected.libs.utils import dateToTimestamp
from protected.models.sysConfig import SysConfig
import sys

#大五人格（Big Five Personality)测试
class BfiCharacterTest(FrontBaseModel):
    def __init__(self):
        self._db_name = 'sssss'
        self._table = 'bfi_character_test'
        self.setPK('id')
        self._table_columns = ['id', 'p_name', 'n_name']
        self._table_columns_rule = {'p_name':['required'], 'n_name':['required']}
        super(BfiCharacterTest, self).__init__()
    #适应性 第1排＋第6排＋第11排＋第16排＋第21排＝
    N = {22:77, 21:73, 20:70, 20:70, 19:66, 18:62, 17:59, 16:55, 15:51, 14:48, 13:44, 12:40, 11:36, 10:33, 9:29, 8:25, 7:21}
    #社交性 第2排＋第7排＋第12排＋第17排＋第22排＝
    E = {25:72, 23:67, 22:65, 21:62, 20:60, 19:57, 18:55, 17:52, 16:50, 15:48, 14:46, 13:43, 12:40, 11:37, 10:35, 9:33, 8:30, 7:28, 6:26, 5:20}
    #开放性 第3排＋第8排＋第13排＋第18排＋第23排＝
    O = {25:79, 24:76, 23:73, 22:70, 21:67, 20:64, 19:62, 18:59, 17:56, 16:54, 15:50, 14:47, 13:45, 12:42, 11:40, 10:37, 9:34, 8:31, 7:28, 6:25, 5:22}
    #利他性 第4排＋第9排＋第14排＋第19排＋第24排＝
    A = {25:71, 24:68, 23:65, 22:62, 21:59, 20:55, 19:54, 18:50, 17:47, 16:44, 15:41, 14:38, 13:35, 12:32, 11:29, 10:27, 9:24, 8:20}
    #道德感 第5排＋第10排＋第15排＋第20排＋第25排＝
    C = {25:69, 24:67, 23:65, 22:63, 21:61, 20:59, 19:55, 18:52, 17:50, 16:48, 15:46, 14:44, 13:41, 12:38, 11:35, 10:33, 9:30, 8:28, 7:26, 6:24}
    @classmethod
    def transform(cls, type, true_val):
        msg = ''
        max_msg = ''
        min_msg = ''
        #适应性
        if type=='N':
            N = int(true_val)
            if N<35:
                msg = '您不太懂得如何从容面对有压力的情况，也因此常常过分担心。但是，您拥有其他人所不具备的情感深度。'
            elif 35<N<=45:
                msg = '与大多数人相比，您常觉得难为情。您看上去似乎难以摆脱焦虑和压力。您对自己的情绪比较敏感。'
            elif 45<N<=55:
                msg = '一般而言，您是平静的。您有时会感觉到压力，不过这些情绪波动多数是由具体情况而非个人特质所吸引。'
            elif 55<N<=65:
                msg = '您是平静，情绪稳定的。您很少被琐事烦扰，有时您会情绪低落，不过这种情绪不会延长很长时间。'
            elif N>65:
                msg = '您很难被压力干扰，亦很少有负面情绪。即便您有时会感到紧张焦虑，这种情绪往往会很快就过去。整体而言，您是平静的，并且您有很好的抗压能力。'
            max_msg = '安全的、镇静的、理性的、感觉迟钝的、无负罪感的'
            min_msg = '兴奋的、忧虑的、警觉的、高度紧张的'
        #外向性
        elif type=='E':
            E = int(true_val)
            if E<35:
                msg = '您是个安静内向的人，您不需要很多人在身边陪伴，有时甚至觉得处理人际关系是件费心劳神的事情。'
            elif 35<E<=45:
                msg = '您在社交场合是个低调的人，您只愿意跟几个亲密的朋友交往。您不害怕社交场合，只不过不是那么享受它们罢了。'
            elif 45<E<=55:
                msg = '您享受社交场合，但是您不认为社交代表了生活的全部。您觉得，有时候停下来，一个人静静地度过一个安静的夜晚也蛮不错。'
            elif 55<E<=65:
                msg = '您在社交场合十分投入，十分活跃。您享受并且寻找不同的社交活动。您尤其喜欢与一大群人谈天说地。'
            elif E>65:
                msg = '您在社交场合高度活跃，并且一直精力充沛。您总是希望成为社交场合的焦点，希望别人对自己发生兴趣。'
            max_msg = '独立的、保守的、难打交道的、阅读艰难的'
            min_msg = '确信的、社交性、热情的、乐观的、健谈的'
        #开放性
        elif type=='O':
            O = int(true_val)
            if O<35:
                msg = '您是个脚踏实地的人，您喜欢简单直接的东西。您认为，不在万不得已的情况下，许多事情不需要改变，这样生活会简单许多。您认为艺术对您并无太多用处。同时，与其他人相比，您更倾向于认为传统是重要的。'
            elif 35<O<=45:
                msg = '您不喜欢复杂的东西，相比于新鲜的事物，您更喜欢自己已经熟悉的事物。与大多数人比较，您比较保守。您喜欢具有实际价值的成果而并非不着边际的想象。'
            elif 45<O<=55:
                msg = '您对生活有梦想但是并不因此而忘乎所以。当情势要求改变时，您接受改变，当转变不是必要的时候，您则不会改变，这种顺其自然的态度是您生活的准则。'
            elif 55<O<=65:
                msg = '您充满好奇心，经常被您认为美好的事物所吸引，而不在乎他人的评价。您有丰富的想象力。与大多数人相比，您更具有创造力。'
            elif O>65:
                msg = '与绝大多数人相比，您有强烈的好奇心和对美好事物的灵敏体验。您的创造与审美能力充分体现了个人色彩，有时甚至能将您引向非传统方向。您享受想象力以及随之而生的奇妙体验。'
            max_msg = '保守的、实践的、有效率的、专业的、有知识深度的'
            min_msg = '兴趣广泛的、好奇的、自由的、追求新奇的'
        #宜人性
        elif type=='A':
            A = int(true_val)
            if A<=35:
                msg = '他人与您极好相处。您友好，有风度，乐于助人并且总为他人着想。您认为大多数人是十分正直的，并且他们值得信任。'
            if 35<A<=45:
                msg = '他人与您相处轻松愉快。您友好亲切，并且顾及他人的感受。您认为大多数人是正直诚实的。'
            elif 45<A<=55:
                msg = '他人与您相处融洽，尤其是您信任的人。您从善意的角度揣测他人的动机，并且认为他人一般是正直诚实的。'
            elif 55<A<=65:
                msg = '由于你习惯怀疑他人的动机，许多人在初次与你接触时觉得您并不好相处，不过，随着时间的推移，你们会慢慢熟悉起来。另外，你喜欢指教他人该如何做事。'
            elif A>65:
                msg = '在必要的时候，您能权衡利弊而做出重要的决定，并且您会指出事情的不足之处，并不顾忌其他人的感受，您常常被认为作风强硬。'
            max_msg = '怀疑的、攻击性的、坚韧的、自私自利的'
            min_msg = '信任的、谦虚的、合作的、坦白的、不喜冲突的'
        #尽职性
        elif type=='C':
            C = int(true_val)
            if C<35:
                msg = '灵活--您有时比较冲动，做事情常凭一时兴起，却乐在其中。您认为生活中有很多事情需要迅速拿主意，与绝大多数人相比，您正是这样一个"迅速决策者"，您的生活丰富多彩甚至有点荒唐，不过你十分享受这样的生活。您最头疼的事情莫过于别人要求您完成工作！'
            elif 35<C<=45:
                msg = '自由--你是个自由随性的人，您喜欢做他人意想不到的事情，并尽力使生活变得更有趣。您并非一个不可靠的人，但是，您有时的确会在一些场合犯错误。'
            elif 45<C<=55:
                msg = '悠闲--您享受自由自在的生活，不过，如果有必要的话，您能够制定并且坚持完成计划。在不同的情况下，您有时可以迅速做出决定，有时则花很长时间深思熟虑。'
            elif 55<C<=65:
                msg = '平衡--您通过制定计划来规避可以预期的麻烦，您的成功来源于毅力，您是值得信赖的人，并且总是为生活中可能出现的挑战做准备。'
            elif C>65:
                msg = '谨慎--您是完美主义者，您喜欢为每一件事情制定详细的计划，这使得您受他人信赖，并且非常成功，您享受执行计划后所收获的果实。'
            max_msg = '自发的、无组织的'
            min_msg = '依附的、有组织的、有原则经验的、谨慎的、固执的'
        return msg, max_msg, min_msg


class UserBfiTest(FrontBaseModel):
    def __init__(self):
        self._table = 'user_bfi_test'
        self.setPK('id')
        self._table_columns = ['id', 'uid', 'bfi_ids_vals', 'create_time', 'update_time', 'N_val', 'E_val', 'O_val', 'A_val', 'C_val']
        self._table_columns_rule = {'uid':['required']}
        super(UserBfiTest, self).__init__()

    def saveCharacterTest(self, uid, bfi_ids_vals, item):
        if not bfi_ids_vals:
            return False
        now = dateToTimestamp()
        info = self.queryOne([('uid', uid)], self._table_columns)
        bct = BfiCharacterTest()
        item['N'] = bct.N[item['N']] if (bct.N).has_key(item['N']) else 0
        item['E'] = bct.E[item['E']] if (bct.E).has_key(item['E']) else 0
        item['O'] = bct.O[item['O']] if (bct.O).has_key(item['O']) else 0
        item['A'] = bct.A[item['A']] if (bct.A).has_key(item['A']) else 0
        item['C'] = bct.C[item['C']] if (bct.C).has_key(item['C']) else 0
        if info:
            tmp = self.updateInfo(filterString=[  ('bfi_ids_vals', bfi_ids_vals),
                                                    ('update_time', now),
                                                    ('N_val', item['N']),
                                                    ('E_val', item['E']),
                                                    ('O_val', item['O']),
                                                    ('A_val', item['A']),
                                                    ('C_val', item['C'])
                                                    ], where=[('uid', uid)])
            if tmp:
                sc = SysConfig()
                item['N'] = item['N']-info['N_val']
                item['E'] = item['E']-info['E_val']
                item['O'] = item['O']-info['O_val']
                item['A'] = item['A']-info['A_val']
                item['C'] = item['C']-info['C_val']
                sc.updateConfig('bfi_total', item)
        else:
            tmp = self.saveOne({'uid': uid,
                                 'bfi_ids_vals': bfi_ids_vals,
                                 'create_time': now,
                                 'update_time': now,
                                 'N_val': item['N'],
                                 'E_val': item['E'],
                                 'O_val': item['O'],
                                 'A_val': item['A'],
                                 'C_val': item['C']
                                 })
            if tmp:
                sc = SysConfig()
                sc.updateConfig('bfi_total', item) #N:0,E:0,O:0,A:0,C:0
                sc.incConfig('bfi_user_total')
        return tmp
