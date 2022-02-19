# https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository
name: Bug Report
description: File a bug report
title: "[Bug]: "
labels: ["bug"]
assignees:
- octocat
body:
- type: markdown
  attributes:
    value: |
      I think I found a problem...
- type: input
  id: contact
  attributes:
    label: Contact Details
    description: How can we get in touch with you if we need more info?
    placeholder: ex. email@example.com
  validations:
    required: false
- type: textarea
  id: what-happened
  attributes:
    label: What happened?
    description: Also tell us, what did you expect to happen?
    placeholder: Tell us what you see!
    value: "A bug happened!"
  validations:
    required: true
- type: dropdown
  id: version
  attributes:
    label: Version
    description: What version of our software are you running?
    options:
    - 1.6.34
    - 1.6.33
    - 1.6.32
    - 1.6.31
    - 1.6.30
  validations:
    required: true
- type: dropdown
  id: browsers
  attributes:
    label: What browsers are you seeing the problem on?
    multiple: true
    options:
    - Firefox
    - Chrome
    - Safari
    - Microsoft Edge
- type: textarea
  id: logs
  attributes:
    label: Relevant log output
    description: Please copy and paste any relevant log output. This will be automatically
      formatted into code, so no need for backticks.
    render: shell
- type: checkboxes
  id: terms
  attributes:
    label: Code of Conduct
    description: By submitting this issue, you agree to follow our [Code of Conduct](https://example.com)
    options:
    - label: I agree to follow this project's Code of Conduct
      required: true
