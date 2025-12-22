Feature: Cross-Platform Setup
  As a developer on any OS
  I want to install claude-victor
  So that I can use it on MacOS or Windows

  Scenario: Fresh install on MacOS
    Given I am on MacOS
    And GitHub CLI is not installed
    And Python 3.9+ is available
    When I run "make install"
    Then GitHub CLI is installed via Homebrew
    And the installation succeeds without errors

  Scenario: Setup Python environment on MacOS
    Given I am on MacOS
    And I have cloned the claude-victor repository
    When I run "make setup-dev"
    Then Python dependencies are installed
    And pytest is available
    And behave is available
    And the package is installed in development mode

  Scenario: Fresh install on Windows
    Given I am on Windows
    And GitHub CLI is not installed
    And Python 3.9+ is available
    When I run "make install"
    Then GitHub CLI is installed via winget
    And the installation succeeds without errors

  Scenario: Setup Python environment on Windows
    Given I am on Windows
    And I have cloned the claude-victor repository
    When I run "make setup-dev"
    Then Python dependencies are installed
    And pytest is available
    And behave is available

  Scenario: Verify relative paths in configuration
    Given I have the claude-victor repository
    When I inspect all configuration files
    Then no absolute paths are found
    And all paths use forward slashes or os.path.join
    And the configuration is portable

  Scenario: Makefile targets work on both platforms
    Given I have the claude-victor repository
    When I run "make --dry-run test-all"
    Then all required targets are defined
    And no platform-specific errors occur

  Scenario: Plugin can be registered on any platform
    Given I am on a supported platform
    And Claude Code is installed
    When I register the claude-victor plugin
    Then the plugin is recognized by Claude Code
    And the /plan-victor command is available

  Scenario: Run unit tests after setup
    Given I have completed "make setup-dev"
    When I run "make test-unit"
    Then all unit tests pass
    And test output shows coverage information

  Scenario: Run BDD tests after setup
    Given I have completed "make setup-dev"
    When I run "make test-bdd"
    Then all BDD scenarios pass
    And Gherkin feature files are executed

  Scenario: Full verification check
    Given I have completed the setup
    When I run "make verify"
    Then all artifact checks pass
    And the output shows checkmarks for each item
    And no failures are reported
