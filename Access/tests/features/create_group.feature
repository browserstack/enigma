Feature: Group
    A collection of users

    Scenario: Create a new Group Success
        Given A group name
        And It does not exists in DB
        And The group can be saved
        And Requester can be added to the group by default
        And Notification can be sent
        When I pass request
        Then I should a get a success message

    Scenario: Create a new Group with duplicate name
        Given A group name
        And It already exists
        When I pass request
        Then I should get an error message