# Contribution Guidelines

Before opening any [ciscoconfparse][1] issues or proposing any pull
requests, please read this document completely.

To get the greatest chance of helpful responses, please also observe the
following.

## Contributions

### Bug Reports

Please be aware of the following things when filing bug reports:

1. Avoid raising duplicate issues. *Please* use the [GitHub issue search][3]
   feature to check whether your bug report or feature request has been
   discussed in the past. Duplicate bug reports and feature requests are a
   non-trivial maintenance burden on the resources of the project. If it is
   clear from your report that you could not find the original, no worries.
   However, we will usually close duplicate issues.
2. When filing bug reports about exceptions or tracebacks, please include the
   *complete* traceback. Partial tracebacks, or just the exception text, are
   not helpful. Issues that do not contain complete tracebacks may be closed
   without warning.
3. Make sure you provide a suitable amount of information to work with. This
   means you should provide:

   - Guidance on **how to reproduce the issue**. Ideally, this should be a
     *small* code sample that can be run immediately by the maintainers.
     Failing that, let us know what you're doing, how often it happens, what
     environment you're using, etc. Be thorough: it prevents us needing to ask
     further questions.
   - Tell us **what you expected to happen**. When we run your example code,
     what are we expecting to happen? What does "success" look like for your
     code?
   - Tell us **what actually happens**. It's not helpful for you to say "it
     doesn't work" or "it fails". Tell us *how* it fails: do you get an
     exception? A hang? How was the actual result different from your expected
     result?
   - Tell us **what version of [ciscoconfparse][1] you're using**, and
     **how you installed it**. Different versions of [ciscoconfparse][1] behave
     differently.  If possible, you should check the latest ciscoconfparse
     release before filing a new bug.

   If you do not provide sufficient detail, it could take us much longer to
   fix your problem.


### Pull Requests

1. Please email Mike Pennington before writing a PR.  We might not be
   interested in the feature, or already have plans to fix an issue.
   Unsolicited PRs may be closed.

2. PRs must include tests for the functionality being added, or bugs being
   fixed.  Needless to say, your PR itself must not fail existing tests.

## Usage Questions

The [GitHub issue tracker][3] is for *bug reports* and *feature requests*.
Please do not use it to ask usage questions about how to use
[ciscoconfparse][1] or how to fix your scripts.  [Stack Overflow][4] or
[Reddit r/networking][5] are good examples of places to ask questions. If
you ask on [Stack Overflow][4], please make sure that your question is
tagged with the [ciscoconfparse tag][4].

## Anti-social behavior

   Harrassment (in any form, or for any reason), intimidation, trolling,
   excessive drama, insults, rudeness, stalking, libel, or other abusive
   behaviors are not welcome for any reason.

## Content policy

   The project maintainers may edit, close, or delete content at their own
   discretion.


  [1]: https://github.com/mpenning/ciscoconfparse
  [2]: http://127.0.0.1/
  [3]: https://github.com/mpenning/ciscoconfparse/issues
  [4]: https://stackoverflow.com/questions/ask?title=How%20do%20I&tags=ciscoconfparse+python
  [5]: https://reddit.com/r/networking
