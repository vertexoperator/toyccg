# -*- coding:utf-8 -*-
import sys,os
sys.path.append( os.path.join(os.path.dirname( os.path.abspath(__file__) ) , ".." , ".." , "toyccg") )
from ccg import LApp,RApp,LB,RB,LBx,Conj,LT,RT,SkipComma,CCGParser

def default_lexicon():
    ret = {}
    ret[u"。"] = ["ROOT\\S" , "ROOT\\S[imp]" , "ROOT\\S[q]" , "ROOT\\S[wq]"]
    ret[u"?"] = ["ROOT\\S[q]" , "ROOT\\S[wq]"]
    for line in open(os.path.join(os.path.dirname( os.path.abspath(__file__) ) ,"ccglex.ma")):
        line = line.strip()
        if len(line)==0:continue
        if line[0]=="#":continue
        ls = line.split('\t')
        ret.setdefault(ls[0].decode('utf-8'),[]).extend( ls[2].split(",") )
    return ret



parser = CCGParser()
parser.combinators = [LApp,RApp,LB,RB,LBx,Conj,SkipComma,RT("NP")]
parser.terminators = ["ROOT","S","S[wq]","S[q]","S[imp]"]
parser.lexicon = default_lexicon()
parser.concatenator = ""


if __name__=="__main__":
   def __repr__(s):
       if sys.stdout.encoding=='UTF-8':
            return s
       else:
            return repr(s)
   for line in sys.stdin:
       line = line.strip()
       line = line.decode('utf-8')
       print(u"test:{}".format(__repr__(line)))
       for t in parser.parse(line):
          for r in t.leaves():
              print(u"{0}\t{1}".format(__repr__(r.token) , r.catname))
          break
       print("")


