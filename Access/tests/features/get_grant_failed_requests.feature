Feature: test get_grant_fail_requests

    Scenario 1: Retrieving all grant failure requests
                Given there are grant failure requests in the database
                When the get_grant_failed_requests method is called
                Then it should return a context containing all grant failure requests sorted by requested_on date in descending order
                And the heading should be "Grant Failures"

    Scenario 2: Filtering grant failure requests by username
                Given there are grant failure requests in the database
                And there is at least one request associated with a specific username
                When the get_grant_failed_requests method is called with a username parameter
                Then it should return a context containing all grant failure requests associated with that username sorted by requested_on date in descending order
                And the heading should be "Grant Failures"

      Scenario 3: Filtering grant failure requests by access type
                  Given there are grant failure requests in the database
                  And there is at least one request associated with a specific access type
                  When the get_grant_failed_requests method is called with an access_type parameter
                  Then it should return a context containing all grant failure requests associated with that access type sorted by requested_on date in descending order
                  And the heading should be "Grant Failures"

      Scenario 4: Handling errors
                  Given an error occurs while executing the method
                  When the get_grant_failed_requests method is called
                  Then it should return an error response with details of the error.
