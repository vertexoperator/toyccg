# -*- coding:utf-8 -*-
from lexicon import *
import inspect
import re

#-- for python2/3 compatibility
from io import open
import sys
if sys.version_info[0] == 3:
   basestring = str
else:
   basestring = basestring


"""
#-- Penn Part of Speech Tags
CC:等位接続詞
CD:数字
DT:限定詞
EX:there構文
FW:外国語
IN:前置詞/従位接続詞
JJ:形容詞/Adjective
JJR:形容詞(比較級)
JJS:形容詞(最上級)
MD:助動詞
NN:名詞(単数形)
NNP:固有名詞(単数形)
NNPS:固有名詞(複数形)
NNS:名詞(複数形)
PDT:限定詞前置語
POS:所有格
PRP:人称代名詞
PRP$:所有代名詞
RB:副詞/Adverb
RBR:副詞(比較級)
RBS:副詞(最上級)
RP:副助詞/Particle
SYM:記号
TO:to
UH:間投詞
UNC:未分類
VB:動詞(基本形)
VBD:動詞(過去形)
VBG:動詞(現在分詞)
VBN:動詞(過去分詞)
VBP:動詞(非三単現)
VBZ:動詞(三単現)
WDT:関係代名詞
WP:疑問代名詞
WP$:疑問代名詞(所有格)
WRB:疑問副詞

"""


BwdApp = Symbol("\\")
FwdApp = Symbol("/")
FORALL = Symbol("forall")


@threadsafe_generator
def mk_gensym():
    sym_id = 0
    while True:
        ret = Symbol("_{0}".format(sym_id))
        yield ret
        sym_id += 1


gensym = mk_gensym()


def subst_single(term , theta):
    if type(term)!=list:
        if term.value() in theta:
            return theta[term.value()]
        else:
            return term
    else:
        return [subst_single(t,theta) for t in term]


def unify(eqlist , vars):
    def recursive(var , term):
       if type(term)!=list:
          return (var==term.value())
       else:
          for t0 in term:
              if recursive(var,t0):
                   return True
       return False
    def subst_multi(eqs , theta):
       ret = []
       for (Lexp,Rexp) in eqs:
           ret.append( (subst_single(Lexp,theta) , subst_single(Rexp,theta)) )
       return ret
    def aux(lt , rt):
       ret = {}
       if type(lt)!=list and type(rt)!=list:
           if not (lt in vars) and not (rt in vars):
              if not(lt==rt):
                 return None
           elif (lt in vars) and not (rt in vars):
              ret[lt.value()] = rt
           elif not (lt in vars) and (rt in vars):
              ret[rt.value()] = lt
           elif (lt in vars) and (rt in vars) and not(lt==rt):
              ret[lt.value()] = rt
       elif type(lt)!=list and type(rt)==list:
           if not (lt in vars):
              return None
           else:
              ret[lt.value()] = rt
       elif type(lt)==list and type(rt)!=list:
           if not (rt in vars):
              return None
           else:
              ret[rt.value()] = lt
       else:
           assert(len(lt)==3),lt
           assert(len(rt)==3),rt
           if not(lt[0]==rt[0]):
              return None
           else:
              ret = solve([(lt[1],rt[1]) , (lt[2],rt[2])])
       return ret
    def solve(eqs):
       theta = {}
       for (Lexp,Rexp) in eqs:
           if type(Lexp)==list and type(Rexp)==list:
              if not (Lexp[0]==Rexp[0]):
                  return None
              theta1 = aux(subst_single(Lexp[1],theta) , subst_single(Rexp[1],theta))
              if theta1==None:return None
              for (k,v) in theta1.items():
                  if recursive(k,v):return None
                  theta[k] = v
              theta2 = aux(subst_single(Lexp[2],theta) , subst_single(Rexp[2],theta))
              if theta2==None:return None
              for (k,v) in theta2.items():
                  if recursive(k,v):return None
                  theta[k] = v
           else:
              theta1 = aux(subst_single(Lexp , theta) , subst_single(Rexp,theta))
              if theta1==None:return None
              for (k,v) in theta1.items():
                  if recursive(k,v):return None
                  theta[k] = v
       return theta
    ret = {}
    eqs = subst_multi(eqlist , ret)
    while True:
       theta = solve(subst_multi(eqlist , ret))
       if theta==None:return None
       if len(theta)==0:break
       for k,v in ret.items():
           ret[k] = subst_single(v , theta)
       for k,v in theta.items():
           ret[k] = v
       _eqs = subst_multi(eqlist , ret)
       if _eqs==eqs:break
    return ret



def term_eq(t1 , t2):
    if type(t1)!=type(t2):
        return False
    elif type(t1)!=list and type(t2)!=list:
        return (t1==t2)
    elif type(t1)==list and type(t2)==list:
        if t1[0].value()=="forall" and t2[0].value()=="forall":
            if len(t1[1])!=len(t2[1]):return False
            Nvars = len(t1[1])
            vars = [next(gensym) for _ in range(2*Nvars)]
            Lt = subst_single(t1[2] , dict(zip([c.value() for c in t1[1]] , vars[:Nvars])))
            Rt = subst_single(t2[2] , dict(zip([c.value() for c in t2[1]] , vars[Nvars:])))
            try:
                vmap = unify([(Lt,Rt)] , vars)
            except:
                assert(False),(t1,t2,vars)
            if vmap==None:return False
            for (k,v) in vmap.items():
                if type(v)==list:return False
                elif not v.value().startswith("_"):return False
            return True
        else:
            return (t1==t2)





def polymorphic(t):
    def _polymorphic(t):
       if type(t)!=list:
          return False
       for t0 in t:
          if type(t0)!=list and t0.value()=="forall":
              return True
          elif type(t0)==list and _polymorphic(t0):
              return True
    if type(t)!=list:
        return False
    else:
        return any([_polymorphic(t0) for t0 in t])


def findvars(term , vars):
    ret = []
    if type(term)!=list:
        if term in vars:
            ret.append(term)
    else:
        ret = sum([findvars(t,vars) for t in term],[])
    return list(set(ret))


#-- right I* combinator (X/Y Y => X)
def RApp(lt , rt):
    if type(lt)==list and lt[0].value()==FwdApp.value() and term_eq(lt[2],rt):
        return lt[1]
    if type(lt)!=list or type(rt)!=list:
        return None
    elif lt[0].value()!="forall" and rt[0].value()!="forall":
        return None
    elif polymorphic(lt) or polymorphic(rt):
        return None
    else:
        var1,var2 = next(gensym),next(gensym)
        oldvars = []
        if lt[0].value()=="forall":
            NB = lt
            LB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            LB = lt
        if rt[0].value()=="forall":
            NB = rt
            RB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            RB = rt
            mgu = unify([([FwdApp , var1, var2] ,LB) , (var2 , RB)] , oldvars+[var1,var2])
            if mgu!=None and (var1.value() in mgu):
                 NB = mgu[var1.value()]
                 nvars = findvars(NB , oldvars+[var1,var2])
                 if len(nvars)>0:
                      NB = [FORALL , nvars , NB]
                 return NB
    return None


#-- left I* combinator (Y X\Y => X)
def LApp(lt , rt):
    if type(rt)==list and rt[0].value()==BwdApp.value() and term_eq(rt[2],lt):
        return rt[1]
    if type(lt)!=list or type(rt)!=list:
        return None
    elif lt[0].value()!="forall" and rt[0].value()!="forall":
        return None
    elif polymorphic(lt) or polymorphic(rt):
        return None
    else:
        var1,var2 = next(gensym),next(gensym)
        oldvars = []
        if lt[0].value()=="forall":
            NB = lt
            LB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            LB = lt
        if rt[0].value()=="forall":
            NB = rt
            RB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            RB = rt
            mgu = unify([(var2 , LB) , ([BwdApp , var1, var2] , RB)] , oldvars+[var1,var2])
            if mgu!=None and (var1.value() in mgu):
                 NB = mgu[var1.value()]
                 nvars = findvars(NB , oldvars+[var1,var2])
                 if len(nvars)>0:
                      NB = [FORALL , nvars , NB]
                 return NB
    return None


#-- X/Y Y/Z => X/Z
def RB(lt , rt):
    if type(lt)!=list or type(rt)!=list:
        return None
    elif rt[0].value()==FwdApp.value() and lt[0].value()==FwdApp.value() and term_eq(rt[1],lt[2]):
        return [FwdApp,lt[1],rt[2]]
    elif lt[0].value()!="forall" and rt[0].value()!="forall":
        return None
    elif polymorphic(lt) or polymorphic(rt):
        return None
    else:
        var1,var2,var3 = next(gensym),next(gensym),next(gensym)
        oldvars = []
        if lt[0].value()=="forall":
            NB = lt
            LB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            LB = lt
        if rt[0].value()=="forall":
            NB = rt
            RB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            RB = rt
            mgu = unify([([FwdApp , var1, var2] ,LB) , ([FwdApp , var2, var3] , RB)] , oldvars+[var1,var2,var3])
            if mgu!=None and (var1.value() in mgu) and (var3.value() in mgu):
                 NB = [FwdApp , mgu[var1.value()] , mgu[var3.value()]]
                 nvars = findvars(NB , oldvars+[var1,var2,var3])
                 if len(nvars)>0:
                     NB = [FORALL , nvars , NB]
                 return NB
    return None




#-- X/Y Y\Z => X\Z
def RBx(lt , rt):
    if type(lt)!=list or type(rt)!=list:
        return None
    elif rt[0].value()==BwdApp.value() and lt[0].value()==FwdApp.value() and term_eq(rt[1],lt[2]):
        return [BwdApp,lt[1],rt[2]]
    if type(lt)!=list or type(rt)!=list:
        return None
    elif lt[0].value()!="forall" and rt[0].value()!="forall":
        return None
    elif polymorphic(lt) or polymorphic(rt):
        return None
    else:
        var1,var2,var3 = next(gensym),next(gensym),next(gensym)
        oldvars = []
        if lt[0].value()=="forall":
            NB = lt
            LB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            LB = lt
        if rt[0].value()=="forall":
            NB = rt
            RB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            RB = rt
            mgu = unify([([FwdApp , var1, var2] ,LB) , ([BwdApp , var2, var3] , RB)] , oldvars+[var1,var2,var3])
            if mgu!=None and (var1.value() in mgu) and (var3.value() in mgu):
                 NB = [BwdApp , mgu[var1.value()] , mgu[var3.value()]]
                 nvars = findvars(NB , oldvars+[var1,var2,var3])
                 if len(nvars)>0:
                     NB = [FORALL , nvars , NB]
                 return NB
    return None


#-- Y\Z X\Y => X\Z
def LB(lt , rt):
    if type(lt)!=list or type(rt)!=list:
        return None
    elif rt[0].value()==BwdApp.value() and lt[0].value()==BwdApp.value() and term_eq(lt[1],rt[2]):
        return [BwdApp,rt[1],lt[2]]
    if type(lt)!=list or type(rt)!=list:
        return None
    elif lt[0].value()!="forall" and rt[0].value()!="forall":
        return None
    elif polymorphic(lt) or polymorphic(rt):
        return None
    else:
        var1,var2,var3 = next(gensym),next(gensym),next(gensym)
        oldvars = []
        if lt[0].value()=="forall":
            NB = lt
            LB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            LB = lt
        if rt[0].value()=="forall":
            NB = rt
            RB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            RB = rt
            mgu = unify([([BwdApp , var2, var3] ,LB) , ([BwdApp , var1, var2] , RB)] , oldvars+[var1,var2,var3])
            if mgu!=None and (var1.value() in mgu) and (var3.value() in mgu):
                 NB = [BwdApp , mgu[var1.value()] , mgu[var3.value()]]
                 nvars = findvars(NB , oldvars+[var1,var2,var3])
                 if len(nvars)>0:
                     NB = [FORALL , nvars , NB]
                 return NB
    return None


#-- Y/Z X\Y ⇒ X/Z
def LBx(lt , rt):
    if type(lt)!=list or type(rt)!=list:
        return None
    elif lt[0].value()==FwdApp.value() and rt[0].value()==BwdApp.value() and term_eq(lt[1],rt[2]):
        return [FwdApp,rt[1],lt[2]]
    elif lt[0].value()!="forall" and rt[0].value()!="forall":
        return None
    elif polymorphic(lt) or polymorphic(rt):
        return None
    else:
        var1,var2,var3 = next(gensym),next(gensym),next(gensym)
        oldvars = []
        if lt[0].value()=="forall":
            NB = lt
            LB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            LB = lt
        if rt[0].value()=="forall":
            NB = rt
            RB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            RB = rt
            mgu = unify([([FwdApp , var2, var3] ,LB) , ([BwdApp , var1, var2] , RB)] , oldvars+[var1,var2,var3])
            if mgu!=None and (var1.value() in mgu) and (var3.value() in mgu):
                 NB = [FwdApp , mgu[var1.value()] , mgu[var3.value()]]
                 nvars = findvars(NB , oldvars+[var1,var2,var3])
                 if len(nvars)>0:
                     NB = [FORALL , nvars , NB]
                 return NB
    return None

"""
Starling bird/functional substitution
(X/Y)/Z Y/Z => X/Z
S f g x = f x (g x)
"""
def RS(lt, rt):
    if type(lt)!=list or type(rt)!=list or type(lt[1])!=list:
        return None
    elif (lt[0],lt[1][0],rt[0])==(FwdApp,FwdApp,FwdApp) and term_eq(lt[1][2] , rt[1]) and term_eq(lt[2] , rt[2]):
        return [FwdApp,lt[1][1],rt[2]]
    if type(lt)!=list or type(rt)!=list:
        return None
    elif lt[0].value()!="forall" and rt[0].value()!="forall":
        return None
    elif polymorphic(lt) or polymorphic(rt):
        return None
    else:
        var1,var2,var3 = next(gensym),next(gensym),next(gensym)
        oldvars = []
        if lt[0].value()=="forall":
            NB = lt
            LB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            LB = lt
        if rt[0].value()=="forall":
            NB = rt
            RB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            RB = rt
            mgu = unify([([FwdApp , [FwdApp , var1, var2] ,var3] ,LB) , ([FwdApp , var2, var3] , RB)] , oldvars+[var1,var2,var3])
            if mgu!=None and (var1.value() in mgu) and (var3.value() in mgu):
                 NB = [FwdApp , mgu[var1.value()] , mgu[var3.value()]]
                 nvars = findvars(NB , oldvars+[var1,var2,var3])
                 if len(nvars)>0:
                     NB = [FORALL , nvars , NB]
                 return NB
    return None



#-- Y\Z (X\Y)\Z => X\Z
def LS(lt, rt):
    if type(lt)!=list or type(rt)!=list or type(rt[1])!=list:
        return None
    elif (lt[0],rt[1][0],rt[0])==(BwdApp,BwdApp,BwdApp) and term_eq(lt[1] , rt[1][2]) and term_eq(lt[2] , rt[2]):
        return [BwdApp,rt[1][1],lt[2]]
    if type(lt)!=list or type(rt)!=list:
        return None
    elif lt[0].value()!="forall" and rt[0].value()!="forall":
        return None
    elif polymorphic(lt) or polymorphic(rt):
        return None
    else:
        var1,var2,var3 = next(gensym),next(gensym),next(gensym)
        oldvars = []
        if lt[0].value()=="forall":
            NB = lt
            LB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            LB = lt
        if rt[0].value()=="forall":
            NB = rt
            RB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            RB = rt
            mgu = unify([([BwdApp , [BwdApp , var1, var2] ,var3] ,RB) , ([BwdApp , var2, var3] , LB)] , oldvars+[var1,var2,var3])
            if mgu!=None and (var1.value() in mgu) and (var3.value() in mgu):
                 NB = [BwdApp , mgu[var1.value()] , mgu[var3.value()]]
                 nvars = findvars(NB , oldvars+[var1,var2,var3])
                 if len(nvars)>0:
                     NB = [FORALL , nvars , NB]
                 return NB
    return None



#-- (X/Y)\Z Y\Z => X\Z
def RSx(lt , rt):
    if type(lt)!=list or type(rt)!=list or type(lt[1])!=list:
        return None
    elif (lt[0],lt[1][0],rt[0])==(BwdApp,FwdApp,BwdApp) and term_eq(lt[1][2] , rt[1]) and term_eq(lt[2] , rt[2]):
        return [BwdApp,lt[1][0],rt[2]]
    if type(lt)!=list or type(rt)!=list:
        return None
    elif lt[0].value()!="forall" and rt[0].value()!="forall":
        return None
    elif polymorphic(lt) or polymorphic(rt):
        return None
    else:
        var1,var2,var3 = next(gensym),next(gensym),next(gensym)
        oldvars = []
        if lt[0].value()=="forall":
            NB = lt
            LB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            LB = lt
        if rt[0].value()=="forall":
            NB = rt
            RB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            RB = rt
            mgu = unify([([BwdApp , [FwdApp , var1, var2] ,var3] ,LB) , ([BwdApp , var2, var3] , RB)] , oldvars+[var1,var2,var3])
            if mgu!=None and (var1.value() in mgu) and (var3.value() in mgu):
                 NB = [BwdApp , mgu[var1.value()] , mgu[var3.value()]]
                 nvars = findvars(NB , oldvars+[var1,var2,var3])
                 if len(nvars)>0:
                     NB = [FORALL , nvars , NB]
                 return NB
    return None



#-- Y/Z (X\Y)/Z => X/Z
def LSx(lt, rt):
    if type(lt)!=list or type(rt)!=list or type(rt[1])!=list:
        return None
    elif (lt[0],rt[1][0],rt[0])==(FwdApp,BwdApp,FwdApp) and term_eq(lt[1] , rt[1][2]) and term_eq(lt[2] , rt[2]):
        return [FwdApp,rt[1][0],lt[2]]
    if type(lt)!=list or type(rt)!=list:
        return None
    elif lt[0].value()!="forall" and rt[0].value()!="forall":
        return None
    elif polymorphic(lt) or polymorphic(rt):
        return None
    else:
        var1,var2,var3 = next(gensym),next(gensym),next(gensym)
        oldvars = []
        if lt[0].value()=="forall":
            NB = lt
            LB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            LB = lt
        if rt[0].value()=="forall":
            NB = rt
            RB = NB[2]
            oldvars = NB[1] + oldvars
        else:
            RB = rt
            mgu = unify([([FwdApp , [BwdApp , var1, var2] ,var3] ,RB) , ([FwdApp , var2, var3] , LB)] , oldvars+[var1,var2,var3])
            if mgu!=None and (var1.value() in mgu) and (var3.value() in mgu):
                 NB = [FwdApp , mgu[var1.value()] , mgu[var3.value()]]
                 nvars = findvars(NB , oldvars+[var1,var2,var3])
                 if len(nvars)>0:
                     NB = [FORALL , nvars , NB]
                 return NB
    return None


#-- X => forall a.a/(a\X)
def RT(t):
   if type(t)!=list and t.value()=="NP":
      var = next(gensym)
      return [FORALL , [var] , [FwdApp , var , [BwdApp,var,t]]]
   return None


#-- X => forall.a\(a/X)
def LT(t):
   assert(type(t)==list or type(t)==Symbol),repr(t)
   if (type(t)!=list and t.value() in ["NP","PP","S"]) or t==[BwdApp,Symbol("S"),Symbol("NP")]:
      var = next(gensym)
      return [FORALL , [var] , [BwdApp , var , [FwdApp,var,t]]]
   return None


#-- CONJ X => X\X
def Conj(lt,rt):
    if type(lt)!=list and lt.value()=="CONJ":
        return [BwdApp , rt, rt]


#-- NP S/NP => NP
#-- This combinator is non-standard
#-- used instead of unary type changing rule "S[dcl]/NP => NP\NP"
def Swap(lt,rt):
    if lt==Symbol("NP") and rt==[FwdApp,Symbol("S"),Symbol("NP")]:
         return Symbol("NP")



"""
Permuted functional composition rules
>CB rule   Y/Z:g  X/Y:f => X/Z:\a->f(g a)
<CB rule   X\Y:f  Y\Z:g => X\Z:\a->f(g a)
"""
def RCB(lt , rt):
    return RB(rt , lt)


#-- X\Y Y\Z => X\Z
def LCB(lt , rt):
    return LB(rt , lt)


"""
In English, I do not use >Bx rule(RBx) , >S rule(RS) , <S rule(LS)
"""
combinators = [LApp,RApp,LB,RB,LBx,LSx,RSx,LT,RT,Conj,Swap]
def CCGChart(tokens,lexicon):
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
   N = len(tokens)
   for n in range(N):
      for m in range(n,N):
          chart[(n,m)] = [(c,tuple()) for c in lexicon.get(tokens[n:m+1] , [])]
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
   if not all([any([len(chart.get((m0,m1),[]))>0 for (m0,m1) in chart.keys() if m0<=n and n<=m1]) for n in range(N)]):
      return chart
   #-- start CYK parsing
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
        if len(toklist)==1:
            w = toklist[0]
            cats = self.static_dics.get(w , [])
            cats.extend( self.static_dics.get(w.lower() , []) )
            if re.match(r'\d+$',w)!=None:
                cats.append( "NP" )
                cats.append( "NP/N[pl]" )
                cats.append( "NP/N" )
            elif re.match(r'\d+th$',w)!=None:
                cats.extend( ["NP", "NP/N[pl]" , "NP/N" , "N/N" , "N[pl]/N[pl]"] )
            if w[-1]=="'" and w[-2]=="s": #-- e.g. Americans'
                cats.extend(["NP/N[pl]" , "NP/N"])
            if len(cats)==0 and w[0].isupper():  #-- guess
                cats.extend( ["NP" , "NP/N" , "N/N", "NP/N[pl]"] )
        else:
            cats = self.static_dics.get(" ".join(toklist) , [])
            if len(cats)==0:
                cats = self.static_dics.get(" ".join(toklist).lower() , [])
        assert(type(cats)==list),toklist
        return ([lexparse(b) for b in set([c for c in cats if isinstance(c,basestring)])]+[c for c in cats if not isinstance(c,basestring)])
    def __setitem__(self,tok,cats):
        self.static_dics[tok] = cats
    def has_key(self,tok):
        return (tok in self.static_dics)
    def get(self,toklist,defval):
        return self.__getitem__(toklist)




def catname(t):
    def _catname(t):
        if type(t)!=list:
            return t.value()
        elif t[0]==FwdApp:
            return "({0}/{1})".format(_catname(t[1]) , _catname(t[2]))
        elif t[0]==BwdApp:
            return "({0}\\{1})".format(_catname(t[1]) , _catname(t[2]))
        elif t[0]==FORALL:
            return "(\\{0}->{1})".format(",".join([x.value() for x in t[1]]) , _catname(t[2]))
        else:
            assert(False),t
    tmp = _catname(t)
    if tmp[0]=="(" and tmp[-1]==")":
        return tmp[1:-1]
    else:
        return tmp



terminators = ["ROOT","S","S[q]","S[wq]","S[imp]"]
def testrun(tokens,lexicon):
   def decode(left_start , right_end , path , chart):
       if len(path)==0:
          return " ".join(tokens[left_start:right_end+1])
       elif len(path)==2:
          idx = path[0]
          cat1,path1 = chart[(left_start,right_end)][idx]
          return (catname(cat1) , decode(left_start,right_end , path1 , chart))
       else:
          assert(len(path)==4),path
          idx1,idx2,left_end,_ = path
          right_start = left_end+1
          cat1,path1 = chart[(left_start,left_end)][idx1]
          cat2,path2 = chart[(right_start,right_end)][idx2]
          return (path[3],(catname(cat1),decode(left_start,left_end , path1 , chart)) , (catname(cat2),decode(right_start,right_end , path2, chart)))
   chart = CCGChart(tokens,lexicon)
   print("test run : tokens={0}".format(str(tokens)))
   for (topcat,path) in chart.get((0,len(tokens)-1) ,[]):
       if type(topcat)!=list and topcat.value() in terminators:
           print( (topcat.value() , decode(0 , len(tokens)-1 , path , chart)) )
           print("")
   print("")


def tagger(tokens,lexicon):
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
              ret.append( (right_start,right_end , cat2) )
          else:
              ret.extend( decode(right_start,right_end ,path2, chart) )
          return ret
   chart = CCGChart(tokens,lexicon)
   for (topcat,path) in chart.get((0,len(tokens)-1) ,[]):
       if type(topcat)!=list and topcat.value() in terminators:
           tagsets = decode(0 , len(tokens)-1 , path , chart)
           tagsets.sort()
           tmp = []
           for (s,e,c) in tagsets:
                tmp.append( (" ".join(tokens[s:e+1]),catname(c)) )
           yield tmp




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






if __name__=="__main__":
   import os,sys
   dic1 = os.path.join(os.path.dirname(os.path.abspath(__file__)) , ".." , "ccglex.en")
   dic2 = os.path.join(os.path.dirname(os.path.abspath(__file__)) , ".." , "phrases.en")
   lexicon = Lexicon(dic1,dic2)
   lexicon['.'] = ["ROOT\\S","ROOT\\S[imp]"]
   lexicon['?'] = ["ROOT\\S[q]","ROOT\\S[wq]"]
   var = next(gensym)
   lexicon[","] = [ "S/S" ,"(S/S)\\VP[pss]" , "(S/S)\\VP[ing]"]
   for line in sys.stdin:
       line = line.strip()
       if len(line)==0:continue
       for tokens in tokenize(line):
           testrun(tokens,lexicon)
       print ("")

