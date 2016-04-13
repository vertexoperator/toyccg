# -*- coding:utf-8 -*-
import sys,os,unicodedata
from ccg import LApp,RApp,LB,RB,RBx,RSx,Conj,SkipComma,Symbol,CCGParser,LT,RT,catname,chart2tree,Tree,Leaf

#-- for python2/3 compatibility
from io import open
if sys.version_info[0] == 3:
   basestring = str
   __stdin__ = sys.stdin.buffer
else:
   basestring = basestring
   __stdin__ = sys.stdin


"""
動詞語幹
TV:transitive verb
IV:intransitive verb
IV[neg]:未然形("S[neg]\\NP[sbj]")
TV[neg]:未然形("(S[neg]\\NP[sbj])\\NP[obj]")
IV[cont],TV[cont]:連用形        ->飛び(ます),死に(ます)
IV[euph],TV[euph]:連用形(過去)  ->飛ん(だ),死ん(だ)
IV[hyp],TV[hyp]:仮定形
IV[pre],TV[pre]:推量計  -> 死の(う)、飛ぼ(う)、やろ(う)

S[q]:疑問文
S[imp]:命令文
S[exc]:感嘆文/あいさつなど
S[null]:主語が省略された文
S[nom]:体言止め(nominal phrase)
S[end]:終助詞付き
S[te]:
S[na]:
S[short]:形容詞単体の文:FwdRel(S[null] , N[base])とLApp(N/N[base] , N[base])が被るので、S[null]にしない
S[attr]:連体形
S[rel]:連体修飾

名詞類
N
N[base]:名詞
N[mid]:ad hoc
N[adv]:副詞可能
N[adj]:形容動詞語幹
N[verb]:動作性名詞(～する/～できる/～させる、などの接続ができる)

名詞句
NP[sbj]
NP[obj]
NP[ga-acc]:ad hoc

助詞
PP[*]:postpositional particles(ad hoc)


RBxコンビネータ:
RBxコンビネータがあると副詞などの扱いが少し楽？
少し |- S/S
速い |- S\\NP[sbj]
少し速い |- RBx(S/S , S\\NP[sbj]) = S\\NP[sbj]


激しく |- (S\\NP[sbj])/(S\\NP[sbj])
攻撃する |- (S\\NP[sbj])\\NP[obj]
激しく攻撃する |- RBx((S\\NP[sbj])/(S\\NP[sbj]) , (S\\NP[sbj])\\NP[obj]) = (S\\NP[sbj])\\NP[obj]

激しく |- (S\\NP[sbj])\\NP[obj])/(S\\NP[sbj])\\NP[obj])
は不要となる。


"しかし"や"もし"などの接続詞は、通常、文頭や節の頭に来るので、S/Sという統語範疇を持つが、
「私はしかし歴史の虚偽を軽蔑しようとはおもわない。」
みたいな文も、文法的にOKになることを、RBxコンビネータで自然に扱える。更に
・もし、私がこれを完食したら、...
・私が、もしこれを完食したら、...
・私がこれを、もし完食したら、...
や
・今、私は宿題をやっている。
・私は、今宿題をやっている。
・私は宿題を今やっている。
などが、全て合文法的で、前者3文と後者3文がそれぞれ意味的に同一である(ニュアンスは若干異なるとは言え)。このことを考慮すると、
(X/Y) (Y\\A)\\B => (X\\A)\\B
のような一般化合成コンビネータも、日本語では使われるべきと思われる。

英語だと、
I usually say what I think
Usually I say what I think
のどちらも合法だが、
But I say what I think.
I but say what I think.
だと、後者の語順は発生しない。従って、
(X/Y) (Y\\A)/B => (X\\A)/B
のようなコンビネータは、英語では、採用できないと思う。

一方で、
https://www.cl.cam.ac.uk/teaching/1011/L107/clark-lecture3.pdf
などを見ると、英語でも
X/Y (Y/A)/B => (X/A)/B
のようなコンビネータは必要でないかと書かれている。


"""


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
    elif catname(rt)=="S[nom]\\NP[sbj]" and catname(lt) in ["S[null]","S[rel]","S[rel]\\NP[obj]","S\\NP[sbj]"]:
       return rt
    elif rt.value()!="N[base]" and rt.value()!="N[mid]":
       return None
    elif catname(lt) in ["S[null]","S[rel]","S[rel]\\NP[obj]","S\\NP[sbj]"]:
       return Symbol("N")
    return None



def sentencize(s):
    quoting = False
    tmp = []
    separators = [u"。" , u"?" , u"？" , u"!" , u"！",u"．"]
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
        self.phrase_dics = {}
        if dic!=None:
             for line in open(dic, encoding='utf-8'):
                 line = line.strip()
                 if len(line)==0:continue
                 if line[0]=="#":continue
                 ls = line.split('\t')
                 self.static_dics.setdefault(ls[0],[]).extend( [c for c in ls[1].split(",")] )
    def __getitem__(self,tok):
        if type(tok)==list:
           w = "".join(tok)
        else:
           w = tok
        if w in self.phrase_dics:
            return self.phrase_dics[w]
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
                return 2
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
            if (t1,t2) in [(1,4),(2,4),(2,5),(4,1)]:
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
   lexicon[u"。"] = ["ROOT\\S","ROOT\\S[null]","ROOT\\S[nom]","ROOT\\S[end]","ROOT\\S[imp]","ROOT\\S[q]","ROOT\\S[wq]"]
   lexicon[u"．"] = lexicon[u"。"]
   lexicon[u"…"] = ["S\\S"]
   lexicon[u"？"] = ["ROOT\\S[q]" , "ROOT\\S[wq]" , "S[q]\\S" , "S[q]\\S[null]" , "S[q]\\S[nom]"]
   lexicon[u"?"] = ["ROOT\\S[q]" , "ROOT\\S[wq]", "S[q]\\S" , "S[q]\\S[null]" , "S[q]\\S[nom]"]
   lexicon[u"、"] = ["COMMA","(N/N)\\N"]
   lexicon[u","] = lexicon[u"、"]
   lexicon[u"，"] = lexicon[u"、"]
   lexicon[u"」"] = ["RQUOTE"]
   lexicon[u"「"] = ["((S[com]/RQUOTE)/S)","((S[com]/RQUOTE)/S[null])","((N/RQUOTE)/N)","(((N\\N[base])/RQUOTE)/N)","(((N\\N)/RQUOTE)/N)"]
   lexicon[u"』"] = ["RQUOTE"]
   lexicon[u"『"] = ["((S[com]/RQUOTE)/S)","((S[com]/RQUOTE)/S[null])","((N/RQUOTE)/N)","((N[base]/RQUOTE)/N[base])"]
   lexicon[u"("] = ["((N\\N)/RBRACKET)/N","((N\\N)/RBRACKET)/S","((N\\N)/RBRACKET)/S[null]"]
   lexicon[u")"] = ["RBRACKET"]
   lexicon[u"（"] = ["((N\\N)/RBRACKET)/N","((N\\N)/RBRACKET)/S","((N\\N)/RBRACKET)/S[null]"]
   lexicon[u"）"] = ["RBRACKET"] 
   lexicon[u"・"] = ["(N/N[base])\\N[base]"]
   lexicon[u"～"] = ["(CD/CD)\\CD"]
   lexicon[u"-"] = ["(CD/CD)\\CD"]
   return lexicon




def SkipCommaJP(lt,rt):
    def check(term):
       if type(term)!=list:
            if term.value().startswith("N["):
                 return False
            elif term.value().startswith("ADJ"):
                 return False
            elif term.value().startswith("PP"):
                 return False
            elif term.value()=="N":
                 return False
            else:
                 return True
       elif term[0].value()=="forall":
            return False
       else:
            assert(len(term)>=2),lt
            return (check(term[1]) and check(term[2]))
    if type(rt)==list or rt.value()!="COMMA":
         return None
    elif not check(lt):
         return None
    return SkipComma(lt,rt)




parser = CCGParser()
parser.combinators = [LApp,RApp,LB,RB,Conj,FwdRel,SkipCommaJP,RT("NP[sbj]"),RBx]
parser.terminators = ["ROOT","S","S[exc]","S[imp]","S[null]","S[q]","S[wq]","S[null-q]","S[nom]"]
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
       else:
           pass
           #assert(False)
       print("")


"""
長文対応用
読点区切りごとに分割して、前から、節ごとに計算を確定していく

"""
def fastrun(text):
    def replace_all(t , treemap):
        if not isinstance(t,Tree):
             if t.token in treemap:
                 return replace_all(treemap[t.token] , treemap)
             else:
                 return t
        else:
             for idx,st in enumerate(t.children):
                  t.replace(idx,replace_all(st,treemap))
             return t
    for sent in sentencize(text):
        treemap = {}
        print(u"fastrun : sentence={0}".format(sent))
        phrases = []
        tmp = []
        quoting = False
        for n,c in enumerate(sent):
           if c==u"「":
               quoting = True
           elif c==u"」":
               quoting = False
           if c in [u"、",u"。",u"．",u"，"]:
               if not quoting and len(tmp)>0:
                   phrases.append( "".join(tmp) )
                   tmp = []
               phrases.append(c)
           else:
               tmp.append(c)
        else:
           if len(tmp)>0:
               phrases.append( "".join(tmp) )
        parser.lexicon.guess( sent )
        phraseParser = CCGParser()
        phraseParser.combinators = parser.combinators 
        phraseParser.terminators = None
        phraseParser.lexicon = parser.lexicon
        phraseParser.concatenator = ""
        chartMap = {}
        tokenMap = {}
        for n,p in enumerate(phrases):
            noResult=True
            if n==len(phrases)-1:
                phraseParser.terminators = parser.terminators
            if n==0:
                for r in phraseParser.chartparse( p ):
                    noResult=False
                else:
                    if not noResult:
                        key = max(r.keys() , key=lambda x:x[1]-x[0])
                        cats = [catname(x[0]) for x in r[key]]
                        chartMap[p] = r
                        tokenMap[p] = p
                    else:
                        assert(False),(repr(p))
            else:
                noResult = True
                for r in phraseParser.chartparse( p ):
                    noResult=False
                else:
                    if not noResult:
                        chartMap[p] = r
                        tokenMap[p] = p
                        key = max(r.keys() , key=lambda x:x[1]-x[0])
                        cats = [catname(x[0]) for x in r[key]]
                        phraseParser.lexicon.phrase_dics.setdefault(p ,[]).extend( list(set(cats)) )
                noResult = True
                for r in phraseParser.chartparse( phrases[:n] + list(p) ):
                    noResult=False
                    if n==len(phrases)-1:
                        chartMap[sent] = r
                        tokenMap[sent] = phrases[:n] + list(p)
                        break
                else:
                    if not noResult:
                        key = "".join(phrases[:n+1])
                        tokenMap[key] = phrases[:n] + list(p)
                        chartMap[key] = r
            key = max(r.keys() , key=lambda x:x[1]-x[0])
            cats = [catname(x[0]) for x in r[key]]
            phraseParser.lexicon.phrase_dics.setdefault("".join(phrases[:n+1]) ,[]).extend( list(set(cats)) )
        r = chartMap[sent]
        key = max(r.keys() , key=lambda x:x[1]-x[0])
        topcat,_ = r[key][0]
        topcat = catname(topcat)
        toptoken = sent
        for _ in range(len(phrases)):
           chart = chartMap[toptoken]
           key = max(chart.keys(),key=lambda x:x[1]-x[0])
           _,path = [x for x in chart[key] if catname(x[0])==topcat][0]
           if True:
              t = chart2tree(chart , path , tokenMap[toptoken])
              if t==None:
                  t = Leaf(topcat , toptoken)
              else:
                  treemap["".join(tokenMap[toptoken])] = t
              r = t.leaves()[0]
              for idx in range(len(phrases)-1):
                  if r.token=="".join(phrases[:idx+1]):
                      break
              else:
                  break
              topcat = r.catname
              toptoken = r.token
        toptree = treemap[sent]
        t = replace_all(toptree , treemap)
        for r in t.leaves():
            if r.token in parser.lexicon.guess_dics:
                print(u"{0}\t{1}\t(guess)".format(r.token , r.catname))
            else:
                print(u"{0}\t{1}".format(r.token , r.catname))
        print("")
        phraseParser.lexicon.phrase_dics = {}



if __name__=="__main__":
   for line in __stdin__:
       line = line.decode('utf-8')
       line = line.strip()
       run(line,type=0)
       #fastrun(line)

