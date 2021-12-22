---
name: Bug Report
description: File a ciscoconfparse bug report
title: "[Bug]: "
labels: ["bug", "triage"]
assignees:
  - mpenning

body:
  - type: markdown
    attributes:
      value: |
      %%%
      This issue tracker is a tool to address bugs in ciscoconfparse itself. 
      Please use Stack Overflow for questions about your own code.

      Replace this comment with a clear outline of what the bug is.
      %%%

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
      placeholder: Tell us what you saw!
      value: |
      %%%
      Describe the expected behavior that should have happened but didn't.
      %%%
    validations:
      required: true

  - type: textarea
    id: logs
    attributes:
      label: Relevant log output
      description: Please copy and paste any relevant log output. This will be automatically formatted into code, so no need for backticks.
      render: shell

  - type: checkboxes
    id: terms
    attributes:
      label: Code of Conduct
      description: By submitting this issue, you agree to follow our [Code of Conduct](
      options:
        - label: I agree to follow this project's Code of Conduct
          required: true




Environment:
- Operating System:
- Python version:
- ciscoconfparse version:
