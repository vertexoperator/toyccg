# -*- coding:utf-8 -*-
import threading
import time
import sys

class threadsafe_iter:
    """Takes an iterator/generator and makes it thread-safe by
    serializing call to the `next` method of given iterator/generator.
    """
    def __init__(self, it):
        self.it = it
        self.lock = threading.Lock()
    def __iter__(self):
        return self
    def next(self):
        with self.lock:
            return self.it.next()


def threadsafe_generator(f):
    """A decorator that takes a generator function and makes it thread-safe.
    """
    if sys.version_info[0] == 2:
        def g(*a, **kw):
            return threadsafe_iter(f(*a, **kw))
        return g
    else:
        return f


@threadsafe_generator
def Counter():
    cnt = 0
    while True:
        yield cnt
        cnt+=1


gen_state = Counter()


#固定文字列を受理するオートマトン
#(nfaジェネレータ、開始状態、開始状態が受理状態でもあるかどうか)を返す
def literal(s):
  __states__ = [next(gen_state) for c in s]
  __states__.append(next(gen_state))
  def __nfa__(state , symbol):
      if state in __states__:
         idx = __states__.index(state)
         if idx<len(s) and symbol==s[idx]:
             yield(__states__[idx+1] , len(s)==idx+1)
  return (__nfa__ , __states__[0] , len(s)==0)



def option(r):
   def __nfa__(state , symbol):
      for it in r[0](state,symbol):yield it
   return (__nfa__, r[1] , True)


def iterate(r):
   def __nfa__(state , symbol):
      for (st,cont) in r[0](state , symbol):
          if cont:
             yield r[1],True
          else:
             yield st,False
   return (__nfa__, r[1], True)


def either(r1 , r2):
    __states__ = [next(gen_state)]
    def __nfa__(state , symbol):
        if state==__states__[0]:
            for it in r1[0](r1[1] , symbol):yield it
            for it in r2[0](r2[1] , symbol):yield it
        else:
            for it in r1[0](state , symbol):yield it
            for it in r2[0](state , symbol):yield it
    return (__nfa__ , __states__[0] , r1[2] or r2[2])


def sequence(*args):
    def __nfa__(state , symbol):
        for n,r in enumerate(args):
            for st,acc in r[0](state,symbol):
               if acc and n<len(args)-1:
                   cn = n + 1
                   while True:
                      if cn==len(args)-1:
                          yield (args[cn][1],args[cn][2])
                          break
                      elif args[cn][2]:
                          yield args[cn][1],all([r[2] for r in args[cn:]])
                          cn += 1
                      else:
                          yield args[cn][1],False
                          break
               yield st,(acc and n==len(args)-1)
    if len(args)>1:
        return (__nfa__ , args[0][1] , all([r[2] for r in args]))




#正規表現に(先頭から)マッチした残りの部分を返す
#greedyではなく、可能な全ての候補をジェネレータで返す
def deriv(nfa , s):
   def reducez(g , init , s):
      __state__ = (init,)
      __memo__ = dict()
      __accept__ = dict()
      for n,sym in enumerate(s):
          if not ((__state__ , sym) in __memo__):
              nextaddr = set([])
              acc = False
              for st in __state__:
                 for nextst,cont in g(st,sym):
                     nextaddr.add( nextst )
                     acc = acc or cont
              if len(nextaddr)==0:break
              __memo__[ (__state__ , sym) ] = tuple(nextaddr)
              __accept__[ tuple(nextaddr) ] = acc
          __state__ = __memo__[ (__state__ , sym) ]
          if __accept__[__state__]:
              yield s[n+1:]
   if nfa[2]:yield s
   for it in reducez(nfa[0] , nfa[1] , s):
      yield it



def uppercase():
   __states__ = [next(gen_state),next(gen_state)]
   def __nfa__(state , symbol):
       if state==__states__[0] and symbol.isupper():
            yield (__states__[1] , True)
   return (__nfa__ , __states__[0] , False)


def lowercase():
   __states__ = [next(gen_state),next(gen_state)]
   def __nfa__(state , symbol):
       if state==__states__[0] and symbol.islower():
            yield (__states__[1] , True)
   return (__nfa__ , __states__[0] , False)



class Symbol(object):
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


def lexparse(_s):
    cat_feat = sequence(literal("[") , lowercase() , iterate(lowercase()) , literal("]"))
    primcat = either(sequence(iterate(uppercase()) , cat_feat) , sequence(uppercase() ,iterate(uppercase())))
    def aux(s):
       for rest in deriv(primcat , s):
            if len(rest)<len(s):
                yield (Symbol(s[:len(s)-len(rest)]) , rest)
       if s[0]=="(":
           for ret1,rest in aux(s[1:]):
               if rest[0]=="/" or rest[0]=="\\":
                  for ret2,rest2 in aux(rest[1:]):
                      if rest2[0]==")":
                          yield ([Symbol(rest[0]),ret1,ret2] , rest2[1:])
    if _s[0]=="(" and _s[-1]==")":
       for (r,s0) in aux(_s):
          if len(s0)==0:return r
    for rest in deriv(primcat,_s):
        if len(rest)==0:return Symbol(_s)
    for (r,s0) in aux("(" + _s + ")"):
        if len(s0)==0:return r




if __name__=="__main__":
   #"(aa|bb?)*"
   reg = iterate(either(sequence(literal("a"),literal("a")) , option(literal("bb"))))
   assert(list(deriv(reg , "aabbaaaabbc")) == ['aabbaaaabbc', 'bbaaaabbc', 'aaaabbc', 'aabbc', 'bbc' , 'c'])
   assert(list(deriv(reg , "ssab"))==['ssab'])
   assert(list(deriv( sequence(iterate(literal("A")) ,iterate(literal("B")))  , "AABABA"))==['AABABA', 'ABABA', 'BABA', 'ABA'])
   assert(list(deriv(sequence(literal("a") ,literal("b"),literal("c")) , "abcd"))==["d"])



