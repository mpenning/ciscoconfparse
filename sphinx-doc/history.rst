=============================
History and Python Apologetic
=============================

:class:`~ciscoconfparse.CiscoConfParse()` was born from audit requirements.  When I first built the module, I was contracting for a company with hundreds of devices; PCI compliance obligated us to perform security audits on the configs and management wanted it done quarterly.  Our company was supposed to have an automated tool, but nobody could get it to work.  I offered to build an audit and diff script instead of our entire team spending hundreds of man-hours on a manual task each quarter.

At first, I tried using a canned Perl config-parsing library; it was great when it worked, but the library suffered from mysterious crashes on certain configs.  I tried auditing the troublesome configs manually, but dealing with the crashes put me behind schedule.  I reached a point where I realized the audit results were going to be late if something didn't change, so I wrote the author for help, but he literally said that he wasn't really sure how the library works. [#]_ 

With the deadline approaching, I wound up spending a full weekend of my own time writing my first endeavor in Python.  It worked so well, I found myself building similar tools for other accounts that weren't even mine.  After more work, I ultimately I published this as open-source software.  ciscoconfparse is available to anyone who wants to invest a little effort on the front-end.  Many companies in the US and Europe are already using it to audit their configs; I only ask that you drop me a line [#]_ and let me know if you like it and how I can improve the library.

.. [#] *This is not so much a slam on the module or author; it's part of Perl syntax.  After six months, most people have a hard time remembering the meaning of those quirky idioms that make their code tick.  Perl's syntax, and its convoluted error messages are why I left ten previous years of Perl experience behind me, and started fresh with Python in 2007.*

.. [#] *mike [~at~] pennington [~dot~] net*
