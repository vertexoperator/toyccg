# -*- coding:utf-8 -*-
import sys,os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)) , ".." , "toyccg"))
from lexicon import *
from ccgparser import *

combinators = [LApp,RApp,LB,RB,LBx,LS,RS,LSx,RSx,LT,RT,Conj]
def JPChart(sentence , lexicon):
   def check_args(fc , path1 , path2):
       #-- restrictions on type-raising and composition
       if len(path2)==2 and fc==RBx and path2[1]=="LT":
           return False
       elif len(path1)==2 and fc==LBx and path1[1]=="RT":
           return False
       #-- conjunction modality
       elif len(path2)==4 and path2[3]=="Conj" and fc!=LApp:
           return False
       #-- NF constraint 1 and 2
       elif len(path1)==4 and path1[3] in ["LB","LBx"] and fc in [LB,LBx]:
           return False
       elif len(path2)==4 and path2[3] in ["LB","LBx"] and fc==LApp:
           return False
       elif len(path1)==4 and path1[3] in ["RB","RBx"] and fc in [RApp,RB,RBx]:
           return False
       #-- NF constraint 5
       elif len(path1)==2 and (fc,path1[1])in [(RApp,"RT")]:
           return False
       #-- NF constraint 5
       elif len(path2)==2 and (fc,path2[1]) in [(LApp,"LT")]:
           return False
       else:
           return True
   chart = {}
   N = len(sentence)
   for n in range(N+1):
      for m in range(N+1):
          if n>m:continue
          chart[(n,m)] = [(c,tuple()) for c in lexicon.get(sentence[n:m+1] , [])]
          #-- add type raising
          rest = []
          for idx0,(cat,_) in enumerate(chart.get((n,m),[])):
              for f in combinators:
                 assert(inspect.isfunction(f))
                 if len(inspect.getargspec(f).args)==1:
                     cat2 = f(cat)
                     path = (idx0 , f.__name__)
                     if cat2!=None:rest.append( (cat2 , path) )
          chart[(n,m)] = chart.get((n,m),[]) + rest
   for width in range(1,N):
      for start in range(0 , N-width):
         for partition in range(0,width):
             left_start = start
             left_end = start + partition
             right_start = left_end + 1
             right_end = start+width
             assert(left_start<=left_end)
             assert(right_start<=right_end)
             assert(left_end<N)
             assert(right_end<N)
             for idx1,(Lcat,Lpath) in enumerate(chart.get((left_start,left_end),[])):
                 for idx2,(Rcat,Rpath) in enumerate(chart.get((right_start,right_end),[])):
                    for f in combinators:
                       assert(inspect.isfunction(f))
                       if len(inspect.getargspec(f).args)==2 and check_args(f,Lpath,Rpath):
                          cat2 = f(Lcat,Rcat)
                          #---- really needs this check? ----
                          if cat2==[FwdApp , Symbol("S") , Symbol("N")]  or cat2==[FwdApp , Symbol("S[q]") , Symbol("N")]:
                              pass
                          elif cat2==[FwdApp , Symbol("S") , Symbol("N[pl]")]:
                              pass
                          elif cat2==[FwdApp , Symbol("NP") , Symbol("N")]:
                              pass
                          elif cat2!=None:
                              path = (idx1,idx2,left_end,f.__name__)
                              chart.setdefault( (left_start,right_end) , []).append( (cat2 , path) )
             #-- add type raising
             rest = []
             for idx,(cat,path0) in enumerate(chart.get((left_start,right_end),[])):
                 assert(cat!=None),cat
                 if len(path0)==4 and path0[3]=="Conj":continue
                 for f in combinators:
                    assert(inspect.isfunction(f))
                    if len(inspect.getargspec(f).args)==1:
                       cat2 = f(cat)
                       if cat2!=None:
                            path = (idx,f.__name__)
                            rest.append( (cat2 , path) )
             chart[(left_start ,right_end)] = chart.get((left_start,right_end),[]) + rest
   return chart


terminators = ["ROOT","S"]

def jptest(sentence,lexicon):
   def decode(left_start , right_end , path , chart):
       ret = []
       if len(path)==0:
          return ret
       elif len(path)==2:
          idx = path[0]
          cat1,path1 = chart[(left_start,right_end)][idx]
          if len(path1)==0:
              return [(left_start , right_end , cat1)]
          else:
              return decode(left_start,right_end , path1 , chart)
       else:
          assert(len(path)==4),path
          idx1,idx2,left_end,_ = path
          right_start = left_end+1
          cat1,path1 = chart[(left_start,left_end)][idx1]
          cat2,path2 = chart[(right_start,right_end)][idx2]
          if len(path1)==0:
              ret.append( (left_start,left_end,cat1) )
          else:
              ret.extend( decode(left_start,left_end , path1 , chart) )
          if len(path2)==0:
              ret.append( (right_start,right_end,cat2) )
          else:
              ret.extend( decode(right_start,right_end ,path2, chart) )
          return ret
   chart = JPChart(sentence,lexicon)
   print(u"test run : sentence={0}".format(sentence))
   for (topcat,path) in chart.get((0,len(sentence)-1) ,[]):
       if type(topcat)!=list and topcat.value() in terminators:
           tagsets = decode(0 , len(sentence)-1 , path , chart)
           tagsets.sort()
           for (s,e,c) in tagsets:
                print (u"{0}\t{1}".format(sentence[s:e+1],catname(c)))
           print ("")
   print("")


"""
動詞語幹
VP[neg]:未然形
VP[cont],VP[past]:連用形
VP[term]:終止形



"""
if __name__=="__main__":
   lexicon = {}
   lexicon[u"私"] = [Symbol("N")]
   lexicon[u"彼"] = [Symbol("N")]
   lexicon[u"それ"] = [Symbol("N")]
   lexicon[u"は"] = [lexparse("NP[sbj]\\N")]
   lexicon[u"が"] = [lexparse("NP[sbj]\\N")]
   lexicon[u"も"] = [lexparse("NP[sbj]\\N")]
   lexicon[u"を"] = [lexparse("NP[obj]\\N")]
   lexicon[u"や"] = [lexparse("(N/N)\\N")]
   lexicon[u"に"] = [lexparse("((S\\NP[sbj])/(S\\NP[sbj]))\\N")]
   lexicon[u"で"] = [lexparse("((S\\NP[sbj])/(S\\NP[sbj]))\\N")]
   lexicon[u"と"] = [lexparse("((S\\NP[sbj])/(S\\NP[sbj]))\\N"),lexparse("(S/S)\S"),Symbol("CONJ")]
   lexicon[u"の"] = [lexparse("(N/N)\\N")]
   lexicon[u"から"] = [lexparse("((S\\NP[sbj])/(S\\NP[sbj]))\\N")]
   lexicon[u"人間"] = [Symbol("N")]
   lexicon[u"です"] = [lexparse("(S\\NP[sbj])\\N")]
   lexicon[u"ます"] = [lexparse("(S\\NP[sbj])\\VP[cont]")]
   lexicon[u"だ"] = [lexparse("(S\\NP[sbj])\\N")]
   lexicon[u"人"] = [Symbol("N")]
   lexicon[u"間"] = [Symbol("N")]
   lexicon[u"この"] = [lexparse("N/N")]
   lexicon[u"すもも"] = [Symbol("N")]
   lexicon[u"これ"] = [Symbol("N")]
   lexicon[u"走る"] = [lexparse("S\\NP[sbj]")]
   lexicon[u"走った"] = [lexparse("S\\NP[sbj]")]
   lexicon[u"会った"] = [lexparse("S\\NP[sbj]")]
   lexicon[u"行った"] = [lexparse("S\\NP[sbj]")]
   lexicon[u"見た"] = [lexparse("(S\\NP[sbj])\\NP[obj]")]
   lexicon[u"行か"] = [Symbol("VP[neg]")]
   lexicon[u"行き"] = [Symbol("VP[cont]")]
   lexicon[u"行く"] = [lexparse("S\\NP[sbj]")]
   lexicon[u"行け"] = [Symbol("VP[neg]")]
   lexicon[u"知ら"] = [Symbol("VP[neg]")]
   lexicon[u"ない"] = [lexparse("(S\\NP[sbj])\\VP[neg]"),lexparse("((S\\NP[sbj])\\NP[obj])\\VP[neg]"),lexparse("S\\NP[sbj]")]
   lexicon[u"滅ぶ"] = [lexparse("S\\NP[sbj]")]
   lexicon[u"襲う"] = [lexparse("(S\\NP[sbj])\\NP[obj]")]
   lexicon[u"詳しい"] = [lexparse("S\\NP[sbj]"),lexparse("N/N")]
   lexicon[u"驚いた"] = [lexparse("S\\NP[sbj]")]
   lexicon[u"食べている"] = [lexparse("(S\\NP[sbj])\\NP[obj]")]
   lexicon[u"とても"] = [lexparse("(S\\NP[sbj])/(S\\NP[sbj])")]
   lexicon[u"速く"] = [lexparse("(S\\NP[sbj])/(S\\NP[sbj])"),Symbol("VP[neg]")]
   lexicon[u"武器"] = [Symbol("N")]
   lexicon[u"職人"] = [Symbol("N"),lexparse("N\\N")]
   lexicon[u"関係"] = [Symbol("N"),lexparse("N\\N")]
   lexicon[u"照射"] = [Symbol("N"),lexparse("N\\N")]
   lexicon[u"摂取"] = [Symbol("N"),lexparse("N\\N")]
   lexicon[u"電車"] = [Symbol("N")]
   lexicon[u"斧"] = [Symbol("N")]
   lexicon[u"風"] = [Symbol("N")]
   lexicon[u"朝"] = [Symbol("N")]
   lexicon[u"世界"] = [Symbol("N")]
   lexicon[u"東京"] = [Symbol("N")]
   lexicon[u"天気"] = [Symbol("N")]
   lexicon[u"子供"] = [Symbol("N")]
   lexicon[u"いる"] = [lexparse("S\\S[te]"),lexparse("S\\NP[sbj]")]
   lexicon[u"寝て"] = [lexparse("S[te]\\NP[sbj]"),lexparse("(S[te]\\NP[sbj])\\NP[obj]"),lexparse("(S\\NP[sbj])/(S\\NP[sbj])"),lexparse("S/S"),Symbol("VP[neg]")]
   lexicon[u"いい"] = [lexparse("N/N")]
   lexicon[u"暴力"] = [lexparse("N")]
   lexicon[u"かわいい"] = [lexparse("N/N"),lexparse("S\\NP[sbj]")]
   lexicon[u"赤い"] = [lexparse("N/N"),lexparse("S\\NP[sbj]")]
   lexicon[u"妹"] = [Symbol("N")]
   lexicon[u"京都"] = [Symbol("N")]
   lexicon[u"友人"] = [Symbol("N")]
   lexicon[u"下"] = [Symbol("N")]
   lexicon[u"重力"] = [Symbol("N")]
   jptest(u"これは人間です" , lexicon)
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
   jptest(u"私は電車で行きます",lexicon)
   jptest(u"私は電車で行く",lexicon)
   jptest(u"私は寝て驚いた",lexicon)
