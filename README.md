Toy CCG Parser
==============

OVERVIEW
--------

compact CCG Parser


Python 2.x or 3.x
-----------------
toyccg is tested with

- CPython 2.7.5
- pypy3  2.4.0 (Python3.2.5 compatible)


USAGE
-----

`python -m toyccg.english < sentences.txt`

`python -m toyccg.japanese < sentences.ja.txt`


TODO
----

* brush up lexicons

* apply to other languages(e.g. Japanese,etc.)

* semantic parsing support

* supporting unsupervised inference of syntactic categories

* add setup.py

* solve CCG grammatical inference


References
----------

* The Syntactic Process (MIT Press, Mark Steedman, 2000)

* 日本語文法の形式理論：活用体系・統語構造・意味合成 (くろしお出版, 戸次大介, 2010)

* Efficient Normal-Form Parsing for Combiantory Categorial Grammar (Jason Eisner, 1996)

* Normal-form parsing for Combinatory Categorial Grammars with generalized composition and type-raising (2010)

* Unsupervised syntax learning with categorial grammars using inference rules (2009)

* A* CCG Parsing with a Supertag-factored Model (2014)
([paper](http://www.aclweb.org/anthology/D14-1107))


