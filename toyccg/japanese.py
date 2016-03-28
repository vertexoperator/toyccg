# -*- coding:utf-8 -*-
import sys,os,unicodedata
from ccg import LApp,RApp,LB,RB,RSx,Conj,SkipComma,lexify,Symbol,CCGParser

#-- for python2/3 compatibility
from io import open
if sys.version_info[0] == 3:
   basestring = str
   __stdin__ = sys.stdin.buffer
else:
   basestring = basestring
   __stdin__ = sys.stdin


#-- special combinator for Japanese
def FwdRel(lt,rt):
    if type(lt)==list or type(rt)==list:
       return None
    elif rt.value()!="N[base]":
       return None
    elif lt.value()=="S[null]" or lt.value()=="S[rel]":
       return Symbol("N")
    return None



def sentencize(s):
    quoting = False
    tmp = []
    separators = [u"。" , u"?" , u"？" , u"!" , u"！"]
    for c in s:
        tmp.append( c )
        if c in separators and not quoting and len(tmp)>0:
            yield ("".join(tmp))
            tmp = []
        elif c==u"」":
            quoting = False
        elif c==u"「":
            quoting = True
    if len(tmp)>0:
        yield ("".join(tmp))



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
            elif t.startswith('LATIN') or t=='SPACE':
                return 2
            elif t.startswith('FULLWIDTH LATIN'):
                return 3
            elif t.startswith('CJK'):  #-- KANJI
                return 4
            elif t.startswith('DIGIT') or t.startswith('FULLWIDTH DIGIT'):
                return 5
            elif c==u'-':
                return 2
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
                 if ctype in [1,2,3]:
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
            elif t1==4 and (t2==7 or t2==9):
               w = w1
               if not w in self.static_dics and not w in self.guess_dics:
                   self.guess_dics[w] = ["N[base]","N"]
        if len(tmp)>0 and ctype in [0,1,2,3,4]:
            w = "".join(tmp)
            if not w in self.static_dics and not w in self.guess_dics:
                self.guess_dics[w] = ["N[base]","N"]



def default_lexicon():
   TOPDIR = os.path.dirname(os.path.abspath(__file__))
   lexicon = JPLexicon(os.path.join(TOPDIR , "data" , "ccglex.jpn"))
   lexicon[u"。"] = ["ROOT\\S","ROOT\\S[null]","ROOT\\S[nom]","ROOT\\S[end]","ROOT\\S[imp]","ROOT\\S[q]"]
   lexicon[u"？"] = ["ROOT\\S[q]" , "S[q]\\S" , "S[q]\\S[null]" , "S[q]\\S[nom]"]
   lexicon[u"?"] = ["ROOT\\S[q]" , "S[q]\\S" , "S[q]\\S[null]" , "S[q]\\S[nom]"]
   lexicon[u"、"] = ["(N/N)\\N" ,"COMMA"]
   lexicon[u","] = ["(N/N)\\N" ,"COMMA"]
   lexicon[u"」"] = ["RQUOTE"]
   lexicon[u"「"] = ["((S[com]/RQUOTE)/S)","((S[com]/RQUOTE)/S[null])","((N/RQUOTE)/N)","(((N\\N[base])/RQUOTE)/N)"]
   lexicon[u"』"] = ["RQUOTE"]
   lexicon[u"『"] = ["((S[com]/RQUOTE)/S)","((S[com]/RQUOTE)/S[null])","((N/RQUOTE)/N)"]
   lexicon[u"("] = ["((N\\N)/RBRACKET)/N","((N\\N)/RBRACKET)/S","((N\\N)/RBRACKET)/S[null]"]
   lexicon[u")"] = ["RBRACKET"]
   lexicon[u"（"] = ["((N\\N)/RBRACKET)/N","((N\\N)/RBRACKET)/S","((N\\N)/RBRACKET)/S[null]"]
   lexicon[u"）"] = ["RBRACKET"] 
   lexicon[u"・"] = ["(N/N[base])\\N[base]"]
   return lexicon



parser = CCGParser()
parser.combinators = [LApp,RApp,LB,RB,RSx,Conj,FwdRel,SkipComma]
parser.terminators = ["ROOT","S","S[exc]","S[imp]","S[null]","S[q]","S[null-q]","S[nom]"]
parser.lexicon = default_lexicon()
parser.concatenator = ""

def run(text,type=0):
   for sentence in sentencize(text):
       print(u"test run : sentence={0}".format(sentence))
       parser.lexicon.guess(sentence)
       for t in parser.parse(sentence):
          if type==0:
              for r in t.leaves():
                 if r.token in parser.lexicon.guess_dics:
                     print(u"{0}\t{1}\t(guess)".format(r.token , r.catname))
                 else:
                     print(u"{0}\t{1}".format(r.token , r.catname))
              break
          else:
              print( t.show() )
              break
       print("")



"""
動詞語幹
TV:transitive verb
IV:intransitive verb
IV[neg],TV[neg]:未然形
IV[cont],TV[cont]:連用形
IV[euph],TV[euph]:連用形(過去)
IV[hyp],TV[hyp]:仮定形

S[q]:疑問文
S[imp]:命令文
S[exc]:感嘆文/あいさつなど
S[null]:主語が省略された文
S[nom]:体言止め(nominal phrase)
S[end]:終助詞付き
S[te]:
S[short]:形容詞単体の文:FwdRel(S[null] , N[base])とLApp(N/N[base] , N[base])が被るので、S[null]にしない
S[rel]

N
N[base]:名詞
N[adv]:副詞可能
N[adj]:形容動詞語幹

"""
if __name__=="__main__":
   for line in __stdin__:
       line = line.decode('utf-8')
       line = line.strip()
       run(line ,  type=0)

