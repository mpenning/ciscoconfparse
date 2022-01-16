# Contribution Guidelines

Before opening any [ciscoconfparse][1] issues or proposing any pull
requests, please read this document completely.

To get the greatest chance of helpful responses, please also observe the
following additional notes:

## Questions

The [GitHub issue tracker][3] is for *bug reports* and *feature requests*.
Please do not use it to ask questions about how to use [ciscoconfparse][1].
These questions should instead be directed to [Stack Overflow][5]. Make sure
that your question is tagged with the [ciscoconfparse][4] tag when asking it on
[Stack Overflow][5], to ensure that it is answered promptly and accurately.

## Good Bug Reports

Please be aware of the following things when filing bug reports:

1. Avoid raising duplicate issues. *Please* use the [GitHub issue search][3]
   feature to check whether your bug report or feature request has been
   discussed in the past. Duplicate bug reports and feature requests are a
   non-trivial maintenance burden on the resources of the project. If it is
   clear from your report that you would have struggled to find the original,
   that's ok, but if searching for a selection of words in your issue title
   would have found the duplicate then the issue will likely be closed.
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
     differently

   If you do not provide all of these things, it could take us much longer to
   fix your problem. If we ask you to clarify these and you never respond, we
   may close your issue without fixing it.

## Pull Requests

1. Please email Mike Pennington before writing a PR.  We might not be
   interested in the feature, or already have plans to fix an issue.
   Unsolicited PRs may be closed.

2. PRs must include tests for the functionality being added, or bugs being
   fixed.  Needless to say, your PR itself must not fail existing tests.

  [1]: https://github.com/mpenning/ciscoconfparse
  [2]: https://github.com/mpenning/ciscoconfparse/issues/new/choose
  [3]: https://github.com/mpenning/ciscoconfparse/issues
  [4]: https://stackoverflow.com/questions/tagged/ciscoconfparse?tab=Newest
  [5]: https://stackoverflow.com/
