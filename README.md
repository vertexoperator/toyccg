Toy CCG Parser
==============

OVERVIEW
--------

- This is a compact CCG Parser.
- It is written in pure python using only python standard libs.
- It does not require any machine learning at all.
- It supports English and Japanese currently. 
- It can support any other natural languages.


Python 2.x or 3.x
-----------------
toyccg is tested with

- CPython 2.7.5
- pypy3  2.4.0 (Python3.2.5 compatible)


USAGE
-----

`python toyccg/ccgparser.py < sentences.txt`


TODO
----

* brush up lexicons

* apply to other languages(e.g. Japanese,etc.)

* semantic parsing support

* supporting unsupervised inference of syntactic categories

* add setup.py

* add document


References
----------

* The Syntactic Process (MIT Press, Mark Steedman, 2000)

* 日本語文法の形式理論：活用体系・統語構造・意味合成 (くろしお出版, 戸次大介, 2010)

* Efficient Normal-Form Parsing for Combiantory Categorial Grammar (Jason Eisner, 1996)

* Normal-form parsing for Combinatory Categorial Grammars with generalized composition and type-raising (2010)

* Unsupervised syntax learning with categorial grammars using inference rules (2009)

* A* CCG Parsing with a Supertag-factored Model (2014)
([paper](http://www.aclweb.org/anthology/D14-1107))


