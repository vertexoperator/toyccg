# -*- coding:utf-8 -*-
import sys,os,unicodedata
from ccg import LApp,RApp,LB,RB,RBx,RSx,Conj,SkipComma,Symbol,CCGParser,LT,RT,catname

#-- for python2/3 compatibility
from io import open
if sys.version_info[0] == 3:
   basestring = str
   __stdin__ = sys.stdin.buffer
else:
   basestring = basestring
   __stdin__ = sys.stdin


#-- special combinator for Japanese
"""
連体修飾
連体節は複数パターンの解析結果を持ちうるが、どれが正しいかは、意味的に決まる

(A)S=Cとなるパターン
(1)「さんまを焼く」「火」: S\\NP[sbj] => (S,O,V,C) = (火,さんま,焼く,S)
(2)「死んだ」「猫」:S\\NP[sbj] => (S,O,V,C) = (猫 , -- , 死んだ , S)

(B)O=Cとなるパターン
(3)「私が作った」「ケーキ」: S[rel]\\NP[obj] => (S,O,V,C) = (私,ケーキ,作った,O)
(3)「彼が殺した」「男」: S[rel]\\NP[obj] => (S,O,V,C) = (彼、男、殺した,O)
(3)「彼の落とした」「財布」: S[rel]\\NP[obj] => (S,O,V,C) = (彼,財布,落とした,O)
(4)「焼いた」「パン」: ((S\\NP[sbj])\\NP[obj]) => (S,O,V,C) = (? , パン,焼いた,O)

(C)S≠CかつO≠C
(5)「私がケーキを作った」「理由」:S[rel] => (S,O,V,C) = (私,ケーキ,作った,理由)
(5)「彼がさんまを焼く」「音」: S[rel] => (S,O,V,C) = (彼,さんま,焼く,音)
(5)「彼が殺した」「証拠」: S[rel] => (S,O,V,C) = (彼, ? , 殺した,証拠)
(6)「ケーキを作った」「理由」:S[null] => (S,O,V,C) = (? , ケーキ,作った,理由)
(6)「さんまを焼く」「音」:S[null] => (S,O,V,C) = (? , さんま , 焼く、音)
(7)「走る」「姿」 : S[null] => (S,O,V,C) = (?,?,走る、姿)
(7)「消える」「様子」:S[null] => (S,O,V,C) = (? , -- , 消える、様子)

「さんまを焼く」「光」などは、(1)か(5)か曖昧

"""
def FwdRel(lt,rt):
    if type(lt)==list or type(rt)==list:
       return None
    elif rt.value()!="N[base]" and rt.value()!="N[mid]":
       return None
    elif catname(lt) in ["S[null]","S[rel]","S[rel]\\NP[obj]","S\\NP[sbj]"]:
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
            if not c in ret:
                ret.append( c )
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
            if (t1,t2) in [(1,4),(2,4)]:
               w = w1+w2
               if not w in self.static_dics and not w in self.guess_dics:
                   self.guess_dics[w] = ["N[base]","N"]
            elif t1==1:
               w = w1
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
   lexicon[u"～"] = ["(CD/CD)\\CD"]
   lexicon[u"-"] = ["(CD/CD)\\CD"]
   return lexicon



class Lrestrict:
   def __init__(self,C):
      self.combinator = C
      self.__name__ = C.__name__
   def __call__(self,lt,rt):
      if type(lt)==list and lt[0].value()=="forall":
          r = self.combinator(lt,rt)
          return r
      else:
          return None



def SkipCommaJP(lt,rt):
    if type(rt)==list or rt.value()!="COMMA":
         return None
    if type(lt)!=list and (lt.value().startswith("N[") or lt.value()=="N"):
         return None
    return SkipComma(lt,rt)


class RSxJP:
    def __init__(self):
        self.__name__="RSx"
    def __call__(self,lt,rt):
        r = RSx(lt,rt)
        if r==None:
            return None
        elif type(r[1])!=list and r[1].value().startswith("N["):
            return None
        elif type(r[1])!=list and r[1].value()=="N":
            return None
        elif type(r[2])!=list and r[2].value().startswith("N["):
            return None
        elif type(r[2])!=list and r[2].value()=="N":
            return None
        elif type(r[1])==list and (r[1][1]=="N[base]" or r[1][2]=="N[base]"):
            return None
        else:
            return r



class RBxJP:
    def __init__(self):
        self.__name__="RBx"
    def __call__(self,lt,rt):
        r = RBx(lt,rt)
        if r==None:
            return None
        elif type(r[1])!=list and r[1].value().startswith("N["):
            return None
        elif type(r[2])!=list and r[2].value().startswith("N["):
            return None
        elif type(r[1])==list and (r[1][1]=="N[base]" or r[1][2]=="N[base]"):
            return None
        else:
            return r



parser = CCGParser()
parser.combinators = [LApp,RApp,LB,RB,RSxJP(),Conj,FwdRel,SkipCommaJP,Lrestrict(RBxJP()),RT("NP[sbj]")]
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
IV[cont],TV[cont]:連用形        ->飛び(ます)
IV[euph],TV[euph]:連用形(過去)  ->飛ん(だ)
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

助詞
PP[*]:postpositional particles
"""
if __name__=="__main__":
   for line in __stdin__:
       line = line.decode('utf-8')
       line = line.strip()
       run(line,type=0)

