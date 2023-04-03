Feature: SlackAccess Grant
    Slack Access grant for workspace feature

    Scenario: Grant Slack Workspace Access Success
        Given A user email
        And user in not invited earlier for workspace
        And Access can be granted to user for slack
        When I pass approval request
        Then return value should be True

    Scenario: Grant Slack Workspace Access Fails
        Given A user email
        And user in not invited earlier for workspace
        And Access cannot be granted to user for slack
        When I pass approval request
        Then return value should be False
