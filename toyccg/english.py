# -*- coding:utf-8 -*-
from ccg import LApp,RApp,LB,RB,LT,RT,Conj,SkipComma,Rel,CCGParser,lexify
import os,sys,re

#-- for python2/3 compatibility
from io import open
if sys.version_info[0] == 3:
   basestring = str
else:
   basestring = basestring


class Lexicon(object):
    def __init__(self, worddic=None , phrasedic=None):
        self.static_dics = {}
        if worddic!=None:
             for line in open(worddic, encoding='utf-8'):
                 line = line.strip()
                 if len(line)==0:continue
                 tok,_,cats = line.split('\t')
                 self.static_dics[tok] = [c for c in cats.split(",")]
        if phrasedic!=None:
             for line in open(phrasedic, encoding='utf-8'):
                 line = line.strip()
                 if len(line)==0:continue
                 tok,cats = line.split('\t')
                 self.static_dics[tok] = [c for c in cats.split(",")]
    def __getitem__(self,toklist):
        if len(toklist)==0:
            return []
        elif len(toklist)==1:
            w = toklist[0]
            cats = self.static_dics.get(w , [])
            if w!=w.lower():
                cats.extend( self.static_dics.get(w.lower() , []) )
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
        else:
            cats = self.static_dics.get(" ".join(toklist) , [])
            if len(cats)==0:
                cats = self.static_dics.get(" ".join(toklist).lower() , [])
        assert(type(cats)==list),toklist
        ret = []
        for c in set(cats):
            if isinstance(c,basestring):
                 ret.append( lexify(c) )
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



def sentencize(s):
    if s[-1]==".":
       ls = (s+" ").split(". ")
    else:
       ls = s.split(". ")
    tmp = []
    for it in ls:
        if len(it.split())==1:
            tmp.append(it)
        else:
            if len(tmp)==0:
                tmp.append(it)
            elif tmp[-1].find(".")>0:
                tmp.append(it)
            elif not tmp[-1] in ["Mr","Mrs","Ms","Mt","St"]:
                x = (". ".join(tmp).strip())
                if not x[-1] in [".","?","!"]:
                    yield (x+".")
                else:
                    yield x
                tmp = [it]
            else:
                tmp.append(it)
    if len(tmp)>0:
       x = "".join(tmp).strip()
       if x!='' and x!=".":yield x


"""
>>> list(tokenize('This is a pen. That is a desk. What\'s your name?'))
[['This', 'is', 'a', 'pen', '.'], ['That', 'is', 'a', 'desk', '.'], ['What\'s", 'your', 'name', '?']]

>>> list(tokenize('"The Call of Cthulhu" is a short story by American writer H. P. Lovecraft.'))
[['"', 'The', 'Call', 'of', 'Cthulhu', '"', 'is', 'a', 'short', 'story', 'by', 'American', 'writer', 'H.', 'P.', 'Lovecraft', '.']]

>>> list(tokenize('The U.S. was founded.'))
[['The', 'U.S.', 'was', 'founded', '.']]

"""
def tokenize(sents):
    for s in sentencize(sents):
       tokens = []
       tmp = []
       for n,c in enumerate(s):
           if ord(c)>=ord('a') and ord(c)<=ord('z'):
              tmp.append(c)
           elif ord(c)>=ord('A') and ord(c)<=ord('Z'):
              tmp.append(c)
           elif ord(c)>=ord('0') and ord(c)<=ord('9'):
              tmp.append(c)
           elif c=="-":
              tmp.append(c)
           elif c=="." and n<len(s)-1:
              tmp.append(c)
           elif c==' ':
              if len(tmp)>0:
                 tokens.append( "".join(tmp) )
                 tmp = []
           elif c==':':
              if n==len(s)-1 or s[n+1]==' ':
                 tokens.append( "".join(tmp) )
                 tmp = []
                 tokens.append( c )
                 yield tokens
                 tokens = []
              else:
                 tmp.append(c)
           elif c in ['?' , '!' , ';']:
              if len(tmp)>0:
                  tokens.append( "".join(tmp) )
                  tmp = []
              tokens.append( c )
              yield tokens
              tokens = []
           elif c=="'":
              tmp.append( c )
           else:
              if len(tmp)>0:
                 tokens.append( "".join(tmp) )
                 tmp = []
              tokens.append(c)
       if len(tmp)>0:
          tokens.append( "".join(tmp) )
       if len(tokens)>0:
          yield tokens


def default_lexicon():
   TOPDIR = os.path.dirname(os.path.abspath(__file__))
   dic1 = os.path.join(TOPDIR , "data" , "ccglex.en")
   dic2 = os.path.join(TOPDIR , "data" , "phrases.en")
   lexicon = Lexicon(dic1,dic2)
   lexicon['.'] = ["ROOT\\S","ROOT\\S[imp]"]
   lexicon[';'] = ["ROOT\\S"]
   lexicon['?'] = ["ROOT\\S[q]","ROOT\\S[wq]"]
   lexicon[","] = [ "(((S/(S\\NP))\\NP)/COMMA)/(S/S)" ,"COMMA" ,"(S/S)\\VP[pss]" , "(NP/NP)\\NP"]
   lexicon["don't"] = ["(S\\NP)/(S\\NP)"]
   return lexicon


parser = CCGParser()
parser.combinators = [LApp,RApp,LB,RB,LT,RT,Conj,SkipComma,Rel]
parser.terminators = ["ROOT","S","S[q]","S[wq]","S[imp]"]
parser.lexicon = default_lexicon()




def run(text,type=0):
   for tokens in tokenize(text):
       print(u"test run : tokens={0}".format(str(tokens)))
       for t in parser.parse(tokens):
          if type==0:
              for r in t.leaves():
                 print(u"{0}\t{1}".format(r.token , r.catname))
              break
          else:
              print( t.show() )
              break
       print("")



if __name__=="__main__":
   for line in sys.stdin:
       line = line.strip()
       if len(line)==0:continue
       run(line)


