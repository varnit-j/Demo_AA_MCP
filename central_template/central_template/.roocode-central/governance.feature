Feature: Organization wide Roo Code governance
  As an Coforge AI Platform and Security team
  We want Roo Code to follow central governance rules
  So that generated code is secure, compliant, and consistent

  Background:
    Given central configuration is loaded from ".roocode-central/org-models.yml"
    And central rules are loaded from ".roocode-central/org-rules.yml"
    And the central data policy is loaded from ".roocode-central/org-data-policy.yml"
    And the central CI policy is loaded from ".roocode-central/org-ci-policy.yml"

  Scenario: Roo Code must not modify locked central files
    When Roo Code generates or edits code in any repository
    Then it must not modify any file under the ".roocode-central/" directory
    And it must not modify any file whose meta section has "locked: true"

  Scenario: Roo Code must use only allowed models through the gateway
    When Roo Code prepares to call a language model
    Then it must choose a model from the allowed central models list
    And it must route the request through the configured internal gateway
    And it must not call a public provider endpoint directly

  Scenario: Roo Code must honor central CI requirements
    When Roo Code opens or updates a pull request
    Then the pull request must require all central CI checks to pass
    And the pull request must require at least the minimum number of approvals
