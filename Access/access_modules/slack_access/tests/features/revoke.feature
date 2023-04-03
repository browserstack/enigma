Feature: SlackAccessRevoke
    Slack Access module revoke access feature

    Scenario: Revoke User Access to a workspace success
        Given A user email
        And Access will be revoked
        When I pass revoke request
        Then return value should be True


    Scenario: Revoke User Access to a workspace fails
        Given A user email
        And Access can not be revoked
        When I pass revoke request
        Then return value should be False

