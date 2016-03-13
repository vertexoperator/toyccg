# -*- coding:utf-8 -*-
import sys,os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)) , ".." , "toyccg"))
from lexicon import *
from ccgparser import *

combinators = [LApp,RApp,LB,RB,LBx,LS,RS,LSx,RSx,LT,RT,Conj]
terminators = ["ROOT","S"]

def jptest(sentence,lexicon):
   def decode(left_start , right_end , path , chart):
       ret = []
       if len(path)==1:
          return ret
       elif len(path)==3:
          idx = path[0]
          cat1,path1 = chart[(left_start,right_end)][idx]
          if len(path1)==0:
              return [(left_start , right_end , cat1)]
          else:
              return decode(left_start,right_end , path1 , chart)
       else:
          assert(len(path)==5),path
          idx1,idx2,left_end,_,_ = path
          right_start = left_end+1
          cat1,path1 = chart[(left_start,left_end)][idx1]
          cat2,path2 = chart[(right_start,right_end)][idx2]
          if len(path1)==1:
              ret.append( (left_start,left_end,cat1) )
          else:
              ret.extend( decode(left_start,left_end , path1 , chart) )
          if len(path2)==1:
              ret.append( (right_start,right_end,cat2) )
          else:
              ret.extend( decode(right_start,right_end ,path2, chart) )
          return ret
   print(u"test run : sentence={0}".format(sentence))
   for chart in buildChart(sentence,lexicon):
       topcat,path = chart[(0,len(sentence)-1)][-1]
       print( (topcat.value() , decode(0 , len(sentence)-1 , path , chart)) )
       print("")
   print("")



class JPLexicon(object):
    def __init__(self, dic=None):
        self.static_dics = {}
        if dic!=None:
             for line in open(dic, encoding='utf-8'):
                 line = line.strip()
                 if len(line)==0:continue
                 ls = line.split('\t')
                 self.static_dics.setdefault(ls[0],[]).extend( [c for c in ls[1].split(",")] )
    def __getitem__(self,tok):
        w = tok
        cats = self.static_dics.get(w , [])
        if len(cats)==0:  #-guess
            if re.match(r'\d+$',w)!=None:
                cats.extend( ["NP","NP/N[pl]" , "NP/N"] )
            elif re.match(r'\d+th$',w)!=None:
                cats.extend( ["NP", "NP/N[pl]" , "NP/N" , "N/N" , "N[pl]/N[pl]"] )
            elif w[-1]=="'" and w[-2]=="s": #-- e.g. Americans'
                cats.extend(["NP/N[pl]" , "NP/N"])
            elif w[0].isupper():   #-- proper noun
                cats.extend( ["NP" , "NP/N" , "N/N", "NP/N[pl]"] )
            elif w[-2:]=='ly':  #-- RB
                cats.extend(["S/S","S\\S","((NP\\NP)/(NP\\NP))","VP[adj]/VP[adj]","S[q]\\S[q]","S[imp]\\S[imp]"])
            elif w[-3:] in ["ive","ble"]: #-- JJ
                cats.extend(["N/N","NP/N[pl]","NP/N","N[pl]/N[pl]","VP[adj]","NP/N"])
        ret = []
        for c in set(cats):
            if isinstance(c,basestring):
                 ret.append( lexparse(c) )
            else:
                 ret.append( c )
        return ret
    def __setitem__(self,tok,cats):
        self.static_dics[tok] = cats
    def has_key(self,tok):
        return (tok in self.static_dics)
    def get(self,toklist,defval):
        ret = self.__getitem__(toklist)
        return ret




"""
動詞語幹
VP[neg]:未然形
VP[cont]:連用形
VP[euph]:連用形(過去)



"""
if __name__=="__main__":
   TOPDIR = os.path.dirname(os.path.abspath(__file__))
   lexicon = JPLexicon(os.path.join(TOPDIR , "ccglex.jpn"))
   #-- 機能語
   lexicon[u"。"] = ["ROOT\\S"]
   lexicon[u"な"] = ["(N/N)\\N[adj]"]
   lexicon[u"は"] = ["NP[nom]\\N"]
   lexicon[u"が"] = ["NP[nom]\\N"]
   lexicon[u"も"] = ["NP[nom]\\N"]
   lexicon[u"を"] = ["NP[acc]\\N"]
   lexicon[u"や"] = ["(N/N)\\N"]
   lexicon[u"に"] = ["((S\\NP[nom])/(S\\NP[nom]))\\N","((S\\NP[nom])/(S\\NP[nom]))\\N[adj]","(S[imp]/S[imp])\\N[adj]"]
   lexicon[u"で"] = ["((S\\NP[nom])/(S\\NP[nom]))\\N"]
   lexicon[u"と"] = ["((S\\NP[nom])/(S\\NP[nom]))\\N","(S/S)\S",Symbol("CONJ")]
   lexicon[u"の"] = ["(N/N)\\N"]
   lexicon[u"から"] = ["((S\\NP[nom])/(S\\NP[nom]))\\N"]
   lexicon[u"です"] = ["(S\\NP[nom])\\N","(S\\NP[nom])\\N[adj]"]
   lexicon[u"ます"] = ["(S\\NP[nom])\\VP[cont]"]
   lexicon[u"だ"] = ["(S\\NP[nom])\\N","(S\\NP[nom])\\N[adj]"]
   lexicon[u"ない"] = ["(S\\NP[nom])\\VP[neg]","((S\\NP[nom])\\NP[acc])\\IV[neg]","(S\\NP[nom])\\VP[a-cont]","(N/N)\\VP[a-cont]","((S\\NP[nom])\\NP[acc])\\TV[neg]","S\\NP[nom]"]
   lexicon[u"ません"] = ["(S\\NP[nom])\\VP[neg]","((S\\NP[nom])\\NP[acc])\\IV[neg]"]
   lexicon[u"いる"] = ["S\\S[te]","S\\NP[nom]"]
   lexicon[u"こと"] = ["N\\S"]
   lexicon[u"た"] = ["(S\\NP[nom])\\IV[euph]","((S\\NP[nom])\\NP[acc])\\VP[euph]"]
   lexicon[u"て"] = ["(S[te]\\NP[nom])\\VP[cont]","((S[te]\\NP[nom])\\NP[acc])\\VP[cont]","((S\\NP[nom])/(S\\NP[nom]))\\VP[cont]"]
   jptest(u"これは人間です。" , lexicon)
   jptest(u"私は走った" , lexicon)
   jptest(u"彼はとても驚いた",lexicon)
   jptest(u"彼はとても速く走った",lexicon)
   jptest(u"彼が走ると世界が滅ぶ",lexicon)
   jptest(u"彼はすももを食べている",lexicon)
   jptest(u"東京の人間は斧を食べている",lexicon)
   jptest(u"子供が寝ている",lexicon)
   jptest(u"子供がいる",lexicon)
   jptest(u"私は東京に行った",lexicon)
   jptest(u"東京はいい天気です",lexicon)
   jptest(u"かわいい私の妹がいる",lexicon)
   jptest(u"私の妹はかわいい",lexicon)
   jptest(u"私はとてもかわいい",lexicon)
   jptest(u"東京の風は赤い",lexicon)
   jptest(u"私は妹と東京に行った",lexicon)
   jptest(u"私は京都と東京に行った",lexicon)
   jptest(u"私の友人と妹は東京に行った",lexicon)
   jptest(u"私は東京から京都に行った",lexicon)
   jptest(u"私は東京で妹と会った",lexicon)
   jptest(u"友人は下で寝ている",lexicon)
   jptest(u"彼は武器職人です",lexicon)
   jptest(u"彼は人間関係に詳しい",lexicon)
   jptest(u"彼は私を知らない",lexicon)
   jptest(u"私や彼は行かない",lexicon)
   jptest(u"私は赤い電車を見た",lexicon)
   jptest(u"私は電車で行きます。",lexicon)
   jptest(u"私は電車で行く。",lexicon)
   jptest(u"私は寝て驚いた",lexicon)
