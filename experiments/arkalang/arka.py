# -*- coding:utf-8 -*-
import sys,os
sys.path.append( os.path.join(os.path.dirname( os.path.abspath(__file__) ) , ".." , ".." , "toyccg") )
from ccg import LApp,RApp,LB,RB,LBx,Conj,LT,RT,SkipComma,CCGParser



class Lexicon(object):
    def __init__(self):
        self.static_dics = {}
        self.static_dics[u"."] = ["ROOT\\S" , "ROOT\\S[imp]" , "ROOT\\S[q]" , "ROOT\\S[wq]"]
        for line in open(os.path.join(os.path.dirname( os.path.abspath(__file__) ) ,"ccglex.arka")):
           line = line.strip()
           if len(line)==0:continue
           if line[0]=="#":continue
           ls = line.split('\t')
           self.static_dics.setdefault(ls[0].decode('utf-8'),[]).extend( ls[1].split(",") )
    def __getitem__(self,tokens):
        if len(tokens)==1:
           return self.static_dics.get(tokens[0],[])
        else:
           return []
    def __setitem__(self,tok,cats):
        self.static_dics[tok] = cats
    def has_key(self,tok):
        return (tok in self.static_dics)
    def get(self,toklist,defval):
        ret = self.__getitem__(toklist)
        return ret


parser = CCGParser()
parser.combinators = [LApp,RApp,LB,RB,Conj,RT("NP[sbj]"),LBx]
parser.terminators = ["ROOT","S","S[wq]","S[q]","S[imp]"]
parser.lexicon = Lexicon()
parser.concatenator = ""

def tokenize(s):
    if len(s)==0:
        return s
    elif s[-1]==".":
        tokens = s[:-1].split()
        tokens.append( s[-1] )
        return tokens
    else:
        return s.split()


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
       for t in parser.parse(tokenize(line)):
          for r in t.leaves():
              print(u"{0}\t{1}".format(__repr__(r.token) , r.catname))
          break
       print("")
