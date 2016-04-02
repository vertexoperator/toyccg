# -*- coding:utf-8 -*-
import sys,os
sys.path.append( os.path.join(os.path.dirname( os.path.abspath(__file__) ) , ".." , "toyccg") )
from ccg import LApp,RApp,LB,RB,LBx,Conj,SkipComma,lexify,Symbol,CCGParser,LT,RT


class Lexicon:
  def __init__(self):
    self.static_dics = {}
    self.static_dics[u"。"] = ["ROOT\\S" , "ROOT\\S[wq]" , "ROOT\\S[q]" , "ROOT\\S[imp]"]
    for line in open(os.path.join(os.path.dirname( os.path.abspath(__file__) ) ,"ccglex.ma")):
        line = line.strip()
        if len(line)==0:continue
        if line[0]=="#":continue
        ls = line.split('\t')
        self.static_dics.setdefault(ls[0].decode('utf-8'),[]).extend( ls[2].split(",") )
  def __getitem__(self,tok):
    w = tok
    cats = self.static_dics.get(w , [])
    ret = [lexify(c) for c in cats]
    return ret
  def get(self,tok,defval):
    ret = self.__getitem__(tok)
    if len(ret)>0:return ret
    return defval


parser = CCGParser()
parser.combinators = [LApp,RApp,LB,RB,LBx,Conj,SkipComma,RT("NP")]
parser.terminators = ["ROOT","S","S[wq]","S[q]","S[imp]"]
parser.lexicon = Lexicon()
parser.concatenator = ""


if __name__=="__main__":
   for line in sys.stdin:
       line = line.strip()
       line = line.decode('utf-8')
       print(u"test:{}".format(line))
       for t in parser.parse(line):
          for r in t.leaves():
              print(u"{0}\t{1}".format(r.token , r.catname))
          break
       print("")


