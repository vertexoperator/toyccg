# -*- coding:utf-8 -*-
import sys,os,unicodedata
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)) , ".." ))
from toyccg import *


#-- special combinator for Japanese
def FwdRel(lt,rt):
    if rt!=Symbol("N[base]"):
       return None
    if lt==Symbol("S[null]") or lt==Symbol("S") or lt==[BwdApp , [BwdApp , Symbol("S") , Symbol("NP[sbj]")] , Symbol("NP[obj]")]:
       return Symbol("N")
    return None



def SkipCommaJP(lt,rt):
    if (type(lt)==list or lt.value()!="N[base]") and type(rt)!=list and rt.value()=="COMMA":
         return lt



jp_combinators = [LApp,RApp,LB,RB,LS,RS,RSx,Conj,FwdRel,SkipCommaJP]
jp_terminators = ["ROOT","S","S[exc]","S[imp]","S[null]","S[q]","S[null-q]","S[nom]"]


def jptest(sentence,lexicon,type=0):
   print(u"test run : sentence={0}".format(sentence))
   lexicon.guess(sentence)
   for t in buildTree(sentence,lexicon,jp_combinators,jp_terminators):
       if type==0:
           for r in t.leaves():
               if r.token in lexicon.guess_dics:
                  print(u"{0} {1} (guess)".format(r.token , r.catname))
               else:
                  print(u"{0} {1}".format(r.token , r.catname))
           break
       else:
           print( unicode(t) )
           break
   print("")



class JPLexicon(object):
    def __init__(self, dic=None):
        self.static_dics = {}
        self.guess_dics = {}
        if dic!=None:
             for line in open(dic, encoding='utf-8'):
                 line = line.strip()
                 if len(line)==0:continue
                 if line[0]=="#":continue
                 ls = line.split('\t')
                 self.static_dics.setdefault(ls[0],[]).extend( [c for c in ls[1].split(",")] )
    def __getitem__(self,tok):
        w = tok
        cats = self.static_dics.get(w , [])
        if len(cats)==0:
            cats = self.guess_dics.get(w , [])
        ret = []
        for c in cats:
            if not isinstance(c,basestring):
                 ret.append( c )
        for c in set([x for x in cats if isinstance(x,basestring)]):
            ret.append( lexify(c) )
            assert(ret[-1]!=None),("lexicon error:{0}".format(c))
        return ret
    def __setitem__(self,tok,cats):
        self.static_dics[tok] = cats
    def setdefault(self,key,defval):
        if key in self.static_dics:
             return self.static_dics[key]
        else:
             return self.static_dics.setdefault(key,defval)
    def has_key(self,tok):
        return (tok in self.static_dics)
    def get(self,toklist,defval):
        ret = self.__getitem__(toklist)
        return ret
    def guess(self , s):
        def chartype(c):
            t = unicodedata.name(c)
            if t.startswith('HIRAGANA'):
                return 0
            elif t.startswith('KATAKANA '):
                return 1
            elif t.startswith('LATIN'):
                return 2
            elif t.startswith('FULLWIDTH LATIN'):
                return 3
            elif t.startswith('CJK'):  #-- KANJI
                return 4
            elif t.startswith('DIGIT') or t.startswith('FULLWIDTH DIGIT'):
                return 5
            elif c==u'-':
                return 6
            elif c==u'。' or c==u'、':
                return 7
            elif c==u'ー':
                return 1
            else:
                return 9
        words = []
        tmp = []
        ctype = None
        for c in s:
            t = chartype(c)
            if len(tmp)==0:
                 tmp.append(c)
                 ctype = t
            elif ctype==t or (ctype==5 and c==u'.'):
                 tmp.append( c )
            else:
                 w = "".join(tmp)
                 words.append( (w,ctype) )
                 if ctype in [0,1,2,3,4]:
                     if not w in self.static_dics and not w in self.guess_dics:
                          self.guess_dics[w] = ["N[base]","N"]
                 elif ctype==5:
                     if not w in self.static_dics and not w in self.guess_dics:
                          self.guess_dics[w] = ["CD","N[base]","N"]
                 tmp = [c]
                 ctype = t
        for ((w1,t1),(w2,t2)) in zip(words,words[1:]):
            if t1==1 and t2==4:
               w = w1+w2
               if not w in self.static_dics and not w in self.guess_dics:
                   self.guess_dics[w] = ["N[base]","N"]
        if len(tmp)>0 and ctype in [0,1,2,3,4]:
            w = "".join(tmp)
            if not w in self.static_dics and not w in self.guess_dics:
                self.guess_dics[w] = ["N[base]","N"]



def sentencize(s):
    quoting = False
    tmp = []
    for c in s:
        tmp.append( c )
        if c==u"。" and not quoting and len(tmp)>0:
            yield ("".join(tmp))
            tmp = []
        elif c==u"」":
            quoting = False
        elif c==u"「":
            quoting = True
    if len(tmp)>0:
        yield ("".join(tmp))

"""
動詞語幹
TV:transitive verb
IV:intransitive verb
IV[neg],TV[neg]:未然形
IV[cont],TV[cont]:連用形
IV[euph],TV[euph]:連用形(過去)

S[q]:疑問文
S[imp]:命令文
S[exc]:感嘆文/あいさつなど
S[null]:主語が省略された文
S[nom]:体言止め(nominal phrase)
S[end]:終助詞付き

"""
if __name__=="__main__":
   TOPDIR = os.path.dirname(os.path.abspath(__file__))
   lexicon = JPLexicon(os.path.join(TOPDIR , "ccglex.jpn"))
   #-- 機能語
   lexicon[u"。"] = ["ROOT\\S","ROOT\\S[null]","ROOT\\S[nom]","ROOT\\S[end]","ROOT\\S[imp]","ROOT\\S[q]"]
   lexicon[u"？"] = ["ROOT\\S[q]" , "S[q]\\S" , "S[q]\\S[null]" , "S[q]\\S[nom]"]
   lexicon[u"?"] = ["ROOT\\S[q]" , "S[q]\\S" , "S[q]\\S[null]" , "S[q]\\S[nom]"]
   lexicon[u"、"] = ["(N/N)\\N" ,"COMMA"]
   lexicon[u","] = ["(N/N)\\N" ,"COMMA"]
   lexicon[u"」"] = ["RQUOTE"]
   lexicon[u"「"] = ["((S[com]/RQUOTE)/S)","((S[com]/RQUOTE)/S[null])","((N/RQUOTE)/N)"]
   lexicon[u"』"] = ["RQUOTE"]
   lexicon[u"『"] = ["((S[com]/RQUOTE)/S)","((S[com]/RQUOTE)/S[null])","((N/RQUOTE)/N)"]
   lexicon[u"("] = ["((N\\N)/RBRACKET)/N)","((N\\N)/RBRACKET)/S)","((N\\N)/RBRACKET)/S[null])"]
   lexicon[u")"] = ["RBRACKET"]
   lexicon[u"たい"] = ["(S\\NP[sbj])\\IV[cont]" , "S[null]\\IV[cont]" ,"((S\\NP[sbj])\\NP[obj])\\TV[cont]","(S[null]\\NP[obj])\\TV[cont]"]
   lexicon.setdefault(u"的",[]).extend( ["N[adj]\\N[base]" , "(N/N[base])\\N[base]"] )
#   lexicon[u"など"] = ["N\\N"]
   #-- (形容詞,非自立)
   lexicon[u"にくい"] = ["(S\\NP[sbj])\\IV[cont]" , "((S\\NP[sbj])\\NP[obj])\\TV[cont]"]
   lexicon[u"やすい"] = ["(S\\NP[sbj])\\IV[cont]" , "((S\\NP[sbj])\\NP[obj])\\TV[cont]"]
   lexicon[u"やすく"] = ["IV[a-cont]\\IV[cont]" , "TV[a-cont]\\TV[cont]"]
   lexicon[u"やすけれ"] = ["IV[a-hyp]\\IV[cont]" , "IV[a-hyp]\\IV[cont]"]
   #--
   lexicon[u"な"] = ["(N/N[base])\\N[adj]","(N[base]/N[base])\\N[adj]"]
   #-- (助詞,格助詞)
   lexicon[u"は"] = ["NP[sbj]\\N","(S/S)\\N"]
   lexicon[u"が"] = ["NP[sbj]\\N","NP[ga-acc]\\N","(S/S)\\S"]
   lexicon[u"のが"] = ["NP[ga-acc]\\S[null]"]
   lexicon[u"も"] = ["(S/S)\\N","NP[sbj]\\N","NP[nom-enum]\\N","(NP[sbj]/NP[nom-enum])\\N","(NP[nom-enum]/NP[nom-enum])\\N"]
   lexicon[u"を"] = ["NP[obj]\\N"]
   lexicon[u"や"] = ["(N/N)\\N"]
   lexicon[u"に"] = ["((S\\NP[sbj])/(S\\NP[sbj]))\\N","((S\\NP[sbj])/(S\\NP[sbj]))\\N[adj]","(S[imp]/S[imp])\\N","(S[null]/S[null])\\N","(S[null]/S[null])\\N[adj]","((S[null]\\NP[obj])/(S[null]\\NP[obj]))\\N","(((S\\NP[sbj])\\NP[obj])/((S\\NP[sbj])\\NP[obj]))\\N[adj]"]
   lexicon[u"へ"] = lexicon[u"に"]
   lexicon[u"で"] = ["((S\\NP[sbj])/(S\\NP[sbj]))\\N","(((S\\NP[sbj])\\NP[obj])/((S\\NP[sbj])\\NP[obj]))\\N","(S[imp]/S[imp])\\N","(S[null]/S[null])\\N","(S[null]/S[null])\\N[adj]"]
   lexicon[u"と"] = ["((S\\NP[sbj])/(S\\NP[sbj]))\\N","(S/S)\S","(N/N)\\N","(S[null]/(S\\NP[sbj]))\\S","((S\\NP[sbj])/(S\\NP[sbj]))\\S","(S[null]/S[null])\\S","(S[null]/S[null])\\S[null]","(S/S)\\S[null]","(S[null]/S[null])\\S[end]","(S/S)\\S[end]","((S\\NP[sbj])/(S\\NP[sbj]))\\S[end]","(S[null]/S[null])\\N","IV[cont]/IV[cont]","TV[cont]/TV[cont]"]
   lexicon[u"の"] = ["(N/N[base])\\N","((S[nom]\\NP[sbj])/(S[nom]\\NP[sbj]))\\N"]
   lexicon.setdefault(u"から",[]).extend( ["((S\\NP[sbj])/(S\\NP[sbj]))\\N"] )
   lexicon[u"ようだ"] = ["S[end]\\S","S[end]\\S[null]"]
   lexicon[u"らしい"] = ["S\\S","S[null]\\S[null]","(N/N)\\N","(S\\NP[sbj])\\N","(S\\NP[sbj])\\N[adj]","((S\\NP[sbj])\\NP[obj])\\N[adj]"]
   lexicon[u"だろう"] = ["S\\S","S[null]\\S[null]","(S\\NP[sbj])\\N[adj]","((S\\NP[sbj])\\NP[obj])\\N[adj]"]
   lexicon.setdefault(u"のに",[]).extend( ["(S\\NP[sbj])/(S\\NP[sbj])","S[null]/S[null]"] )
   #-- (助詞,接続助詞)
   lexicon[u"ながら"] = ["((S/S)\\NP[sbj])\\IV[cont]","((S[null]/S[null])\\NP[obj])\\TV[cont]","((S/S)\\NP[obj])\\TV[cont]","(S[null]/S[null])\\IV[cont]","(S[imp]/S[imp])\\IV[cont]","((S[imp]/S[imp])\\NP[obj])\\TV[cont]"]
   lexicon.setdefault(u"つつ",[]).extend( lexicon[u"ながら"] )
   lexicon[u"ので"] = ["(S/S)\\S","(S/S[null])\\S","(S/S)\\S[null]","(S/S[null])\\S[null]"]
   lexicon.setdefault(u"のに",[]).extend( lexicon[u"ので"] )
   lexicon.setdefault(u"から",[]).extend( lexicon[u"ので"] )
   lexicon.setdefault(u"が",[]).extend( lexicon[u"ので"] )
   lexicon.setdefault(u"けど",[]).extend( lexicon[u"ので"] )
   lexicon.setdefault(u"けれど",[]).extend( lexicon[u"ので"] )
   lexicon.setdefault(u"けれども",[]).extend( lexicon[u"ので"] )
   lexicon.setdefault(u"ならば",[]).extend( lexicon[u"ので"] )
   #--
   lexicon.setdefault(u"のだ",[]).extend( ["S[null]\\S[null]","S\\S"] )
   lexicon.setdefault(u"のです",[]).extend( ["S[null]\\S[null]","S\\S"] )
   #-- (助詞,格助詞,連語)
   lexicon[u"について"] = ["(S/S)\\N","(S[null]/S[null])\\N"]
   lexicon[u"については"] = ["(S/S)\\N","(S[null]/S[null])\\N"]
   lexicon[u"に於いて"] = ["(S/S)\\N","(S[null]/S[null])\\N"]
   lexicon[u"に於いては"] = ["(S/S)\\N","(S[null]/S[null])\\N"]
   lexicon[u"に対して"] = ["(S/S)\\N","(S[null]/S[null])\\N","(S[imp]/S[imp])\\N"]
   lexicon[u"に対しては"] = ["(S/S)\\N","(S[null]/S[null])\\N"]
   lexicon[u"によって"] = ["(S/S)\\N","(S[null]/S[null])\\N"]
   lexicon[u"によっては"] = ["(S/S)\\N","(S[null]/S[null])\\N"]
   lexicon[u"に関して"] = ["(S/S)\\N","(S[null]/S[null])\\N"]
   lexicon[u"に関しては"] = ["(S/S)\\N","(S[null]/S[null])\\N"]
   lexicon[u"にあたって"] = ["(S/S)\\N","(S/S)\\S[null]","(S/S)\\S"]
   lexicon[u"によると"] = ["(S/S)\\N","(S[null]/S[null])\\N"]
   lexicon[u"による"] = ["(N/N)\\N"]
   lexicon[u"に於ける"] = ["(N/N)\\N"]
   lexicon[u"にわたる"] = ["(N/N)\\N"]
   lexicon[u"に関する"] = ["(N/N)\\N"]
   #--
   lexicon.setdefault(u"では",[]).extend(["(S/S)\\N","(S[null]/S[null])\\N"])
   lexicon.setdefault(u"には",[]).extend(["(S/S)\\N","(S[null]/S[null])\\N"])
   #--
   lexicon[u"です"] = ["(S\\NP[sbj])\\N","(S\\NP[sbj])\\N[adj]","((S\\NP[sbj])\\NP[obj])\\N[adj]","S[null]\\N","S[null]\\N[adj]"]
   lexicon[u"ではない"] = lexicon[u"です"]
   lexicon[u"でしょう"] = ["(S\\NP[sbj])\\N","(S\\NP[sbj])\\N[adj]","((S\\NP[sbj])\\NP[obj])\\N[adj]","S[null]\\N","S[null]\\N[adj]"]
   lexicon[u"でした"] = ["(S\\NP[sbj])\\N","(S\\NP[sbj])\\N[adj]","((S\\NP[sbj])\\NP[obj])\\N[adj]","S[null]\\N","S[null]\\N[adj]"]
   lexicon[u"だった"] = lexicon[u"でした"]
   lexicon[u"である"] = lexicon[u"でした"]
   lexicon[u"ます"] = ["(S\\NP[sbj])\\IV[cont]","S[null]\\IV[cont]","((S\\NP[sbj])\\NP[obj])\\TV[cont]","(S[null]\\NP[obj])\\TV[cont]"]
   lexicon[u"ました"] = lexicon[u"ます"]
   lexicon[u"だ"] = ["(S\\NP[sbj])\\N","(S\\NP[sbj])\\N[adj]","((S\\NP[sbj])\\NP[ga-acc])\\N[adj]","((S\\NP[sbj])\\NP[obj])\\N[adj]","S[null]\\N","S[null]\\N[adj]"]
   lexicon[u"ない"] = ["(S\\NP[sbj])\\IV[neg]","((S\\NP[sbj])\\NP[obj])\\TV[neg]","(S\\NP[sbj])\\IV[a-cont]","(N/N)\\IV[a-cont]","((S\\NP[sbj])\\NP[obj])\\TV[neg]","S\\NP[sbj]","S[null]\\IV[neg]","(N/N)\\N[base]","(S\\NP[sbj])\\N[base]"]
   lexicon[u"なけれ"] = ["IV[a-hyp]\\IV[neg]","TV[a-hyp]\\TV[neg]","IV[a-hyp]\\N[base]"]
   lexicon[u"なかっ"] = ["IV[euph]\\IV[neg]","IV[cont]\\IV[neg]","IV[a-cont]\\N[base]"]
   lexicon[u"ません"] = ["(S\\NP[sbj])\\IV[neg]","((S\\NP[sbj])\\NP[obj])\\TV[neg]"]
   lexicon[u"いる"] = ["S\\S[te]","S\\NP[sbj]"]
   lexicon.setdefault(u"い",[]).extend( ["IV[a-cont]\\S[te]"] )
   lexicon[u"た"] = ["(S\\NP[sbj])\\IV[euph]","(S\\NP[sbj])\\IV[a-cont]","S[null]\\IV[euph]","S[null]\\IV[a-cont]","((S\\NP[sbj])\\NP[obj])\\TV[euph]","(S[null]\\NP[obj])\\TV[euph]"]
   lexicon.setdefault(u"だ",[]).extend( ["(S\\NP[sbj])\\IV[euph]","S[null]\\IV[euph]","((S\\NP[sbj])\\NP[obj])\\TV[euph]","(S[null]\\NP[obj])\\TV[euph]"] )
   lexicon[u"ば"] = ["((S/S)\\NP[sbj])\\IV[hyp]","(S[null]/S[null])\\IV[hyp]","((S/(S\\NP[sbj]))\\NP[sbj])\\IV[hyp]","((S/S)\\NP[sbj])\\IV[a-hyp]","((S/(S\\NP[sbj]))\\NP[sbj])\\IV[a-hyp]","((S/S)\\NP[obj])\\TV[hyp]","((S[null]/S[null])\\NP[obj])\\TV[hyp]"]
   lexicon[u"て"] = ["(S[te]\\NP[sbj])\\IV[cont]","((S/S)\\NP[sbj])\\IV[cont]","(S/S)\\IV[cont]","(S[null]/S[null])\\IV[cont]","(S[te]\\NP[sbj])\\IV[euph]","((S[te]\\NP[sbj])\\NP[obj])\\TV[cont]","((S\\NP[sbj])/(S\\NP[sbj]))\\TV[cont]","((S[null]/S[null])\\NP[obj])\\TV[cont]"]
   lexicon.setdefault(u"で",[]).extend(["(S[te]\\NP[sbj])\\IV[cont]","((S/S)\\NP[sbj])\\IV[cont]","(S[te]\\NP[sbj])\\IV[euph]","((S[te]\\NP[sbj])\\NP[obj])\\TV[cont]","((S\\NP[sbj])/(S\\NP[sbj]))\\TV[cont]","((S[null]/S[null])\\NP[obj])\\TV[cont]","(S[null]/S[null])\\IV[cont]"])
   #-- 名詞(サ変接続)+"する"
   lexicon.setdefault(u"する",[]).extend( ["(S\\NP[sbj])\\N[base]","((S\\NP[sbj])\\NP[obj])\\N[base]","(S[null]\\NP[obj])\\N[base]","S[null]\\N[base]"] )
   lexicon.setdefault(u"される",[]).extend( ["(S\\NP[sbj])\\N[base]","S[null]\\N[base]"] )
   lexicon[u"させる"] = lexicon[u"する"]
   lexicon[u"できる"] = lexicon[u"する"]
   tmpl = ["IV[neg]\\N","TV[neg]\\N","IV[cont]\\N","TV[cont]\\N","IV[euph]\\N","TV[euph]\\N"]
   lexicon.setdefault(u"し",[]).extend( tmpl )
   lexicon[u"させ"] = tmpl
   #-- (動詞、接尾)
   lexicon.setdefault(u"れる" , []).extend(["((S\\NP[sbj])\\NP[obj])\\TV[neg]","(S\\NP[sbj])\\IV[neg]","S[null]\\IV[neg]"])
   lexicon.setdefault(u"られる" , []).extend(["((S\\NP[sbj])\\NP[obj])\\TV[neg]","(S\\NP[sbj])\\IV[neg]","S[null]\\IV[neg]"])
   lexicon.setdefault(u"れ",[]).extend(["TV[neg]\\TV[neg]","IV[neg]\\IV[neg]","TV[hyp]\\TV[neg]","IV[hyp]\\IV[neg]","TV[euph]\\TV[neg]","IV[euph]\\IV[neg]"])
   lexicon.setdefault(u"れれ",[]).extend( ["IV[hyp]\\IV[neg]" , "TV[hyp]\\TV[neg]"] )
   lexicon.setdefault(u"られ",[]).extend(["TV[neg]\\TV[neg]","IV[neg]\\IV[neg]","TV[hyp]\\TV[neg]","IV[hyp]\\IV[neg]","TV[euph]\\TV[neg]","IV[euph]\\IV[neg]","((S/S)\\NP[sbj])\\IV[neg]"])
   lexicon.setdefault(u"せる" , []).extend(["((S\\NP[sbj])\\NP[obj])\\TV[neg]","(S\\NP[sbj])\\IV[neg]","S[null]\\IV[neg]"])
   lexicon.setdefault(u"させる" , []).extend(["((S\\NP[sbj])\\NP[obj])\\TV[neg]","(S\\NP[sbj])\\IV[neg]","S[null]\\IV[neg]"])
   lexicon.setdefault(u"せ",[]).extend(["TV[cont]\\TV[neg]","IV[cont]\\IV[neg]","TV[euph]\\TV[neg]","IV[euph]\\IV[neg]"])
   lexicon.setdefault(u"がる",[]).extend(["((S\\NP[sbj])\\NP[obj])\\TV[cont]","(S\\NP[sbj])\\IV[neg]","S[null]\\IV[cont]"])
   lexicon.setdefault(u"がら",[]).extend( ["TV[neg]\\TV[cont]","IV[neg]\\IV[cont]"] )
   lexicon.setdefault(u"がれ",[]).extend( ["TV[hyp]\\TV[cont]","IV[hyp]\\IV[cont]"] )
   lexicon.setdefault(u"たがる",[]).extend(["((S\\NP[sbj])\\NP[obj])\\TV[cont]","(S\\NP[sbj])\\IV[neg]","S[null]\\IV[cont]"])
   lexicon.setdefault(u"たがら",[]).extend( ["TV[neg]\\TV[cont]","IV[neg]\\IV[cont]"] )
   lexicon.setdefault(u"たがれ",[]).extend( ["TV[hyp]\\TV[cont]","IV[hyp]\\IV[cont]"] )
   #--
   lexicon.setdefault(u"よう",[]).extend(["(S[end]\\NP[sbj])\\IV[neg]" , "S[end]\\IV[neg]" , "(S[end]\\NP[obj])\\TV[neg]"] )
   #--終助詞
   lexicon.setdefault(u"か",[]).extend(["S[q]\\S" , "S[q]\\S[null]"])
   lexicon.setdefault(u"よ",[]).extend(["S[end]\\S" , "S[end]\\S[null]"])
   lexicon.setdefault(u"よね",[]).extend(["S[end]\\S" , "S[end]\\S[null]"])
   lexicon.setdefault(u"なぁ",[]).extend(["S[end]\\S" , "S[end]\\S[null]"])
   lexicon.setdefault(u"よな",[]).extend(["S[end]\\S" , "S[end]\\S[null]"])
   lexicon.setdefault(u"の",[]).extend(["S[end]\\S" , "S[end]\\S[null]"])
   lexicon.setdefault(u"ね",[]).extend(["S[end]\\S" , "S[end]\\S[null]"])
   lexicon.setdefault(u"のか",[]).extend(["S[q]\\S" , "S[q]\\S[null]"])
   lexicon.setdefault(u"なさい",[]).extend(["S[imp]\\IV[cont]" , "(S[imp]\\NP[obj])\\TV[cont]"] )
   lexicon.setdefault(u"な",[]).extend(["S[imp]\\IV[term]" , "(S[imp]\\NP[obj])\\TV[term]"])
   #--
   lexicon.setdefault(u"のは",[]).extend(["NP[ga-acc]\\S[null]","NP[sbj]\\S[null]","NP[sbj]\\S"])
   lexicon.setdefault(u"のが",[]).extend(["NP[ga-acc]\\S[null]","NP[sbj]\\S[null]","NP[sbj]\\S"])
   lexicon.setdefault(u"と",[]).extend(["S[quote]\\S[com]","S[quote]\\S","S[quote]\\S[null]","(S[null]/S[null])\\S[imp]","(S/S)\\S[imp]"])
   lexicon.setdefault(u"とは",[]).extend( ["NP[sbj]\\S" , "NP[sbj]\\S[null]" ,"NP[sbj]\\N"] )
   lexicon.setdefault(u"しまう",[]).extend( ["S\\S[te]","S[null]\\(S[te]\\NP[sbj])"] )
   lexicon.setdefault(u"言った",[]).extend(["(S\\S[quote])\\NP[sbj]"])
   #--
   lexicon.setdefault(u"どう",[]).extend( ["S[null]/S[null]" , "IV[hyp]/IV[hyp]" , "IV[cont]/IV[cont]"] )
   lexicon.setdefault(u"こう",[]).extend( ["S[null]/S[null]" , "IV[hyp]/IV[hyp]" , "IV[cont]/IV[cont]"] )
   lexicon.setdefault(u"そう",[]).extend( ["S[null]/S[null]" , "IV[hyp]/IV[hyp]" , "IV[cont]/IV[cont]"] )
   #--
   lexicon[u"圏論"] = ["N","N[base]"]
   lexicon[u"テレビゲーム"] = ["N","N[base]"]
   lexicon[u"給付水準"] = ["N","N[base]"]
   lexicon.setdefault(u"ミス",[]).extend( ["N","N[base]","N\\N[base]","N[base]\\N[base]"] )
   """
   for line in open( os.path.join(TOPDIR , "sentences.ja.txt") ,encoding='utf-8'):
       line = line.strip()
       for sent in sentencize(line):
           jptest(sent , lexicon , type=0)
   """
