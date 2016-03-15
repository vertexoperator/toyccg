# -*- coding:utf-8 -*-
import sys,os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)) , ".." , "toyccg"))
from lexicon import *
from ccgparser import *

jp_combinators = [LApp,RApp,LB,RB,LBx,LS,RS,LSx,RSx,LT,RT,Conj]
jp_terminators = ["ROOT","S","S[exc]","S[imp]","S[null]","S[q]","S[null-q]","S[nom]"]

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
   for chart in buildChart(sentence,lexicon,jp_combinators,jp_terminators):
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
        ret = []
        for c in cats:
            if not isinstance(c,basestring):
                 ret.append( c )
        for c in set([x for x in cats if isinstance(x,basestring)]):
            ret.append( lexparse(c) )
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




"""
動詞語幹
VP[neg]:未然形
VP[cont]:連用形
VP[euph]:連用形(過去)

S[q]:疑問文
S[imp]:命令文
S[exc]:感嘆文
S[null]:主語が省略された文
S[nom]:体言止め(nominal phrase)

"""
if __name__=="__main__":
   TOPDIR = os.path.dirname(os.path.abspath(__file__))
   lexicon = JPLexicon(os.path.join(TOPDIR , "ccglex.jpn"))
   #-- 機能語
   lexicon[u"。"] = ["ROOT\\S","ROOT\\S[null]"]
   lexicon[u"、"] = ["(N/N)\\N" ,[FORALL ,[Symbol("X")] , [BwdApp , Symbol("X") , Symbol("X")]]]
   lexicon[u"たい"] = ["(S\\NP[nom])\\IV[cont]" , "((S\\NP[nom])\\NP[acc])\\VP[cont]"]
   #-- (形容詞,非自立)
   lexicon[u"にくい"] = ["(S\\NP[nom])\\IV[cont]" , "((S\\NP[nom])\\NP[acc])\\VP[cont]"]
   lexicon[u"やすい"] = ["(S\\NP[nom])\\IV[cont]" , "((S\\NP[nom])\\NP[acc])\\VP[cont]"]
   lexicon[u"やすく"] = ["IV[a-cont]\\IV[cont]" , "VP[a-cont]\\VP[cont]"]
   lexicon[u"やすけれ"] = ["IV[a-hyp]\\IV[cont]" , "IV[a-hyp]\\IV[cont]"]
   #--
   lexicon[u"な"] = ["(N/N)\\N[adj]"]
   lexicon[u"は"] = ["NP[nom]\\N"]
   lexicon[u"が"] = ["NP[nom]\\N","NP[ga-acc]\\N","(S/S)\\S"]
   lexicon[u"も"] = ["NP[nom]\\N","NP[nom-enum]\\N","(NP[nom]/NP[nom-enum])\\N","(NP[nom-enum]/NP[nom-enum])\\N"]
   lexicon[u"を"] = ["NP[acc]\\N"]
   lexicon[u"や"] = ["(N/N)\\N"]
   lexicon[u"に"] = ["((S\\NP[nom])/(S\\NP[nom]))\\N","((S\\NP[nom])/(S\\NP[nom]))\\N[adj]","(S[imp]/S[imp])\\N[adj]","(S[null]/S[null])\\N","(S[null]/S[null])\\N[adj]"]
   lexicon[u"で"] = ["((S\\NP[nom])/(S\\NP[nom]))\\N","(((S\\NP[nom])\\NP[acc])/((S\\NP[nom])\\NP[acc]))\\N","(S[imp]\\S[imp])\\N","(S[null]/S[null])\\N","(S[null]/S[null])\\N[adj]"]
   lexicon[u"と"] = ["((S\\NP[nom])/(S\\NP[nom]))\\N","(S/S)\S","CONJ","NP[acc]\\S"]
   lexicon[u"の"] = ["(N/N)\\N","((S[nom]\\NP[nom])/(S[nom]\\NP[nom]))\\N"]
   lexicon.setdefault(u"から",[]).extend( ["((S\\NP[nom])/(S\\NP[nom]))\\N","(S/S)\\S"] )
   lexicon[u"ようだ"] = ["S\\S"]
   lexicon[u"らしい"] = ["S\\S","(N/N)\\N","(S\\NP[nom])\\N"]
   lexicon[u"だろう"] = ["S\\S","(S\\NP[nom])\\N[adj]"]
   #-- (助詞,接続助詞)
   lexicon[u"ながら"] = ["((S/S)\\NP[nom])\\IV[cont]","((S/S)\\NP[acc])\\VP[cont]","((S[null]/S[null])\\NP[acc])\\VP[cont]","(S[null]/S[null])\\IV[cont]"]
   lexicon.setdefault(u"つつ",[]).extend( lexicon[u"ながら"] )
   lexicon[u"ので"] = ["(S/S)\\S","(S/S[null])\\S","(S/S)\\S[null]","(S/S[null])\\S[null]"]
   lexicon.setdefault(u"のに",[]).extend( lexicon[u"ので"] )
   lexicon.setdefault(u"から",[]).extend( lexicon[u"ので"] )
   lexicon.setdefault(u"が",[]).extend( lexicon[u"ので"] )
   lexicon.setdefault(u"けど",[]).extend( lexicon[u"ので"] )
   lexicon.setdefault(u"けれど",[]).extend( lexicon[u"ので"] )
   lexicon.setdefault(u"けれども",[]).extend( lexicon[u"ので"] )
   lexicon.setdefault(u"ならば",[]).extend( lexicon[u"ので"] )
   #-- (助詞,格助詞,連語)
   lexicon[u"について"] = ["(S/S)\\N","(S[null]/S[null])\\N"]
   lexicon[u"については"] = ["(S/S)\\N","(S[null]/S[null])\\N"]
   lexicon[u"に於いて"] = ["(S/S)\\N","(S[null]/S[null])\\N"]
   lexicon[u"に於いては"] = ["(S/S)\\N","(S[null]/S[null])\\N"]
   lexicon[u"に対して"] = ["(S/S)\\N","(S[null]/S[null])\\N"]
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
   lexicon[u"です"] = ["(S\\NP[nom])\\N","(S\\NP[nom])\\N[adj]","S[null]\\N","S[null]\\N[adj]"]
   lexicon[u"でしょう"] = ["(S\\NP[nom])\\N","(S\\NP[nom])\\N[adj]","S[null]\\N","S[null]\\N[adj]"]
   lexicon[u"でした"] = ["(S\\NP[nom])\\N","(S\\NP[nom])\\N[adj]","S[null]\\N","S[null]\\N[adj]"]
   lexicon[u"ます"] = ["(S\\NP[nom])\\IV[cont]","S[null]\\IV[cont]","((S\\NP[nom])\\NP[acc])\\VP[cont]","(S[null]\\NP[acc])\\VP[cont]"]
   lexicon[u"ました"] = lexicon[u"ます"]
   lexicon[u"だ"] = ["(S\\NP[nom])\\N","(S\\NP[nom])\\N[adj]","((S\\NP[nom])\\NP[ga-acc])\\N[adj]","((S\\NP[nom])\\NP[acc])\\N[adj]","S[null]\\N","S[null]\\N[adj]"]
   lexicon[u"ない"] = ["(S\\NP[nom])\\VP[neg]","((S\\NP[nom])\\NP[acc])\\IV[neg]","(S\\NP[nom])\\VP[a-cont]","(N/N)\\VP[a-cont]","((S\\NP[nom])\\NP[acc])\\TV[neg]","S\\NP[nom]"]
   lexicon[u"なけれ"] = ["IV[a-hyp]\\IV[neg]","VP[a-hyp]\\TV[neg]"]
   lexicon[u"ません"] = ["(S\\NP[nom])\\VP[neg]","((S\\NP[nom])\\NP[acc])\\IV[neg]"]
   lexicon[u"いる"] = ["S\\S[te]","S\\NP[nom]"]
#   lexicon[u"こと"] = ["N\\S"]
   lexicon[u"た"] = ["(S\\NP[nom])\\IV[euph]","((S\\NP[nom])\\NP[acc])\\VP[euph]"]
   lexicon[u"ば"] = ["((S/S)\\NP[nom])\\IV[hyp]","((S/(S\\NP[nom]))\\NP[nom])\\IV[hyp]","((S/S)\\NP[nom])\\IV[a-hyp]","((S/(S\\NP[nom]))\\NP[nom])\\IV[a-hyp]"]
   lexicon[u"て"] = ["(S[te]\\NP[nom])\\IV[cont]","((S/S)\\NP[nom])\\IV[cont]","(S[te]\\NP[nom])\\IV[euph]","((S[te]\\NP[nom])\\NP[acc])\\VP[cont]","((S\\NP[nom])/(S\\NP[nom]))\\VP[cont]"]
   #-- 名詞(サ変接続)+"する"
   lexicon.setdefault(u"する",[]).extend( ["(S\\NP[nom])\\N","S[null]\\N"] )
   lexicon[u"させる"] = lexicon[u"する"]
   tmpl = ["IV[neg]\\N","VP[neg]\\N","IV[cont]\\N","VP[cont]\\N","IV[euph]\\N","VP[euph]\\N"]
   lexicon.setdefault(u"し",[]).extend( tmpl )
   lexicon[u"させ"] = tmpl
   #--
   jptest(u"これは人間です。" , lexicon)
   jptest(u"私は走った" , lexicon)
   jptest(u"彼はとても驚いた",lexicon)
   jptest(u"彼はとても速く走った",lexicon)
   jptest(u"彼が走ると世界が滅ぶ",lexicon)
   jptest(u"彼はすももを食べている",lexicon)
   jptest(u"東京の人間は斧を食べている",lexicon)
   jptest(u"子供が寝ている",lexicon)
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
   jptest(u"私は彼が嫌いだ",lexicon)
   jptest(u"私は彼を嫌いだ",lexicon)
   jptest(u"その店は来年の夏に開業する。",lexicon)
   jptest(u"私は、数学が得意だ。",lexicon)
   jptest(u"虫が多くて私は困っている。",lexicon)
   jptest(u"それは、彼の得意な戦法です。",lexicon)
   jptest(u"風が吹けば、桶屋が儲かる。",lexicon)
   jptest(u"それが正しければ、大発見だ。",lexicon)
   jptest(u"しかし、彼が辞めると、私が困る。",lexicon)
   jptest(u"彼も私も正しい",lexicon)
   jptest(u"すももも桃も桃の内",lexicon)
#   jptest(u"象は鼻が長い",lexicon)
