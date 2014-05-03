What's new in version 1.0.0
===========================

In the seven years since I first wrote :mod:`ciscoconfparse`, my understanding 
of Python improved and I found many missing things. As such, I started a major 
rewrite to :mod:`ciscoconfparse` version 0.9; the rewrite introduced several 
important changes:

- Python3 compatibility
- Major improvement in config parsing speed
- Much better unit-test coverage
- Too many bugfixes to count
- New feature - :mod:`ciscoconfparse` inserts, deletes and appends config lines
- Rearchitected the library, with an eye towards more future improvements
- Revisions in scripting flow.  All users are encouraged to use :class:`~models_cisco.IOSCfgLine()` objects whenever possible.  Typically, you'll start by matching them with :func:`~ciscoconfparse.CiscoConfParse.find_objects()`.  Working directly with :class:`~models_cisco.IOSCfgLine()` objects makes your scripts less complicated and it also makes them faster than using legacy :mod:`ciscoconfparse` syntax.

