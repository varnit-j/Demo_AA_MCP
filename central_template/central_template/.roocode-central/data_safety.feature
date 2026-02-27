Feature: Data safety for Roo Code usage
  As the Coforge Security Team
  We want Roo Code and developers to follow data safety rules
  So that no sensitive production data is exposed to external providers

  Background:
    Given the central data policy is loaded from ".roocode-central/org-data-policy.yml"

  Scenario: Prohibit sending production data in prompts
    When a developer provides a prompt to Roo Code
    Then the prompt must not contain production customer data
    And the prompt must not contain secrets or credentials

  Scenario: Enforce redaction at the gateway
    When Roo Code sends a request through the internal gateway
    Then the gateway must redact configured sensitive fields
    And the redacted payload must be the only content sent to external providers

  Add More Scenarios as per policy....
