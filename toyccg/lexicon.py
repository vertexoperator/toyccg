# -*- coding:utf-8 -*-
"""
simple (inefficient) PEG parser for CCG lexicon
"""
class Parser:
    def parse(self, a):
        pass


class Many(Parser):
    __slots__ = ["parser"]
    def __init__(self, p):
        self.parser = p
    def parse(self, a):
        m = self.parser.parse(a)
        res = []
        rem = a
        while m:
            (rem, r) = m
            res.append(r)
            m = self.parser.parse(rem)
        return (rem, "".join(res))


class Many1(Parser):
    __slots__ = ["parser"]
    def __init__(self, p):
        self.parser = p
    def parse(self, a):
        m = self.parser.parse(a)
        if m:
            (rem, res) = m
            (rem2, res2) = Many(self.parser).parse(rem)
            return (rem2, res + res2)
        return None



class Char(Parser):
    __slots__ = ["ch"]
    def __init__(self, c):
        self.ch = c
    def parse(self, a):
        try:
            if a[0] == self.ch:
                return (a[1:], self.ch)
        except:
            pass
        return None



class Cond(Parser):
    __slots__ = ["cond"]
    def __init__(self, cond):
        self.cond = cond
    def parse(self, a):
        try:
            if self.cond(a[0]):
                return (a[1:], a[0])
        except:
            pass
        return None


class Sequence(Parser):
    __slots__ = ["parsers"]
    def __init__(self, *_parsers):
        self.parsers = _parsers
    def parse(self, a):
        if len(self.parsers)==0:return (a,[])
        m = (a,[])
        ret = []
        for n,p in enumerate(self.parsers):
            if m==None:return None
            rem,res = m
            if n>0:ret.append(res)
            m = p.parse(rem)
        if m:
            rem,res= m
            ret.append( res )
            return (rem,ret)
        return None



class Try(Parser):
    __slots__ = ["parser"]
    def __init__(self, p):
        self.parser = p
    def parse(self, s):
        m = self.parser.parse(s)
        return m if m else (s, [])



class Choice(Parser):
    __slots__=["p1","p2"]
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
    def parse(self, s):
        (rem, res) = Try(self.p1).parse(s)
        if len(rem) == len(s):
            return self.p2.parse(s)
        return (rem, res)


class Lazy(Parser):
    __slots__ = ["parser"]
    def __init__(self):
        self.parser = None
    def set(self , p):
        self.parser = p
    def parse(self, s):
        return self.parser.parse(s)




class Symbol(object):
   __slots__ = ["val"]
   def __init__(self,_val):
       self.val = _val
   def value(self):
       return self.val
   def __str__(self):
       return self.val
   def __eq__(self,other):
       return (type(other)==type(self) and self.val==other.val)
   def __ne__(self,other):
       return (type(other)!=type(self) or self.val!=other.val)
   def __repr__(self):
       return "Symbol('{0}')".format(self.val)
   def __hash__(self):
       return self.val.__hash__()


class buildPrimCat(Parser):
    __slots__ = ["parser"]
    def __init__(self,p):
       self.parser = p
    def parse(self,s):
       m = self.parser.parse(s)
       if m:
          rem,res = m
          if res[1]==[]:
             retval = res[0]
          else:
             retval = res[0]+"".join(res[1])
          return (rem,Symbol(retval))
       return m


class buildDerivCat(Parser):
    __slots__ = ["parser"]
    def __init__(self,p):
       self.parser = p
    def parse(self,s):
       m = self.parser.parse(s)
       if m:
          rem,res = m
          if len(res)==5:
              retval = [Symbol(res[2]) , res[1] , res[3]]
              return (rem,retval)
          elif len(res)==3:
              retval = [Symbol(res[1]) , res[0] , res[2]]
              return (rem,retval)
          else:
              assert(False)
       return m





Upper = Cond(lambda x:x.isupper())
Lower = Cond(lambda x:x.islower() or x=="-")
CatFeat = Sequence(Char('[') , Many1(Lower) , Char(']'))
PrimCat = buildPrimCat( Sequence( Many1(Upper) , Try(CatFeat) ))
Lexicon = Lazy()
TopDerivCat = buildDerivCat( Sequence( Lexicon , Choice(Char("/") , Char("\\")) , Lexicon ) )
DerivCat = buildDerivCat( Sequence(Char("(") , Lexicon , Choice(Char("/") , Char("\\")) , Lexicon , Char(")")) )
Lexicon.set(Choice(PrimCat , DerivCat))
TopLexicon = Choice(TopDerivCat , Lexicon)


def lexparse(s):
    rem,res = TopLexicon.parse(s)
    if len(rem)==0:
        return res
    else:
        return None

