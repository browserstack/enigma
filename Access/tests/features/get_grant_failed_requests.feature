Feature: test get_grant_fail_requests

    Scenario: Retrieving all grant failure requests
        Given there are grant failure requests in the database
        When the get_grant_failed_requests method is called
        Then it should return a context containing all grant failure requests sorted by requested_on date in descending order

    Scenario: Handling errors
        Given an error occurs while executing the method
        When the get_grant_failed_requests method is called
        Then it should return an error response with details of the error.
