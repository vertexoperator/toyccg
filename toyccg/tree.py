# -*- coding:utf-8 -*-

class Tree:
    def __init__(self,node,*args):
        assert(type(node)==str)
        self.node = node
        self.children = args
    def __unicode__(self):
        return (u"({0} {1})".format(self.node , u" ".join([unicode(c) for c in self.children])))


class Leaf:
    def __init__(self , catname , token):
       self.catname = catname
       self.token = token
    def __unicode__(self):
       return (u"[{1}:{0}]".format(self.catname , self.token))


